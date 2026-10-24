"""Helpers for s2_peak: the preacher's word sampler, gaze/drift paths re-timed onto song time,
multi-hit landing and a head chorus whose members
step forward to say a word.

Everything here writes plain TIMELINE.md layers through a comp.Comp.
"""
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "render"))
from bezier import Path as BPath  # noqa: E402
from comp import dense, keys, mul  # noqa: E402

FACE = "media/derived/face.mp4"      # the face-tracked rant in its own time, with his voice
FACE_DUR = 36.8
PDIR = ROOT / "projects/meine"

# Word samples in face.mp4 time: (clip in, anchor, clip out). The anchor (the stressed onset of
# the key word, from analysis/rant_words.json) is what lands on the beat; the rest is pickup/tail.
SAMPLES = {
    "missiles": (18.96, 19.02, 19.62),             # "...Israel MISSILES." cleanest: 0.5 s of air after
    "missiles.b": (10.20, 10.262, 10.86),          # "more and more MISSILES."
    "missiles.c": (11.86, 11.922, 12.43),          # "more MISSILES in Israel"
    "missiles.d": (14.10, 14.142, 14.64),          # "as many MISSILES as"
    "missiles.e": (21.54, 21.58, 22.04),           # "all the MISSILES"
    "hellfire missiles": (5.10, 5.721, 6.24),      # pickup "Hellfire", "missiles" on the beat
    "more and more missiles": (9.52, 10.262, 10.86),
    "they need more missiles": (11.05, 11.922, 12.43),
    "give israel missiles": (18.12, 19.02, 19.62),
    "thou shalt give israel missiles": (17.50, 19.02, 19.62),
    "all the missiles they need": (21.15, 21.58, 22.62),
    "not paying enough": (33.45, 33.49, 34.55),
    "should be paying 75": (34.74, 34.77, 36.62),  # "I should be paying seventy-five percent"
    "75": (35.28, 35.30, 36.62),
    "ripped from me": (26.30, 26.36, 27.42),
    # his other lines (ember: "we have SO many more voicelines"), anchor on the stressed word
    "trillion bajillion": (1.24, 1.60, 3.34),      # "one TRILLION bajillion dollars"
    "weak and unprotected": (6.48, 7.86, 8.98),    # "because they're so WEAK and unprotected"
}

# stretches of face.mp4 with no word onsets near the loop seams, for silent mouthing copies
MOUTH_LOOP = (0.5, 34.5)


def _path(rel):
    return BPath(json.loads((PDIR / rel).read_text()))


def retime_path(path_rel, src_in, t0, t1, center=(720, 540), k=1.0, scale_k=1.0, loop=MOUTH_LOOP,
                dt=0.04, clamp=None):
    """A face-time Bezier path (paths/face_self_*.json) re-timed for a head playing face.mp4 from
    `src_in` at song time t0 (looping over `loop`). Positions are mapped about the canvas centre:
    p -> center + (p - (720, 540)) * k. Returns (pos, scale) dense signals."""
    P = _path(path_rel)
    a, b = loop
    pos, sc = [], []
    n = int(math.ceil((t1 - t0) / dt)) + 1
    for i in range(n):
        s = a + ((src_in - a) + i * dt) % (b - a)
        x, y = P(s)
        x, y = center[0] + (x - 720) * k, center[1] + (y - 540) * k
        if clamp:
            x, y = min(max(x, clamp[0]), clamp[2]), min(max(y, clamp[1]), clamp[3])
        pos.append([round(x, 1), round(y, 1)])
        sc.append(round(P.scale(s) * scale_k, 4))
    return dense(t0, dt, pos), dense(t0, dt, sc)


