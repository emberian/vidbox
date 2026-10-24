"""3:45 - the end (bar 118 -> 7:53): the dip, the main peak, the plateau, the outro.
Bar-by-bar map and choices in s2_peak_NOTES.md.

uv run python projects/meine/comps/sections/s2_peak.py
uv run python render/tl.py projects/meine/comps/out/section_s2_peak.timeline.json --range A B --jobs 3
"""
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parents[3] / "render"), str(HERE)]
from comp import beat, keys, mul, rng, section_main, shape_points  # noqa: E402
import s2_kit as K  # noqa: E402

SPAN = (224.967, 473.5)
GAZE = "paths/face_self_gaze.json"
DRIFT = "paths/face_self_drift.json"
PIC = (0, 158, 1440, 922)          # Meine's picture area
AP_CROP = [0.04, 0.16, 0.92, 0.9]   # drops AP's top-right bug, top-left credits, NBC/AJ corner bugs
PRE_WAR = ("-war", "2019", "2023-may-round")
# clips with subtitles/lower-thirds inside the frame that no crop removes: kept out of the pools
CAPTIONED = {"aj-high-powered-bombs-explainer", "ap-interceptions-telaviv-jlm-feb2026", "ap-flares-cloudy-night-2025-12-b",
             "fa-rafah-bomb-identification", "idf-beit-hanoun-launcher-2014"}
WEAPONS_CROP = [0.06, 0.16, 0.94, 0.76]   # news bugs/credits at the top corners, slates and lower-thirds below
OIR_CROP = [0.06, 0.16, 0.94, 0.68]       # OIR strike tapes type their description along the bottom


def bars(c, b, beat_in_bar=0):
    return c.bar(b, beat_in_bar)


def okay(seg):
    """Footage we use freely: current war, no identifiable victims, not caption-covered."""
    if any(t.endswith(PRE_WAR[0]) or t in PRE_WAR[1:] for t in seg.tags):
        return False
    return seg.s.get("identifiable_victims") is not True


# ---- looks ----
def ir_fx(k=0, levels=6):
    return [{"op": "posterize", "levels": levels},
            {"op": "chroma", "px": rng(1, 14, beat(1, "decay", tau=0.16)), "angle": 37 * k}]


def night_fx(k=0):   # bright-on-black ground footage: key the dark away
    return [{"op": "lumakey", "low": 0.12, "high": 0.5},
            {"op": "chroma", "px": rng(0, 8, beat(1, "decay", tau=0.14)), "angle": 90 + 23 * k}]


def head_fx(i, levels=None, noise=0.5):
    return [{"op": "hue", "deg": rng(i * 40, i * 40 + 120, beat(8, "sine", offset=i / 8))},
            {"op": "posterize", "levels": levels or 3 + i % 4},
            {"op": "noise", "scale": 30 + 9 * i, "mode": "overlay", "color": "rgb", "speed": 0.9, "seed": i,
             "amount": rng(0.15, noise, beat(1, "decay", tau=0.2))},
            {"op": "chroma", "px": rng(0, 12, beat(1, "decay", tau=0.12)), "angle": i * 40}]


