"""Render a timeline (render/TIMELINE.md).

usage: uv run python render/tl.py TIMELINE.json [--full] [--range A B] [--jobs N] [-o OUT]

Default is a half-size preview written next to the timeline as NAME.mp4 (what the studio's
timeline viewer plays); --full renders 1:1 to NAME.full.mp4. --jobs splits the range into
chunks rendered in parallel processes (each with a short pre-roll so trails settle).
"""
import argparse
import functools
import json
import math
import os
import subprocess
import sys
import tempfile
import time as wall
from bisect import bisect_left, bisect_right
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import fx as FX  # noqa: E402
from media import Reader  # noqa: E402
from signals import Ctx, Music, compile_signal, compile_time  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
PICTURE = (0, 158, 1440, 922)   # Meine's letterboxed picture area (canvas px)
MAX_LAYER_AREA = 16   # a layer drawn larger than 16 canvases (4x each way) is a broken signal, not a zoom
LENGTH_PARAMS = {"px", "scale", "period"}   # fx params in canvas px: scaled with the preview
PREROLL = 1.0
SR = 48000          # audio bus sample rate
AFADE = 0.006       # s: fade on every audio edge (layer start/end, stutter cuts) so nothing clicks


def is_new_time(T):
    """True for the time forms compiled to a TimeMap (seq, speed signals); the original forms keep
    their closed-form lambdas."""
    return "seq" in T or not isinstance(T.get("speed", 1.0), (int, float))


def _union_add(xs, ys, lo, hi):
    """Add [lo, hi] to a union of disjoint intervals kept as sorted starts xs / ends ys (touching
    intervals merge)."""
    i, j = bisect_left(ys, lo), bisect_right(xs, hi)   # components [i, j) overlap or touch it
    if i < j:
        lo, hi = min(lo, xs[i]), max(hi, ys[j - 1])
    xs[i:j], ys[i:j] = [lo], [hi]


def revisit_spans(tm, t0, t1, pad=0.05):
    """Source intervals a time map plays backwards or visits more than once over [t0, t1):
    decoded once into media.SPANS instead of re-seeking (reverses, stutters). Both the material
    seen so far and the result are kept as interval unions, so n retriggers of one slice cost O(n),
    not n^2 / 2 overlap pieces; the padded, merged result depends only on the union."""
    sx, sy, px, py = [], [], [], []   # seen so far; revisited (starts, ends)
    for r in tm.runs:
        a, b = max(r.a, t0), min(r.b, t1)
        if b <= a or r.kind == "hold":
            continue
        s = r.src_vec(np.linspace(a, b, 64))
        lo, hi = float(s.min()), float(s.max())
        if np.any(np.diff(s) < -1e-9):
            _union_add(px, py, lo, hi)
        else:
            k0, k1 = bisect_right(sy, lo), bisect_left(sx, hi)   # seen components overlapping it
            for x, y in list(zip(sx[k0:k1], sy[k0:k1])):
                if min(hi, y) > max(lo, x):
                    _union_add(px, py, max(lo, x), min(hi, y))
        _union_add(sx, sy, lo, hi)
    merged = []
    for lo, hi in sorted((max(0.0, lo - pad), hi + pad) for lo, hi in zip(px, py)):
        if merged and lo <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], hi))
        else:
            merged.append((lo, hi))
    return merged


@functools.lru_cache(maxsize=None)
def probe(src):
    """(width, height) of a source's first video stream; once per file per process (a timeline
    has hundreds of layers over a few dozen files)."""
    out = json.loads(subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
         "stream=width,height", "-of", "json", str(src)],
        capture_output=True, text=True, check=True).stdout)["streams"][0]
    return out["width"], out["height"]


_mask_cache = {}
MASK_CACHE_MB = 64   # a pulsing masked layer makes a new size every frame; a full-canvas mask is 6 MB


