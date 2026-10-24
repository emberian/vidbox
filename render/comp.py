"""Composition library: write timelines (render/TIMELINE.md) in musical terms.

    from comp import Comp
    c = Comp("meine", "my_draft", range=(0, 75), sync="missiles_on_beat")
    c.add(c.background())
    for s, h in c.find("weapons", kind="explosion", min_strength=4)[:4]:
        c.footage(s, at=c.bar(20), hit=h, blend="screen", fx=[...])
    c.save()        # -> projects/meine/comps/out/my_draft.timeline.json

Times are song seconds. Hits are visual-frame impact points from the footage catalogs.

Time ops (TIMELINE.md "Time ops"); each places a layer and returns it, extra kwargs are layer props:
    c.stutter(seg, at, hit=0, n=3, div=0.5, slice=0.12)      flash retriggered on eighths
    c.freeze(seg, at, hit=0, beats=2, then="continue")       hold the hit frame 2 beats
    c.ramp(seg, at, speeds=(1, 0.25), beats=4, hit=0)        slow-mo into a hit landing at `at`
    c.reverse(seg, at, hit=0)                                backwards, hit frame at `at`
    c.varispeed(seg, at, speed=rng(0.4, 2, beat()), dur=8)   speed as any signal
    c.footage_multi(seg, hits=[0, 2, 3], at=[t1, t2, t3])    several hits each on its beat
    c.groove(seg, at, dur=16)                                motion_tempo cycle locked to the grid
    c.say("missiles#3", at, stutter=2)                       the preacher says it, onset at `at`
    c.timed(seg, at, [play(...), hold(...), ramp(...), stut(...)])   any piece list
"""
import json
import math
import random
from bisect import bisect_left, bisect_right
from pathlib import Path

import numpy as np

from signals import Ctx, Music, compile_time

ROOT = Path(__file__).resolve().parent.parent
FACE = "media/derived/face.mp4"                 # the preacher, face-tracked, with his voice (raw clip time)
RANT_WORDS = "analysis/rant_words.json"         # forced-aligned word times in FACE's own clock


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


# ---- time pieces for {"time": {"seq": [...]}} (TIMELINE.md "Time ops"); song-second durations ----
def play(src, dur, speed=1.0):
    """Play from source time `src` for `dur` song seconds (speed < 0 plays backwards)."""
    return {"dur": round(dur, 4), "in": round(src, 4), "speed": speed}


def hold(src, dur):
    """Freeze on the frame showing at source time `src` for `dur` song seconds (silent)."""
    return {"dur": round(dur, 4), "hold": round(src, 4)}


def ramp(src, dur, v0, v1, ease="smooth"):
    """Play from `src` with the speed going v0 -> v1 over `dur` song seconds (ease linear|smooth)."""
    return {"dur": round(dur, 4), "in": round(src, 4), "speed": [v0, v1], "ease": ease}


def stut(src, slice, every, n, speed=1.0):
    """n triggers, `every` song s apart, each playing `slice` song s from `src` (the gap holds the
    slice's last frame); the last trigger plays its slice in full. Uniform spacing: for
    grid-exact triggers across an uneven beat grid use Comp.stutter."""
    return {"dur": round(slice, 4), "in": round(src, 4), "speed": speed, "repeat": int(n), "every": round(every, 4)}


def seq_dur(pieces):
    tot = 0.0
    for p in pieces:
        n = p.get("repeat", 1)
        tot += (n - 1) * p.get("every", p["dur"]) + p["dur"] if "repeat" in p else p["dur"]
    return tot


