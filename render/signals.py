"""Signals: per-frame parameter values, possibly driven by the music. Spec in TIMELINE.md.

compile_signal(spec, ctx) -> f(t) returning a float or a length-2 numpy array.
"""
import json
import math
from bisect import bisect_right
from pathlib import Path

import numpy as np

from bezier import Path as BezierPath


class Music:
    """Beat grid, onsets and intensity of the song (analysis/beats.json)."""

    def __init__(self, beats_json):
        d = json.loads(Path(beats_json).read_text())
        self.beats = np.array(d["beats"])
        self.downbeats = np.array(d["downbeats"])
        self.period = float(np.median(np.diff(self.beats)))
        # beat index of the first downbeat: phase origin for multi-beat periods
        self.db0 = int(np.argmin(np.abs(self.beats - self.downbeats[0])))
        self.onsets = d["onsets"]
        self.onset_t = [o[0] for o in self.onsets]
        self.int_dt = d["intensity"]["dt"]
        self.int_v = np.array(d["intensity"]["values"])
        self._smoothed = {}

    def beat_pos(self, t):
        """Continuous beat count at t (beats extrapolated at the median period off the ends)."""
        B = self.beats
        if t < B[0]:
            return (t - B[0]) / self.period
        if t >= B[-1]:
            return len(B) - 1 + (t - B[-1]) / self.period
        i = bisect_right(B, t) - 1
        return i + (t - B[i]) / (B[i + 1] - B[i])

    def phase(self, t, div=1.0, offset=0.0):
        c = (self.beat_pos(t) - self.db0) / div - offset
        return c - math.floor(c)

    def intensity(self, t, smooth=0.0):
        v = self.int_v
        if smooth > 0:
            key = round(smooth, 3)
            if key not in self._smoothed:
                k = max(1, int(smooth / self.int_dt))
                pad = np.pad(v, k, mode="edge")
                self._smoothed[key] = np.convolve(pad, np.ones(2 * k + 1) / (2 * k + 1), "valid")
            v = self._smoothed[key]
        x = min(max(t / self.int_dt, 0), len(v) - 1)
        i = min(int(x), len(v) - 2)
        return float(v[i] + (v[i + 1] - v[i]) * (x - i))

    def onset_env(self, t, tau=0.15, minimum=0.3):
        i = bisect_right(self.onset_t, t) - 1
        best = 0.0
        while i >= 0 and t - self.onsets[i][0] < 6 * tau:
            ot, s = self.onsets[i]
            if s >= minimum:
                best = max(best, s * math.exp(-(t - ot) / tau))
            i -= 1
        return best


class Ctx:
    def __init__(self, music, project_dir):
        self.music = music
        self.pdir = Path(project_dir)
        self._paths = {}

    def path(self, rel):
        if rel not in self._paths:
            self._paths[rel] = BezierPath(json.loads((self.pdir / rel).read_text()))
        return self._paths[rel]


def _shape(name, ph, period, p):
    if name == "decay":
        return math.exp(-ph * period / p.get("tau", 0.12))
    if name == "pulse":
        return 1.0 if ph < p.get("width", 0.25) else 0.0
    if name == "saw":
        return ph
    if name == "ramp":
        return 1.0 - ph
    if name == "sine":
        return 0.5 - 0.5 * math.cos(2 * math.pi * ph)
    if name == "tri":
        return 1.0 - abs(2 * ph - 1)
    raise ValueError(f"unknown beat shape {name!r}")


def _interp_keys(keys, t, ease):
    ts = [k[0] for k in keys]
    if t <= ts[0]:
        return np.asarray(keys[0][1], float)
    if t >= ts[-1]:
        return np.asarray(keys[-1][1], float)
    i = bisect_right(ts, t) - 1
    (t0, v0), (t1, v1) = keys[i], keys[i + 1]
    u = (t - t0) / (t1 - t0)
    if ease == "hold":
        u = 0.0
    elif ease == "smooth":
        u = u * u * (3 - 2 * u)
    return np.asarray(v0, float) + (np.asarray(v1, float) - np.asarray(v0, float)) * u


