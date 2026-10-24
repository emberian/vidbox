"""Helpers for s1_build: head copies with characters, gaze-steered and bounced motion,
formation sequences with morphs, multi-hit landing and grooved (retimed) footage.

Everything returns plain timeline dicts/signals (render/TIMELINE.md), built on comp.py.
"""
import json
import math
import random
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "render"))
from bezier import Path as BezierPath  # noqa: E402
from comp import beat, dense, keys, rng  # noqa: E402

FACE = "media/derived/face.mp4"        # 36.79 s, 480x600, his own clock
FACE_LOOP = [0.3, 36.4]
PATHS = ROOT / "projects/meine/paths"
DT = 0.04
_path_cache = {}


def path(name):
    if name not in _path_cache:
        _path_cache[name] = BezierPath(json.loads((PATHS / f"{name}.json").read_text()))
    return _path_cache[name]


def src_time(t, t0, src_in, speed=1.0, loop=FACE_LOOP):
    s = src_in + (t - t0) * speed
    if loop:
        a, b = loop
        s = a + (s - a) % (b - a)
    return s


def smooth(u):
    u = min(max(u, 0.0), 1.0)
    return u * u * (3 - 2 * u)


# ---- characters: an fx stack per head copy ----
def character(i, energy=None):
    """fx stack for head copy i. energy: a 0..1 signal scaling how hard it pulses (default: on the beat)."""
    e = energy if energy is not None else beat(1, "decay", tau=0.18)
    hue0 = (i * 47) % 360
    C = [
        # 0: chromatic hue cycle, RGB split on every beat
        [{"op": "hue", "deg": rng(hue0, hue0 + 180, beat(4, "saw"))},
         {"op": "chroma", "px": rng(2, 22, e), "angle": 15}],
        # 1: blender-ish RGB noise texture, overlay
        [{"op": "noise", "scale": 34, "octaves": 3, "mode": "overlay", "color": "rgb", "speed": 0.9, "seed": 11,
          "amount": rng(0.35, 0.85, e)},
         {"op": "sat", "factor": 1.6}],
        # 2: posterized blood duotone
        [{"op": "posterize", "levels": 3},
         {"op": "duotone", "dark": [0.08, 0.0, 0.04], "light": [1.0, 0.25, 0.12]},
         {"op": "chroma", "px": rng(0, 12, e), "angle": 90}],
        # 3: hard threshold cracked by Voronoi edges (Blender's crackle)
        [{"op": "contrast", "factor": 1.4},
         {"op": "threshold", "level": rng(0.42, 0.3, e), "soft": 0.05},
         {"op": "voronoi", "feature": "edge", "scale": 26, "speed": 0.6, "seed": 3, "mode": "mul", "amount": 0.8},
         {"op": "tint", "color": [0.7, 1.0, 0.8]}],
        # 4: pixelated, pixel size kicks on the beat
        [{"op": "pixelate", "px": rng(3, 18, e)},
         {"op": "hue", "deg": rng(hue0, hue0 - 90, beat(2, "tri"))},
         {"op": "sat", "factor": 1.8}],
        # 5: liquid warp + green/magenta noise
        [{"op": "warp", "scale": 60, "px": rng(4, 22, e), "speed": 0.8, "seed": 5},
         {"op": "noise", "scale": 70, "mode": "overlay", "color": [0.3, 1.0, 0.6], "speed": 0.5, "seed": 5,
          "amount": 0.6}],
        # 6: negative, chroma-split
        [{"op": "invert"},
         {"op": "hue", "deg": rng(0, 360, beat(8, "saw"))},
         {"op": "chroma", "px": rng(3, 16, e), "angle": 200}],
        # 7: cyan/magenta duotone, scanlines
        [{"op": "posterize", "levels": 4},
         {"op": "duotone", "dark": [0.15, 0.0, 0.35], "light": [0.3, 1.0, 1.0]},
         {"op": "scanlines", "period": 4, "dark": 0.45}],
        # 8: gold posterize, noise burn
        [{"op": "posterize", "levels": 5},
         {"op": "duotone", "dark": [0.1, 0.05, 0.0], "light": [1.0, 0.85, 0.3]},
         {"op": "noise", "scale": 50, "octaves": 4, "mode": "mul", "speed": 0.6, "seed": 8, "amount": rng(0.2, 0.6, e)}],
        # 9: thermal: his face through the strike camera's ironbow palette, cycling on the bar
        [{"op": "gradmap", "palette": "ironbow", "cycle": beat(4, "saw")},
         {"op": "chroma", "px": rng(0, 10, e), "angle": 0}],
        # 10: crystallized: each Voronoi cell flat-filled
        [{"op": "voronoi", "feature": "cells", "scale": 22, "speed": 0.5, "seed": 10, "lines": 0.3},
         {"op": "sat", "factor": 1.7}],
        # 11: halftone pop-art, dots swell on the beat
        [{"op": "halftone", "mode": "rgb", "period": rng(7, 12, e)}],
        # 12: neon edges, acid palette
        [{"op": "gradmap", "palette": "acid", "cycle": beat(2, "saw")},
         {"op": "edgeglow", "base": 0.5, "color": "source", "gain": rng(0.8, 2.0, e)}],
        # 13: time-smeared RGB (each channel a different moment), glitch bands on the beat
        [{"op": "chromatime", "delay": 3},
         {"op": "glitch", "strength": rng(0, 0.8, e), "seed": 13}],
    ]
    return C[i % len(C)]