def resolve_word(words, ref):
    """'missiles#3' (3rd occurrence, as tools/retime.py resolves it) or an index -> word dict."""
    if isinstance(ref, int):
        return words[ref]
    key, _, n = ref.partition("#")
    hits = [w for w in words if w["key"] == key.lower()]
    if not hits:
        raise KeyError(f"no word {key!r} in transcript")
    k = int(n or 1)
    if k > len(hits):
        raise KeyError(f"only {len(hits)} x {key!r}, asked for #{k}")
    return hits[k - 1]


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
                 **props}
        # a caller's meta adds to the catalog link and hits rather than replacing them
        layer["meta"] = {"catalog": seg.catalog, "clip": seg.clip["id"], "seg": seg.idx, "hits_song": hits_song,
                         **props.get("meta", {})}
        self.layers.append(layer)
        return layer

    def add(self, layer):
        self.layers.append(layer)
        return layer

    # ---- time ops: stutter, freeze, ramps, reverse, multi-hit, groove, words ----
    def beat_pos(self, t):
        """Continuous beat number at song time t (inverse of beat())."""
        B = self.beats
        if t < B[0] or t >= B[-1]:
            ref = B[0] if t < B[0] else B[-1]
            return (0 if t < B[0] else len(B) - 1) + (t - ref) / self.period
        i = max(0, min(bisect_right(B, t) - 1, len(B) - 2))
        return i + (t - B[i]) / (B[i + 1] - B[i])

    def beats_after(self, t, n):
        """Song time n beats (fractional ok, negative ok) after t, along the real beat grid."""
        return self.beat(self.beat_pos(t) + n)

    @property
    def ctx(self):
        if not hasattr(self, "_ctx"):
            self._ctx = Ctx(Music(self.pdir / "analysis/beats.json"), self.pdir)
        return self._ctx

    def _timed_layer(self, seg, t0, t1, time, id, extra_meta=None, **props):
        """A layer over song [t0, t1) with any `time` form; hits_song from the shared TimeMap."""
        tm = compile_time(time, t0, t1, self.ctx)
        hits_song = []
        for x in seg.hits:
            hits_song += [t for t in tm.song_times(x["t"], t0, t1)]
        layer = {"id": id, "tags": [seg.catalog] + seg.tags[:3], "src": seg.file,
                 "t0": round(t0, 4), "t1": round(t1, 4), "time": time,
                 **props}
        layer["meta"] = {"catalog": seg.catalog, "clip": seg.clip["id"], "seg": seg.idx,
                         "hits_song": sorted(round(h, 3) for h in hits_song), **(extra_meta or {}),
                         **props.get("meta", {})}
        self.layers.append(layer)
        return layer

    def timed(self, seg, at, pieces, until=None, id=None, **props):
        """Place a segment with an explicit piece list (play/hold/ramp/stut) starting at song time
        `at`. The layer lasts the pieces' total length (or until `until`; past the pieces it
        continues at the last piece's final speed)."""
        t1 = until if until is not None else at + seq_dur(pieces)
        return self._timed_layer(seg, at, t1, {"seq": pieces}, id or f"{seg.clip['id']}#{seg.idx}@{at:.2f}", **props)

    def _hit_src(self, seg, hit, src):
        return seg.hits[hit]["t"] if hit is not None else (seg.t_in if src is None else src)

    def stutter(self, seg, at, hit=None, src=None, n=3, div=0.5, slice=None, speed=1.0, before=0.0, after=None,
                id=None, **props):
        """Retrigger a short slice on the beat grid: the source point (hit `hit`, or `src`, or the
        segment start) lands at `at` and again every `div` beats, n times in all; the last trigger
        plays on for `after` song s (default: the rest of the segment). slice: song s each early
        trigger plays before freezing (default: the whole division, a continuous retrigger).
        before: song s of normal lead-in ahead of `at`. A strike's flash 3x on eighths:
        c.stutter(seg, at=c.bar(20), hit=0, n=3, div=0.5, slice=0.12)."""
        p = self._hit_src(seg, hit, src)
        trig = [self.beats_after(at, k * div) for k in range(n)]
        pieces = [play(p - before * speed, before, speed)] if before > 0 else []
        for k in range(n - 1):
            gap = trig[k + 1] - trig[k]
            sl = gap if slice is None else min(slice, gap)
            pieces.append(play(p, sl, speed))
            if gap > sl + 1e-6:
                pieces.append(hold(p + sl * speed, gap - sl))
        rest = (seg.t_out - p) / abs(speed) if after is None else after
        pieces.append(play(p, max(rest, 1e-3), speed))
        L = self._timed_layer(seg, at - before, trig[-1] + rest, {"seq": pieces},
                              id or f"{seg.clip['id']}#{seg.idx}@{at:.2f}~stutter", {"stutter": trig}, **props)
        return L

    def freeze(self, seg, at, hit, beats=2.0, before=None, then="continue", after=None, id=None, **props):
        """Play into hit `hit` so it lands at `at`, hold that frame for `beats` beats (ending on the
        grid), then `then`: "continue" (play on from the hit for `after` song s, default the rest)
        or "cut" (the layer ends with the hold)."""
        h = seg.hits[hit]["t"]
        pre = (h - seg.t_in) if before is None else min(before, h - seg.t_in)
        t_rel = self.beats_after(at, beats)
        pieces = ([play(h - pre, pre)] if pre > 1e-6 else []) + [hold(h, t_rel - at)]
        t1 = t_rel
        if then == "continue":
            rest = (seg.t_out - h) if after is None else after
            pieces.append(play(h, rest))
            t1 = t_rel + rest
        elif then != "cut":
            raise ValueError(f"then={then!r}: continue | cut")
        return self._timed_layer(seg, at - pre, t1, {"seq": pieces},
                                 id or f"{seg.clip['id']}#{seg.idx}@{at:.2f}~freeze", {"freeze": [at, t_rel]}, **props)

    def ramp(self, seg, at, speeds=(1.0, 0.25), beats=4.0, hit=None, src=None, ease="smooth", after=None, id=None,
             **props):
        """Speed ramp over `beats` beats from speeds[0] to speeds[1]. With `hit`, the ramp ENDS at
        `at` with the hit landing exactly there (slow-mo into an impact: speeds=(1, 0.2)); without,
        the ramp STARTS at `at` from `src` (default the segment start). After the ramp the speed
        stays at speeds[1] for `after` song s (default: until the segment ends)."""
        v0, v1 = speeds
        if hit is not None:
            ta, tb = self.beats_after(at, -beats), at
            covered = (tb - ta) * (v0 + v1) / 2   # both easings average to the mean speed
            s0 = seg.hits[hit]["t"] - covered
            if s0 < seg.t_in - 1e-6:
                print(f"  ramp {seg.ref}: starts {seg.t_in - s0:.2f}s before the segment (at {s0:.2f})")
        else:
            ta, tb = at, self.beats_after(at, beats)
            s0 = seg.t_in if src is None else src
        s_end = s0 + (tb - ta) * (v0 + v1) / 2
        rest = max(0.0, (seg.t_out - s_end) / max(abs(v1), 1e-3)) if after is None else after
        pieces = [ramp(s0, tb - ta, v0, v1, ease), play(s_end, max(rest, 1e-3), v1)]
        return self._timed_layer(seg, ta, tb + rest, {"seq": pieces},
                                 id or f"{seg.clip['id']}#{seg.idx}@{at:.2f}~ramp", {"ramp": [ta, tb]}, **props)

    def varispeed(self, seg, at, speed, dur, src=None, id=None, **props):
        """Playback speed as any signal (keys, beat-locked shapes...), integrated: e.g.
        speed=rng(0.4, 2.2, beat(1, "decay", tau=0.15)) surges on every beat."""
        time = {"in": seg.t_in if src is None else src, "speed": speed}
        return self._timed_layer(seg, at, at + dur, time, id or f"{seg.clip['id']}#{seg.idx}@{at:.2f}~vari", **props)

    def reverse(self, seg, at, hit=None, speed=1.0, before=None, after=None, id=None, **props):
        """Play the segment backwards. With `hit`, the hit frame shows exactly at `at` (an explosion
        un-exploding into its flash); before/after: song s kept around it."""
        if hit is not None:
            h = seg.hits[hit]["t"]
            pre = (seg.t_out - h) / speed if before is None else min(before, (seg.t_out - h) / speed)
            post = (h - seg.t_in) / speed if after is None else min(after, (h - seg.t_in) / speed)
            t0, t1, start = at - pre, at + post, h + pre * speed
        else:
            dur = (seg.t_out - seg.t_in) / speed if after is None else after
            t0, t1, start = at, at + dur, seg.t_out
        return self._timed_layer(seg, t0, t1, {"in": round(start, 4), "speed": -speed},
                                 id or f"{seg.clip['id']}#{seg.idx}@{at:.2f}~rev", **props)

    def footage_multi(self, seg, hits, at, before=None, after=None, speed=1.0, limits=(0.25, 4.0), id=None, **props):
        """Land several hits of one segment on chosen song times: hits=[i, j, ...] (hit indices,
        increasing in source time), at=[t_i, t_j, ...] (increasing). Between hits the speed is
        whatever makes the next one land; before the first and after the last it is `speed`.
        Warns when a stretch leaves `limits`; per-piece speeds are in meta.speeds."""
        if len(hits) != len(at) or not hits:
            raise ValueError("hits and at must be equal-length, non-empty")
        hs = [seg.hits[i]["t"] for i in hits]
        if any(b <= a for a, b in zip(hs, hs[1:])) or any(b <= a for a, b in zip(at, at[1:])):
            raise ValueError(f"hits {hs} and at {at} must both increase")
        pre = (hs[0] - seg.t_in) / speed if before is None else min(before, (hs[0] - seg.t_in) / speed)
        post = (seg.t_out - hs[-1]) / speed if after is None else min(after, (seg.t_out - hs[-1]) / speed)
        song = [at[0] - pre] + list(at) + [at[-1] + post]
        src = [hs[0] - pre * speed] + hs + [hs[-1] + post * speed]
        speeds = [round((src[k + 1] - src[k]) / (song[k + 1] - song[k]), 3) for k in range(len(song) - 1)
                  if song[k + 1] > song[k]]
        for k, v in enumerate(speeds):
            if not limits[0] <= v <= limits[1]:
                print(f"  footage_multi {seg.ref}: piece {k} runs at x{v} (outside {limits})")
        time = {"map": {"song": [round(x, 4) for x in song], "src": [round(x, 4) for x in src]}}
        return self._timed_layer(seg, song[0], song[-1], time, id or f"{seg.clip['id']}#{seg.idx}@{at[0]:.2f}~multi",
                                 {"speeds": speeds}, **props)

    def groove(self, seg, at, dur=None, lengths=(0.5, 1, 2, 4), limits=(0.6, 1.6), anchor=None, cycle=None, id=None,
               **props):
        """Lock rhythmic footage to the music: one motion cycle (seg `motion_tempo` s, or `cycle`)
        spans a musical length (the one of `lengths` beats needing the speed nearest 1x within
        `limits`; if none fits, 8 and 16 beats are tried, then the nearest is taken with a
        warning). Phase: source time `anchor` (default the segment's first hit, else its start)
        lands on `at` snapped to the beat, and every following cycle lands on the grid too (a
        piecewise map, so tempo wobbles in the beat track are followed). Returns the layer;
        meta.groove = {cycle, beats, speed}."""
        T = cycle or seg.s.get("motion_tempo")
        if not T:
            raise ValueError(f"{seg.ref} has no motion_tempo; pass cycle=")
        cand = [(L, T / (L * self.period)) for L in lengths]
        fit = [c for c in cand if limits[0] <= c[1] <= limits[1]]
        if not fit:
            cand += [(L, T / (L * self.period)) for L in (8, 16)]
            fit = [c for c in cand if limits[0] <= c[1] <= limits[1]]
        if not fit:
            print(f"  groove {seg.ref}: no musical length gives a speed within {limits}; taking the nearest")
        L, sp = min(fit or cand, key=lambda c: abs(math.log(c[1])))
        p = anchor if anchor is not None else (seg.hits[0]["t"] if seg.hits else seg.t_in)
        at = self.snap(at, 0.5 if L < 1 else 1.0)
        dur = (seg.t_out - p) / sp if dur is None else dur
        b0, song, src, k = self.beat_pos(at), [], [], 0
        while True:
            song.append(round(self.beat(b0 + k * L), 4))
            src.append(round(p + k * T, 4))
            if song[-1] >= at + dur:
                break
            k += 1
        time = {"map": {"song": song, "src": src}}
        return self._timed_layer(seg, at, at + dur, time, id or f"{seg.clip['id']}#{seg.idx}@{at:.2f}~groove",
                                 {"groove": {"cycle": T, "beats": L, "speed": round(sp, 4)}}, **props)

    # ---- the preacher's words ----
    def raw_words(self, words=RANT_WORDS):
        if not hasattr(self, "_raw_words"):
            self._raw_words = {}
        if words not in self._raw_words:
            self._raw_words[words] = json.loads((self.pdir / words).read_text())["words"]
        return self._raw_words[words]

    def say(self, ref, at, repeat=1, every=None, stutter=0, slice=0.12, div=0.25, stretch=1.0, gain=1.0,
            tail=0.06, nudge=0.0, video=True, src=FACE, words=RANT_WORDS, mode="tempo", id=None, **props):
        """The preacher says word `ref` ('missiles#3' = 3rd occurrence, or an index into
        analysis/rant_words.json) starting exactly at song time `at`, in his voice (and face, from
        media/derived/face.mp4; video=False keeps only the voice).
        stutter=k: k clipped fragments (`slice` source s of the word's start) one every `div` beats
        before the whole word ("mi-mi-missiles" = stutter=2); the first fragment starts at `at`.
        repeat=n: say the whole word n times, `every` beats apart (default: the word's length
        rounded up to half a beat). stretch: >1 slower, pitch kept (ffmpeg atempo; mode="tape"
        changes pitch with speed). tail: source s kept after the aligned end so the release isn't
        clipped. nudge: source s added to the aligned start (negative starts the word earlier, e.g.
        to keep a breathy "h" the aligner put late). gain: voice level. Audio edges get 6 ms fades. Other props (pos, scale, size,
        mask, fx, opacity...) style the head; defaults: 480x600 oval at the canvas centre."""
        w = resolve_word(self.raw_words(words), ref)
        s0, s1 = w["start"] + nudge, w["end"] + tail
        sp = 1.0 / stretch
        word_len = (s1 - s0) * stretch            # song seconds for the whole word
        frag_len = min(slice, s1 - s0) * stretch
        pieces, t, onsets = [], at, []
        for k in range(stutter):
            nxt = self.beats_after(at, (k + 1) * div)
            gap = nxt - t
            pieces.append(play(s0, min(frag_len, gap), sp))
            if gap > frag_len + 1e-6:
                pieces.append(hold(s0 + frag_len * sp, gap - frag_len))
            onsets.append(round(t, 4))
            t = nxt
        if every is None:
            every = math.ceil(word_len / self.period * 2 - 1e-6) / 2
        main = t
        for r in range(repeat):
            onsets.append(round(t, 4))
            if r == repeat - 1:
                pieces.append(play(s0, word_len, sp))
                t += word_len
            else:
                nxt = self.beats_after(main, (r + 1) * every)
                gap = nxt - t
                pieces.append(play(s0, min(word_len, gap), sp))
                if gap > word_len + 1e-6:
                    pieces.append(hold(s0 + word_len * sp, gap - word_len))
                t = nxt
        layer = {"id": id or f"say:{ref}@{at:.2f}", "tags": ["head", "say"], "src": src,
                 "t0": round(at, 4), "t1": round(t, 4), "time": {"seq": pieces},
                 "size": [480, 600], "pos": [self.W / 2, self.H / 2 - 20], "mask": {"shape": "oval", "feather": 0.28},
                 "audio": {"gain": gain, "mode": mode},
                 "meta": {"word": w["w"], "ref": ref, "src_word": [w["start"], w["end"]], "hits_song": onsets}}
        layer.update(props)
        if not video:
            layer["opacity"] = 0
            layer["tags"] = ["voice", "say"]
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

    def save(self, path=None):
        out = Path(path) if path else self.pdir / "comps/out" / f"{self.name}.timeline.json"
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
        # each hit: on a beat, on an eighth/sixteenth (deliberate stutters), or genuinely off-grid
        on_beat, on_sub, offgrid = 0, 0, []
        for L in self.layers:
            for h in L.get("meta", {}).get("hits_song", []):
                pos = self.beat_pos(h)
                err = lambda div: abs(pos / div - round(pos / div)) * div * self.period
                if err(1) <= 0.03:
                    on_beat += 1
                elif err(0.25) <= 0.03:
                    on_sub += 1
                else:
                    offgrid.append((L["id"], h))
        print(f"{out.relative_to(ROOT) if out.is_relative_to(ROOT) else out}: {len(self.layers)} layers; "
              f"hits: {on_beat} on beat, {on_sub} on 8ths/16ths, {len(offgrid)} off the grid",
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