def _scalar(v):
    v = np.asarray(v, float)
    return float(v) if v.ndim == 0 else v


def compile_signal(spec, ctx):
    if isinstance(spec, (int, float)):
        c = float(spec)
        return lambda t: c
    if isinstance(spec, list):
        if len(spec) == 2:
            fx, fy = compile_signal(spec[0], ctx), compile_signal(spec[1], ctx)
            return lambda t: np.array([fx(t), fy(t)])
        raise ValueError(f"vector signals have 2 components, got {spec!r}")
    if not isinstance(spec, dict) or len(spec) == 0:
        raise ValueError(f"bad signal {spec!r}")
    m = ctx.music
    if "k" in spec:
        keys, ease = sorted(spec["k"], key=lambda k: k[0]), spec.get("ease", "linear")
        return lambda t: _scalar(_interp_keys(keys, t, ease))
    if "dense" in spec:
        d = spec["dense"]
        t0, dt, v = d["t0"], d["dt"], np.asarray(d["v"], float)
        n = len(v)

        def dense(t):
            x = min(max((t - t0) / dt, 0), n - 1)
            i = min(int(x), max(n - 2, 0))
            return _scalar(v[i] if n == 1 else v[i] + (v[i + 1] - v[i]) * (x - i))
        return dense
    if "path" in spec:
        p = ctx.path(spec["path"])
        return lambda t: np.array(p(t), float)
    if "pathscale" in spec:
        p = ctx.path(spec["pathscale"])
        return lambda t: p.scale(t)
    if "beat" in spec:
        b = spec["beat"]
        div, shape, off = b.get("div", 1.0), b.get("shape", "decay"), b.get("offset", 0.0)
        period = div * m.period
        return lambda t: _shape(shape, m.phase(t, div, off), period, b)
    if "intensity" in spec:
        sm = spec["intensity"].get("smooth", 0.0)
        return lambda t: m.intensity(t, sm)
    if "onset" in spec:
        o = spec["onset"]
        tau, mn = o.get("tau", 0.15), o.get("min", 0.3)
        return lambda t: m.onset_env(t, tau, mn)
    if "range" in spec:
        lo, hi = spec["range"]
        f = compile_signal(spec["of"], ctx)
        return lambda t: lo + (hi - lo) * f(t)
    if "clamp" in spec:
        lo, hi = spec["clamp"]
        f = compile_signal(spec["of"], ctx)
        return lambda t: min(max(f(t), lo), hi)
    if "add" in spec:
        fs = [compile_signal(s, ctx) for s in spec["add"]]
        return lambda t: sum(f(t) for f in fs)
    if "mul" in spec:
        fs = [compile_signal(s, ctx) for s in spec["mul"]]

        def mul(t):
            r = 1.0
            for f in fs:
                r = r * f(t)
            return r
        return mul
    raise ValueError(f"unknown signal form {list(spec)}")


# ---- time maps: song time -> source time (TIMELINE.md "Time") ----
# A TimeMap is a list of contiguous runs covering the layer's song span. The renderer uses it
# for the frame (latest frame with timestamp <= src(t)), for the layer's audio, and comp.py for
# hits_song. The original forms (in/speed, loop, map, hold) keep their own closed-form lambdas in
# the renderer; their runs here exist for audio and meta and agree with them exactly.

def _ease_int(x, ease):
    """Integral over [0, x] of the ramp's easing curve e(u) (e = u or smoothstep)."""
    if ease == "smooth":
        return x ** 3 - x ** 4 / 2
    return x * x / 2


def _ease(x, ease):
    return x * x * (3 - 2 * x) if ease == "smooth" else x