def say(c, at, sample="missiles", pos=(720, 540), scale=0.5, gain=1.0, size=(480, 600), id=None,
        fx=None, mask=None, opacity=0.95, pop=None, **props):
    """The preacher says `sample` with its anchor landing on song time `at` (put that on a beat)."""
    a, anc, b = SAMPLES[sample]
    t0, t1 = at - (anc - a), at + (b - anc)
    sc = scale
    if pop:   # grow into the word and settle
        sc = mul(scale, keys([t0, 1.0], [at, pop], [t1, pop * 0.92], ease="smooth"))
    layer = {"id": id or f"say:{sample}@{at:.2f}", "tags": ["head", "say"], "src": FACE,
             "t0": round(t0, 4), "t1": round(t1, 4), "time": {"in": a, "speed": 1.0},
             "size": list(size), "pos": pos, "scale": sc,
             "mask": mask or {"shape": "oval", "feather": 0.28}, "opacity": opacity,
             "fade": {"in": 0.05, "out": 0.08}, "audio": {"gain": gain},
             "meta": {"word": sample, "hits_song": [round(at, 3)]}, **props}
    if fx:
        layer["fx"] = fx
    return c.add(layer)


def mute_signal(intervals, base=1.0, xf=0.05):
    """Opacity `base`, dropping to 0 inside each (a, b) interval (cross-fading over xf)."""
    if not intervals:
        return base
    pts = [[0.0, base]]
    for a, b in sorted(intervals):
        pts += [[a - xf, base], [a, 0.0], [b, 0.0], [b + xf, base]]
    return keys(*pts)