def head(id, t0, t1, pos, scale, src_in=0.0, speed=1.0, fx=(), opacity=1.0, fade=None, tags=("head", "copy"),
         hold=None, rot=0, feather=0.3, src=FACE, loop=FACE_LOOP, **extra):
    L = {"id": id, "tags": list(tags), "src": src, "t0": round(t0, 4), "t1": round(t1, 4),
         "time": {"hold": hold} if hold is not None else {"in": round(src_in, 3), "speed": speed, **({"loop": loop} if loop else {})},
         "size": [480, 600], "mask": {"shape": "oval", "feather": feather},
         "pos": pos, "scale": scale, "opacity": opacity, "fx": list(fx)}
    if rot:
        L["rot"] = rot
    if fade:
        L["fade"] = fade
    L.update(extra)
    return L


# ---- motion ----
def dense_track(t0, t1, fn, dt=DT):
    """fn(t) -> (x, y, s). Returns (pos_signal, scale_signal) sampled every dt."""
    P, S = [], []
    for t in np.arange(t0, t1 + dt, dt):
        x, y, s = fn(float(t))
        P.append([round(x, 1), round(y, 1)])
        S.append(round(s, 4))
    return dense(round(t0, 4), dt, P), dense(round(t0, 4), dt, S)


def gaze_offset(t, t0, src_in, speed=1.0, name="face_self_gaze", k=0.3):
    """Where his own face is looking, as an offset from frame centre, scaled by k; and the path's scale."""
    p = path(name)
    s = src_time(t, t0, src_in, speed)
    x, y = p(s)
    return k * (x - 720), k * (y - 540), p.scale(s)


def bounce_keys(c, t0, t1, box, choices, seed=0, start=None):
    """Pong flights between box walls, every wall contact on a beat. choices(t) -> tuple of
    beats-per-crossing allowed at time t (so crossings can speed up as the music does).
    Returns a list of [t, [x, y]] keyframes."""
    r = random.Random(seed)
    x0, y0, x1, y1 = box
    p = list(start) if start else [r.uniform(x0, x1), r.uniform(y0, y1)]
    t = c.snap(t0)
    K = [[round(t0, 4), [round(p[0], 1), round(p[1], 1)]]]
    last = None
    while t < t1:
        nb = r.choice(choices(t))
        tn = c.snap(t + nb * c.period)
        if tn <= t + 1e-6:   # nb < 0.5 snaps back onto t: the keys would grow forever
            raise ValueError(f"bounce_keys: {nb} beats from {t:.3f} does not reach the next beat")
        side = r.choice([s for s in "lrtb" if s != last])
        last = side
        q = {"l": [x0, r.uniform(y0, y1)], "r": [x1, r.uniform(y0, y1)],
             "t": [r.uniform(x0, x1), y0], "b": [r.uniform(x0, x1), y1]}[side]
        K.append([round(tn, 4), [round(q[0], 1), round(q[1], 1)]])
        t = tn
    return K


