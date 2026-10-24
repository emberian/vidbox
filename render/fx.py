"""Effects. Each op: fn(img, alpha, p, t, state) -> (img, alpha).

img: float32 (h, w, 3) in 0..1. alpha: float32 (h, w). p: params already evaluated at t
(constants pass through). state: per-layer dict that persists across frames (for trails).
`amount` (default 1) on any op mixes the result over its input. Spec in TIMELINE.md.
"""
import math

import cv2
import numpy as np

from noise import fbm

LUMA = np.array([0.299, 0.587, 0.114], np.float32)
OPS = {}


def op(name):
    def reg(f):
        OPS[name] = f
        return f
    return reg


def luma(img):
    return img @ LUMA


def smoothstep(e0, e1, x):
    u = np.clip((x - e0) / max(e1 - e0, 1e-6), 0, 1)
    return u * u * (3 - 2 * u)


@op("posterize")
def posterize(img, a, p, t, st):
    n = max(2.0, p.get("levels", 4))
    return np.round(img * (n - 1)) / (n - 1), a


@op("chroma")
def chroma(img, a, p, t, st):
    px, ang = p.get("px", 6), math.radians(p.get("angle", 0))
    if abs(px) < 0.25:
        return img, a
    h, w = img.shape[:2]
    out = img.copy()
    for c, sgn in ((0, 1), (2, -1)):
        M = np.float32([[1, 0, sgn * px * math.cos(ang)], [0, 1, sgn * px * math.sin(ang)]])
        out[..., c] = cv2.warpAffine(img[..., c], M, (w, h), borderMode=cv2.BORDER_REFLECT)
    return out, a


@op("noise")
def noise(img, a, p, t, st):
    h, w = img.shape[:2]
    kw = dict(scale=p.get("scale", 200), octaves=p.get("octaves", 4), speed=p.get("speed", 0.3))
    seed = int(p.get("seed", 0))
    color = p.get("color", [1, 1, 1])
    if color == "rgb":
        n = np.stack([fbm(h, w, t, seed=seed + i, **kw) for i in range(3)], -1)
    else:
        n = fbm(h, w, t, seed=seed, **kw)[..., None] * np.asarray(color, np.float32)
    mode = p.get("mode", "overlay")
    if mode == "mul":
        out = img * n
    elif mode == "screen":
        out = 1 - (1 - img) * (1 - n)
    elif mode == "add":
        out = np.clip(img + n - 0.5, 0, 1)
    elif mode == "overlay":
        out = np.where(img < 0.5, 2 * img * n, 1 - 2 * (1 - img) * (1 - n))
    elif mode == "luma":   # noise replaces brightness, keeps hue
        L = luma(img)[..., None]
        out = np.clip(img / np.maximum(L, 1e-3) * n.mean(-1, keepdims=True), 0, 1)
    else:
        raise ValueError(f"noise mode {mode!r}")
    return out, a


