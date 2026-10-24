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