def mask(spec, w, h):
    if not spec:
        return None
    key = (spec.get("shape"), spec.get("feather", 0.2), w, h)
    if key not in _mask_cache:
        y, x = np.mgrid[0:h, 0:w].astype(np.float32) + 0.5
        f = max(spec.get("feather", 0.2), 1e-3)
        if spec["shape"] == "oval":
            r = np.hypot((x - w / 2) / (w / 2), (y - h / 2) / (h / 2))
            m = np.clip((1 - r) / f, 0, 1)
        elif spec["shape"] == "rect":
            dx = np.minimum(x, w - x) / (w / 2)
            dy = np.minimum(y, h - y) / (h / 2)
            m = np.clip(np.minimum(dx, dy) / f, 0, 1)
        else:
            raise ValueError(f"mask shape {spec['shape']!r}")
        if len(_mask_cache) > 64 or sum(v.nbytes for v in _mask_cache.values()) + m.nbytes > MASK_CACHE_MB * 2 ** 20:
            _mask_cache.clear()
        _mask_cache[key] = m.astype(np.float32)
    return _mask_cache[key]


BLENDS = {
    "normal": lambda b, l: l,
    "screen": lambda b, l: 1 - (1 - b) * (1 - l),
    "add": lambda b, l: np.minimum(1, b + l),
    "multiply": lambda b, l: b * l,
    "difference": lambda b, l: np.abs(b - l),
    "lighten": np.maximum,
    "darken": np.minimum,
    "overlay": lambda b, l: np.where(b < 0.5, 2 * b * l, 1 - 2 * (1 - b) * (1 - l)),
}