def interp_keys(K, t):
    ts = [k[0] for k in K]
    if t <= ts[0]:
        return K[0][1]
    if t >= ts[-1]:
        return K[-1][1]
    i = int(np.searchsorted(ts, t, side="right")) - 1
    (a, p), (b, q) = K[i], K[i + 1]
    u = (t - a) / (b - a)
    return [p[0] + (q[0] - p[0]) * u, p[1] + (q[1] - p[1]) * u]


# ---- formations ----
def shape16(name, n):
    """Unit-ish 3D point sets for n copies."""
    if name == "cube":
        V = [(x, y, z) for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)]
        E = [(0, y, z) for y in (-1, 1) for z in (-1, 1)] + [(x, 0, z) for x in (-1, 1) for z in (-1, 1)] + \
            [(x, y, 0) for x in (-1, 1) for y in (-1, 1)]
        P = [tuple(v * 0.8 for v in p) for p in V + E]
        return [P[i % len(P)] for i in range(n)]
    if name == "sphere":
        g = math.pi * (3 - math.sqrt(5))
        return [(math.cos(g * i) * math.sqrt(1 - y * y), y, math.sin(g * i) * math.sqrt(1 - y * y))
                for i, y in ((i, 1 - 2 * (i + 0.5) / n) for i in range(n))]
    if name == "helix":   # double helix, two strands
        out = []
        for i in range(n):
            strand, j = i % 2, i // 2
            m = max(n // 2 - 1, 1)
            a = j * 2 * math.pi / m * 0.9 + strand * math.pi
            out.append((0.75 * math.cos(a), -1.15 + 2.3 * j / m, 0.75 * math.sin(a)))
        return out
    if name == "ring":
        return [(math.cos(2 * math.pi * i / n), 0, math.sin(2 * math.pi * i / n)) for i in range(n)]
    if name == "grid":    # a flat 4x4 sheet facing camera
        s = int(math.ceil(math.sqrt(n)))
        return [(-1 + 2 * (i % s) / (s - 1), -1 + 2 * (i // s) / (s - 1), 0) for i in range(n)]
    if name == "point":
        return [(0, 0, 0)] * n
    if name == "torus":
        return [((1 + 0.35 * math.cos(3 * 2 * math.pi * i / n)) * math.cos(2 * math.pi * i / n),
                 0.35 * math.sin(3 * 2 * math.pi * i / n),
                 (1 + 0.35 * math.cos(3 * 2 * math.pi * i / n)) * math.sin(2 * math.pi * i / n)) for i in range(n)]
    raise ValueError(name)


def formation_track(c, n, blocks, t_end, center, radius, base_scale=0.17, depth=3.2, morph_beats=2,
                    tilt=0.45, wobble_bars=8.0, pulse=None, dt=DT):
    """Copies tracing a sequence of 3D shapes, perspective-projected, rotation locked to the bar grid.
    blocks: [(shape, t_start, spin), ...] ascending; each holds until the next starts (the last until
    t_end), morphing into the next over its final `morph_beats` beats (smoothstep). spin per block:
      ("smooth", bars)  one Y turn every `bars` bars
      ("step", frac)    snaps round by `frac` of a turn on every downbeat, eased over the first beat
      ("beat", frac)    the same on every beat
      ("still", 0)
    Rotation is continuous across blocks. center(t) / radius(t) may be callables; pulse(t) multiplies
    the radius. Returns [(pos_signal, scale_signal)] per copy."""
    t0 = blocks[0][1]
    bar_len = 4 * c.period
    pts = [shape16(b[0], n) for b in blocks]
    starts = [b[1] for b in blocks] + [t_end]
    ctr = center if callable(center) else (lambda t: center)
    rad = radius if callable(radius) else (lambda t: radius)

    def block_angle(k, t):
        mode, v = blocks[k][2]
        ts = starts[k]
        if mode == "smooth":
            return 2 * math.pi * (t - ts) / (v * bar_len)
        if mode in ("step", "beat"):
            unit = bar_len if mode == "step" else c.period
            x = (t - ts) / unit
            whole = math.floor(x)
            return 2 * math.pi * v * (whole + smooth((x - whole) * (4 if mode == "step" else 2)))
        return 0.0
    base = [0.0]
    for k in range(len(blocks) - 1):
        base.append(base[-1] + block_angle(k, starts[k + 1]))
    ts_all = np.arange(t0, t_end + dt, dt)
    tracks = [([], []) for _ in range(n)]
    for t in ts_all:
        t = float(t)
        k = max(i for i in range(len(blocks)) if starts[i] <= t + 1e-9)
        P = pts[k]
        if k + 1 < len(blocks):
            m0 = starts[k + 1] - morph_beats * c.period
            u = smooth((t - m0) / (morph_beats * c.period)) if t > m0 else 0.0
            if u > 0:
                Q = pts[k + 1]
                P = [tuple(p[d] + (q[d] - p[d]) * u for d in range(3)) for p, q in zip(P, Q)]
        a = base[k] + block_angle(k, t)
        b = tilt * math.sin(2 * math.pi * (t - t0) / (wobble_bars * bar_len))
        ca, sa, cb, sb = math.cos(a), math.sin(a), math.cos(b), math.sin(b)
        cx, cy = ctr(t)
        R = rad(t) * (pulse(t) if pulse else 1.0)
        for j, (x, y, z) in enumerate(P):
            x1, z1 = x * ca + z * sa, -x * sa + z * ca
            y2, z2 = y * cb - z1 * sb, y * sb + z1 * cb
            persp = depth / (depth + z2)
            tracks[j][0].append([round(cx + x1 * R * persp, 1), round(cy + y2 * R * persp, 1)])
            tracks[j][1].append(round(base_scale * persp, 4))
    return [(dense(round(t0, 4), dt, p), dense(round(t0, 4), dt, s)) for p, s in tracks]


# ---- framing ----
_dims = {}
PIC_W, PIC_H = 1440, 764     # Meine's letterboxed picture area


def dims(src):
    if src not in _dims:
        import subprocess
        out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                              "stream=width,height", "-of", "csv=p=0", str(ROOT / src)],
                             capture_output=True, text=True, check=True).stdout.strip().split(",")
        _dims[src] = (int(out[0]), int(out[1]))
    return _dims[src]


def aspect_crop(src, aspect, crop=(0, 0, 1, 1), anchor=0.5):
    """Shrink a normalized crop so the cropped source has the given aspect (w/h)."""
    w, h = dims(src)
    x0, y0, x1, y1 = crop
    cw, ch = (x1 - x0) * w, (y1 - y0) * h
    if cw / ch > aspect:      # too wide: trim x
        nw = ch * aspect / w
        x0 = x0 + ((x1 - x0) - nw) * anchor
        x1 = x0 + nw
    else:
        nh = cw / aspect / h
        y0 = y0 + ((y1 - y0) - nh) * anchor
        y1 = y0 + nh
    return [round(x0, 4), round(y0, 4), round(x1, 4), round(y1, 4)]


def picture(seg_or_src, crop=(0, 0, 1, 1), anchor=0.5):
    """Props that fill exactly Meine's picture area (y 158..922), cropping the source to fit."""
    src = seg_or_src if isinstance(seg_or_src, str) else seg_or_src.file
    return {"crop": aspect_crop(src, PIC_W / PIC_H, crop, anchor), "size": [PIC_W, PIC_H], "pos": [720, 540]}


def panel(seg_or_src, w, h, pos, crop=(0, 0, 1, 1), feather=0.06):
    """Props for an inset window of w x h canvas px at pos (signal), source cropped to its aspect."""
    src = seg_or_src if isinstance(seg_or_src, str) else seg_or_src.file
    return {"crop": aspect_crop(src, w / h, crop), "size": [w, h], "pos": pos,
            "mask": {"shape": "rect", "feather": feather}}


# ---- footage timing ----
def land_hits(c, seg, at, hits=None, div=1.0, before=0.6, after=1.5, max_dev=0.35, id=None, **props):
    """Multi-hit landing: the first chosen hit lands at `at`; each later hit on the grid point (div
    beats) nearest its natural spacing, skipping any that would push the speed beyond 1 +- max_dev.
    Delegates to comp.Comp.footage_multi."""
    hits = list(range(len(seg.hits))) if hits is None else list(hits)
    H = [seg.hits[i]["t"] for i in hits]
    song, keep = [at], [hits[0]]
    last_src = H[0]
    for i, h in zip(hits[1:], H[1:]):
        tgt = c.snap(song[-1] + (h - last_src), div)
        if tgt <= song[-1]:
            tgt = c.beats_after(song[-1], div)
        if abs((h - last_src) / (tgt - song[-1]) - 1) > max_dev:
            continue
        song.append(tgt)
        keep.append(i)
        last_src = h
    return c.footage_multi(seg, keep, song, before=before, after=after, id=id, **props)


def map_footage(c, seg, song, src, hits_song=(), id=None, **props):
    """Place a segment with an explicit piecewise song->source map."""
    layer = {"id": id or f"{seg.clip['id']}#{seg.idx}@{song[0]:.2f}map", "tags": [seg.catalog] + seg.tags[:3],
             "src": seg.file, "t0": round(song[0], 4), "t1": round(song[-1], 4),
             "time": {"map": {"song": [round(x, 4) for x in song], "src": [round(x, 4) for x in src]}},
             "meta": {"catalog": seg.catalog, "clip": seg.clip["id"], "seg": seg.idx,
                      "hits_song": [round(x, 3) for x in hits_song]},
             **props}
    c.layers.append(layer)
    return layer


def groove(c, seg, at, dur, cycle, beats, src_in=None, id=None, **props):
    """Rhythmic footage locked to the grid: one motion cycle (`cycle` source s) per `beats` beats,
    phase-anchored at source time src_in (comp.Comp.groove, forced to that musical length)."""
    lay = c.groove(seg, at, dur=dur, lengths=(beats,), limits=(0.2, 5.0), anchor=src_in, cycle=cycle, id=id, **props)
    lay["tags"].append("groove")
    return lay


# ---- real speakers (tools/preacher_prep.py -> media/derived/preachers/<clip>__<line>.mp4 + .json) ----
PREACH = "media/derived/preachers"
IVOICES = "media/derived/israeli_voices"     # tools/preacher_prep.py --catalog israeli_voices
SPEECH_DIRS = {"preachers": PREACH, "israeli_voices": IVOICES}


def speech(stem, base=PREACH):
    """The sidecar of a prepared line: span in the raw file, speaker, words in the clip's own clock (and,
    for a translated catalog, its lang and lines: text, translation and source, in the clip's clock)."""
    return json.loads((ROOT / base / f"{stem}.json").read_text())


def word_at(ln, word, k=1):
    """Clip time of the k-th occurrence of `word` (case and punctuation ignored)."""
    key = word.lower().strip(".,?!'\"")
    hits = [w for w in ln["words"] if w["w"].lower().strip(".,?!'\"") == key]
    if len(hits) < k:
        raise KeyError(f"{ln['clip']}/{ln['label']}: no {word!r} #{k}")
    return hits[k - 1]["start"]
