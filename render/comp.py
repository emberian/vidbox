"""Composition library: write timelines (render/TIMELINE.md) in musical terms.

    from comp import Comp
    c = Comp("meine", "my_draft", range=(0, 75), sync="missiles_on_beat")
    c.add(c.background())
    for s, h in c.find("weapons", kind="explosion", min_strength=4)[:4]:
        c.footage(s, at=c.bar(20), hit=h, blend="screen", fx=[...])
    c.save()        # -> projects/meine/comps/out/my_draft.timeline.json

Times are song seconds. Hits are visual-frame impact points from the footage catalogs.
"""
import json
import math
import random
from bisect import bisect_left
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent


# ---- signal builders (plain dicts; see TIMELINE.md) ----
def keys(*pairs, ease="linear"):
    return {"k": [list(p) for p in pairs], "ease": ease}


def beat(div=1.0, shape="decay", **kw):
    return {"beat": {"div": div, "shape": shape, **kw}}


def rng(lo, hi, of):
    return {"range": [lo, hi], "of": of}


def intensity(smooth=1.0):
    return {"intensity": {"smooth": smooth}}


def onset(tau=0.15, min=0.3):
    return {"onset": {"tau": tau, "min": min}}


def mul(*s):
    return {"mul": list(s)}


def add(*s):
    return {"add": list(s)}


def dense(t0, dt, values):
    return {"dense": {"t0": t0, "dt": dt, "v": values}}


class Seg:
    """One catalogued footage segment."""

    def __init__(self, catalog, clip, idx):
        self.catalog, self.clip, self.idx = catalog, clip, idx
        s = clip["segments"][idx]
        self.s = s
        self.file, self.t_in, self.t_out = clip["file"], s["in"], s["out"]
        self.hits = s.get("hits", [])
        self.tags = s.get("tags", [])

    @property
    def ref(self):
        return f"{self.catalog}:{self.clip['id']}#{self.idx}"

    def __repr__(self):
        return f"<Seg {self.ref} {self.t_in:.1f}-{self.t_out:.1f} {self.s.get('desc', '')[:60]!r}>"


