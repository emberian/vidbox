"""Additional effects (see FX_EXTRA.md). Registered into fx.OPS with @op, like fx.py's.

Conventions shared by every op here:
- Lengths are canvas px and named px / scale / period, so tl.py halves them for previews.
- Randomness is a pure function of (seed, t): chunked renders agree frame for frame.
- History ops keep at most HIST_CAP frames (< tl.PREROLL at 25 fps), so a chunk that starts
  mid-song has a full, identical history by its first visible frame. A jump in t (seek, layer
  re-entering) resets state.
- Recursive ops (feedback, flowmosh) forget geometrically; their seam error is fb**25.
- Internal clocks run on the beat grid (fx.cycles / fx.grid_index): rates snap to 2**k per beat,
  phase 0 on the first downbeat, motion eased per beat. clock: "seconds" opts out.
"""

import math
from collections import deque

import cv2
import numpy as np

from fx import clock_of, cycles, grid_index, luma, op, smoothstep
from noise import fbm

HIST_CAP = 24      # frames of history any op may keep (1 s pre-roll = 25 frames at 25 fps)
GAP = 0.1          # s: a larger step in t (or going backwards) resets per-op state


# ---------------------------------------------------------------- shared helpers
def _beat_crossed(p, t, per_sec):
    """True on the first frame (25 fps) of each grid step of fx.grid_index(p, ., per_sec)."""
    return grid_index(p, t, per_sec) != grid_index(p, t - 1 / 25, per_sec)


def _fresh(st, t):
    """True when state must be dropped (first frame, seek, or t went backwards)."""
    last = st.get("_t")
    st["_t"] = t
    return last is None or t <= last or t - last > GAP


def _resize(x, shape):
    h, w = shape[:2]
    if x.shape[:2] == (h, w):
        return x
    return cv2.resize(x, (w, h), interpolation=cv2.INTER_LINEAR)


def _u8(x):
    return (np.clip(x, 0, 1) * 255 + 0.5).astype(np.uint8)


def _center(p, w, h, key="center"):
    c = p.get(key, (0.5, 0.5))
    return float(c[0]) * w, float(c[1]) * h


def _grid(st, h, w):
    if st.get("_grid_key") != (h, w):
        gx, gy = np.meshgrid(np.arange(w, dtype=np.float32), np.arange(h, dtype=np.float32))
        st["_grid_key"], st["_gx"], st["_gy"] = (h, w), gx, gy
    return st["_gx"], st["_gy"]


def _hue_matrix(deg):
    """3x3 RGB hue rotation about the grey axis (luma-preserving enough for trails)."""
    th = math.radians(deg)
    c, s = math.cos(th), math.sin(th)
    k = 1 / 3
    q = math.sqrt(k)
    return np.float32([
        [c + (1 - c) * k, k * (1 - c) - q * s, k * (1 - c) + q * s],
        [k * (1 - c) + q * s, c + k * (1 - c), k * (1 - c) - q * s],
        [k * (1 - c) - q * s, k * (1 - c) + q * s, c + k * (1 - c)],
    ])


def _blend(img, n, mode):
    """Blend a (h, w, 1|3) texture n in 0..1 over img (same modes as fx.noise)."""
    if mode == "mul":
        return img * n
    if mode == "screen":
        return 1 - (1 - img) * (1 - n)
    if mode == "add":
        return np.clip(img + n - 0.5, 0, 1)
    if mode == "overlay":
        return np.where(img < 0.5, 2 * img * n, 1 - 2 * (1 - img) * (1 - n))
    if mode == "luma":
        L = luma(img)[..., None]
        return np.clip(img / np.maximum(L, 1e-3) * n.mean(-1, keepdims=True), 0, 1)
    if mode == "replace":
        return np.broadcast_to(n, img.shape).astype(np.float32)
    raise ValueError(f"blend mode {mode!r}")