def composite(canvas, img, alpha, cx, cy, rot, mode, clip=None):
    """clip: (x0, y0, x1, y1) in canvas px; the layer only lands inside it."""
    H, W = canvas.shape[:2]
    h, w = img.shape[:2]
    blend = BLENDS[mode]
    if rot == 0 and w * h > 0.6 * W * H:   # big layer: integer placement is fine
        x0, y0 = int(round(cx - w / 2)), int(round(cy - h / 2))
        L, A = img, alpha
    else:   # small or rotated: sub-pixel, rotated warp into its bounding box
        th = math.radians(rot)
        c, s = math.cos(th), math.sin(th)
        bw, bh = abs(w * c) + abs(h * s), abs(w * s) + abs(h * c)
        x0, y0 = int(math.floor(cx - bw / 2)), int(math.floor(cy - bh / 2))
        bw_i, bh_i = int(math.ceil(bw)) + 2, int(math.ceil(bh)) + 2
        # layer px -> bbox px: rotate about the layer centre, place centre at (cx, cy)
        M = np.float32([[c, s, 0], [-s, c, 0]])
        M[:, 2] = np.array([cx - x0, cy - y0]) - M[:, :2] @ np.array([w / 2, h / 2])
        L = cv2.warpAffine(img, M, (bw_i, bh_i), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
        A = cv2.warpAffine(alpha, M, (bw_i, bh_i), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    h, w = L.shape[:2]
    cx0, cy0, cx1, cy1 = clip if clip else (0, 0, W, H)
    dx0, dy0 = max(int(cx0), x0), max(int(cy0), y0)
    dx1, dy1 = min(W, int(cx1), x0 + w), min(H, int(cy1), y0 + h)
    sx0, sy0 = dx0 - x0, dy0 - y0
    if dx1 <= dx0 or dy1 <= dy0:
        return
    Ls = L[sy0:sy0 + dy1 - dy0, sx0:sx0 + dx1 - dx0]
    As = A[sy0:sy0 + dy1 - dy0, sx0:sx0 + dx1 - dx0, None]
    base = canvas[dy0:dy1, dx0:dx1]
    base += (blend(base, Ls) - base) * As


class Params:
    """Compiled-signal cache. Keys are tuples ending in the parameter name."""

    def __init__(self, ctx, k):
        self.ctx, self.k, self._sig = ctx, k, {}
        self.clock = FX.Clock(ctx.music)   # beat grid for ops' internal clocks (fx.cycles)

    def sig(self, key, spec, default):
        if key not in self._sig:
            self._sig[key] = compile_signal(spec if spec is not None else default, self.ctx)
        return self._sig[key]

    def param(self, spec, key, t):
        """Evaluate an fx param; strings and colour triples pass through as constants."""
        if isinstance(spec, str) or (isinstance(spec, list) and len(spec) != 2):
            return spec
        v = self.sig(key, spec, None)(t)
        return v * self.k if key[-1] in LENGTH_PARAMS else v

    def run_fx(self, fx_list, img, alpha, t, state, scope):
        return FX.apply(fx_list, img, alpha, t, state, lambda spec, key: self.param(spec, (scope,) + key, t),
                        clock=self.clock)


class Layer(Params):
    def __init__(self, spec, ctx, W, H, k):
        super().__init__(ctx, k)
        self.s = spec
        self.id = spec.get("id", "?")
        self.t0, self.t1 = spec["t0"], spec["t1"]
        self.src = ROOT / spec["src"]
        self.reader, self.state = None, {}
        sw, sh = probe(self.src)
        crop = spec.get("crop")
        if crop:
            sw, sh = sw * (crop[2] - crop[0]), sh * (crop[3] - crop[1])
        self.native = (sw, sh)
        if "size" in spec:
            bw, bh = spec["size"]
        else:
            fit = spec.get("fit", "cover")
            if fit == "native":
                f = 1.0
            elif fit == "contain":
                f = min(W / sw, H / sh)
            elif fit == "picture":
                f = max((PICTURE[2] - PICTURE[0]) / sw, (PICTURE[3] - PICTURE[1]) / sh)
            else:
                f = max(W / sw, H / sh)
            bw, bh = sw * f, sh * f
        self.base = (bw * k, bh * k)
        T = spec.get("time", {"in": 0.0, "speed": 1.0})
        self.spans = None
        if is_new_time(T):
            tm = compile_time(T, self.t0, self.t1, ctx)
            self.src_time = tm
            self.spans = revisit_spans(tm, self.t0, self.t1) or None
        elif "map" in T:
            song, src = T["map"]["song"], T["map"]["src"]
            self.src_time = lambda t: float(np.interp(t, song, src))
        elif "hold" in T:
            self.src_time = lambda t: T["hold"]
        else:
            tin, sp, loop = T.get("in", 0.0), T.get("speed", 1.0), T.get("loop")
            if loop:
                a, b = loop
                self.src_time = lambda t: a + ((tin - a) + (t - self.t0) * sp) % (b - a)
            else:
                self.src_time = lambda t: tin + (t - self.t0) * sp
                if sp < 0:   # reverse: decode the span once
                    self.spans = revisit_spans(compile_time(T, self.t0, self.t1), self.t0, self.t1) or None
        fade = spec.get("fade", {})
        self.fin, self.fout = fade.get("in", 0.0), fade.get("out", 0.0)

    def open(self):
        # Decode at the largest size this layer reaches over its WHOLE life (never above the
        # source's own), sampled densely enough to catch beat pulses. Must not depend on where
        # a render chunk starts, or parallel chunks decode at different sizes and seams show.
        n = int(min(4000, max(24, (self.t1 - self.t0) * 12.5)))
        scales = [self.sig("scale", self.s.get("scale"), 1)(t) for t in np.linspace(self.t0, self.t1, n)]
        smax = max(1e-3, max(abs(x) for x in scales))
        w, h = self.base[0] * smax, self.base[1] * smax
        f = min(1.0, self.native[0] / w, self.native[1] / h)
        size = (max(2, int(w * f)) // 2 * 2, max(2, int(h * f)) // 2 * 2)
        self.reader = Reader(self.src, self.s.get("crop"), size, spans=self.spans)

    def close(self):
        if self.reader:
            self.reader.close()
            self.reader = None

    def draw(self, canvas, t):
        s = self.s
        op = self.sig("opacity", s.get("opacity"), 1)(t)
        if self.fin > 0:
            op *= min(1.0, (t - self.t0) / self.fin)
        if self.fout > 0:
            op *= min(1.0, (self.t1 - t) / self.fout)
        sc = self.sig("scale", s.get("scale"), 1)(t)
        if op <= 0.002 or sc <= 0.002:
            return
        dw, dh = max(2, int(round(self.base[0] * sc))), max(2, int(round(self.base[1] * sc)))
        if dw * dh > MAX_LAYER_AREA * canvas.shape[0] * canvas.shape[1]:   # each float copy below is dw*dh*12 bytes
            raise ValueError(f"layer {self.id} at t={t:.3f}: {dw}x{dh} px (scale {sc:.3g}) is over "
                             f"{MAX_LAYER_AREA}x the canvas")
        frame = self.reader.get(self.src_time(t))
        if (dw, dh) != (frame.shape[1], frame.shape[0]):   # usually equal: decoded at display size
            frame = cv2.resize(frame, (dw, dh), interpolation=cv2.INTER_AREA if dw < frame.shape[1] else cv2.INTER_LINEAR)
        img = frame.astype(np.float32) * (1 / 255)
        m = mask(s.get("mask"), dw, dh)
        alpha = (m if m is not None else np.ones((dh, dw), np.float32)) * op
        if s.get("fx"):
            img, alpha = self.run_fx(s["fx"], img, alpha, t, self.state, "fx")
        H, W = canvas.shape[:2]
        pos = self.sig("pos", s.get("pos"), [W / self.k / 2, H / self.k / 2])(t)
        rot = self.sig("rot", s.get("rot"), 0)(t)
        clip = s.get("clip")
        if clip == "picture":
            clip = PICTURE
        if clip:
            clip = tuple(v * self.k for v in clip)
        composite(canvas, img, alpha, pos[0] * self.k, pos[1] * self.k, rot, s.get("blend", "normal"), clip)


def render_video(tl, frames, k, out, ctx, warm=0):
    """Render frame indices `frames` (song frame numbers); the first `warm` are pre-roll."""
    W, H = (int(tl["size"][0] * k) // 2 * 2, int(tl["size"][1] * k) // 2 * 2)
    fps = tl["fps"]
    # only the layers this frame range touches (a chunk of a full-song timeline sees a few dozen)
    lo, hi = (frames[0] / fps, frames[-1] / fps) if len(frames) else (0.0, -1.0)
    layers = [Layer(L, ctx, *tl["size"], k) for L in tl["layers"] if L["t0"] <= hi and L["t1"] > lo]
    post = Params(ctx, k) if tl.get("post") else None
    enc = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(fps),
         "-i", "-", "-c:v", "libx264", "-crf", os.environ.get("VIDBOX_CRF", "17" if k == 1 else "22"), "-preset", "medium" if k == 1 else "veryfast",
         "-pix_fmt", "yuv420p", "-an", str(out)],
        stdin=subprocess.PIPE)
    post_state = {}
    t_start = wall.time()
    for j, fno in enumerate(frames):
        t = fno / fps
        canvas = np.zeros((H, W, 3), np.float32)
        for L in layers:
            if L.t0 <= t < L.t1:
                if L.reader is None:
                    L.open()
                L.draw(canvas, t)
            elif L.reader is not None and t >= L.t1:
                L.close()
        if post:
            ones = np.ones((H, W), np.float32)
            canvas, _ = post.run_fx(tl["post"], canvas, ones, t, post_state, "post")
        if j >= warm:
            enc.stdin.write((np.clip(canvas, 0, 1) * 255 + 0.5).astype(np.uint8).tobytes())
        if j % 50 == 0 and j:
            el = wall.time() - t_start
            print(f"\r  {out.name}: {j}/{len(frames)} {j / el:.1f} fps", end="", file=sys.stderr)
    enc.stdin.close()
    enc.wait()
    for L in layers:
        L.close()
    print(file=sys.stderr)
    return enc.returncode


def atempo_chain(f):
    if not 0 < f < math.inf:   # 0 or inf would loop forever below, appending filters
        raise ValueError(f"atempo factor {f}")
    tempo = []
    while f > 2.0:
        tempo.append("atempo=2.0"); f /= 2
    while f < 0.5:
        tempo.append("atempo=0.5"); f /= 0.5
    if abs(f - 1) > 1e-3:
        tempo.append(f"atempo={f:.5f}")
    return tempo


_audio_cache = {}


def source_audio(src, until):
    """(samples [n, 2] float32 at SR, offset) for a media file's audio from its start up to
    `until` s; sample index of canonical (video-clock) time t = round(t * SR) + offset.
    None if the file has no audio stream."""
    key = str(src)
    if key in _audio_cache and _audio_cache[key][2] >= until:
        return _audio_cache[key][:2]
    info = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,start_time",
                                      "-of", "json", str(src)], capture_output=True, text=True, check=True).stdout)
    st = {s["codec_type"]: float(s.get("start_time") or 0) for s in info["streams"][::-1]}
    if "audio" not in st:
        _audio_cache[key] = (None, 0, float("inf"))
        return None, 0
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(src), "-t", f"{until + 1.0:.3f}", "-vn", "-ac", "2",
                          "-ar", str(SR), "-f", "f32le", "-"], capture_output=True, check=True).stdout
    y = np.frombuffer(raw, np.float32).reshape(-1, 2)
    off = int(round((st.get("video", st["audio"]) - st["audio"]) * SR))
    _audio_cache[key] = (y, off, until)
    return y, off