# ---- 3:45-4:15  handoff, dip, countdown, re-entry (bars 118-131) ----
def dip_and_reentry(c, P):
    b118, b120, b124, b132 = (bars(c, b) for b in (118, 120, 124, 132))
    # the preacher alone, steered by his gaze, over the last two bars of the rise
    pos, sc = K.retime_path(GAZE, 6.0, b118, b120, center=(720, 540), k=0.75, scale_k=0.95,
                            clamp=(240, 300, 1200, 780))
    # lane A collapses its heads to the centre at scale ~0.15 on bar 118: he grows out of that point
    gl = 2 * c.period
    pv, sv = [], []
    for i in range(len(pos["dense"]["v"])):
        t = b118 + i * 0.04
        u = K.smooth((t - b118) / gl)
        q, qs = pos["dense"]["v"][i], sc["dense"]["v"][i]
        pv.append([round(720 + (q[0] - 720) * u, 1), round(540 + (q[1] - 540) * u, 1)])
        sv.append(round(0.15 + (qs - 0.15) * u, 4))
    pos, sc = K.dense(b118, 0.04, pv), K.dense(b118, 0.04, sv)
    say_t0 = b120 - (K.SAMPLES["give israel missiles"][1] - K.SAMPLES["give israel missiles"][0])
    c.add({"id": "P-gaze", "tags": ["head", "P"], "src": K.FACE, "t0": b118, "t1": say_t0,
           "time": {"in": 6.0, "speed": 1.0, "loop": list(K.MOUTH_LOOP)}, "size": [480, 600],
           "pos": pos, "scale": sc, "mask": {"shape": "oval", "feather": 0.28}, "opacity": 0.8,
           "fade": {"in": 0.3}, "fx": [{"op": "chroma", "px": rng(0, 6, beat(1, "decay", tau=0.15))}]})
    # the music falls away on bar 120: a white-hot strike lands on it and freezes as he says it
    # Khan Younis, Feb 2026: a close night blast that whites out the whole frame
    khan = c.seg("y2026:guardian-khanyounis-night-strike-2026-02-06#0")
    c.footage(khan, at=b120, hit=1, before=1.2, after=1.6, blend="screen", fit="picture", crop=[0.02, 0.12, 0.8, 0.95],
              fade={"in": 0.4, "out": 1.4}, fx=ir_fx(0, 8), opacity=0.75, id="khanyounis-into-dip")
    # ...and the tracking shot itself stops: Meine freezes on that frame for the breath, then
    # starts moving again on the kick (bar 124)
    meine = c.proj["background"]["src"]
    c.add({"id": "meine-freeze", "tags": ["bg", "freeze"], "src": meine, "t0": b120, "t1": b124,
           "time": {"hold": b120}, "fit": "native",
           "opacity": keys([b120, 1.0], [b120 + 2 * c.period, 0.55], [b124 - 0.5, 0.45], [b124, 0.0]),
           "fx": [{"op": "sat", "factor": keys([b120, 1.0], [b120 + 3, 0.2])},
                  {"op": "blur", "px": keys([b120, 0], [b124, 6])}]})
    K.say(c, b120, "give israel missiles", pos=K.ev(pos, say_t0), scale=K.ev(sc, say_t0),
          gain=1.0, pop=1.15, id="P-says-into-dip")
    c.duck(b120, hold=6 * c.period, depth=0.3, release=2.0)

    c.duck(b120 + 0.1, hold=b124 - b120 - 0.25, depth=0.0, attack=0.1, release=0.15)   # only the freeze shows
    # the breath (bars 120-123): a morgue worker cuts shroud cloth, one cut every ~3 beats
    shroud = c.seg("ground:ap-aqsa-shroud-laundry-2023-10#3")
    c.add({"id": "shroud-cloth", "tags": ["ground", "shrouds"], "src": shroud.file, "t0": b120 + 2 * c.period,
           "t1": b124 + 0.3, "time": {"in": 84.0, "speed": 1.0}, "fit": "picture", "crop": [0, 0.13, 0.86, 1],
           "opacity": 0.8, "blend": "screen", "fade": {"in": 1.4, "out": 0.4},
           "fx": [{"op": "sat", "factor": 0.35}, {"op": "levels", "black": 0.04, "white": 0.95, "gamma": 0.9}]})
    # P, small now, drifts across the cloth (the drift path, shrunk), watching
    dpos, dsc = K.retime_path(DRIFT, 12.0, b120, b124, center=(720, 520), k=0.55, scale_k=0.45)
    c.add({"id": "P-drift", "tags": ["head", "P"], "src": K.FACE, "t0": b120 + 0.6, "t1": b124 - 0.1,
           "time": {"in": 12.0, "speed": 0.5, "loop": list(K.MOUTH_LOOP)}, "size": [480, 600],
           "pos": dpos, "scale": dsc, "mask": {"shape": "oval", "feather": 0.3}, "opacity": 0.7,
           "fade": {"in": 0.8, "out": 0.2}, "fx": [{"op": "sat", "factor": 0.3}, {"op": "posterize", "levels": 5}]})

    # the countdown: TARGET, 3, 2, 1 every two beats, the strike on bar 124 as the kick returns
    cd = c.seg("weapons:mq9-live-hellfire-holloman#7")
    c.footage_multi(cd, [0, 1, 2, 3], [bars(c, 122, 2), bars(c, 123), bars(c, 123, 2), b124], before=1.6, after=3.2,
           fit="picture", blend="screen", opacity=keys([b124 - 0.2, 0.9], [b124, 1.0]), fade={"in": 0.5, "out": 0.9}, id="countdown",
           fx=[{"op": "contrast", "factor": 1.15}, {"op": "chroma", "px": rng(0, 10, beat(2, "decay", tau=0.2))}])
    K.say(c, b124, "missiles", pos=(720, 520), scale=0.62, gain=1.1, pop=1.25, id="P-says-drop",
          fx=[{"op": "posterize", "levels": 6}])
    c.duck(b124, hold=1.4, depth=0.3)
    return b132


# ---- footage pools and one strike placement ----
class Pools:
    """Hit pools, drawn round-robin so the same take doesn't come back too soon."""

    def __init__(self, c):
        def pool(cat, tags, min_strength=4, overlay=True, max_graphic=2):
            out = []
            for s, h in c.find(cat, tags=tags, kind="any", min_strength=min_strength, max_graphic=max_graphic,
                               shuffle=False):
                if okay(s) and s.clip["id"] not in CAPTIONED and (not overlay or s.s.get("overlay_ok", True)):
                    out.append((s, h))
            out.sort(key=lambda sh: (-sh[0].hits[sh[1]].get("strength", 3), sh[0].ref, sh[1]))
            return out
        self.ir = [x for x in pool("weapons", ["IR", "black-hot", "white-hot"]) if "IR" in x[0].tags or "black-hot" in x[0].tags]
        self.fire = [x for x in pool("weapons", ["fireball", "aerial", "night", "launch", "flash"])
                     if x not in self.ir and "IR" not in x[0].tags and not {"range", "desert", "marketing"} & set(x[0].tags)]
        self.gnight = [x for x in pool("ground", ["strike"]) if "night" in x[0].tags]
        self.gday = [x for x in pool("ground", ["strike"]) if "night" not in x[0].tags]
        self.i = {k: 0 for k in ("ir", "fire", "gnight", "gday")}
        self.used = {}

    def take(self, kind, at=None, gap=20.0):
        P = getattr(self, kind)
        for _ in range(len(P)):
            s, h = P[self.i[kind] % len(P)]
            self.i[kind] += 1
            last = self.used.get(s.clip["id"])
            if at is None or last is None or at - last > gap:
                self.used[s.clip["id"]] = at
                return s, h
        return P[self.i[kind] % len(P)]


def look_for(seg, k):
    tg = set(seg.tags)
    if "black-hot" in tg:
        # Meine is night driving from ~4:15 on: invert so the ink-blot blasts glow, then screen
        return dict(blend="screen", fx=[{"op": "invert"}, {"op": "levels", "black": 0.35, "white": 0.95}] + ir_fx(k, 7))
    if "IR" in tg or "white-hot" in tg:   # over the night road: let the hot parts through, not the grey
        return dict(blend="screen", fx=[{"op": "lumakey", "low": 0.3, "high": 0.7}] + ir_fx(k, 6))
    if {"night", "black-bg", "flash"} & tg:
        return dict(blend="screen", fx=night_fx(k))
    return dict(blend="normal", fx=[{"op": "posterize", "levels": 7}, {"op": "sat", "factor": 1.25}] + ir_fx(k, 12)[1:])