@op("warp")
def warp(img, a, p, t, st):
    h, w = img.shape[:2]
    px = p.get("px", 20)
    if px < 0.25:
        return img, a
    kw = dict(scale=p.get("scale", 160), octaves=p.get("octaves", 3), speed=p.get("speed", 0.4))
    seed = int(p.get("seed", 0))
    # low-res displacement field, upsampled: smooth and cheap
    sh, sw = max(8, h // 4), max(8, w // 4)
    kw["scale"] = kw["scale"] / 4
    dx = cv2.resize((fbm(sh, sw, t, seed=seed, **kw) - 0.5) * 2 * px, (w, h))
    dy = cv2.resize((fbm(sh, sw, t, seed=seed + 7, **kw) - 0.5) * 2 * px, (w, h))
    gx, gy = np.meshgrid(np.arange(w, dtype=np.float32), np.arange(h, dtype=np.float32))
    mx, my = gx + dx, gy + dy
    img = cv2.remap(img, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    a = cv2.remap(a, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    return img, a


@op("threshold")
def threshold(img, a, p, t, st):
    v = smoothstep(p.get("level", 0.5) - p.get("soft", 0.02), p.get("level", 0.5) + p.get("soft", 0.02), luma(img))
    return np.repeat(v[..., None], 3, -1), a


@op("duotone")
def duotone(img, a, p, t, st):
    d = np.asarray(p.get("dark", [0, 0, 0]), np.float32)
    l = np.asarray(p.get("light", [1, 1, 1]), np.float32)
    return d + (l - d) * luma(img)[..., None], a


@op("invert")
def invert(img, a, p, t, st):
    return 1 - img, a


@op("hue")
def hue(img, a, p, t, st):
    hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)   # float: H in 0..360
    hsv[..., 0] = (hsv[..., 0] + p.get("deg", 0)) % 360
    return cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB), a


@op("sat")
def sat(img, a, p, t, st):
    L = luma(img)[..., None]
    return np.clip(L + (img - L) * p.get("factor", 1), 0, 1), a


@op("contrast")
def contrast(img, a, p, t, st):
    return np.clip((img - 0.5) * p.get("factor", 1) + 0.5 + p.get("bright", 0), 0, 1), a


@op("levels")
def levels(img, a, p, t, st):
    b, w = p.get("black", 0), p.get("white", 1)
    out = np.clip((img - b) / max(w - b, 1e-3), 0, 1)
    return out ** (1 / max(p.get("gamma", 1), 1e-3)), a


@op("lumakey")
def lumakey(img, a, p, t, st):
    return img, a * smoothstep(p.get("low", 0.1), p.get("high", 0.4), luma(img))


@op("kaleido")
def kaleido(img, a, p, t, st):
    h, w = img.shape[:2]
    n = max(2, int(p.get("segments", 6)))
    rot = math.radians(p.get("angle", 0))
    key = (h, w, n)
    if st.get("_kal_key") != key:
        gx, gy = np.meshgrid(np.arange(w, dtype=np.float32) - w / 2, np.arange(h, dtype=np.float32) - h / 2)
        st["_kal_key"], st["_kal_r"], st["_kal_th"] = key, np.hypot(gx, gy), np.arctan2(gy, gx)
    r, th = st["_kal_r"], st["_kal_th"] + rot
    wedge = 2 * math.pi / n
    m = np.mod(th, wedge)
    m = np.where(m > wedge / 2, wedge - m, m)   # mirror alternate halves
    mx = (r * np.cos(m) + w / 2).astype(np.float32)
    my = (r * np.sin(m) + h / 2).astype(np.float32)
    img = cv2.remap(img, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    a = cv2.remap(a, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    return img, a


@op("pixelate")
def pixelate(img, a, p, t, st):
    px = max(1, int(p.get("px", 8)))
    if px == 1:
        return img, a
    h, w = img.shape[:2]
    small = cv2.resize(img, (max(1, w // px), max(1, h // px)), interpolation=cv2.INTER_AREA)
    return cv2.resize(small, (w, h), interpolation=cv2.INTER_NEAREST), a


@op("blur")
def blur(img, a, p, t, st):
    s = p.get("px", 4)
    if s < 0.3:
        return img, a
    return cv2.GaussianBlur(img, (0, 0), s), a


@op("scanlines")
def scanlines(img, a, p, t, st):
    h = img.shape[0]
    per, dark = max(2, int(p.get("period", 4))), p.get("dark", 0.4)
    rows = 1 - dark * (np.arange(h) % per < per / 2)
    return img * rows[:, None, None].astype(np.float32), a


@op("echo")
def echo(img, a, p, t, st):
    prev = st.get("echo")
    if prev is not None and prev[0].shape == img.shape:
        d = p.get("decay", 0.85)
        img = np.maximum(img, prev[0] * d)
        a = np.maximum(a, prev[1] * d)
    st["echo"] = (img, a)
    return img, a


@op("tint")
def tint(img, a, p, t, st):
    c = np.asarray(p.get("color", [1, 0, 0]), np.float32)
    return img * c, a


def apply(fx_list, img, alpha, t, state, ev):
    """Run an fx stack. ev(param_spec) evaluates a signal at t (constants pass through)."""
    for i, spec in enumerate(fx_list):
        f = OPS[spec["op"]]
        p = {k: ev(v, (i, k)) for k, v in spec.items() if k != "op"}
        st = state.setdefault(i, {})
        amt = p.get("amount", 1.0)
        if amt <= 0:
            continue
        out, oa = f(img, alpha, p, t, st)
        if amt < 1:
            out = img + (out - img) * amt
            oa = alpha + (oa - alpha) * amt
        img, alpha = out.astype(np.float32, copy=False), oa.astype(np.float32, copy=False)
    return img, alpha