class Run:
    """One piece of a time map over song [a, b).
    kind: "lin" (s0 + v (t - a)), "hold" (s0), "ramp" (speed v0 -> v1 over d, eased),
    "curve" (tabulated: ts -> ss)."""

    def __init__(self, a, b, kind, s0=0.0, v=0.0, v0=0.0, v1=0.0, ease="linear", ts=None, ss=None):
        self.a, self.b, self.kind = a, b, kind
        self.s0, self.v, self.v0, self.v1, self.ease = s0, v, v0, v1, ease
        self.ts, self.ss = ts, ss

    def src(self, t):
        if self.kind == "lin":
            return self.s0 + self.v * (t - self.a)
        if self.kind == "hold":
            return self.s0
        if self.kind == "ramp":
            d = self.b - self.a
            x = min(max((t - self.a) / d, 0.0), 1.0)
            extra = max(0.0, t - self.b)   # past the ramp's end: continue at v1
            return self.s0 + d * (self.v0 * x + (self.v1 - self.v0) * _ease_int(x, self.ease)) + self.v1 * extra
        return float(np.interp(t, self.ts, self.ss))

    def src_vec(self, t):
        t = np.asarray(t, float)
        if self.kind == "lin":
            return self.s0 + self.v * (t - self.a)
        if self.kind == "hold":
            return np.full(t.shape, self.s0)
        if self.kind == "ramp":
            d = self.b - self.a
            x = np.clip((t - self.a) / d, 0.0, 1.0)
            return self.s0 + d * (self.v0 * x + (self.v1 - self.v0) * _ease_int(x, self.ease)) + \
                self.v1 * np.maximum(0.0, t - self.b)
        return np.interp(t, self.ts, self.ss)

    def speed_at(self, t):
        if self.kind == "lin":
            return self.v
        if self.kind == "hold":
            return 0.0
        if self.kind == "ramp":
            x = min(max((t - self.a) / (self.b - self.a), 0.0), 1.0)
            return self.v0 + (self.v1 - self.v0) * _ease(x, self.ease)
        i = min(max(int(np.searchsorted(self.ts, t)), 1), len(self.ts) - 1)
        return float((self.ss[i] - self.ss[i - 1]) / (self.ts[i] - self.ts[i - 1]))

    def constant_speed(self):
        """The run's speed if it is constant (lin/hold), else None."""
        return self.v if self.kind == "lin" else 0.0 if self.kind == "hold" else None

    def __repr__(self):
        return f"<Run {self.kind} {self.a:.3f}-{self.b:.3f} src {self.src(self.a):.3f}->{self.src(self.b):.3f}>"


class TimeMap:
    def __init__(self, runs):
        self.runs = [r for r in runs if r.b > r.a + 1e-9] or runs[:1]
        self.starts = [r.a for r in self.runs]

    def run_at(self, t):
        i = bisect_right(self.starts, t + 1e-9) - 1
        return self.runs[min(max(i, 0), len(self.runs) - 1)]

    def __call__(self, t):
        return self.run_at(t).src(t)

    @property
    def end(self):
        return self.runs[-1].b

    def song_times(self, h, t0=None, t1=None, step=0.002):
        """Song times in [t0, t1) at which source time h is reached (where a hit at h shows)."""
        out = []
        for r in self.runs:
            a, b = max(r.a, t0 if t0 is not None else r.a), min(r.b, t1 if t1 is not None else r.b)
            if b <= a:
                continue
            if r.kind == "hold":
                if abs(r.s0 - h) < 1e-6:
                    out.append(a)
            elif r.kind == "lin":
                if abs(r.v) > 1e-12:
                    t = r.a + (h - r.s0) / r.v
                    if a - 1e-9 <= t < b:
                        out.append(t)
            else:
                ts = np.arange(a, b + step, step)
                d = r.src_vec(ts) - h
                for i in np.nonzero((d[:-1] <= 0) & (d[1:] > 0) | (d[:-1] >= 0) & (d[1:] < 0))[0]:
                    u = d[i] / (d[i] - d[i + 1]) if d[i] != d[i + 1] else 0.0
                    t = ts[i] + u * step
                    if t < b:
                        out.append(float(t))
        return sorted(set(round(t, 4) for t in out))