class Chorus:
    """N silent copies of the preacher; any member can step forward and say a word (it is
    hidden while a speaking copy at its own position and scale, popped larger, says it)."""

    def __init__(self, c, n, src_offsets=None):
        self.c, self.n = c, n
        self.parts = [[] for _ in range(n)]      # per copy: [(t0, t1, pos, scale, props)]
        self.mutes = [[] for _ in range(n)]
        self.src_offsets = src_offsets or [(i * 4.3) % 30 + 0.5 for i in range(n)]

    def part(self, j, t0, t1, pos, scale, **props):
        self.parts[j].append((t0, t1, pos, scale, props))

    def where(self, j, t):
        for p in self.parts[j]:
            if p[0] <= t < p[1]:
                return p
        return None

    def speak(self, j, at, sample="missiles", pop=1.8, gain=1.0, fx=None, **kw):
        p = self.where(j, at)
        if p is None:
            raise ValueError(f"copy {j} not on screen at {at}")
        a, anc, b = SAMPLES[sample]
        self.mutes[j].append((at - (anc - a), at + (b - anc)))
        base_size = p[4].get("size", [480, 600])
        return say(self.c, at, sample, pos=p[2], scale=p[3], gain=gain, size=base_size, pop=pop,
                   fx=fx if fx is not None else p[4].get("say_fx"), id=f"say{j}:{sample}@{at:.2f}", **kw)

    def speak_real(self, j, at, stem, key, k=1, first=None, last=None, catalog="preachers", pop=1.8, gain=2.4,
                   sub=None, fx=None, pre=0.08, post=0.15):
        """Copy j steps forward as a REAL speaker: a phrase of a prepared face-tracked line (s1_lib.speech:
        media/derived/preachers or media/derived/israeli_voices) whose word `key` (k-th occurrence) starts
        exactly at `at`; the phrase runs from word `first` to word `last` (each `word` or (word, k); default:
        the key word alone). Same place, scale and pop as a Hyde word, the copy hidden meanwhile. A line not
        in English carries meta.lang and the subtitle `sub` (the faithful translation of exactly the phrase)."""
        import s1_lib
        p = self.where(j, at)
        if p is None:
            raise ValueError(f"copy {j} not on screen at {at}")
        base = s1_lib.SPEECH_DIRS[catalog]
        ln = s1_lib.speech(stem, base)

        def find(spec):
            word, n = spec if isinstance(spec, tuple) else (spec, 1)
            hits = [w for w in ln["words"] if w["w"].lower().strip(".,?!'\"") == word.lower()]
            if len(hits) < n:
                raise KeyError(f"{stem}: no {word!r} #{n}")
            return hits[n - 1]
        kw = find((key, k))
        a = max(0.0, (find(first)["start"] if first else kw["start"]) - pre)
        b = min(ln["span"][1] - ln["span"][0], (find(last)["end"] if last else kw["end"]) + post)
        t0 = at - (kw["start"] - a)
        t1 = t0 + (b - a)
        self.mutes[j].append((t0, t1))
        L = {"id": f"real{j}:{stem}@{at:.2f}", "tags": ["head", "say", "chorus", "real-line"],
             "src": f"{base}/{stem}.mp4", "t0": round(t0, 4), "t1": round(t1, 4), "time": {"in": round(a, 3), "speed": 1.0},
             "size": [480, 600], "pos": p[2], "scale": mul(p[3], keys([t0, 1.0], [at, pop], [t1, pop * 0.92], ease="smooth")),
             "mask": {"shape": "oval", "feather": 0.28}, "opacity": 0.95, "fade": {"in": 0.05, "out": 0.08},
             "audio": {"gain": gain}, "fx": fx if fx is not None else p[4].get("say_fx", []),
             "meta": {"catalog": catalog, "clip": stem, "seg": 0, "hits_song": [round(at, 3)], "word": key,
                      "people": [{"name": ln["person"], "role": ln["role"], "date": ln["date"],
                                  "source": ln["source_url"]}]}}
        if ln.get("lang", "en") != "en":
            if not sub:
                raise ValueError(f"{stem}: a {ln['lang']} phrase needs its subtitle")
            L["meta"]["lang"] = ln["lang"]
            self.c.subtitle(sub, t0 - 0.05, t1 - t0 + 0.45, id=f"sub:{L['id']}", meta={"z": 6, "lang": ln["lang"]})
        return self.c.add(L)

    def stutter(self, j, at, ref="missiles#4", stutter=2, div=0.25, pop=2.0, gain=1.0, fx=None, **kw):
        """Like speak, through comp.say (the time lane's sampler): "mi-mi-missiles" with the
        fragments on the grid starting at `at`."""
        p = self.where(j, at)
        if p is None:
            raise ValueError(f"copy {j} not on screen at {at}")
        L = self.c.say(ref, at, stutter=stutter, div=div, gain=gain, pos=p[2],
                       scale=mul(p[3], keys([at, pop * 0.8], [at + 0.3, pop], ease="smooth")),
                       fx=fx if fx is not None else p[4].get("say_fx"), id=f"stut{j}:{ref}@{at:.2f}",
                       fade={"in": 0.03, "out": 0.08}, **kw)
        self.mutes[j].append((L["t0"], L["t1"]))
        return L

    def emit(self):
        for j in range(self.n):
            for k, (t0, t1, pos, sc, props) in enumerate(self.parts[j]):
                props = {kk: v for kk, v in props.items() if kk != "say_fx"}
                base_op = props.pop("opacity", 0.9)
                ms = [(a, b) for a, b in self.mutes[j] if b > t0 and a < t1]
                if ms:
                    op = mute_signal(ms, 1.0)
                    base_op = mul(base_op, op) if not isinstance(base_op, (int, float)) or base_op != 1 else op
                L = {"id": f"chorus{j}.{k}", "tags": ["head", "chorus"], "src": FACE,
                     "t0": round(t0, 4), "t1": round(t1, 4),
                     "time": {"in": round(self.src_offsets[j], 3), "speed": 1.0, "loop": list(MOUTH_LOOP)},
                     "size": [480, 600], "mask": {"shape": "oval", "feather": 0.3},
                     "pos": pos, "scale": sc, "opacity": base_op, **props}
                self.c.add(L)