class Comp:
    def __init__(self, project, name, range=None, sync=None, seed=0):
        self.project, self.name = project, name
        self.pdir = ROOT / "projects" / project
        self.proj = json.loads((self.pdir / "project.json").read_text())
        b = json.loads((self.pdir / "analysis/beats.json").read_text())
        self.beats, self.downbeats = b["beats"], b["downbeats"]
        self.period = float(np.median(np.diff(self.beats)))
        self.sync = json.loads((self.pdir / f"sync/{sync}.resolved.json").read_text()) if sync else None
        # every catalog in footage/ (weapons, ground, and any later lane's)
        self.cat = {f.stem: json.loads(f.read_text())["clips"] for f in sorted((self.pdir / "footage").glob("*.json"))}
        self.range = list(range or (0, self.proj.get("duration", 473.5)))
        self.layers, self.post = [], []
        self.ducks = []   # background opacity dips, see duck()
        self.rand = random.Random(seed)
        self.W, self.H = self.proj["size"]

    # ---- musical time ----
    def beat(self, n):
        """Song time of beat n (fractional n interpolates)."""
        i = int(math.floor(n))
        if i < 0 or i + 1 >= len(self.beats):
            return self.beats[0] + n * self.period
        return self.beats[i] + (n - i) * (self.beats[i + 1] - self.beats[i])

    def bar(self, n, beat_in_bar=0):
        """Song time of bar n (0-based, downbeats), plus beats into the bar."""
        db = self.downbeats[int(n)]
        if beat_in_bar == 0:
            return db
        i = int(np.argmin(np.abs(np.array(self.beats) - db)))
        return self.beat(i + beat_in_bar)

    def bar_of(self, t):
        return bisect_left(self.downbeats, t + 1e-6) - 1

    def snap(self, t, div=1.0):
        """Nearest grid point (div in beats: 1 = beats, 0.5 = eighths, 4 = bars)."""
        if div >= 4:
            return min(self.downbeats, key=lambda d: abs(d - t))
        pos = bisect_left(self.beats, t)
        lo = max(0, pos - 1)
        frac = (t - self.beats[lo]) / self.period
        return self.beat(lo + round(frac / div) * div)

    def word(self, ref, edge="start"):
        """Song time of a word in the retimed rant: 'missiles#3' (3rd occurrence) or index."""
        W = self.sync["words"]
        if isinstance(ref, int):
            return W[ref][edge]
        key, _, n = ref.partition("#")
        hits = [w for w in W if w["key"] == key.lower()]
        return hits[int(n or 1) - 1][edge]

    def words(self, key):
        return [w for w in self.sync["words"] if w["key"] == key]

    # ---- footage ----
    def seg(self, ref):
        """'ground:clip-id#2' -> Seg."""
        cat, _, rest = ref.partition(":")
        cid, _, i = rest.partition("#")
        clip = next(c for c in self.cat[cat] if c["id"] == cid)
        return Seg(cat, clip, int(i or 0))

    def segments(self, catalog=None):
        for cat in ([catalog] if catalog else self.cat):
            for c in self.cat[cat]:
                for i in range(len(c["segments"])):
                    yield Seg(cat, c, i)

    def find(self, catalog=None, tags=(), kind=None, min_strength=0, min_intensity=0, max_graphic=3,
             overlay_ok=None, shuffle=True):
        """[(Seg, hit_index)] for hits matching, or [(Seg, None)] when kind is None."""
        out = []
        for s in self.segments(catalog):
            if tags and not set(tags) & set(s.tags):
                continue
            if s.s.get("intensity", 0) < min_intensity or s.s.get("graphic", 0) > max_graphic:
                continue
            if overlay_ok is not None and s.s.get("overlay_ok", True) != overlay_ok:
                continue
            if kind is None:
                out.append((s, None))
            else:
                for i, h in enumerate(s.hits):
                    if (kind == "any" or h["kind"] == kind) and h.get("strength", 3) >= min_strength:
                        out.append((s, i))
        if shuffle:
            self.rand.shuffle(out)
        return out

    def footage(self, seg, at, hit=None, before=None, after=None, speed=1.0, id=None, **props):
        """Place a segment so its hit `hit` lands exactly at song time `at` (or, with hit=None,
        so the segment starts at `at`). before/after: seconds of song time to keep around the
        hit (default: as much of the segment as exists)."""
        if hit is not None:
            h = seg.hits[hit]["t"]
            pre = (h - seg.t_in) / speed if before is None else min(before, (h - seg.t_in) / speed)
            post = (seg.t_out - h) / speed if after is None else min(after, (seg.t_out - h) / speed)
            t0, t1 = at - pre, at + post
            src_in = h - pre * speed
        else:
            dur = (seg.t_out - seg.t_in) / speed if after is None else after
            t0, t1, src_in = at, at + dur, seg.t_in
        hits_song = [round(t0 + (x["t"] - src_in) / speed, 3) for x in seg.hits
                     if src_in <= x["t"] <= src_in + (t1 - t0) * speed]
        layer = {"id": id or f"{seg.clip['id']}#{seg.idx}@{at:.2f}", "tags": [seg.catalog] + seg.tags[:3],
                 "src": seg.file, "t0": round(t0, 4), "t1": round(t1, 4),
                 "time": {"in": round(src_in, 4), "speed": speed},
                 "meta": {"catalog": seg.catalog, "clip": seg.clip["id"], "seg": seg.idx, "hits_song": hits_song},
                 **props}
        self.layers.append(layer)
        return layer

    def add(self, layer):
        self.layers.append(layer)
        return layer

    def background(self, **props):
        bg = self.proj["background"]
        return {"id": "meine", "tags": ["bg"], "src": bg["src"], "t0": self.range[0], "t1": self.range[1],
                "time": {"in": self.range[0], "speed": 1.0}, "fit": "native", **props}

    def duck(self, at, hold=1.0, depth=0.4, attack=0.12, release=0.6):
        """Dip the Meine background to `depth` opacity around song time `at` (reached `attack` s
        before it, held `hold` s after, recovering over `release`), so footage can shine through.
        Overlapping ducks merge (the deepest wins)."""
        self.ducks.append((at - attack, at, at + hold, at + hold + release, depth))

    def _duck_signal(self):
        if not self.ducks:
            return None
        pts = sorted({round(x, 4) for d in self.ducks for x in d[:4]} | {self.range[0], self.range[1]})

        def level(t):
            v = 1.0
            for a0, a1, h1, r1, depth in self.ducks:
                if a0 <= t <= r1:
                    u = (t - a0) / (a1 - a0) if t < a1 else 1.0 if t <= h1 else 1 - (t - h1) / (r1 - h1)
                    v = min(v, 1 - (1 - depth) * u)
            return round(v, 4)
        return keys(*[[t, level(t)] for t in pts], ease="smooth")

    def save(self):
        out = self.pdir / "comps/out" / f"{self.name}.timeline.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        tl = {"version": 1, "project": self.project, "size": self.proj["size"], "fps": self.proj["fps"],
              "range": self.range, "music": {"src": self.proj["background"]["src"],
                                             "gain": self.proj["background"].get("gain", 1.0)},
              "layers": self.layers, "post": self.post}
        duck = self._duck_signal()
        for L in tl["layers"]:
            if L.get("id") == "meine" and duck and "opacity" not in L:
                L["opacity"] = duck
        out.write_text(json.dumps(tl, indent=1) + "\n")
        offgrid = [(L["id"], h) for L in self.layers for h in L.get("meta", {}).get("hits_song", [])
                   if min(abs(h - b) for b in self.beats) > 0.03]
        print(f"{out.relative_to(ROOT)}: {len(self.layers)} layers; {len(offgrid)} hits off the beat grid",
              *(f"\n  off-grid: {i} @ {h:.3f}" for i, h in offgrid[:8]))
        return out