def strike(c, seg, h, at, before=0.5, after=1.6, depth=0.45, opacity=0.9, k=0, duck_hold=0.8, **props):
    """One hit landing on `at`, styled by what the footage is (IR, black-hot, night, day)."""
    L = look_for(seg, k)
    L.update(props)
    crop = L.pop("crop", AP_CROP if seg.catalog == "ground" else
                  OIR_CROP if seg.clip["id"].startswith("oir-") else WEAPONS_CROP)
    lay = c.footage(seg, at=at, hit=h, before=before, after=after, fit=L.pop("fit", "picture"), crop=crop,
                    fade=L.pop("fade", {"in": min(0.15, before), "out": 0.5}), opacity=opacity, **L)
    if depth is not None:
        c.duck(at, hold=duck_hold, depth=depth)
    return lay


# ---- untreated reality: full frame, normal blend, no fx, its own sound; everything else steps away ----
ZINATI_SRC = "https://www.youtube.com/watch?v=vQdUgwKtwEY"


def real(c, ref, t0, t1, src_in, gain=1.0, music=0.25, people=None, crop=AP_CROP, window=True, id=None, **props):
    """The dead and the wounded as filmed: no effects, no keying, no kaleidoscope, its own audio.
    While a `window` is open the preacher, the chorus, the beds and the strike-cam are muted
    (see build's post-pass) and the music dips to `music`."""
    seg = c.seg(ref)
    L = {"id": id or f"real:{seg.clip['id']}@{t0:.2f}", "tags": ["real", seg.catalog], "src": seg.file,
         "t0": round(t0, 4), "t1": round(t1, 4), "time": {"in": src_in, "speed": 1.0}, "fit": "picture",
         "crop": crop, "blend": "normal", "opacity": 1.0, "clip": "picture", "audio": {"gain": gain},
         "fade": {"in": 0.04, "out": 0.1},
         "meta": {"catalog": seg.catalog, "clip": seg.clip["id"], "seg": seg.idx, "hits_song": [],
                  "graphic": seg.s.get("graphic"), "identifiable_victims": seg.s.get("identifiable_victims")}}
    if people:
        L["meta"]["people"] = people
    L.update(props)
    c.add(L)
    if window:
        c._s2_real.append((t0, t1))
    if music is not None:
        c.duck_music(t0, hold=t1 - t0, depth=music, attack=0.05, release=0.6)
    return L


# ---- the chorus: eight copies that split off him, trace shapes, scatter, regroup, and leave ----
def chorus(c):
    N = 8
    B = lambda b, k=0: bars(c, b, k)  # noqa: E731
    bar_len = 4 * c.period
    tau = 2 * math.pi
    enter = [B(124, 2)] + [B(124 + j) for j in range(1, N)]
    leave = [B(196) + j * 1.5 * bar_len for j in range(N)]        # one every 6 beats from bar 196
    t_start, t_end = enter[0], leave[-1] + bar_len

    def rate(t):   # radians per second about Y
        if t < B(132):
            return tau / (4 * bar_len)
        if t < B(144):
            return tau / (2 * bar_len)
        if t < B(152):
            return tau / (6 * bar_len)
        if t < B(167):
            return tau / (2 * bar_len)
        if t < B(168):
            return 0.0                    # the gap bar: everything stops
        if t < B(196):
            return tau / bar_len
        return tau / (4 * bar_len)
    angle = K.integral(rate, t_start)
    cube, ring, helix, sphere = (shape_points(s, N) for s in ("cube", "ring", "helix", "sphere"))
    shape = K.morph([cube, cube, ring, ring, helix, helix, sphere, sphere, cube, cube, helix, helix, ring],
                    [B(124), B(139), B(141), B(152), B(154), B(160), B(162), B(168), B(169), B(176), B(178),
                     B(188), B(190)])

    def radius(t):
        r = 190 if t < B(132) else 220 if t < B(168) else 250 if t < B(196) else 250 + 140 * (t - B(196)) / (8 * bar_len)
        return r * (1 + 0.10 * K.pulse(c, t, 4, 0.25)) if t >= B(132) else r

    def scale(t):
        s = 0.17 if t < B(152) else 0.14 if t < B(168) else 0.105
        return s * (1 + 0.18 * K.pulse(c, t, 1, 0.12)) if t >= B(132) else s

    def center(t):
        if t < B(168) or t >= B(196):
            return (720, 520)
        u = (t - B(168)) / (8 * bar_len) * tau     # a slow figure-eight over the hottest stretch
        return (720 + 230 * math.sin(u), 520 + 90 * math.sin(2 * u))

    tilt = lambda t: 0.45 * math.sin(tau * (t - t_start) / (7 * bar_len))  # noqa: E731
    orb = K.orbit(N, t_start, t_end, shape, angle, tilt, center, radius, scale, depth=5.5)

    # the lull (bars 144-151): the formation scatters into drift mode and regroups
    drift = [K.retime_path(DRIFT, 3.0 + 4.1 * j, B(143), B(153), center=(720, 540), k=0.9, scale_k=0.28,
                           clamp=(110, 230, 1330, 850)) for j in range(N)]
    ch = K.Chorus(c, N)
    dt = 0.04
    for j in range(N):
        t0, t1 = enter[j], leave[j] + bar_len
        ts = [t0 + i * dt for i in range(int((t1 - t0) / dt) + 1)]
        pv, sv = [], []
        for t in ts:
            p, s = K.ev(orb[j][0], t), K.ev(orb[j][1], t)
            # entry: from his face into the slot over one bar
            u = K.smooth((t - t0) / bar_len)
            p = [720 + (p[0] - 720) * u, 520 + (p[1] - 520) * u]
            s = 0.45 + (s - 0.45) * u
            # lull: drift
            w = K.smooth((t - B(144)) / bar_len) * (1 - K.smooth((t - B(151)) / bar_len))
            if w > 0:
                q, qs = K.ev(drift[j][0], t), K.ev(drift[j][1], t)
                p = [p[0] + (q[0] - p[0]) * w, p[1] + (q[1] - p[1]) * w]
                s = s + (qs - s) * w
            # leaving: fly outward and away
            v = K.smooth((t - leave[j]) / bar_len)
            if v > 0:
                ang = math.atan2(p[1] - 540, p[0] - 720) if (p[0], p[1]) != (720, 540) else j
                p = [p[0] + math.cos(ang) * 900 * v, p[1] + math.sin(ang) * 700 * v]
                s = s * (1 + 1.5 * v)
            pv.append([round(p[0], 1), round(p[1], 1)])
            sv.append(round(s, 4))
        ch.part(j, t0, t1, K.dense(t0, dt, pv), K.dense(t0, dt, sv), fx=head_fx(j),
                opacity=0.9, fade={"in": 0.3, "out": bar_len * 0.6},
                rot=rng(-10, 10, beat(4, "sine", offset=j / N)),
                say_fx=[{"op": "posterize", "levels": 6}, {"op": "chroma", "px": rng(2, 14, beat(1, "decay", tau=0.15)),
                                                            "angle": 40 * j}])
    return ch