def _seq_runs(pieces, t0):
    runs, a = [], t0
    for p in pieces:
        d = float(p["dur"])
        if "hold" in p:
            runs.append(Run(a, a + d, "hold", s0=float(p["hold"])))
            a += d
            continue
        s, sp = float(p["in"]), p.get("speed", 1.0)
        if isinstance(sp, list):   # ramp [v0, v1]
            if "repeat" in p:
                raise ValueError("repeat is for constant-speed pieces")
            runs.append(Run(a, a + d, "ramp", s0=s, v0=float(sp[0]), v1=float(sp[1]), ease=p.get("ease", "linear")))
            a += d
            continue
        sp = float(sp)
        n, every = int(p.get("repeat", 1)), float(p.get("every", d))
        for k in range(n):
            last = k == n - 1
            play = d if last else min(d, every)
            runs.append(Run(a, a + play, "lin", s0=s, v=sp))
            if not last and every > play:   # gap until the next trigger: hold the slice's last frame
                runs.append(Run(a + play, a + every, "hold", s0=s + sp * play))
            a += play if last else every
    return runs


def compile_time(T, t0, t1, ctx=None, dt=0.001):
    """TimeMap for a layer's `time` spec over song [t0, t1)."""
    T = T or {"in": 0.0, "speed": 1.0}
    if "seq" in T:
        runs = _seq_runs(T["seq"], t0)
        if not runs:
            raise ValueError("empty seq")
        last = runs[-1]
        end = last.b
        if end < t1:   # past the seq: continue at the last piece's final speed
            runs.append(Run(end, t1, "lin", s0=last.src(end), v=last.speed_at(end)))
        return TimeMap(runs)
    if "map" in T:
        song, src = [float(x) for x in T["map"]["song"]], [float(x) for x in T["map"]["src"]]
        runs = [Run(min(t0, song[0]) - 1.0, song[0], "hold", s0=src[0])]
        for i in range(len(song) - 1):
            if song[i + 1] > song[i]:
                runs.append(Run(song[i], song[i + 1], "lin", s0=src[i],
                                v=(src[i + 1] - src[i]) / (song[i + 1] - song[i])))
        runs.append(Run(song[-1], max(t1, song[-1]) + 1.0, "hold", s0=src[-1]))
        return TimeMap(runs)
    if "hold" in T:
        return TimeMap([Run(t0, t1, "hold", s0=float(T["hold"]))])
    tin, sp, loop = float(T.get("in", 0.0)), T.get("speed", 1.0), T.get("loop")
    if not isinstance(sp, (int, float)):   # speed signal: integrate it
        if loop:
            raise ValueError("loop with a speed signal is not supported; use seq")
        if ctx is None:
            raise ValueError("a speed signal needs a Ctx")
        f = compile_signal(sp, ctx)
        ts = np.arange(t0, t1 + 2 * dt, dt)
        v = np.array([float(f(t)) for t in ts])
        ss = tin + np.concatenate([[0.0], np.cumsum((v[1:] + v[:-1]) * 0.5 * dt)])
        return TimeMap([Run(t0, t1, "curve", ts=ts, ss=ss)])
    sp = float(sp)
    if not loop:
        return TimeMap([Run(t0, t1, "lin", s0=tin, v=sp)])
    a, b = loop
    runs, t = [], t0
    while t < t1 - 1e-9:
        s = a + ((tin - a) + (t - t0) * sp) % (b - a)
        if sp > 0:
            tn = t + (b - s) / sp
        elif sp < 0:
            tn = t + (s - a) / -sp
            if tn <= t + 1e-9:   # sitting exactly on a: wraps immediately
                s, tn = b, t + (b - a) / -sp
        else:
            tn = t1
        runs.append(Run(t, min(tn, t1), "lin", s0=s, v=sp))
        t = tn
    return TimeMap(runs)