def section_main(name, span, build, sync="missiles_on_beat", pad=2.0):
    """Run a section script standalone: its span (plus a little padding) with the background,
    saved as comps/out/section_<name>.timeline.json for quick previews in the viewer."""
    c = Comp("meine", f"section_{name}", range=(max(0.0, span[0] - pad), span[1] + pad), sync=sync)
    c.add(c.background())
    build(c)
    return c.save()


# ---- motion builders: dense pos/scale signals for head copies ----
SHAPES = {
    "cube": [(x, y, z) for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)],
    "octahedron": [(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)],
}


def shape_points(name, n):
    if name in SHAPES:
        P = SHAPES[name]
        return [P[i % len(P)] for i in range(n)]
    if name == "ring":
        return [(math.cos(2 * math.pi * i / n), 0, math.sin(2 * math.pi * i / n)) for i in range(n)]
    if name == "sphere":   # Fibonacci sphere
        g = math.pi * (3 - math.sqrt(5))
        return [(math.cos(g * i) * math.sqrt(1 - y * y), y, math.sin(g * i) * math.sqrt(1 - y * y))
                for i, y in ((i, 1 - 2 * (i + 0.5) / n) for i in range(n))]
    if name == "helix":
        return [(math.cos(i * 1.3), -1 + 2 * i / max(n - 1, 1), math.sin(i * 1.3)) for i in range(n)]
    raise ValueError(name)


def formation(comp, shape, n, t0, t1, center, radius, spin_bars=2.0, tilt_bars=7.0, depth=3.5,
              base_scale=0.3, dt=0.04):
    """Copies at the vertices of a 3D shape rotating on the beat grid, perspective-projected.
    One full turn about Y every `spin_bars` bars; a slower wobble about X every `tilt_bars`.
    Returns [(pos_signal, scale_signal), ...] per copy."""
    pts = shape_points(shape, n)
    bar_len = 4 * comp.period
    ts = np.arange(t0, t1 + dt, dt)
    out = [([], []) for _ in pts]
    for t in ts:
        a = 2 * math.pi * (t - t0) / (spin_bars * bar_len)
        b = 0.5 * math.sin(2 * math.pi * (t - t0) / (tilt_bars * bar_len))
        ca, sa, cb, sb = math.cos(a), math.sin(a), math.cos(b), math.sin(b)
        for j, (x, y, z) in enumerate(pts):
            x1, z1 = x * ca + z * sa, -x * sa + z * ca     # spin about Y
            y2, z2 = y * cb - z1 * sb, y * sb + z1 * cb    # tilt about X
            persp = depth / (depth + z2)
            out[j][0].append([round(center[0] + x1 * radius * persp, 1), round(center[1] + y2 * radius * persp, 1)])
            out[j][1].append(round(base_scale * persp, 4))
    return [(dense(t0, dt, p), dense(t0, dt, s)) for p, s in out]


def bounce(comp, t0, t1, box, beats_per_crossing=(2, 3, 4), seed=0, dt=0.04):
    """Pong-style motion: straight flights between box walls, each wall contact on a beat.
    box = (x0, y0, x1, y1) for the centre. Returns a pos signal."""
    r = random.Random(seed)
    x0, y0, x1, y1 = box
    p = [r.uniform(x0, x1), r.uniform(y0, y1)]
    t = comp.snap(t0)
    keysl = [[round(t0, 4), [round(p[0], 1), round(p[1], 1)]]]
    while t < t1:
        nb = r.choice(beats_per_crossing)
        tn = t + nb * comp.period
        side = r.choice("lrtb")
        q = {"l": [x0, r.uniform(y0, y1)], "r": [x1, r.uniform(y0, y1)],
             "t": [r.uniform(x0, x1), y0], "b": [r.uniform(x0, x1), y1]}[side]
        keysl.append([round(comp.snap(tn), 4), [round(q[0], 1), round(q[1], 1)]])
        t = tn
    return keys(*keysl)