# ---- evaluating our own signals at build time (for motion that chains from one to the next) ----
def ev(sig, t):
    if isinstance(sig, (int, float)):
        return sig
    if isinstance(sig, (list, tuple)):
        return [ev(s, t) for s in sig]
    if "dense" in sig:
        d = sig["dense"]
        v, n = d["v"], len(d["v"])
        x = min(max((t - d["t0"]) / d["dt"], 0), n - 1)
        i = min(int(x), max(n - 2, 0))
        if n == 1:
            return v[0]
        a, b, u = v[i], v[i + 1], x - i
        return [a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u] if isinstance(a, list) else a + (b - a) * u
    if "k" in sig:
        K = sorted(sig["k"], key=lambda k: k[0])
        if t <= K[0][0]:
            return K[0][1]
        for (ta, va), (tb, vb) in zip(K, K[1:]):
            if ta <= t <= tb:
                u = (t - ta) / (tb - ta) if tb > ta else 1
                if sig.get("ease") == "smooth":
                    u = u * u * (3 - 2 * u)
                elif sig.get("ease") == "hold":
                    u = 0
                return [a + (b - a) * u for a, b in zip(va, vb)] if isinstance(va, list) else va + (vb - va) * u
        return K[-1][1]
    raise ValueError(f"ev: can't evaluate {list(sig)}")


def smooth(u):
    u = min(max(u, 0.0), 1.0)
    return u * u * (3 - 2 * u)


def glide(a_sig, b_sig, t0, t1, dt=0.04):
    """A dense signal moving from signal a (at t0) to signal b (at t1), both still evaluated live."""
    v = []
    n = int(math.ceil((t1 - t0) / dt)) + 1
    for i in range(n):
        t = t0 + i * dt
        u = smooth((t - t0) / (t1 - t0))
        a, b = ev(a_sig, t), ev(b_sig, t)
        v.append([round(a[0] + (b[0] - a[0]) * u, 1), round(a[1] + (b[1] - a[1]) * u, 1)] if isinstance(a, list)
                 else round(a + (b - a) * u, 4))
    return dense(t0, dt, v)


def orbit(n, t0, t1, shape_fn, angle_fn, tilt_fn=lambda t: 0.0, center_fn=lambda t: (720, 540),
          radius_fn=lambda t: 240, scale_fn=lambda t: 0.25, depth=3.5, dt=0.04):
    """Copies at the points of a (possibly morphing) 3D shape, spun about Y by angle_fn(t)
    (radians) and tilted about X by tilt_fn(t), perspective-projected. All arguments are
    functions of song time, so speed changes stay continuous. Returns [(pos, scale)]."""
    out = [([], []) for _ in range(n)]
    ts = [t0 + i * dt for i in range(int(math.ceil((t1 - t0) / dt)) + 1)]
    for t in ts:
        pts = shape_fn(t)
        a, b = angle_fn(t), tilt_fn(t)
        ca, sa, cb, sb = math.cos(a), math.sin(a), math.cos(b), math.sin(b)
        cx, cy = center_fn(t)
        R, S = radius_fn(t), scale_fn(t)
        for j, (x, y, z) in enumerate(pts):
            x1, z1 = x * ca + z * sa, -x * sa + z * ca
            y2, z2 = y * cb - z1 * sb, y * sb + z1 * cb
            persp = depth / (depth + z2)
            out[j][0].append([round(cx + x1 * R * persp, 1), round(cy + y2 * R * persp, 1)])
            out[j][1].append(round(S * persp, 4))
    return [(dense(t0, dt, p), dense(t0, dt, s)) for p, s in out]


def morph(shapes, times):
    """shape_fn: piecewise morph between point lists `shapes` at song `times` (eased)."""
    def f(t):
        if t <= times[0]:
            return shapes[0]
        for i in range(len(times) - 1):
            if t <= times[i + 1]:
                u = smooth((t - times[i]) / (times[i + 1] - times[i]))
                return [tuple(a + (b - a) * u for a, b in zip(p, q)) for p, q in zip(shapes[i], shapes[i + 1])]
        return shapes[-1]
    return f