# ---- 4:00-4:34  re-entry (124-131, kick only) and the first peak (132-143) ----
def reentry_and_peak1(c, pools, ch):
    B = lambda b, k=0: bars(c, b, k)  # noqa: E731
    # one continuous IDF strike-cam take over Gaza (1 Aug 2026, "leaving crater"): four hits at
    # natural speed (x1.0) on bars 126, 132, 135 and 140; the IDF's own picture, in a window
    crater = c.seg("y2026:idf-gaza-crater-strikecam-2026-08-01#0")
    crater_hits = [(0.0, 1.57), (0, 13.05), (0, 18.89), (0, 28.56)]
    take_bars = (126, 132, 135, 140)
    song = [B(126) - 1.0] + [B(b) for b in take_bars] + [B(140) + 1.4]
    src = [1.57 - 1.0] + [h for _, h in crater_hits] + [28.56 + 1.4]
    c.add({"id": "idf-crater-take", "tags": ["y2026", "IR", "strike", "idf"], "src": crater.file,
           "t0": round(song[0], 4), "t1": round(song[-1], 4),
           "time": {"map": {"song": [round(x, 4) for x in song], "src": src}},
           "fit": "picture", "crop": [0.05, 0.09, 0.87, 0.7], "blend": "normal", "opacity": 0.8,
           "fade": {"in": 0.8, "out": 0.6}, "mask": {"shape": "rect", "feather": 0.12}, "fx": ir_fx(1, 6),
           "meta": {"catalog": "y2026", "clip": crater.clip["id"], "seg": 0,
                    "hits_song": [round(B(b), 3) for b in take_bars]}})
    for b in take_bars:
        c.duck(B(b), hold=0.9, depth=0.45)
    # Israel's strikes elsewhere, on the bars the take leaves open
    for b, ref in ((128, "y2026:idf-iran-air-defence-strike-2026-06-08#0"),
                   (130, "y2026:idf-gaza-weapons-sites-strikecam-2026-09-09#0")):
        strike(c, c.seg(ref), 0, B(b), before=0.4, after=1.4, depth=0.45, k=b, opacity=0.8,
               crop=[0.14, 0.1, 0.87, 0.72])   # x0 0.14 drops the vertical "IDF / AFP" credit
    # Rafah at night, three domes of light on the odd bars
    rafah = c.seg("ground:afp-rafah-night-strikes-flares-2023-12#0")
    c.footage_multi(rafah, [0, 1, 2], [B(125), B(126, 2), B(127, 2)], before=0.8, after=1.6, fit="picture",
           crop=[0, 0, 1, 0.9], blend="screen", opacity=0.95, fade={"in": 0.3, "out": 0.8}, fx=night_fx(0),
           id="rafah-domes")
    blasts = c.seg("ground:ap-night-blasts-from-israel-2025-09#2")
    c.footage_multi(blasts, [0, 1], [B(129), B(129, 2)], before=0.5, after=1.4, fit="picture", crop=AP_CROP,
           blend="screen", opacity=0.95, fade={"in": 0.2, "out": 0.7}, fx=night_fx(2), id="blasts-129")
    strike(c, c.seg("ground:reuters-explosions-overnight-2023-10-22#2"), 0, B(131), before=0.1, after=1.8,
           depth=0.5, k=3)

    # peak 1: ground on the odd bars, more weapons on the even bars past the Iran take
    for b in (133, 135, 137, 139, 141, 143):
        s, h = pools.take("gnight" if b % 4 == 1 else "gday", B(b))
        strike(c, s, h, B(b), before=0.4, after=1.7, depth=0.45, k=b)
    for b in (138, 140, 142):
        s, h = pools.take("fire" if b != 140 else "ir", B(b))
        strike(c, s, h, B(b), before=0.4, after=1.6, depth=0.4, k=b)
    # a dense accent on the last bar before the lull: hits on beats 2, 3, 4
    for k in (1, 2, 3):
        s, h = pools.take("ir", B(143, k))
        strike(c, s, h, B(143, k), before=0.1, after=0.42, depth=None, k=k, opacity=0.7,
               fade={"in": 0.03, "out": 0.15})

    # the chorus speaks: all together on the drop into peak 1, then one at a time every four bars
    for j, smp in ((0, "missiles"), (3, "missiles.b"), (6, "missiles.c")):
        ch.speak(j, B(132), smp, gain=0.7, pop=2.2)
    c.duck(B(132), hold=1.2, depth=0.3)
    for j, b in ((1, 136), (5, 140)):
        ch.speak(j, B(b), "missiles.d" if b == 136 else "missiles", gain=1.0, pop=2.4)
    ch.speak(2, B(142, 2), "more and more missiles", gain=1.0, pop=2.0)