def _bloom(x, px):
    """Soft glow of x: two Gaussian scales computed at quarter resolution."""
    h, w = x.shape[:2]
    f = 4 if min(h, w) >= 64 else 1
    small = cv2.resize(x, (max(1, w // f), max(1, h // f)), interpolation=cv2.INTER_AREA) if f > 1 else x
    s = max(0.5, px / f)
    g = cv2.GaussianBlur(small, (0, 0), s) * 0.6 + cv2.GaussianBlur(small, (0, 0), s * 3) * 0.4
    return cv2.resize(g, (w, h), interpolation=cv2.INTER_LINEAR) if f > 1 else g


class _Ring:
    """Last N frames (uint8 img + alpha) with their capture shapes kept, plus a stacked copy
    at the current shape for gathers. Frames are resampled once, from their original, never
    repeatedly (a pulsing layer changes shape every frame)."""

    def __init__(self, n):
        self.n = n
        self.orig = deque(maxlen=n)   # (img u8, alpha u8) at capture shape
        self.stack = None             # (n, h, w, 3) u8 at the current shape
        self.astack = None
        self.count = 0                # frames pushed

    def push(self, img, a):
        h, w = img.shape[:2]
        iu, au = _u8(img), _u8(a)
        if self.stack is None or self.stack.shape[1:3] != (h, w):
            self.stack = np.empty((self.n, h, w, 3), np.uint8)
            self.astack = np.empty((self.n, h, w), np.uint8)
            for j, (oi, oa) in enumerate(self.orig):   # rebuild from originals
                slot = (self.count - len(self.orig) + j) % self.n
                self.stack[slot] = _resize(oi, (h, w))
                self.astack[slot] = _resize(oa, (h, w))
            own = True
        else:
            own = False
        slot = self.count % self.n
        self.stack[slot] = iu
        self.astack[slot] = au
        # original: a view into the stack while shapes are steady, an own copy otherwise
        self.orig.append((iu, au) if own else (self.stack[slot], self.astack[slot]))
        self.count += 1

    def __len__(self):
        return len(self.orig)

    def slot(self, d):
        """Stack index of the frame d frames ago (0 = newest), clamped to what exists."""
        d = int(min(max(d, 0), len(self.orig) - 1))
        return (self.count - 1 - d) % self.n

    def frame(self, d):
        """Float img, alpha d frames ago; fractional d interpolates."""
        d = min(max(float(d), 0.0), len(self.orig) - 1.0)
        i0 = int(math.floor(d))
        f = d - i0
        s0 = self.slot(i0)
        img = self.stack[s0].astype(np.float32) * (1 / 255)
        a = self.astack[s0].astype(np.float32) * (1 / 255)
        if f > 1e-3:
            s1 = self.slot(i0 + 1)
            img += (self.stack[s1].astype(np.float32) * (1 / 255) - img) * f
            a += (self.astack[s1].astype(np.float32) * (1 / 255) - a) * f
        return img, a


def _ring(st, t, n):
    if _fresh(st, t) or "ring" not in st or st["ring"].n != n:
        st["ring"] = _Ring(n)
    return st["ring"]


# ---------------------------------------------------------------- time / feedback
def _fb_matrix(p, w, h):
    cx, cy = _center(p, w, h)
    M = cv2.getRotationMatrix2D((cx, cy), p.get("rot", 0.0), p.get("zoom", 1.03))
    d = p.get("px", (0.0, 0.0))
    d = (0.0, float(d)) if np.ndim(d) == 0 else d   # a bare number drifts vertically
    M[0, 2] += float(d[0])
    M[1, 2] += float(d[1])
    return np.vstack([M, [0.0, 0.0, 1.0]])


def _fb_combine(mode, img, a, wi, wa, fb):
    if mode == "under":     # current frame over its echoes (straight alpha)
        a3 = a[..., None]
        oa = a + wa * (1 - a)
        return (img * a3 + wi * wa[..., None] * (1 - a3)) / np.maximum(oa, 1e-4)[..., None], oa
    if mode == "max":
        out = np.maximum(img, wi)
    elif mode == "screen":
        out = 1 - (1 - img) * (1 - wi)
    elif mode == "mix":
        out = img * (1 - fb) + wi
    else:
        raise ValueError(f"feedback mode {mode!r}")
    return out, np.maximum(a, wa)


def _fb_look(wi, p, steps):
    hue = p.get("hue", 0.0) * steps
    if abs(hue) > 1e-3:
        wi = np.clip(cv2.transform(wi, _hue_matrix(hue)), 0, 1)
    tint = p.get("tint")
    if tint is not None:   # per-step colour multiplier: trails age toward this colour
        wi = wi * np.asarray(tint, np.float32) ** steps
    return wi


@op("feedback")
def feedback(img, a, p, t, st):
    """Zoom/rotate feedback -> tunnel trails.
    every = 1: classic recursion (last output, transformed, mixed back in); forgets as fb**frames.
    every > 1: discrete echoes, a copy stamped every N song frames, each moved by the transforms
    of the stamps since; at most `echoes` copies within the last HIST_CAP frames, so chunked
    renders agree exactly. `pad` grows the layer by that fraction per side (transparent), so
    trails can leave the box."""
    pad = float(p.get("pad", 0.0))
    if pad > 0:
        ph, pw = int(img.shape[0] * pad), int(img.shape[1] * pad)
        img = cv2.copyMakeBorder(img, ph, ph, pw, pw, cv2.BORDER_CONSTANT, value=(0, 0, 0))
        a = cv2.copyMakeBorder(a, ph, ph, pw, pw, cv2.BORDER_CONSTANT, value=0)
    h, w = img.shape[:2]
    fb = float(np.clip(p.get("fb", 0.8), 0, 0.97))
    mode = p.get("mode", "max")
    if _fresh(st, t):
        st.pop("prev", None)
        st.pop("stamps", None)
    every = max(1, int(p.get("every", 1)))
    if every > 1 or "beats" in p:
        fno = int(math.floor(t * 25 + 1e-6))
        stamps = st.setdefault("stamps", [])          # [frame no, img, alpha, 3x3 matrix, steps]
        # stamp on the beat grid: `every` frames snaps to 2**k stamps per beat (3 -> 16ths), or
        # one stamp per `beats`; clock "seconds" keeps the old every-N-frames
        stamp = (fno % every == 0) if p.get("clock") == "seconds" else _beat_crossed(p, t, 25 / every)
        if stamp:
            M = _fb_matrix(p, w, h)
            for s_ in stamps:
                s_[3], s_[4] = M @ s_[3], s_[4] + 1
            if h * w > 500_000:   # stored at the half res the echoes are drawn at
                stamps.append([fno, cv2.resize(img, (w // 2, h // 2), interpolation=cv2.INTER_AREA),
                               cv2.resize(a, (w // 2, h // 2), interpolation=cv2.INTER_AREA), M, 1])
            else:
                stamps.append([fno, img, a, M, 1])
        k = max(1, int(p.get("echoes", 6)))
        stamps[:] = [s_ for s_ in stamps if fno - s_[0] <= HIST_CAP][-k:]
        if stamp:
            stamps[-1][3] = np.eye(3)   # this frame's own stamp: drawn as the current frame
            stamps[-1][4] = 0
        if not stamps or fb <= 0:
            return img, a
        # echoes are soft trails: build them at half res on big frames, upsample once
        f = 2 if h * w > 500_000 else 1
        hs, ws = h // f, w // f
        Sc = np.diag([1.0 / f, 1.0 / f, 1.0])
        Si = np.diag([float(f), float(f), 1.0])
        acc_p = np.zeros((hs, ws, 3), np.float32)   # premultiplied colour (under) / colour (max)
        acc_a = np.zeros((hs, ws), np.float32)
        tint = np.asarray(p.get("tint", [1, 1, 1]), np.float32)
        for fno_s, si, sa, C, steps in stamps:          # oldest first
            if steps == 0:
                continue
            si, sa = _resize(si, (hs, ws)), _resize(sa, (hs, ws))
            A2 = (Sc @ C @ Si)[:2]
            wi = cv2.warpAffine(si, A2, (ws, hs), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
            wa = cv2.warpAffine(sa, A2, (ws, hs), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
            K = np.diag(tint ** steps) @ _hue_matrix(p.get("hue", 0.0) * steps)
            if mode != "under":
                K = K * fb ** steps
            wi = cv2.transform(wi, K.astype(np.float32))
            wa *= fb ** steps
            if mode == "under":   # newer echo over older, premultiplied
                acc_p = wi * wa[..., None] + acc_p * (1 - wa[..., None])
                acc_a = wa + acc_a * (1 - wa)
            else:
                acc_p = np.maximum(acc_p, wi)
                acc_a = np.maximum(acc_a, wa)
        if mode == "under":
            acc_p = acc_p / np.maximum(acc_a, 1e-4)[..., None]
        acc_p = np.clip(acc_p, 0, 1)
        if f > 1:
            acc_p, acc_a = _resize(acc_p, (h, w)), _resize(acc_a, (h, w))
        return _fb_combine(mode, img, a, acc_p, acc_a, fb)
    prev = st.get("prev")
    if prev is not None and fb > 0:
        pi, pa = _resize(prev[0], (h, w)), _resize(prev[1], (h, w))
        A2 = _fb_matrix(p, w, h)[:2]
        wi = cv2.warpAffine(pi, A2, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
        wa = cv2.warpAffine(pa, A2, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
        wi = _fb_look(wi, p, 1)
        wa *= fb
        if mode != "under":    # opaque modes fade the colour; "under" fades only alpha
            wi *= fb
        out, oa = _fb_combine(mode, img, a, wi, wa, fb)
    else:
        out, oa = img, a
    st["prev"] = (out, oa)
    return out, oa


@op("chromatime")
def chromatime(img, a, p, t, st):
    """Each RGB channel from a different moment: R now, G `delay` frames ago, B 2*delay."""
    R = _ring(st, t, HIST_CAP + 1)
    R.push(img, a)
    d = p.get("delay", 4)
    if "delay_beats" in p:   # musical lag: 0.25 = a 16th note
        d = p["delay_beats"] * clock_of(p).spb * 25
    d = float(np.clip(d, 0, HIST_CAP / 2))
    order = p.get("order", "rgb")    # first letter = now, last = oldest
    out = np.empty_like(img)
    oa = a.copy()
    for k, ch in enumerate(order):
        c = "rgb".index(ch)
        if k == 0 or d < 1e-3:
            out[..., c] = img[..., c]
            continue
        fi, fa = R.frame(d * k)
        out[..., c] = fi[..., c]
        oa = np.maximum(oa, fa)
    return out, oa


@op("slitscan")
def slitscan(img, a, p, t, st):
    """Every row / column / ring / noise-region of the frame comes from a different moment."""
    depth = p.get("depth", 16)
    if "depth_beats" in p:   # 1 = one beat of time across the frame
        depth = p["depth_beats"] * clock_of(p).spb * 25
    depth = int(np.clip(round(depth), 1, HIST_CAP))
    R = _ring(st, t, HIST_CAP + 1)
    R.push(img, a)
    h, w = img.shape[:2]
    n = len(R)
    axis = p.get("axis", "y")
    if axis == "y":
        u = np.linspace(0, 1, h, dtype=np.float32)
    elif axis == "x":
        u = np.linspace(0, 1, w, dtype=np.float32)
    elif axis == "radial":
        gx, gy = _grid(st, h, w)
        cx, cy = _center(p, w, h)
        u = np.hypot((gx - cx) / (w / 2), (gy - cy) / (h / 2)) / math.sqrt(2)
    elif axis == "noise":
        sh, sw = max(8, h // 4), max(8, w // 4)
        sp = p.get("speed", 0.2)
        ck = None if p.get("clock") == "seconds" else cycles(p, t, sp)
        u = cv2.resize(fbm(sh, sw, t, scale=p.get("scale", 240) / 4, octaves=2, speed=sp,
                           seed=int(p.get("seed", 0)), clock=ck), (w, h))
    else:
        raise ValueError(f"slitscan axis {axis!r}")
    if p.get("reverse", 0):
        u = 1 - u
    d = np.minimum(u * depth, n - 1)
    d0 = d.astype(np.int32)
    f = (d - d0).astype(np.float32)
    s0 = (R.count - 1 - d0) % R.n
    s1 = (R.count - 1 - np.minimum(d0 + 1, n - 1)) % R.n
    S, A = R.stack, R.astack
    if axis in ("y", "x"):
        idx = np.arange(u.shape[0])
        if axis == "y":
            g0, g1 = S[s0, idx], S[s1, idx]
            a0, a1 = A[s0, idx], A[s1, idx]
            ff = f[:, None]
        else:
            g0 = S[s0, :, idx].transpose(1, 0, 2)
            g1 = S[s1, :, idx].transpose(1, 0, 2)
            a0, a1 = A[s0, :, idx].T, A[s1, :, idx].T
            ff = f[None, :]
    else:   # per-pixel: gather rows of a flat (n*h*w, 3) view
        hw = h * w
        pix = np.arange(hw, dtype=np.int64)
        l0, l1 = s0.ravel().astype(np.int64) * hw + pix, s1.ravel().astype(np.int64) * hw + pix
        Sf, Af = S.reshape(-1, 3), A.reshape(-1)
        g0, g1 = Sf[l0].reshape(h, w, 3), Sf[l1].reshape(h, w, 3)
        a0, a1 = Af[l0].reshape(h, w), Af[l1].reshape(h, w)
        ff = f
    k = 1 / 255
    o0 = g0.astype(np.float32) * k
    out = o0 + (g1.astype(np.float32) * k - o0) * ff[..., None]
    oa0 = a0.astype(np.float32) * k
    oa = oa0 + (a1.astype(np.float32) * k - oa0) * ff
    return out, oa


@op("flowmosh")
def flowmosh(img, a, p, t, st):
    """Datamosh-ish smear: the previous OUTPUT is dragged along the current frame's optical flow,
    and only `refresh` of the real frame leaks back in. Spike refresh on a beat for 'I-frames'."""
    h, w = img.shape[:2]
    res = int(p.get("res", 192))
    f = max(1.0, max(h, w) / res)
    sw, sh = max(16, int(w / f)), max(16, int(h / f))
    g = cv2.resize(cv2.cvtColor(img, cv2.COLOR_RGB2GRAY), (sw, sh), interpolation=cv2.INTER_AREA)
    g8 = _u8(g)
    fresh = _fresh(st, t)
    prev = None if fresh else st.get("prev")
    if prev is None:
        out, oa = img, a
    else:
        pg, pi, pa = prev
        pg = cv2.resize(pg, (sw, sh)) if pg.shape != (sh, sw) else pg
        flow = cv2.calcOpticalFlowFarneback(g8, pg, None, 0.5, 2, 9, 2, 5, 1.1, 0)
        gain = p.get("gain", 1.0)
        bpx = p.get("px", 0)
        if bpx >= 2:   # one motion vector per px block, like a codec's macroblocks
            bw_, bh_ = max(1, int(w / bpx)), max(1, int(h / bpx))
            fl = cv2.resize(cv2.resize(flow, (bw_, bh_), interpolation=cv2.INTER_AREA), (w, h),
                            interpolation=cv2.INTER_NEAREST)
        else:
            fl = cv2.resize(flow, (w, h), interpolation=cv2.INTER_LINEAR)
        gx, gy = _grid(st, h, w)
        mx = gx + fl[..., 0] * (gain * w / sw)
        my = gy + fl[..., 1] * (gain * h / sh)
        wi = cv2.remap(_resize(pi, (h, w)), mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
        wa = cv2.remap(_resize(pa, (h, w)), mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
        r = float(np.clip(p.get("refresh", 0.15), 0.02, 1))
        ib = p.get("iframe", 2)   # beats between clean I-frames (0 = none); keeps seams exact
        if ib and p.get("clock") != "seconds" and _beat_crossed({"beats": ib, "_clock": p.get("_clock")}, t, 0):
            r = 1.0
        out = wi + (img - wi) * r
        oa = wa + (a - wa) * r
    st["prev"] = (g8, out, oa)
    return out, oa


# ---------------------------------------------------------------- colour
def _stops(*cs):
    return [np.float32(c) / 255 for c in cs]


PALETTES = {   # name: (colour stops dark -> light, cyclic?)
    "ironbow": (_stops((0, 0, 0), (32, 0, 90), (120, 0, 140), (210, 40, 90), (250, 120, 20),
                       (255, 210, 60), (255, 255, 230)), False),
    "whitehot": (_stops((0, 0, 0), (60, 64, 66), (170, 175, 175), (255, 255, 255)), False),
    "blackhot": (_stops((255, 255, 255), (170, 175, 175), (60, 64, 66), (0, 0, 0)), False),
    "nightvision": (_stops((0, 8, 0), (10, 70, 20), (60, 200, 70), (210, 255, 200)), False),
    "blood": (_stops((0, 0, 0), (60, 0, 4), (160, 10, 10), (240, 60, 40), (255, 220, 210)), False),
    "gold": (_stops((0, 0, 0), (50, 25, 5), (150, 95, 20), (235, 190, 80), (255, 245, 210)), False),
    "y2k": (_stops((8, 10, 40), (0, 120, 200), (120, 240, 255), (255, 255, 255), (255, 120, 220),
                   (110, 30, 160)), True),
    "acid": (_stops((255, 0, 140), (255, 230, 0), (0, 255, 200), (60, 0, 255)), True),
    "rainbow": (_stops((255, 0, 0), (255, 255, 0), (0, 255, 0), (0, 255, 255), (0, 0, 255),
                       (255, 0, 255)), True),
}


def _lut(stops, cyclic, n=256):
    stops = [np.asarray(s, np.float32) for s in stops]
    if cyclic:
        stops = stops + [stops[0]]
    x = np.linspace(0, 1, len(stops))
    u = np.linspace(0, 1, n)
    return np.stack([np.interp(u, x, [s[c] for s in stops]) for c in range(3)], -1).astype(np.float32)


@op("gradmap")
def gradmap(img, a, p, t, st):
    """Luma through a palette (thermal ironbow, nightvision, y2k chrome, acid...); `cycle` scrolls
    the palette (drive it with a beat saw), `repeat` bands it."""
    pal = p.get("palette", "ironbow")
    if isinstance(pal, str):
        stops, cyclic = PALETTES[pal]
    else:
        stops, cyclic = [np.float32(c) for c in pal], bool(p.get("cyclic", 0))
    key = (str(pal), cyclic)
    if st.get("_lut_key") != key:
        st["_lut_key"], st["_lut"] = key, _lut(stops, cyclic, 1024)
    lut = st["_lut"]
    L = cv2.cvtColor(np.clip(img, 0, 1), cv2.COLOR_RGB2GRAY)
    gamma = p.get("gamma", 1.0)
    if gamma != 1.0:
        L = L ** (1 / max(gamma, 1e-3))
    cyc = p.get("cycle", 0.0)
    if "beats" in p:   # built-in cycling: one palette turn per `beats`, stepping on each beat
        cyc = cyc + cycles(p, t, 0.0)
    u = L * p.get("repeat", 1.0) + cyc
    if cyclic:
        u = u - np.floor(u)
    else:   # mirror so cycling a ramp palette ping-pongs instead of jumping
        u = 1 - np.abs(1 - np.mod(u, 2))
    idx = np.clip((u * 1023).astype(np.int32), 0, 1023)
    return lut[idx], a


@op("dither")
def dither(img, a, p, t, st):
    """Posterize with ordered (Bayer) or hashed-noise dither, optionally in chunky px cells."""
    h, w = img.shape[:2]
    px = max(1, int(round(p.get("px", 2))))
    n = max(2.0, p.get("levels", 4))
    small = cv2.resize(img, (max(1, w // px), max(1, h // px)), interpolation=cv2.INTER_AREA) if px > 1 else img
    sh, sw = small.shape[:2]
    mode = p.get("mode", "bayer")
    if mode == "bayer":
        key = ("bayer", sh, sw)
        if st.get("_dk") != key:
            b = np.array([[0]], np.float32)
            for _ in range(3):
                b = np.block([[4 * b, 4 * b + 2], [4 * b + 3, 4 * b + 1]])
            b = (b + 0.5) / 64
            st["_dk"], st["_dm"] = key, np.tile(b, (sh // 8 + 1, sw // 8 + 1))[:sh, :sw]
        T = st["_dm"]
    elif mode == "noise":
        fr = grid_index(p, t, p.get("rate", 12.5)) if p.get("rate", 12.5) > 0 else 0
        T = np.random.default_rng((int(p.get("seed", 0)), fr, 911)).random((sh, sw), dtype=np.float32)
    else:
        raise ValueError(f"dither mode {mode!r}")
    q = np.floor(small * (n - 1) + T[..., None]) / (n - 1)
    q = np.clip(q, 0, 1).astype(np.float32)
    if px > 1:
        q = cv2.resize(q, (w, h), interpolation=cv2.INTER_NEAREST)
    return q, a


# ---------------------------------------------------------------- geometry
@op("mirror")
def mirror(img, a, p, t, st):
    """Mirror symmetry: h (left onto right), v (top onto bottom), quad, or tile (n x n flips).
    `shift` slides the mirror axis (-0.5..0.5 of the frame)."""
    h, w = img.shape[:2]
    mode = p.get("mode", "h")
    sh = p.get("shift", 0.0)
    if mode == "tile":
        n = max(1, int(p.get("tiles", 2)))
        key = ("tile", h, w, n, round(sh, 4))
        if st.get("_mk") != key:
            def axis(L):
                u = (np.arange(L) + 0.5) / L * n + sh * n
                k = np.floor(u)
                fr = u - k
                fr = np.where(np.mod(k, 2) == 1, 1 - fr, fr)
                return np.clip((fr * L).astype(np.int32), 0, L - 1)
            st["_mk"], st["_mi"] = key, (axis(h), axis(w))
    else:
        key = (mode, h, w, round(sh, 4))
        if st.get("_mk") != key:
            def axis(L, on):
                i = np.arange(L)
                if not on:
                    return i
                c = int(round(L * (0.5 + sh)))
                c = min(max(c, 1), L - 1)
                return np.where(i < c, i, np.clip(2 * c - 1 - i, 0, L - 1)).astype(np.int32)
            st["_mk"], st["_mi"] = key, (axis(h, mode in ("v", "quad")), axis(w, mode in ("h", "quad")))
    yi, xi = st["_mi"]
    return img[yi][:, xi], a[yi][:, xi]


@op("radialblur")
def radialblur(img, a, p, t, st):
    """Zoom (and/or spin) blur about `center`: 2**passes samples via repeated doubling."""
    zoom = p.get("strength", 0.08)
    spin = p.get("spin", 0.0)
    if abs(zoom) < 1e-3 and abs(spin) < 1e-2:
        return img, a
    h, w = img.shape[:2]
    cx, cy = _center(p, w, h)
    passes = int(np.clip(p.get("passes", 3), 1, 5))
    m = 2 ** passes - 1
    z1, r1 = (1 + zoom) ** (1 / m), spin / m
    out, oa = img, a
    for i in range(passes):
        k = 2 ** i
        M = cv2.getRotationMatrix2D((cx, cy), r1 * k, z1 ** k)
        out = 0.5 * (out + cv2.warpAffine(out, M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT))
        oa = 0.5 * (oa + cv2.warpAffine(oa, M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT))
    return out, oa


@op("shock")
def shock(img, a, p, t, st):
    """A ring of radial displacement expanding from `center` as `phase` goes 0 -> 1 (drive with a
    beat saw for a shockwave per kick). `rgb` splits the channels across the ring."""
    if "phase" in p or p.get("clock") == "seconds":
        ph = float(p.get("phase", 0.0))
    else:   # default: a wave per `beats` (1), launched on the beat
        ph = (clock_of(p).beat(t) / (p.get("beats", 1.0) or 1.0)) % 1.0
    amp = p.get("px", 24) * (1 - ph) ** p.get("decay", 1.5)
    if amp < 0.25 or ph >= 1:
        return img, a
    h, w = img.shape[:2]
    gx, gy = _grid(st, h, w)
    cx, cy = _center(p, w, h)
    key = (h, w, round(cx, 2), round(cy, 2))
    if st.get("_sk") != key:
        dx, dy = gx - cx, gy - cy
        r = np.hypot(dx, dy) + 1e-3
        st["_sk"], st["_sr"], st["_sdir"] = key, r, (dx / r, dy / r)
    r, (ux, uy) = st["_sr"], st["_sdir"]
    R = ph * math.hypot(max(cx, w - cx), max(cy, h - cy))
    width = max(2.0, p.get("period", 80))
    z = (r - R) / width
    d = amp * z * np.exp(0.5 - 0.5 * z * z)     # derivative of a Gaussian: push out, pull in
    rgb = p.get("rgb", 0.0)
    if rgb > 1e-3:
        out = np.empty_like(img)
        for c, s in ((0, 1 + rgb), (1, 1.0), (2, 1 - rgb)):
            out[..., c] = cv2.remap(np.ascontiguousarray(img[..., c]), gx - ux * d * s, gy - uy * d * s, cv2.INTER_LINEAR,
                                    borderMode=cv2.BORDER_REFLECT)
    else:
        out = cv2.remap(img, gx - ux * d, gy - uy * d, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    oa = cv2.remap(a, gx - ux * d, gy - uy * d, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
    return out, oa


# ---------------------------------------------------------------- print / screen
def _ht_maps(h, w, period, angle):
    th = math.radians(angle)
    c, s = math.cos(th), math.sin(th)
    gx, gy = np.meshgrid(np.arange(w, dtype=np.float32) + 0.5, np.arange(h, dtype=np.float32) + 0.5)
    u = (gx * c + gy * s) / period
    v = (-gx * s + gy * c) / period
    ku, kv = np.floor(u) + 0.5, np.floor(v) + 0.5
    dist = np.hypot(u - ku, v - kv) * period            # px to the cell centre
    mx = ((ku * c - kv * s) * period).astype(np.float32)   # cell centre back in xy
    my = ((ku * s + kv * c) * period).astype(np.float32)
    return dist.astype(np.float32), mx, my


@op("halftone")
def halftone(img, a, p, t, st):
    """Halftone dots on a rotated grid. mode rgb: one screen per channel at 3 angles (pop-art /
    LED wall); mono: luma dots in `ink` on `paper`. Dot area follows brightness."""
    h, w = img.shape[:2]
    per = max(3.0, p.get("period", 10))
    ang = p.get("angle", 45.0)
    mode = p.get("mode", "rgb")
    aa = 0.75
    pre = cv2.GaussianBlur(img, (0, 0), per / 3)
    angles = [ang + 15, ang + 75, ang] if mode == "rgb" else [ang]
    cache = st.setdefault("_ht", {})
    dots = []
    for k, an in enumerate(angles):
        key = (h, w, round(per, 2), round(an % 180, 1))
        if key not in cache:
            if len(cache) > 6:
                cache.clear()
            cache[key] = _ht_maps(h, w, per, an)
        dist, mx, my = cache[key]
        src = np.ascontiguousarray(pre[..., k]) if mode == "rgb" else cv2.cvtColor(pre, cv2.COLOR_RGB2GRAY)
        v = cv2.remap(src, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        if p.get("invert", 0):
            v = 1 - v
        r = per * np.sqrt(np.clip(v, 0, 1) / math.pi) * 1.12
        dots.append(np.clip((r - dist) / aa + 0.5, 0, 1))
    if mode == "rgb":
        out = np.stack(dots, -1)
    else:
        ink = np.asarray(p.get("ink", [1, 1, 1]), np.float32)
        paper = np.asarray(p.get("paper", [0, 0, 0]), np.float32)
        out = paper + (ink - paper) * dots[0][..., None]
    return out.astype(np.float32), a


@op("vhs")
def vhs(img, a, p, t, st):
    """Tape: per-row wobble, a rolling tracking band, chroma bleed, streaky noise."""
    h, w = img.shape[:2]
    seed = int(p.get("seed", 0))
    fr = int(math.floor(t * 25 + 1e-6))
    rng = np.random.default_rng((seed, fr, 77))
    y = np.arange(h, dtype=np.float32)
    per = max(4.0, p.get("period", 140))
    free = p.get("clock") == "seconds"
    wob = t * 0.7 if free else cycles({k: v for k, v in p.items() if k != "beats"}, t, 0.7, ease=False)
    off = p.get("px", 3) * (np.sin(2 * math.pi * (y / per + wob)) * 0.6
                            + cv2.resize(rng.standard_normal((max(2, h // 6), 1)).astype(np.float32),
                                         (1, h))[:, 0] * 0.4)
    band = p.get("band", 0.4)
    bh = 0.08 * h
    if band > 1e-3:
        if free:
            by = ((t * p.get("roll", 0.23) + (seed * 0.37)) % 1.3 - 0.15) * h
        else:   # one pass per 2**k beats (default 2 bars), starting on a downbeat
            u = cycles(p, t, p.get("roll", 0.23), ease=False) + (seed % 4) / 4
            by = ((u % 1.0) * 1.3 - 0.15) * h
        bz = np.clip(1 - np.abs(y - by) / bh, 0, 1) ** 2
        off = off + bz * band * (0.05 * w) * (0.6 + 0.4 * rng.standard_normal(h).astype(np.float32))
    gx, gy = _grid(st, h, w)
    out = cv2.remap(img, gx + off[:, None], gy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    bleed = p.get("scale", 6)
    if bleed >= 1:
        Y, Cr, Cb = cv2.split(cv2.cvtColor(out, cv2.COLOR_RGB2YCrCb))
        k = int(round(bleed)) | 1
        M = np.float32([[1, 0, bleed * 0.6], [0, 1, 0]])
        Cr, Cb = (cv2.warpAffine(cv2.blur(c, (k, 1)), M, (w, h), borderMode=cv2.BORDER_REPLICATE) for c in (Cr, Cb))
        out = np.clip(cv2.cvtColor(cv2.merge([Y, Cr, Cb]), cv2.COLOR_YCrCb2RGB), 0, 1)
    nz = p.get("noise", 0.06)
    if nz > 1e-3:
        streak = rng.standard_normal((h, max(2, w // 12))).astype(np.float32)
        streak = cv2.resize(streak, (w, h), interpolation=cv2.INTER_LINEAR)
        amt = nz * (1 + (6 * band * bz[:, None] if band > 1e-3 else 0))
        out = np.clip(out + (streak * amt)[..., None], 0, 1)
    return out, a


# ---------------------------------------------------------------- light
@op("bloom")
def bloom(img, a, p, t, st):
    """Glow from the highlights (above `thresh`), added back; `color` tints the glow."""
    th, knee = p.get("thresh", 0.65), p.get("knee", 0.15)
    hi = img * smoothstep(th - knee, th + knee, luma(img))[..., None]
    g = _bloom(hi, p.get("px", 24)) * p.get("gain", 0.8)
    col = p.get("color")
    if col is not None:
        g = g * np.asarray(col, np.float32)
    return np.clip(img + g, 0, 1), a


@op("edgeglow")
def edgeglow(img, a, p, t, st):
    """Neon outlines: Sobel edges of luma, coloured (`color` or "source"), bloomed, screened over
    the image dimmed to `base` (0 = lines on black). `scale` pre-blurs (px): raise it on busy
    texture (rubble) so only the big contours glow."""
    L = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    L = cv2.GaussianBlur(L, (0, 0), max(0.5, p.get("scale", 2.0)))
    gx = cv2.Sobel(L, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(L, cv2.CV_32F, 0, 1, ksize=3)
    th = p.get("thresh", 0.12)
    e = smoothstep(th, th * 2.5, np.sqrt(gx * gx + gy * gy))[..., None]
    col = p.get("color", [0.35, 1.0, 0.9])
    lines = e * (img * 1.6 if col == "source" else np.asarray(col, np.float32))
    glow = np.clip((lines + _bloom(lines, p.get("px", 8)) * p.get("glow", 1.5)) * p.get("gain", 1.0), 0, 1)
    return 1 - (1 - img * p.get("base", 0.6)) * (1 - glow), a


# ---------------------------------------------------------------- glitch / texture
@op("glitch")
def glitch(img, a, p, t, st):
    """Block-shift glitch. `strength` (0 = off; drive with an onset or beat decay) sets how many
    bands/blocks break and how far. The pattern is fixed for `hold` s, chosen from (seed, t)."""
    s = float(p.get("strength", 0.0))
    if s < 0.02:
        return img, a
    h, w = img.shape[:2]
    hold = max(0.02, p.get("hold", 0.08))
    step = int(math.floor(t / hold + 1e-6)) if p.get("clock") == "seconds" else grid_index(p, t, 1 / hold)
    rng = np.random.default_rng((int(p.get("seed", 0)), step, 13))
    px = p.get("px", 60)
    split = p.get("rgb", 0.5)
    out, oa = img.copy(), a.copy()
    if p.get("mode", "bands") == "bands":
        nb = max(2, int(p.get("blocks", 14)))
        cuts = np.sort(rng.integers(0, h, nb - 1))
        edges = np.concatenate([[0], cuts, [h]])
        for y0, y1 in zip(edges[:-1], edges[1:]):
            if y1 <= y0 or rng.random() > s:
                continue
            dx = int(rng.normal() * px * s)
            band = np.roll(img[y0:y1], dx, axis=1)
            if split > 0 and rng.random() < 0.6:
                e = int(px * 0.25 * split * s * (1 if rng.random() < 0.5 else -1))
                band[..., 0] = np.roll(band[..., 0], e, axis=1)
                band[..., 2] = np.roll(band[..., 2], -e, axis=1)
            out[y0:y1] = band
            oa[y0:y1] = np.roll(a[y0:y1], dx, axis=1)
    else:   # "blocks": macroblock corruption copied from elsewhere in the frame
        bs = max(4, int(p.get("scale", 32)))
        nblk = int(s * p.get("blocks", 14) * 2)
        for _ in range(nblk):
            bw, bh_ = bs * int(rng.integers(1, 5)), bs * int(rng.integers(1, 3))
            if bw >= w or bh_ >= h:
                continue
            x0, y0 = int(rng.integers(0, w - bw)), int(rng.integers(0, h - bh_))
            sx = int(np.clip(x0 + rng.normal() * px, 0, w - bw))
            sy = int(np.clip(y0 + rng.normal() * px * 0.3, 0, h - bh_))
            blk = img[sy:sy + bh_, sx:sx + bw]
            if rng.random() < 0.5:   # blown-out 'compression' colour
                blk = np.round(blk * 3) / 3
            if split > 0 and rng.random() < 0.4:
                blk = blk[..., ::-1]
            out[y0:y0 + bh_, x0:x0 + bw] = blk
    return out, oa


_VTAB = 64


def _vor_points(seed):
    r = np.random.default_rng((seed, 4242))
    return r.random((_VTAB, _VTAB, 2), dtype=np.float32), r.random((_VTAB, _VTAB, 2), dtype=np.float32), \
        r.random((_VTAB, _VTAB, 3), dtype=np.float32)


@op("voronoi")
def voronoi(img, a, p, t, st):
    """Animated Worley/Voronoi texture (Blender's Voronoi Texture). feature: f1 (soft cells), edge
    (F2-F1 crackle lines), cells (each cell flat-filled with the image under it: 'crystallize'),
    or random (each cell a random colour). Blended like fx.noise (mode)."""
    h, w = img.shape[:2]
    cell = max(4.0, p.get("scale", 80))
    f = int(np.clip(cell // 10, 1, 4))
    sh, sw = max(4, h // f), max(4, w // f)
    cs = cell / f
    seed = int(p.get("seed", 0))
    if st.get("_vk") != seed:
        st["_vk"], st["_vp"] = seed, _vor_points(seed)
    base, phase, colr = st["_vp"]
    spd = p.get("speed", 0.4)
    jit = 0.4 * (np.sin(2 * math.pi * (phase + cycles(p, t, spd * 0.5))))   # points orbit, a step per beat
    pts = base * 0.2 + 0.4 + jit                                  # 0..1 within the cell
    gy, gx = np.mgrid[0:sh, 0:sw].astype(np.float32)
    u, v = (gx + 0.5) / cs, (gy + 0.5) / cs
    iu, iv = np.floor(u).astype(np.int32), np.floor(v).astype(np.int32)
    d1 = np.full((sh, sw), 1e9, np.float32)
    d2 = d1.copy()
    best = np.zeros((sh, sw, 2), np.int32)
    for oy in (-1, 0, 1):
        for ox in (-1, 0, 1):
            cu, cv = iu + ox, iv + oy
            P = pts[cv % _VTAB, cu % _VTAB]
            dd = (cu + P[..., 0] - u) ** 2 + (cv + P[..., 1] - v) ** 2
            closer = dd < d1
            d2 = np.where(closer, d1, np.minimum(d2, dd))
            d1 = np.where(closer, dd, d1)
            best = np.where(closer[..., None], np.stack([cu, cv], -1), best)
    feat = p.get("feature", "f1")
    if feat == "f1":
        n = np.clip(np.sqrt(d1), 0, 1)[..., None]
    elif feat == "edge":
        e = np.sqrt(d2) - np.sqrt(d1)
        n = (1 - smoothstep(0.0, p.get("width", 0.08), e))[..., None]
    elif feat in ("cells", "random"):
        bu, bv = best[..., 0], best[..., 1]
        if feat == "random":
            n = colr[bv % _VTAB, bu % _VTAB]
        else:
            P = pts[bv % _VTAB, bu % _VTAB]
            mx = ((bu + P[..., 0]) * cs * f).astype(np.float32)
            my = ((bv + P[..., 1]) * cs * f).astype(np.float32)
            n = cv2.remap(cv2.GaussianBlur(img, (0, 0), max(0.5, cell / 12)), np.clip(mx, 0, w - 1),
                          np.clip(my, 0, h - 1), cv2.INTER_LINEAR)
        lines = p.get("lines", 0.4 if feat == "cells" else 0.0)
        if lines > 0:   # stained-glass leading between cells
            e = np.sqrt(d2) - np.sqrt(d1)
            n = n * (1 - lines * (1 - smoothstep(0.0, 0.12, e)))[..., None]
    else:
        raise ValueError(f"voronoi feature {feat!r}")
    if f > 1:
        n = cv2.resize(n.astype(np.float32), (w, h), interpolation=cv2.INTER_LINEAR)
        if n.ndim == 2:
            n = n[..., None]
    n = n.astype(np.float32)
    color = p.get("color")
    if color is not None and n.shape[-1] == 1:
        n = n * np.asarray(color, np.float32)
    mode = p.get("mode", "replace" if feat == "cells" else "overlay")
    return _blend(img, n, mode).astype(np.float32), a


# ---------------------------------------------------------------- hue key
@op("huekey")
def huekey(img, a, p, t, st):
    """Keep only pixels near a hue: alpha *= hue match * saturation gate * value gate. hue in
    degrees (0 red, 120 green, 240 blue), width = half-width in degrees, soft = feather in degrees;
    sat / val: smoothstep(min, min + soft_sv) gates (drop greys and darks). invert=1 keys the hue out."""
    hsv = cv2.cvtColor(np.clip(img, 0, 1).astype(np.float32), cv2.COLOR_RGB2HSV)   # H 0..360, S, V 0..1
    d = np.abs((hsv[..., 0] - p.get("hue", 0.0) + 180.0) % 360.0 - 180.0)
    w, soft = p.get("width", 20.0), max(p.get("soft", 10.0), 1e-3)
    m = 1.0 - smoothstep(w, w + soft, d)
    ssv = p.get("soft_sv", 0.1)
    m = m * smoothstep(p.get("sat", 0.3), p.get("sat", 0.3) + ssv, hsv[..., 1])
    m = m * smoothstep(p.get("val", 0.2), p.get("val", 0.2) + ssv, hsv[..., 2])
    if p.get("invert", 0):
        m = 1.0 - m
    return img, a * m.astype(np.float32)