def integral(rate_fn, t0, dt=0.01):
    """angle_fn from a rate function (radians per second): a cached numerical integral."""
    cache = {"t": t0, "a": 0.0}

    def f(t):
        if t < cache["t"]:
            cache["t"], cache["a"] = t0, 0.0
        while cache["t"] + dt <= t:
            cache["a"] += rate_fn(cache["t"]) * dt
            cache["t"] += dt
        return cache["a"] + rate_fn(cache["t"]) * (t - cache["t"])
    return f


def since_beat(c, t, div=1):
    """Seconds since the last beat (div=1) or downbeat (div=4) at song time t."""
    from bisect import bisect_right
    grid = c.downbeats if div >= 4 else c.beats
    i = bisect_right(grid, t) - 1
    return t - grid[i] if i >= 0 else 1e9


def pulse(c, t, div=1, tau=0.12):
    return math.exp(-since_beat(c, t, div) / tau)


# ---- blasts the catalogue didn't mark: brightness onsets, so strike pools need never repeat ----
ONSET_CACHE = PDIR / "comps/out/section_s2_peak.onsets.json"
ONSET_FPS = 50          # decode rate: frame-exact for 25/30 fps sources (duplicated frames)


def _luma_frames(file, t0, t1, w=80, h=45):
    import subprocess
    import numpy as np
    out = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t0:.3f}", "-i", str(ROOT / file), "-t", f"{t1 - t0:.3f}",
                          "-vf", f"fps={ONSET_FPS},scale={w}:{h},format=gray", "-f", "rawvideo", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(out, np.uint8).reshape(-1, h, w).astype(np.float32)


def onsets(seg, invert=False, min_gap=1.0):
    """[(source t, score)] of sudden brightenings in a segment: a blast's flash, a fireball's
    bloom (for black-hot IR, `invert`: the blast is a sudden darkening). Score: the jump of the
    brightest 5% of the picture plus the mean, over 2 frames at 50 fps, in 0-255 levels. Hard
    cuts score too; the caller keeps only onsets that also brighten (not just change)."""
    import numpy as np
    key = f"{seg.file}|{seg.t_in:.3f}|{seg.t_out:.3f}|{int(invert)}"
    cache = json.loads(ONSET_CACHE.read_text()) if ONSET_CACHE.exists() else {}
    if key not in cache:
        fr = _luma_frames(seg.file, seg.t_in, seg.t_out)
        if invert:
            fr = 255.0 - fr
        flat = fr.reshape(len(fr), -1)
        p95 = np.percentile(flat, 95, axis=1)
        mean = flat.mean(axis=1)
        # how much of the picture changed: a cut changes nearly all of it, a blast a region
        chg = np.zeros(len(fr))
        chg[2:] = (np.abs(flat[2:] - flat[:-2]) > 40).mean(axis=1)
        d = np.zeros(len(fr))
        d[2:] = np.maximum(0, p95[2:] - p95[:-2]) + np.maximum(0, mean[2:] - mean[:-2])
        thr = max(14.0, 5 * float(np.median(d)) + 1e-6)
        r = int(0.4 * ONSET_FPS)
        found = []
        for i in range(2, len(d)):
            if d[i] < thr or d[i] < d[max(0, i - r):i + r + 1].max():
                continue
            if chg[i] > 0.85:            # the whole frame changed: a cut, not a blast
                continue
            j = i - 1 if d[i - 1] > 0.5 * d[i] else i     # the first frame of the jump
            found.append((round(seg.t_in + j / ONSET_FPS, 3), round(float(d[i]), 1)))
        keep = []
        for t, s in sorted(found, key=lambda x: -x[1]):
            if all(abs(t - u) >= min_gap for u, _ in keep):
                keep.append((t, s))
        cache[key] = sorted(keep)
        ONSET_CACHE.write_text(json.dumps(cache, indent=0) + "\n")
    return [tuple(x) for x in cache[key]]