# ---- 4:34-4:50  the lull (144-151): the displaced; the chorus drifts ----
def lull(c, ch):
    B = lambda b, k=0: bars(c, b, k)  # noqa: E731
    coast = c.seg("ground:ap-drone-coast-road-return-2025-01-long#3")     # top-down walkers
    c.groove(coast, B(144), dur=B(148) - B(144) + 0.6, fit="picture", crop=AP_CROP, opacity=0.8,
             fade={"in": 0.5, "out": 0.6}, fx=[{"op": "sat", "factor": 0.55}, {"op": "posterize", "levels": 10}],
             id="walkers-topdown")
    flour = c.seg("ground:ap-zikim-flour-multitude-2025-07-30#2")
    c.groove(flour, B(148), dur=B(152) - B(148) + 0.3, fit="picture", crop=AP_CROP, opacity=0.8,
             fade={"in": 0.6, "out": 0.3}, fx=[{"op": "sat", "factor": 0.6}, {"op": "posterize", "levels": 10}],
             id="flour-multitude")
    c.duck(B(144), hold=B(152) - B(144) - 0.4, depth=0.35, attack=0.6, release=0.3)
    # over the hungry, the money he says is ripped from him
    ch.speak(4, B(149), "ripped from me", gain=1.0, pop=2.6)


# ---- 4:50-5:20  peak 2 (152-166), the gap bar (167) ----
def peak2(c, pools, ch):
    B = lambda b, k=0: bars(c, b, k)  # noqa: E731
    tunnel = {"op": "feedback", "fb": 0.6, "zoom": 1.035, "rot": rng(-3, 3, beat(8, "sine")), "mode": "max"}
    for b in range(152, 167):
        kind = ("ir", "gnight", "fire", "gday")[b % 4]
        s, h = pools.take(kind, B(b))
        L = strike(c, s, h, B(b), before=0.35, after=1.8, depth=0.4, k=b)
        L["fx"] = L["fx"] + [tunnel]
    # the chorus speaks every two bars, on the downbeat, round the circle
    smp = ["missiles", "missiles.b", "missiles.c", "missiles.e"]
    for n, b in enumerate(range(152, 167, 2)):
        ch.speak((n * 3) % 8, B(b), smp[n % 4], gain=0.95, pop=2.4)
    ch.stutter(7, B(165, 2), "missiles#5", stutter=2, gain=1.0)

    # 160-163: the strike-cam stops; a grid of four untreated takes from the ground, one per beat,
    # held four bars, all their sounds at once
    tiles = [("y2026:ap-jabaliya-strike-shifa-arrivals-2026-07-14#1", 12.0, AP_CROP),       # the wounded carried in
             ("ground:ap-jabaliya-dig-for-victims-2025-03#1", 20.0, AP_CROP),               # digging by hand
             ("y2026:roya-civil-defence-worker-shifa-2026-09-01#1", 8.5, [0, 0.3, 1, 0.62]),  # stretcher, blood
             ("y2026:ap-khanyounis-mourning-overnight-strikes-2026-08-02#2", 20.5, AP_CROP)]  # men kneel over shrouds
    cells = [(360, 349), (1080, 349), (360, 731), (1080, 731)]
    for k, ((ref, src_in, crop), (x, y)) in enumerate(zip(tiles, cells)):
        t0 = c.beat(c.beat_pos(B(160)) + k)
        real(c, ref, t0, B(164), src_in, gain=0.6, music=0.3 if k == 0 else None, crop=crop,
             size=[720, 382], pos=[x, y], fit=None, id=f"real:grid{k}")
    c._s2_real.append((B(160), B(164)))

    # bar 167: the music holds its breath; the last strike freezes and he states his terms
    s, h = pools.take("ir", B(167))
    c.freeze(s, B(167), h, beats=4, then="cut", before=0.3, fit="picture", crop=[0, 0.09, 1, 0.86],
             blend="screen", opacity=0.7, fx=[{"op": "invert"}, {"op": "gradmap", "palette": "blood"}],
             fade={"out": 0.2}, id="gap-freeze")
    K.say(c, B(167), "should be paying 75", pos=(720, 520), scale=0.8, gain=1.15, pop=1.1, id="P-75",
          fx=[{"op": "posterize", "levels": 5}, {"op": "chroma", "px": 6}])
    c.duck(B(167), hold=B(168) - B(167) - 0.3, depth=0.15, attack=0.1, release=0.2)


# ---- 5:20-6:13  the hottest stretch (168-195): atrocity, atrocity, atrocity; music, music, music ----
# one-bar punctures of the hypnosis: untreated, full frame, their own sound
PUNCTURES = {
    171: ("y2026:ap-khanyounis-morgue-bodies-2026-07-29#1", 13.0, None),            # bodies on a steel morgue tray
    # the wounded lifted into an ambulance by torchlight after an overnight strike in central Gaza, 9 Jan
    # 2026 (Roya News): Roya logo, date tag and handle cropped; its loud street sound brought down to
    # sit with the others. (Shifa arrivals #1 is the grid's tile at 160; a segment is used once.)
    175: ("ground:roya-night-rescue-central-gaza-2026-01#0", 5.0, None, [0.12, 0.14, 1.0, 0.86], 0.2),
    179: ("y2026:roya-civil-defence-bones-nuseirat-2026-09-05#1", 5.0, None),       # bones laid on dark cloth
    187: ("y2026:ap-khanyounis-mourning-overnight-strikes-2026-08-02#0", 1.0, None),  # women bent over the shrouds
    191: ("y2026:mee-112-remains-flags-2026-08-03#0", 1.0, None),    # (crop drops the Instagram credit)                   # 112 remains, photos taped on
}