def _take(y, i0, n):
    out = np.zeros((n, 2), np.float32)
    a, b = max(0, i0), min(len(y), i0 + n)
    if b > a:
        out[a - i0:b - i0] = y[a:b]
    return out


def _atempo(x, f, n_out=None):
    """Pitch-preserving tempo change of stereo samples by factor f (ffmpeg atempo). n_out: samples
    needed; ffmpeg stops a second past them (its output is len(x) / f, unbounded as f -> 0)."""
    lim = ["-t", f"{n_out / SR + 1.0:.6f}"] if n_out is not None else []
    p = subprocess.run(["ffmpeg", "-v", "error", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-",
                        "-af", ",".join(atempo_chain(f)) or "anull", *lim, "-f", "f32le", "-"],
                       input=np.ascontiguousarray(x, np.float32).tobytes(), capture_output=True, check=True)
    return np.frombuffer(p.stdout, np.float32).reshape(-1, 2)


def _fit(x, n):
    return x[:n] if len(x) >= n else np.concatenate([x, np.zeros((n - len(x), 2), np.float32)])


AT_CTX = 2.0  # s of song time: most atempo context a slow constant-speed run gets (see layer_audio)
AXF = 0.005   # s: crossfade half-width where two pieces join continuously (e.g. map knots)