def hottest(c, pools, ch):
    B = lambda b, k=0: bars(c, b, k)  # noqa: E731
    # a kaleidoscope bed of the rubble fields, palette-cycling, changing every eight bars
    beds = [("ground:ap-drone-beit-lahiya-2025-02#2", "ironbow"), ("ground:ap-drone-gazacity-ruins-2025-10-long#2", "blood"),
            ("ground:ap-drone-beit-lahiya-2025-02#0", "acid"), ("ground:ap-muwasi-tents-strike-2025-06#5", "nightvision")]
    for k, (ref, pal) in enumerate(beds):
        seg = c.seg(ref)
        t0, t1 = B(168 + 8 * k), min(B(176 + 8 * k), B(196))
        if t0 >= B(196):
            break
        c.add({"id": f"bed{k}", "tags": ["ground", "bed"], "src": seg.file, "t0": t0 - 0.3, "t1": t1 + 0.3,
               "time": {"in": seg.t_in, "speed": 0.7}, "fit": "picture", "crop": AP_CROP, "blend": "screen",
               "opacity": rng(0.12, 0.42, beat(4, "decay", tau=0.35)), "fade": {"in": 0.3, "out": 0.3},
               "fx": [{"op": "kaleido", "segments": 6 + 2 * (k % 2), "angle": rng(0, 60, beat(16, "saw"))},
                      {"op": "gradmap", "palette": pal, "cycle": beat(8, "saw"), "repeat": 1.5}]})
    c.duck(B(168), hold=B(196) - B(168) - 0.5, depth=0.6, attack=0.2, release=1.0)

    tunnel = {"op": "feedback", "fb": 0.62, "zoom": 1.045, "rot": rng(-4, 4, beat(4, "sine")), "mode": "max"}
    for b in range(168, 196):
        if b == 184:
            # the human cost, on the downbeat, as he names the weapon: Bureij, May 2026, a phone
            # video of a night street; the blast lands behind a man and throws him off his feet.
            # Portrait, in its own frame, untouched, with its own sound (the blast, the street).
            bureij = c.seg("y2026:anadolu-bureij-night-blast-street-2026-05-19#1")
            L = c.footage(bureij, at=B(b), hit=0, before=1.6, after=2.0, size=[440, 782], pos=[720, 540],
                          crop=[0, 0.1, 1, 0.86], blend="normal", opacity=1.0, fade={"in": 0.3, "out": 0.4},
                          mask={"shape": "rect", "feather": 0.02}, id="real:bureij-blast")
            L["tags"] = ["real"] + L["tags"]
            L["audio"] = {"gain": 1.2}
            c.duck(B(b), hold=1.6, depth=0.2)
            c.duck_music(B(b) - 0.2, hold=2.0, depth=0.35, attack=0.2)
            continue
        if b == 185:
            # ...and what follows: bodies rushed from an ambulance into the Khan Younis morgue
            # (AP, 29 Jul 2026), full frame, its own sound, the music down
            real(c, "y2026:ap-khanyounis-morgue-bodies-2026-07-29#0", B(b), B(b + 2), 1.0, gain=1.2, music=0.15,
                 id="real:morgue-arrival")
            continue
        if b == 186:
            continue
        if b in PUNCTURES:
            ref, src_in, people, *own = PUNCTURES[b]
            crop, gain = own if own else ([0.1, 0.16, 0.92, 0.9], 1.1)
            real(c, ref, B(b), B(b + 1), src_in, gain=gain, music=0.25, id=f"real:puncture-{b}", people=people,
                 crop=crop)
            continue
        kind = ("gnight", "ir", "gday", "fire")[b % 4]
        s, h = pools.take(kind, B(b), gap=15)
        L = strike(c, s, h, B(b), before=0.3, after=1.9, depth=0.35, k=b, opacity=0.88)
        L["fx"] = L["fx"] + [tunnel]
        if b % 2 == 1:   # off-beat accents: the same take stutters on the "and" of beat 3
            s2, h2 = pools.take("ir", B(b, 2.5), gap=10)
            c.stutter(s2, B(b, 2), hit=h2, n=3, div=0.5, slice=0.1, after=0.3, fit="picture",
                      crop=OIR_CROP if s2.clip["id"].startswith("oir-") else WEAPONS_CROP,
                      blend="screen", opacity=0.55, fade={"out": 0.15},
                      fx=[{"op": "invert"}, {"op": "levels", "black": 0.4}] + ir_fx(b, 5))
    # last two bars: a hit on every beat
    for k in range(8):
        at = c.beat(c.beat_pos(B(194)) + k)
        s, h = pools.take(("ir", "gnight")[k % 2], at, gap=4)
        strike(c, s, h, at, before=0.05, after=0.42,
               depth=None, k=k, opacity=0.75, fade={"in": 0.02, "out": 0.12})

    # the chorus: a word every two bars, stutters on the four-bar phrase ends, Hellfire named over Bureij
    smp = ["missiles", "missiles.c", "missiles.b", "missiles.e", "missiles.d"]
    for n, b in enumerate(range(168, 196, 2)):
        if b == 184:
            continue
        if b % 8 == 6:
            ch.stutter(n % 8, B(b), "missiles#5", stutter=3, gain=1.0)
        else:
            ch.speak(n % 8, B(b), smp[n % 5], gain=0.9, pop=2.6)
    K.say(c, B(184), "hellfire missiles", pos=(1180, 400), scale=0.3, gain=1.15, pop=None, id="P-hellfire",
          fx=[{"op": "posterize", "levels": 5}, {"op": "gradmap", "palette": "whitehot"}])


# ---- 6:13-6:36  cooling (196-207): the chorus leaves one by one; longer looks ----
def cooling(c, pools, ch):
    B = lambda b, k=0: bars(c, b, k)  # noqa: E731
    for b in (196, 198, 200, 202, 204):
        s, h = pools.take(("gnight", "ir", "gday")[(b // 2) % 3], B(b), gap=30)
        strike(c, s, h, B(b), before=0.6, after=3.0, depth=0.45, k=b, opacity=0.8)
    fire = c.seg("ground:ap-ansar-tent-strike-fire-2026-03#2")
    c.add({"id": "tent-fire", "tags": ["ground", "tents", "fire"], "src": fire.file, "t0": B(198), "t1": B(206),
           "time": {"in": 33.0, "speed": 1.0}, "fit": "picture", "crop": AP_CROP, "blend": "screen",
           "opacity": 0.6, "fade": {"in": 1.5, "out": 1.5}, "fx": [{"op": "lumakey", "low": 0.1, "high": 0.45}]})
    # 6:28 (bar 204): Gaza City, 15 Sep 2026. Eyewitness footage (Tamer Labbad, via the Guardian):
    # after a first strike wounded a civil defence paramedic, 15-year-old Mohammad Abdul Zinati went
    # to check on him and was killed by a second strike. Once, untreated, his own sound, the music
    # almost gone. It is NOT landed on the grid: it starts on the bar and plays as it happened.
    # (2.0-7.4 s of the source: the Guardian's circle marks the incoming munition at ~4.5 s; the
    # title card that follows is not used.) Then a bar of black before the funeral.
    zin = real(c, "y2026:guardian-deconstructed-zinati-strike-2026-09-15#1", B(204), B(204) + 4.9, 2.0,
               gain=1.3, music=0.05, crop=[0.0, 0.1, 1.0, 1.0], id="real:zinati",
               people=[{"name": "Mohammad Abdul Zinati", "age": 15, "role": "killed", "source": ZINATI_SRC},
                       {"name": "Sharif Shadi Labad", "role": "injured (civil defence paramedic)",
                        "source": ZINATI_SRC},
                       {"name": "Tamer Labbad", "role": "filmed it (eyewitness)", "source": ZINATI_SRC}])
    c._s2_real.append((B(204), B(208)))          # the black after it belongs to the window too
    c.duck_music(B(204), hold=B(208) - B(204) - 0.2, depth=0.05, attack=0.05, release=0.5)
    c.duck(B(204), hold=B(208) - B(204), depth=0.0, attack=0.05, release=0.2)
    for n, b in enumerate((197, 199, 201)):
        ch.speak(n + 5, B(b), ("missiles", "missiles.c", "all the missiles they need")[n], gain=0.9, pop=2.2)


# ---- 6:36-7:33  plateau (208-237): the dead held; the machine; prayer over the dead; the preacher returns ----
def plateau(c):
    B = lambda b, k=0: bars(c, b, k)  # noqa: E731
    # 208-215 (15 s, one take): the mass funeral of the Hassayna and Abu Sharia families, Gaza City,
    # 4 Aug 2026 -- an aerial of the rectangle of flag-wrapped bodies, then along the rows. Their own
    # sound; the kick keeps pulsing underneath.
    real(c, "y2026:ap-mass-funeral-hassayna-2026-08-04#2", B(208), B(216), 20.4, gain=1.0, music=0.3,
         crop=[0.06, 0.12, 0.96, 0.78], id="real:mass-funeral")
    # 216-223: the machine, and him: the MK-84 containers craned off at Ashdod, a shroud cut in a window
    ashdod = c.seg("weapons:imod-mk84-ashdod-feb2025#1")
    c.groove(ashdod, B(216), dur=B(224) - B(216), fit="picture", crop=[0.07, 0.09, 1, 0.95], blend="screen",
             opacity=0.8, fade={"in": 1.0, "out": 1.0}, fx=[{"op": "lumakey", "low": 0.1, "high": 0.45}],
             id="ashdod-crane")
    shroud = c.seg("ground:ap-aqsa-shroud-laundry-2023-10#3")
    c.groove(shroud, B(218), dur=B(224) - B(218), cycle=1.4, anchor=86.0, fit="picture", crop=[0, 0.13, 0.86, 1],
             blend="screen", opacity=keys([B(218), 0.0], [B(220), 0.5], [B(223), 0.5], [B(224), 0.0]),
             mask={"shape": "rect", "feather": 0.2}, size=[760, 428], pos=[720, 540],
             fx=[{"op": "sat", "factor": 0.4}], id="shroud-cut")
    strike(c, c.seg("ground:afp-rafah-night-strikes-flares-2023-12#0"), 1, B(220), before=0.6, after=2.6,
           depth=0.4, k=220, opacity=0.75)
    # 224-231 (15 s, one take, src 56.0-71.2 inside the single shot 54.7-79.9): outside al-Aqsa
    # Martyrs Hospital, Deir al-Balah, 28 Dec 2023 (AP): men stand in prayer over the white body bags
    # laid on the pavement, ambulances behind, a boy watching. Burial after the cranes unload the bombs.
    # Its own quiet sound (source ~-42 dBFS), raised to gain 3.0 so the murmur is heard under the kick.
    # (Hammad's sieve is shown once, in s1.)
    real(c, "ground:ap-aqsa-body-bags-prayer-2023-12#2", B(224), B(232), 56.0, gain=3.0, music=0.3,
         id="real:aqsa-prayer")
    # 230-237: the blueprint factory and the crowd walking north, under him again
    walkers = c.seg("ground:ap-drone-return-north-coast-2025-01#1")
    c.groove(walkers, B(232), dur=B(238) - B(232), fit="picture", crop=AP_CROP, opacity=0.6,
             fade={"in": 1.5, "out": 1.5}, fx=[{"op": "sat", "factor": 0.5}], id="walkers-crowd")
    f35 = c.seg("weapons:lm-f35-factory-animation#0")
    c.add({"id": "f35-blueprint", "tags": ["weapons", "factory"], "src": f35.file, "t0": B(232), "t1": B(238),
           "time": {"in": 20.0, "speed": 1.0}, "fit": "picture", "crop": [0, 0, 1, 0.8], "blend": "screen",
           "opacity": 0.55, "fade": {"in": 2.0, "out": 2.0}, "fx": [{"op": "lumakey", "low": 0.05, "high": 0.35}]})

    # him, alone, gaze-steered, only where the dead are not on screen
    pos, sc = K.retime_path(GAZE, 20.0, B(216), B(239), center=(720, 540), k=0.7,
                            scale_k=0.36, clamp=(200, 300, 1240, 780))
    lines = [(217, "they need more missiles"), (221, "thou shalt give israel missiles"),
             (233, "not paying enough"), (236, "missiles")]
    mutes = []
    for b, smp in lines:
        a, anc, e = K.SAMPLES[smp]
        at = B(b)
        mutes.append((at - (anc - a), at + (e - anc)))
        K.say(c, at, smp, pos=pos, scale=mul(sc, 1.15), gain=1.0, id=f"P-plateau-{b}",
              fx=[{"op": "posterize", "levels": 6}])
        c.duck(at, hold=1.0, depth=0.45)
    for t0, t1, idn in ((B(216), B(224), "P-plateau"), (B(232), B(239), "P-plateau2")):
        c.add({"id": idn, "tags": ["head", "P"], "src": K.FACE, "t0": t0, "t1": t1,
               "time": {"in": 20.0, "speed": 1.0, "loop": list(K.MOUTH_LOOP)}, "size": [480, 600], "pos": pos,
               "scale": sc, "mask": {"shape": "oval", "feather": 0.28}, "opacity": K.mute_signal(mutes, 0.8),
               "fade": {"in": 1.5, "out": 0.6},
               "fx": [{"op": "posterize", "levels": 6}, {"op": "noise", "scale": 60, "mode": "overlay", "speed": 0.6,
                                                          "amount": rng(0.1, 0.35, beat(1, "decay", tau=0.2))}]})
    return pos, sc


# ---- 7:33-7:53  outro ----
def outro(c, pos, sc, kind="walkers"):
    B = lambda b, k=0: bars(c, b, k)  # noqa: E731
    last_beat = c.beats[-1]
    end = SPAN[1]
    # his last word, on the last bar of the grid; then he shrinks to nothing
    c.add({"id": "P-out", "tags": ["head", "P"], "src": K.FACE, "t0": B(239), "t1": last_beat + 2.0,
           "time": {"in": 30.0, "speed": 0.5}, "size": [480, 600], "pos": K.ev(pos, B(239)),
           "scale": keys([B(239), K.ev(sc, B(239))], [last_beat + 2.0, 0.0], ease="smooth"),
           "mask": {"shape": "oval", "feather": 0.3}, "opacity": 0.8, "fx": [{"op": "posterize", "levels": 4}]})
    if kind == "walkers":
        # the last image: the misty coast road, the river of people walking north, outliving him
        road = c.seg("ground:ap-drone-coast-road-return-2025-01-long#0")
        c.add({"id": "outro-road", "tags": ["ground", "displacement"], "src": road.file, "t0": B(236), "t1": end,
               "time": {"in": 2.0, "speed": 0.8}, "fit": "picture", "crop": AP_CROP,
               "opacity": keys([B(236), 0.0], [B(239), 0.75], [last_beat + 4, 0.75], [end - 0.5, 0.0], ease="smooth"),
               "fx": [{"op": "sat", "factor": 0.45}]})
    elif kind == "shroud":
        shroud = c.seg("ground:ap-aqsa-shroud-laundry-2023-10#3")
        c.add({"id": "outro-shroud", "tags": ["ground", "shrouds"], "src": shroud.file, "t0": B(236), "t1": end,
               "time": {"in": 104.0, "speed": 0.6}, "fit": "picture", "crop": [0, 0.13, 0.86, 1],
               "opacity": keys([B(236), 0.0], [B(239), 0.7], [last_beat + 4, 0.7], [end - 0.5, 0.0], ease="smooth"),
               "fx": [{"op": "sat", "factor": 0.2}]})
    # kind == "head": nothing else; the night road and his shrinking face are the last image


def build(c, outro_kind="walkers"):
    first = len(c.layers)
    c._s2_real = []
    pools = Pools(c)
    dip_and_reentry(c, None)
    ch = chorus(c)
    reentry_and_peak1(c, pools, ch)
    lull(c, ch)
    peak2(c, pools, ch)
    hottest(c, pools, ch)
    cooling(c, pools, ch)
    ch.emit()
    pos, sc = plateau(c)
    outro(c, pos, sc, outro_kind)
    # inside each window of untreated reality: the preacher's words are cut, everything that isn't
    # the real footage goes dark (the chorus, the beds, the strike-cam, his head), Meine included
    W = []
    for a, b in sorted(c._s2_real):          # merge overlapping windows (the grid's tiles share one)
        if W and a <= W[-1][1] + 0.1:
            W[-1] = (W[-1][0], max(W[-1][1], b))
        else:
            W.append((a, b))
    keep = []
    for L in c.layers[first:]:
        ov = [(a, b) for a, b in W if L["t1"] > a and L["t0"] < b]
        if "real" in L.get("tags", []) or not ov:
            keep.append(L)
            continue
        if "audio" in L:           # a spoken word over the dead: drop it
            continue
        L["opacity"] = mul(L.get("opacity", 1.0), K.mute_signal(ov, 1.0, xf=0.04))
        keep.append(L)
    c.layers[first:] = keep
    for a, b in W:
        c.duck(a, hold=b - a, depth=0.0, attack=0.04, release=0.3)
    # footage stays inside Meine's picture area (y 158..922); the floating heads may cross the bars
    for L in c.layers[first:]:
        if "head" not in L.get("tags", []) and L.get("fit", "cover") != "native":
            L.setdefault("clip", "picture")


if __name__ == "__main__":
    section_main("s2_peak", SPAN, build)