def layer_audio(L, r0, r1, ctx):
    """(start sample relative to r0, samples) for a layer whose time is any form: the source
    audio follows the same TimeMap as the frames, sample-exactly. Constant-speed runs keep pitch
    (atempo; audio.mode "tape" resamples instead); ramps and speed signals are tape (varispeed);
    holds are silent. Discontinuities (cuts, stutter retriggers, holds, layer edges) get AFADE
    fades; continuous joins between pieces of different speed are crossfaded over +-AXF."""
    T = L.get("time", {"in": 0.0, "speed": 1.0})
    a, b = max(L["t0"], r0), min(L["t1"], r1)
    n = int(round((b - a) * SR))
    if n <= 0:
        return None
    tm = compile_time(T, L["t0"], L["t1"], ctx)
    A = L["audio"]
    mode, fade = A.get("mode", "tempo"), A.get("fade", AFADE)
    runs = []
    for r in tm.runs:
        ra, rb = max(r.a, a), min(r.b, b)
        i0, i1 = int(round((ra - a) * SR)), int(round((rb - a) * SR))
        if i1 > i0 and r.constant_speed() != 0.0:
            runs.append((r, i0, i1, r.src(ra), r.src(rb)))
    if not runs:
        return None
    until = max(max(s0, s1) for _, _, _, s0, s1 in runs) + 0.1
    y, off = source_audio(ROOT / L["src"], until)
    if y is None:
        print(f"  audio skipped for {L.get('id')}: {L['src']} has no audio", file=sys.stderr)
        return None

    def render(r, j0, j1):
        """Samples for song-sample indices [j0, j1) through run r (extrapolated past its ends)."""
        m = j1 - j0
        v = r.constant_speed()
        ta, tb = a + j0 / SR, a + j1 / SR
        if v is not None:
            s0, s1 = r.s0 + v * (ta - r.a), r.s0 + v * (tb - r.a)
            if abs(abs(v) - 1) < 1e-3:
                if v > 0:
                    return _take(y, int(round(s0 * SR)) + off, m)
                return _take(y, int(round(s1 * SR)) + off, m)[::-1]
            if mode == "tempo":
                lo, hi = min(s0, s1), max(s0, s1)
                # source context so atempo has no edge transient: 0.05 s, but never more than
                # AT_CTX of song time once stretched (at |v| < 0.025 it would be lead / |v| s of output)
                c = min(0.05, AT_CTX * abs(v))
                c_lo, c_hi = min(c, max(0.0, lo)), c
                x = _take(y, int(round((lo - c_lo) * SR)) + off, int(round((hi - lo + c_lo + c_hi) * SR)))
                lead = c_hi if v < 0 else c_lo
                k = int(round(lead / abs(v) * SR))
                x = _atempo(x[::-1] if v < 0 else x, abs(v), k + m)
                return _fit(x[k:], m)
        pos = r.src_vec(ta + np.arange(m) / SR) * SR + off   # tape
        j = np.clip(np.floor(pos).astype(np.int64), 0, max(len(y) - 2, 0))
        u = (pos - j)[:, None].astype(np.float32)
        x = (y[j] * (1 - u) + y[j + 1] * u) if len(y) > 1 else np.zeros((m, 2), np.float32)
        x[(pos < 0) | (pos >= len(y) - 1)] = 0
        return x.astype(np.float32)

    out = np.zeros((n, 2), np.float32)
    nf = max(1, int(round(fade * SR)))
    e = int(round(AXF * SR))
    for k, (r, i0, i1, s0, s1) in enumerate(runs):
        prev = runs[k - 1] if k else None
        nxt = runs[k + 1] if k + 1 < len(runs) else None
        j_in = prev is not None and prev[2] == i0 and abs(prev[4] - s0) < 2 / SR
        j_out = nxt is not None and nxt[1] == i1 and abs(nxt[3] - s1) < 2 / SR
        w0 = max(0, i0 - e) if j_in else i0
        w1 = min(n, i1 + e) if j_out else i1
        x = render(r, w0, w1)
        g = np.ones(w1 - w0, np.float32)
        if j_in:   # linear crossfade with the previous piece: the two weights sum to 1
            g[:min(2 * e, len(g))] = np.clip((np.arange(min(2 * e, len(g))) + (w0 - (i0 - e)) + 0.5) / (2 * e), 0, 1)
        else:
            w = min(nf, (i1 - i0) // 2)
            g[:w] *= np.linspace(0, 1, w, dtype=np.float32)
        if j_out:
            q = min(2 * e, len(g))
            g[len(g) - q:] *= np.clip(((i1 + e) - (w1 - q + np.arange(q)) - 0.5) / (2 * e), 0, 1)
        else:
            w = min(nf, (i1 - i0) // 2)
            g[len(g) - w:] *= np.linspace(1, 0, w, dtype=np.float32)
        out[w0:w1] += x * g[:, None]
    out *= float(A.get("gain", 1.0))
    return int(round((a - r0) * SR)), out


ENV_RATE = 1000   # Hz: music volume envelope sampling


def mux_audio(tl, video, out, r0, r1, ctx=None):
    """Mux `video` with the music and every audio layer over song [r0, r1). Layers are mixed into
    one sample-exact bus by layer_audio (all time forms, constant speed included); ffmpeg only adds
    the music, which it seeks itself."""
    if ctx is None:
        pdir = ROOT / "projects" / tl["project"]
        ctx = Ctx(Music(pdir / "analysis/beats.json"), pdir)
    ins = ["-i", str(video), "-ss", f"{r0:.4f}", "-i", str(ROOT / tl["music"]["src"])]
    # asetpts on every input: the music's first opus packet has pts < 0, which otherwise makes the
    # mp4 keep 1008 samples of AAC priming (the whole mix 21 ms late against the picture)
    mg = tl["music"].get("gain", 1.0)
    if isinstance(mg, (int, float)):
        chains = [f"[1:a]asetpts=PTS-STARTPTS,volume={mg},apad=whole_dur={r1 - r0:.4f}[a0]"]   # pad: renders may outrun the song
        env_path = None
    else:   # a signal: the music's volume follows it (e.g. dipping so source audio punches through)
        g = compile_signal(mg, ctx)
        env = np.array([g(r0 + i / ENV_RATE) for i in range(int((r1 - r0) * ENV_RATE) + 2)], np.float32)
        env_path = Path(video).with_name("music_env.f32")
        env_path.write_bytes(env.tobytes())
        chains = [f"[1:a]asetpts=PTS-STARTPTS,aresample={SR},aformat=sample_fmts=flt:channel_layouts=stereo[mus]"]
    n = 1
    bus = None
    for L in tl["layers"]:
        if "audio" not in L or L["t1"] <= r0 or L["t0"] >= r1:
            continue
        got = layer_audio(L, r0, r1, ctx)
        if got is not None:
            if bus is None:
                bus = np.zeros((int(round((r1 - r0) * SR)), 2), np.float32)
            i0, x = got
            m = min(len(x), len(bus) - i0)
            bus[i0:i0 + m] += x[:m]
    if bus is not None:
        bus_path = Path(video).with_name("audio_bus.f32")
        bus_path.write_bytes(bus.tobytes())
        ins += ["-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", str(bus_path)]
        chains.append(f"[{n + 1}:a]asetpts=PTS-STARTPTS[a{n}]")
        n += 1
    if env_path is not None:   # the envelope is the last input
        ins += ["-f", "f32le", "-ar", str(ENV_RATE), "-ac", "1", "-i", str(env_path)]
        chains.append(f"[{len([x for x in ins if x == '-i']) - 1}:a]aresample={SR},pan=stereo|c0=c0|c1=c0,"
                      f"aformat=sample_fmts=flt:channel_layouts=stereo[env];[mus][env]amultiply,apad=whole_dur={r1 - r0:.4f}[a0]")
    graph = ";".join(chains) + ";" + "".join(f"[a{i}]" for i in range(n)) + \
        f"amix=inputs={n}:normalize=0:duration=first,alimiter=limit=0.95:latency=1[aout]"   # latency=1: no 5 ms lookahead delay
    subprocess.run(["ffmpeg", "-v", "error", "-y", *ins, "-filter_complex", graph, "-map", "0:v", "-map", "[aout]",
                    "-t", f"{r1 - r0:.4f}", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart",
                    str(out)], check=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("timeline")
    ap.add_argument("--full", action="store_true")
    ap.add_argument("--range", nargs=2, type=float)
    ap.add_argument("--jobs", type=int, default=1)
    ap.add_argument("-o", "--out")
    ap.add_argument("--chunk", help=argparse.SUPPRESS)   # internal: "a b warm out" frame range
    a = ap.parse_args()

    tl_path = Path(a.timeline).resolve()
    tl = json.loads(tl_path.read_text())
    pdir = ROOT / "projects" / tl["project"]
    ctx = Ctx(Music(pdir / "analysis/beats.json"), pdir)
    k = 1.0 if a.full else 0.5
    fps = tl["fps"]

    if a.chunk:
        f0, f1, warm, out = a.chunk.split()
        sys.exit(render_video(tl, range(int(f0), int(f1)), k, Path(out), ctx, int(warm)))

    r0, r1 = a.range or tl["range"]
    base = tl_path.name.removesuffix(".timeline.json").removesuffix(".json")
    out = Path(a.out) if a.out else tl_path.parent / f"{base}{'.full' if a.full else ''}.mp4"
    F0, F1 = round(r0 * fps), round(r1 * fps)
    t_wall = wall.time()
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        jobs = max(1, min(a.jobs, (F1 - F0) // (fps * 4) or 1))
        bounds = np.linspace(F0, F1, jobs + 1).round().astype(int)
        procs, parts = [], []
        for i in range(jobs):
            s, e = int(bounds[i]), int(bounds[i + 1])
            warm = int(PREROLL * fps) if i > 0 else 0
            part = tmp / f"part{i:03d}.mp4"
            parts.append(part)
            procs.append(subprocess.Popen([sys.executable, __file__, str(tl_path), *(["--full"] if a.full else []),
                                           "--chunk", f"{s - warm} {e} {warm} {part}"]))
        codes = [p.wait() for p in procs]
        if any(codes):
            sys.exit(f"chunk render failed: {codes}")
        (tmp / "list.txt").write_text("".join(f"file '{p}'\n" for p in parts))
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", tmp / "list.txt",
                        "-c", "copy", tmp / "video.mp4"], check=True)
        mux_audio(tl, tmp / "video.mp4", out, r0, r1, ctx)
    print(f"wrote {out} ({r1 - r0:.1f}s of song) in {wall.time() - t_wall:.1f}s with {jobs} job(s)",
          file=sys.stderr)


if __name__ == "__main__":
    main()
