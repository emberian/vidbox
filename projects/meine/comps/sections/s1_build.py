"""0:38 - 3:45 (bars 20-118): absence, the second rant, absence, the return.

ember's direction (v2): his face is there only while he talks. After the s0 rant his head fades
away and the supply chain and the strikes carry bars 20-43 with Meine. At bar 44 (84.0 s) he rants
again, retimed so every "missiles" lands on the grid (sync/rant2.json -> media/derived/face_rant2.mp4),
steered by his gaze; on the first "Hellfire missiles" he splits into eight copies that mouth the rant
with him, pass "thou / shalt / give / Israel" between them, fold into a formation around him and
bounce through "I'm not paying enough". At the end of the rant (120.9 s) every head fades out. No
heads through the breakdown and the early rise. He fades back in at bar 110 (3:29.7), says "they need
more and more MISSILES" with MISSILES on bar 112, splits again, and the copies carry the climb into the
handoff at bar 118. Bar-by-bar map in s1_build_NOTES.md.
"""
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parents[3] / "render"), str(HERE)]
from comp import add, beat, intensity, keys, mul, rng, section_main  # noqa: E402
import s1_lib as L  # noqa: E402

SPAN = (38.301, 224.967)
ROOT_ = HERE.parents[3]
RANT2 = json.loads((ROOT_ / "projects/meine/sync/rant2.resolved.json").read_text())
FACE2 = "media/derived/face_rant2.mp4"          # clip time = song time - RANT2["start"]
GAZE2 = "paths/face_rant2_gaze.json"
R2_START, R2_END = RANT2["map"]["song"][0], RANT2["map"]["song"][-1]   # 84.013 .. 120.93


def r2(i):
    """Song time of rant word index i (analysis/rant_words.json numbering) in rant 2."""
    return next(w for w in RANT2["words"] if w["i"] == i)["start"]
PICTURE_C = (720, 540)
FORM_C = (720, 520)
SIZES = [0.62, 0.47, 0.40, 0.34, 0.30, 0.27, 0.23, 0.20]
BOX = (170, 300, 1270, 800)       # head centres stay inside the picture area
HOMES = [(560, 470), (1010, 380), (300, 330), (1230, 560), (720, 760), (420, 700), (930, 690), (1150, 300)]
CLIP_CROP = {   # per-clip caption/slate crops (swept 2026-10-24)
    "times-radio-idf-bombardment": [0.06, 0.16, 0.94, 0.76],    # "ISRAEL DEFENSE FORCES HANDOUT", channel bugs
    "idf-beit-hanoun": [0.06, 0.24, 0.94, 0.76],                # "Secondary Explosions" label
    "idf-": [0.06, 0.16, 0.94, 0.76],                           # IDF releases rebroadcast with lower-thirds, bugs
    "wsj-gaza-highrise": [0.12, 0.16, 0.88, 1.0],               # "GAZA OCT 12" top-left, WSJ bug top-right
    "aj-high-powered-bombs-explainer": [0.16, 0.2, 1.0, 0.68],  # subtitles
}
AP_CROP = [0.0, 0.16, 1.0, 1.0]    # drops AP's top-right bug (x 0.78-0.87, y 0-0.15)
NEWS_CROP = [0.0, 0.16, 1.0, 0.85]  # ground strikes: AP bug, place labels, lower thirds, network bugs
TIGHT_CROP = [0.0, 0.18, 1.0, 0.72]  # the rise's ground strikes: place captions and headlines ("ISRAEL BOMBS",
                                     # "GAZA CITY, GAZA STRIP") sit lower than NEWS_CROP's edge


def hit_fx(k, levels=6):
    return [{"op": "posterize", "levels": levels},
            {"op": "chroma", "px": rng(2, 18, beat(1, "decay", tau=0.18)), "angle": 37 * k}]


# ---------------------------------------------------------------- 36.8-40: he fades away
def s0_fade(c):
    """The s0 preacher stops at 36.84 (end of the rant) on his last frame; it dissolves over ~3.4 s,
    sinking a little, so his absence is felt rather than cut. Matches s0's layer (size, mask, opacity)."""
    t0, t1 = c.sync["map"]["song"][-1], c.bar(21)
    gz = L.path("face_self_gaze_synced")
    x, y = gz(36.8)
    c.add(L.head("s0-fade", t0, t1, keys([t0, [x, y]], [t1, [x - 40, y + 30]], ease="smooth"),
                 keys([t0, gz.scale(36.8)], [t1, gz.scale(36.8) * 0.9], ease="smooth"),
                 fx=[{"op": "blur", "px": keys([t0, 0], [t1, 6])}],
                 opacity=keys([t0, 0.75], [t1, 0.0], ease="smooth"), feather=0.28,
                 tags=("head", "fade"), src="media/derived/face_missiles_on_beat.mp4", hold=36.7))


# ---------------------------------------------------------------- bars 20-27: Meine, a fireball, the forge
def opening(c):
    b20, b28 = c.bar(20), c.bar(28)
    # the first downbeat after he stops: the "Apache in G Major" false-colour fireball
    tads = c.seg("weapons:hellfire-symphony-tads#5")
    c.duck(b20, hold=0.8, depth=0.4)
    c.footage(tads, at=b20, hit=0, before=0.12, after=2.6, blend="screen", opacity=0.9,
              fade={"in": 0.1, "out": 1.2}, fx=hit_fx(0, 7), id="split-fireball",
              **L.picture(tads, crop=[0.05, 0.05, 0.95, 0.88]))
    # supply chain: red-hot 155 mm noses into the press, one press stroke per two bars
    scr = c.seg("weapons:scranton-155mm-nosing-redhot#0")
    L.groove(c, scr, at=c.bar(21), dur=b28 - c.bar(21) + 1.0, cycle=4.0, beats=8,
             opacity=0.85, fade={"in": 1.5, "out": 1.0},
             fx=[{"op": "huekey", "hue": 8, "width": 24, "soft": 14, "sat": 0.35, "val": 0.25},
                 {"op": "sat", "factor": 1.4}, {"op": "bloom", "thresh": 0.5, "px": 18, "gain": 0.7}], id="scranton",
             **L.picture(scr))


def beat_decay(c, tau=0.15):
    """python-side beat envelope (for motion computed here, not in the renderer)."""
    import bisect
    B = c.beats

    def f(t):
        i = bisect.bisect_right(B, t) - 1
        return math.exp(-(t - B[i]) / tau) if i >= 0 else 0.0
    return f


def cut_keys(times, on_sets, total_t0, total_t1):
    """Opacity keys (hold) that switch on inside each [a, b) of on_sets, off elsewhere."""
    K = [[total_t0 - 0.01, 0]]
    for a, b in on_sets:
        K += [[a, 1], [b, 0]]
    K.append([total_t1, 0])
    return keys(*K, ease="hold")


def panel_cuts(c, seg, src_in, t0, t1, beats_on, w, h, pos, crop=(0, 0, 1, 1), id=None, fx=(), opacity=1.0,
               blend="normal", speed=1.0, loop=None):
    """An inset window running continuously t0..t1 but only visible on the given beats-of-bar
    (e.g. (0, 1) = first two beats of each bar): hard cuts on the grid."""
    on = []
    bar = c.bar_of(t0 + 0.01)
    while c.bar(bar) < t1 - 0.01:
        for b in beats_on:
            a = c.bar(bar, b)
            if t0 - 0.01 <= a < t1 - 0.01:
                on.append((a, min(c.bar(bar, b + 1), t1)))
        bar += 1
    if loop:    # a looped panel as an explicit map: one linear piece per pass, a 1 ms jump back between them
        a, b = loop
        per = (b - a) / speed
        song, srcs, t = [], [], t0
        while t < t1:
            e = min(t + per, t1)
            song += [round(t, 4), round(e - 0.001, 4)]
            srcs += [round(a, 4), round(a + (e - 0.001 - t) * speed, 4)]
            t = e
        time = {"map": {"song": song, "src": srcs}}
    else:
        time = {"in": src_in, "speed": speed}
    lay = {"id": id or f"{seg.clip['id']}#{seg.idx}@{t0:.2f}panel", "tags": [seg.catalog, "panel"] + seg.tags[:2],
           "src": seg.file, "t0": round(t0, 4), "t1": round(t1, 4), "time": time,
           "opacity": mul(cut_keys(None, on, t0, t1), opacity), "blend": blend,
           "fx": list(fx), "meta": {"catalog": seg.catalog, "clip": seg.clip["id"], "seg": seg.idx, "hits_song": []},
           **L.panel(seg, w, h, pos, crop)}
    c.add(lay)
    return lay


ARCHIVE = [{"op": "sat", "factor": 0.55}, {"op": "contrast", "factor": 1.25}, {"op": "posterize", "levels": 7}]


# ---------------------------------------------------------------- bars 28-43: the supply chain, no heads
def supply_chain(c):
    t_conv, b28, b32, b36, b40, b44 = c.bar(27, 1), c.bar(28), c.bar(32), c.bar(36), c.bar(40), c.bar(44)
    # -- supply chain, cut and grooved to the grid --
    # 28-31: JDAM build. A fuze screwed home (Whiteman) / blue-gloved hands seating a sensor (Balad)
    panel_cuts(c, c.seg("weapons:jdam-build-whiteman#2"), 27.0, b28, b32, (0, 1), 460, 330, [270, 540],
               fx=ARCHIVE, id="jdam-fuze")
    panel_cuts(c, c.seg("weapons:jdam-build-whiteman#1"), 19.5, b28, b32, (2, 3), 460, 330, [1170, 540],
               fx=ARCHIVE, id="jdam-hands")
    panel_cuts(c, c.seg("weapons:jdam-build-whiteman#3"), 36.0, c.bar(30), b32, (2, 3), 460, 330, [270, 540],
               fx=ARCHIVE, id="jdam-noses")
    # 32-35: the MK-84 ship at Ashdod, crane cycle (5 s) to two bars, screened over Meine
    ash = c.seg("weapons:imod-mk84-ashdod-feb2025#1")
    L.groove(c, ash, at=b32, dur=b36 - b32, cycle=5.0, beats=8, src_in=11.0, blend="screen", opacity=0.7,
             fade={"in": 0.3, "out": 0.4}, fx=[{"op": "levels", "black": 0.12, "white": 0.85}],
             id="ashdod", **L.picture(ash, crop=(0.12, 0.14, 1, 1)))   # IMOD camera icon top-left
    # 36-39: the first US munitions C-17 into Nevatim (vertical phone video: a tall window)
    c17 = c.seg("weapons:c17-first-us-munitions-israel-oct2023#0")
    lay = c.footage(c17, at=b36, after=b40 - b36, speed=1.0, id="c17-nevatim",
                    fade={"in": 0.15, "out": 0.3}, fx=[{"op": "contrast", "factor": 1.15}],
                    **L.panel(c17, 340, 600, keys([b36, [1180, 540]], [b40, [1120, 540]]), crop=(0.23, 0, 0.77, 1)))
    lay["time"]["in"] = 6.0
    c17b = c.seg("weapons:c17-first-us-munitions-israel-oct2023#1")
    panel_cuts(c, c17b, 34.0, c.bar(37), b40, (0, 1, 2, 3), 380, 300, [300, 755], fx=ARCHIVE, id="c17-apron")
    # 40-43: Hellfires out of their crates and onto the rail
    panel_cuts(c, c.seg("weapons:mq9-live-hellfire-holloman#1"), 13.4, b40, b44, (0, 1), 430, 330, [270, 560],
               crop=(0.42, 0, 1, 1), loop=(13.4, 16.0), id="hellfire-rail-night")   # loop: text cards follow
    panel_cuts(c, c.seg("weapons:mq9-hellfire-reload-gulfport#1"), 10.0, b40, b44, (2,), 430, 330, [1170, 480],
               crop=(0, 0, 1, 0.62), loop=(10.0, 12.4), fx=ARCHIVE, id="hellfire-crates")
    panel_cuts(c, c.seg("weapons:mq9-hellfire-reload-gulfport#2"), 12.8, b40, b44, (3,), 430, 330, [1170, 480],
               crop=(0, 0, 1, 0.62), fx=ARCHIVE, id="hellfire-carry")   # DVIDS caption below

    # -- strikes on the four-bar downbeats --
    # (the IDF Gaza crater strike-cam is s2's: one continuous four-hit take there, so it is not used here)
    for k, (ref, h, blend, depth) in enumerate([("weapons:times-radio-idf-bombardment-oct2023#2", 0, "screen", 0.5),
                                                ("weapons:idf-strikes-jan2014-blackhot#1", 0, "multiply", None),
                                                ("weapons:hellfire-symphony-tads#4", 0, "screen", 0.45)]):
        seg = c.seg(ref)
        at = [b32, b36, b40][k]
        if depth:
            c.duck(at, hold=0.6, depth=depth)
        crop = next((v for kk, v in CLIP_CROP.items() if seg.clip["id"].startswith(kk)), (0, 0, 1, 1))
        lay = c.footage(seg, at=at, hit=h, before=0.1, after=1.8, blend=blend, opacity=0.9,
                        fade={"in": 0.08, "out": 0.9}, fx=hit_fx(k + 1, 6), id=f"form-strike{k}",
                        **L.picture(seg, crop=crop))
        lay["meta"]["z"] = 2


# ---------------------------------------------------------------- bars 44-63: the second rant
def dense_val(sig, t):
    d = sig["dense"]
    x = min(max((t - d["t0"]) / d["dt"], 0), len(d["v"]) - 1)
    i = min(int(x), max(len(d["v"]) - 2, 0))
    a, b = d["v"][i], d["v"][min(i + 1, len(d["v"]) - 1)]
    u = x - i
    if isinstance(a, list):
        return [a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u]
    return a + (b - a) * u


MAIN_K = 0.72      # rant 2's main head: the gaze path grows him to 1.9x on eye contact; with eight copies
                   # around him that filled the frame, so he is held a little smaller than in s0


def rant2(c):
    b43, b44, b47, b56, b60, b64 = (c.bar(n) for n in (43, 44, 47, 56, 60, 64))
    off = RANT2["start"]                     # face_rant2.mp4 clip time = song time - off
    gz = L.path("face_rant2_gaze")
    main_fx = [{"op": "chroma", "px": rng(0, 10, beat(1, "decay", tau=0.12)), "angle": 0}]
    # he fades in over bar 43 on his first frame, then rants from bar 44, steered by his gaze (like s0)
    x0, y0 = gz(R2_START)
    c.add(L.head("r2-in", b43, R2_START, [x0, y0], gz.scale(R2_START) * MAIN_K, hold=0.2, src=FACE2, loop=None,
                 feather=0.28, opacity=keys([b43, 0.0], [R2_START, 0.75], ease="smooth"), tags=("head", "rant2")))
    main = L.head("r2-main", R2_START, R2_END, {"path": GAZE2}, mul({"pathscale": GAZE2}, MAIN_K), src_in=R2_START - off,
                  src=FACE2, loop=None, feather=0.28, opacity=0.75, fx=main_fx, audio={"gain": 1.0},
                  tags=("head", "rant2"), meta={"rant": "rant2", "hits_song": [round(r2(i), 3) for i in (13, 25, 29, 36, 50, 57)]})
    c.add(main)
    xe, ye = gz(R2_END)
    c.add(L.head("r2-out", R2_END - 0.02, b64, keys([R2_END, [xe, ye]], [b64, [xe - 30, ye + 40]], ease="smooth"),
                 keys([R2_END, gz.scale(R2_END) * MAIN_K], [b64, gz.scale(R2_END) * MAIN_K * 0.9]), hold=R2_END - off - 0.08, src=FACE2,
                 loop=None, feather=0.28, opacity=keys([R2_END, 0.75], [b64, 0.0], ease="smooth"),
                 fx=[{"op": "blur", "px": keys([R2_END, 0], [b64, 6])}], tags=("head", "rant2", "fade")))

    def main_pos(t):
        x, y = gz(min(max(t, R2_START), R2_END))
        return x, y

    # -- on "Hellfire MISSILES" (bar 47) he splits: a copy peels off on every beat and mouths the rant
    #    with him, in unison (same retimed clip, silent); the copies go where his gaze goes --
    W2 = {k: r2(i) for k, i in (("thou", 46), ("shalt", 47), ("give", 48), ("israel", 49), ("m5", 50), ("thou2", 51),
                                 ("shalt2", 52), ("give2", 53), ("israel2", 54), ("all", 55), ("m6", 57),
                                 ("enough1", 92), ("enough2", 96))}
    passing = [("thou", 0), ("shalt", 1), ("give", 2), ("israel", 3), ("thou2", 4), ("shalt2", 5), ("give2", 6),
               ("israel2", 7), ("all", 0)]
    pulse_env = beat_decay(c, 0.14)
    blocks = [("ring", b56, ("beat", 1 / 16)), ("sphere", c.bar(58), ("step", 0.25)), ("point", c.bar(59, 3), ("still", 0))]
    form = L.formation_track(c, 20, blocks, b60 + 0.04, lambda t: main_pos(t), 340, base_scale=0.13, depth=4.0,
                             morph_beats=2, tilt=0.7, wobble_bars=4, pulse=lambda t: 1 + 0.1 * pulse_env(t))

    def choices(t):
        return (2,) if t < c.bar(62) else (1,)
    for i in range(8):
        t_out, t_home = c.bar(47, i), c.bar(47, i + 1)
        hx, hy = HOMES[i]
        s_i = SIZES[i] * 0.85
        BK = L.bounce_keys(c, b60 + c.period, R2_END, BOX, choices, seed=60 + i)

        def fn(t, i=i, t_out=t_out, t_home=t_home, hx=hx, hy=hy, s_i=s_i, BK=BK):
            mx, my = main_pos(t)
            ms = gz.scale(min(max(t, R2_START), R2_END)) * MAIN_K
            gxo, gyo = (mx - 720) * 0.25, (my - 540) * 0.25          # where he looks, they drift
            # A/B: out of him, home, drifting with his gaze
            u = L.smooth((t - t_out) / (t_home - t_out))
            x = mx + (hx + gxo - mx) * u
            y = my + (hy + gyo - my) * u
            s = 0.9 * ms + (s_i * (0.8 + 0.2 * ms) - 0.9 * ms) * u
            # C: the formation around him, bars 56-59 (gathered over the last two beats of 55)
            w = L.smooth((t - c.bar(55, 2)) / (b56 - c.bar(55, 2))) * (1 - L.smooth((t - b60) / c.period))
            if w > 0:
                fx_, fy_ = dense_val(form[i][0], t)
                fs = dense_val(form[i][1], t)
                x, y, s = x + (fx_ - x) * w, y + (fy_ - y) * w, s + (fs - s) * w
            # D: bars 60-63 they bounce off the walls on the beats
            if t >= b60:
                v = L.smooth((t - b60) / c.period)
                bx, by = L.interp_keys(BK, t)
                x, y, s = x + (bx - x) * v, y + (by - y) * v, s + (s_i - s) * v
            # E: the rant is over; they fall back into him and fade with him
            e = L.smooth((t - R2_END) / (b64 - R2_END - 0.3))
            if e > 0:
                x, y, s = x + (mx - x) * e, y + (my - y) * e, s + (0.3 - s) * e
            return x, y, s
        pos, sc = L.dense_track(t_out, b64, fn)
        # word passing: on each of "thou shalt give Israel" (twice) one copy swells; on MISSILES
        # and on "enough" every copy does
        sw = [[t_out, 1.0]]
        for k, (w_, j) in enumerate(passing):
            if j == i:
                t = W2[w_]
                sw += [[t - 0.04, 1.0], [t + 0.04, 1.8], [t + 0.3, 1.8], [t + 0.42, 1.0]]
        for w_ in ("m5", "m6", "enough1", "enough2"):
            t = W2[w_]
            sw += [[t - 0.04, 1.0], [t + 0.03, 1.45], [t + 0.25, 1.45], [t + 0.5, 1.0]]
        sw = sorted(sw)
        c.add(L.head(f"r2copy{i}", t_out, b64, pos, mul(sc, keys(*sw), rng(0.94, 1.12, beat(1, "decay", tau=0.15))),
                     src_in=t_out - off, src=FACE2, loop=None, fx=L.character(BOUNCE_CHARS[i]),
                     rot=rng(-10, 10, beat(4, "sine", offset=i / 8)),
                     opacity=keys([t_out, 0.95], [R2_END, 0.95], [b64, 0.0], ease="smooth"),
                     tags=("head", "copy", "rant2")))
    # twelve more, small, only for the formation (bars 56-59), also mouthing the rant
    for i in range(8, 20):
        pos, sc = form[i]
        c.add(L.head(f"r2form{i}", c.bar(55, 2), b60 + c.period, pos, sc, src_in=c.bar(55, 2) - off, src=FACE2, loop=None,
                     fx=L.character((i + 3) % 14), opacity=0.95, fade={"in": 0.5, "out": 0.3},
                     tags=("head", "formation", "rant2")))

    # -- a strike lands on every "missiles" he says, Meine dipped under each --
    m = [r2(i) for i in (13, 25, 29, 36, 50, 57)]
    strike(c, "weapons:hellfire-symphony-tads#1", m[0], hit=0, duck=0.4, after=2.2, k=1, id="r2-hellfire-launch")
    rafah = c.seg("ground:afp-rafah-night-strikes-flares-2023-12#0")
    c.duck(m[1], hold=2.5, depth=0.45)
    lay = L.land_hits(c, rafah, m[1], div=1, before=0.5, after=1.2, blend="screen", opacity=0.95,
                      fade={"in": 0.2, "out": 0.6}, fx=hit_fx(5), id="rafah-domes", **L.picture(rafah))
    lay["meta"]["z"] = 2
    lay["tags"].append("strike")
    shore = c.seg("weapons:idf-gaza-strikes-oct13-2023#3")
    c.duck(m[2], hold=1.4, depth=0.4)
    lay = c.stutter(shore, at=m[2], hit=0, n=3, div=0.5, slice=0.14, after=1.6, fade={"in": 0.05, "out": 0.8},
                    fx=hit_fx(48), id="shore-stutter", **L.picture(shore))
    lay["meta"]["z"] = 2
    lay["tags"].append("strike")
    strike(c, "ground:reuters-explosions-overnight-2023-10-22#2", m[3], duck=0.4, crop=NEWS_CROP, k=3,
           id="r2-strike-m4")
    strike(c, "weapons:idf-gaza-strikes-oct13-2023#4", m[4], blend="normal", duck=0.35, after=2.0, k=4,
           id="r2-strike-m5")
    strike(c, "ground:ap-night-blast-gazacity-2014-07-20#0", m[5], duck=0.35, crop=NEWS_CROP, k=5,
           id="r2-strike-m6")


# ---------------------------------------------------------------- bars 44-71: the build
BOUNCE_K = {}
BOUNCE_CHARS = [0, 1, 2, 9, 10, 5, 12, 13]


def strike(c, ref, at, hit=0, blend="screen", duck=None, before=0.12, after=1.9, key=None, k=0, opacity=0.9,
           z=2, full=False, crop=(0, 0, 1, 1), extra_fx=(), **kw):
    seg = c.seg(ref)
    if duck:
        c.duck(at, hold=0.7, depth=duck)
    fx = ([{"op": "lumakey", "low": key[0], "high": key[1]}] if key else []) + hit_fx(k) + list(extra_fx)
    if tuple(crop) == (0, 0, 1, 1):
        crop = next((v for k, v in CLIP_CROP.items() if seg.clip["id"].startswith(k)), crop)
    frame = {"fit": "cover", "crop": list(crop)} if full else L.picture(seg, crop=crop)
    lay = c.footage(seg, at=at, hit=hit, before=before, after=after, blend=blend, opacity=opacity,
                    fade={"in": 0.06, "out": 0.8}, fx=fx, **frame, **kw)
    lay["meta"]["z"] = z
    lay["tags"].append("strike")
    return lay


def untreated(c, seg, at, hit=None, until=None, src=None, gain=0.9, people=None, id=None, before=0.0, **frame):
    """Reality, undecorated: normal blend, no fx, no key, its own sound; lands `hit` on `at` (or starts
    at `at` from source time `src`) and plays at 1x until `until`. frame: picture/panel props."""
    if hit is not None:
        h = seg.hits[hit]["t"]
        t0, s0 = at - before, h - before
    else:
        t0, s0 = at, seg.t_in if src is None else src
    lay = {"id": id or f"{seg.clip['id']}#{seg.idx}@{at:.2f}~real", "tags": [seg.catalog, "untreated"] + seg.tags[:2],
           "src": seg.file, "t0": round(t0, 4), "t1": round(until, 4), "time": {"in": round(s0, 4), "speed": 1.0},
           "blend": "normal", "audio": {"gain": gain}, "fade": {"in": 0.04, "out": 0.25},
           "meta": {"catalog": seg.catalog, "clip": seg.clip["id"], "seg": seg.idx, "z": 2.5, "untreated": True,
                    "hits_song": [round(at, 3)] if hit is not None else []}, **frame}
    if people:
        lay["meta"]["people"] = people
    c.add(lay)
    return lay


BAR_S = 4 * 0.476      # one bar at 126 BPM: the shortest music-duck release (ember: ducks must linger)


def music_dip(c, t0, t1, depth):
    """ember's duck rule: only a hold of 4+ bars may go deep (0.15-0.3); anything shorter stays
    shallow (0.5-0.7). Every release lasts at least a bar."""
    if t1 - t0 < 4 * BAR_S - 0.05:
        depth = max(depth, 0.5)
    c.duck_music(t0, hold=t1 - t0, depth=depth, attack=0.15, release=2.0)


def lower_third(c, lines, at, dur, id):
    """One name card at a time, in the letterbox under the picture. A new card cuts the previous one
    short, but each stays up at least 2 s (the new one waits if it must)."""
    prev = getattr(c, "_s1_card", None)
    if prev is not None and prev["t1"] > at:
        at = max(at, prev["t0"] + 2.0)
        prev["t1"] = round(at, 4)
    lay = c.text_card(lines, at, dur, pos=(110, 932), size=36, id=id, tags=["text", "lower-third"], meta={"z": 6})
    c._s1_card = lay
    return lay


def speaker(c, stem, word, at, k=1, oval=True, pos=(720, 540), scale=None, size=None, crop=(0, 0, 1, 1),
            src_in=0.0, until=None, play=False, swell=(), gain=2.8, duck=0.5, card=None, card_dur=None, z=3.5,
            fade=(0.25, 0.4), video=True, opacity=0.92, id=None, **extra):
    """A real politician or preacher, named on screen, saying a line from media/derived/preachers.
    `word` (its k-th occurrence) starts exactly at song time `at`, which is on the grid.
    oval: a floating face-tracked head, like Hyde's; else a framed window (size, crop) of the broadcast.
    play: join the beat-locked play (pulse on the beat, a little sway and RGB split): only over the
    arsenal, the strike-cam and the beds, never over the dead, where speakers stay still and plain.
    swell: words on which the head swells (like Hyde's copies on "missiles"). video=False: voice only.
    card: lower-third lines, set in the letterbox below the picture so they never cover a face or a
    victim. duck: the music dip under the voice (music_dip applies ember's depth rule)."""
    ln = L.speech(stem)
    zero = at - L.word_at(ln, word, k)                 # song time of the clip's first frame
    t0 = zero + src_in
    t1 = until if until is not None else zero + (ln["span"][1] - ln["span"][0])
    src = f"{L.PREACH}/{stem}.mp4"
    lay = {"id": id or f"spk:{stem}", "tags": (["head", "speaker"] if oval else ["speaker", "window"]),
           "src": src, "t0": round(t0, 4), "t1": round(t1, 4), "time": {"in": round(src_in, 3), "speed": 1.0},
           "audio": {"gain": gain}, "fade": {"in": fade[0], "out": fade[1]}, "opacity": opacity,
           "meta": {"catalog": "preachers", "clip": stem, "seg": 0, "hits_song": [round(at, 3)], "z": z,
                    "people": [{"name": ln["person"], "role": ln["role"], "date": ln["date"],
                                "source": ln["source_url"]}]}}
    sc = scale if scale is not None else (0.6 if oval else 1.0)
    if swell:
        sw = [[t0, 1.0]]
        for w in swell:
            t = zero + L.word_at(ln, *(w if isinstance(w, tuple) else (w,)))
            sw += [[t - 0.05, 1.0], [t + 0.04, 1.2], [t + 0.32, 1.2], [t + 0.55, 1.0]]
        sc = mul(sc, keys(*sorted(sw), ease="smooth"))
    if play:
        sc = mul(sc, rng(0.96, 1.06, beat(1, "decay", tau=0.16)))
        lay["rot"] = rng(-3, 3, beat(8, "sine"))
        lay["fx"] = [{"op": "chroma", "px": rng(0, 7, beat(1, "decay", tau=0.14)), "angle": 20}]
    if oval:
        lay.update({"size": [480, 600], "mask": {"shape": "oval", "feather": 0.26}, "pos": pos, "scale": sc})
    else:
        w, h = size
        lay.update({"size": [w, h], "crop": L.aspect_crop(src, w / h, crop), "pos": pos, "scale": sc,
                    "mask": {"shape": "rect", "feather": 0.03}})
    if not video:
        lay["opacity"] = 0
        lay["tags"] = ["voice", "speaker"]
    lay.update(extra)
    c.add(lay)
    if duck:
        music_dip(c, t0, t1, duck)
    if card:
        lower_third(c, card, t0 + 0.15, card_dur or min(max(t1 - t0, 4.0), 7.0), id=f"card:{stem}")
    return lay


# ---------------------------------------------------------------- bars 21-42: the politicians
def politicians(c):
    """Between the rants, over the supply chain: real politicians saying it in earnest, each named and
    dated, a key word of each on the grid. They join the beat play here (this is the arsenal)."""
    bar = c.bar
    # Graham: Hiroshima "was the right decision" / "Give Israel the BOMBS they need" (BOMBS on bar 25)
    speaker(c, "graham_mtp_bombs__hiroshima_bombs", "bombs", bar(25), pos=keys([bar(21), [430, 480]], [bar(27), [520, 450]],
            ease="smooth"), scale=0.62, play=True, swell=("bombs", "Hiroshima"),
            card=["Sen. Lindsey Graham (R-SC)", "Meet the Press, NBC  ·  12 May 2024"])
    # Johnson, then Cruz: Genesis 12:3, "bless" landing on bar 27 and bar 30
    speaker(c, "johnson_bible_bless__bless_curse", "bless", bar(27), pos=[720, 400], scale=0.6, play=True, gain=3.3,
            swell=("blesses", "curses"),
            card=["Speaker Mike Johnson (R-LA)", "Speaker of the US House  ·  Capitol press briefing  ·  23 Jul 2024"])
    speaker(c, "cruz_tucker_bless__taught_bless", "bless", bar(30), pos=[720, 410], scale=0.6, play=True,
            swell=("Bible", "blessed"), card=["Sen. Ted Cruz (R-TX)", "The Tucker Carlson Show  ·  18 Jun 2025"])
    # ... and Tucker Carlson: "Where is that?", WHERE on bar 31 (the broadcast's own cut from Cruz to him)
    speaker(c, "cruz_tucker_bless__where_is_that", "Where", bar(31), oval=False, size=(400, 225), pos=[720, 330],
            crop=(0.08, 0, 0.92, 1), fade=(0.06, 0.3), z=3.6,
            card=["Tucker Carlson", "to Sen. Ted Cruz  ·  The Tucker Carlson Show  ·  18 Jun 2025"], card_dur=3.0)
    # Walberg (voice only: filmed from behind): "...like Nagasaki and Hiroshima. Get it over QUICK" on bar 36,
    # where the black-hot strike lands
    speaker(c, "walberg_nagasaki__nagasaki_quick", "quick", bar(36), video=False, oval=False, size=(480, 270),
            card=["Rep. Tim Walberg (R-MI)", "former pastor  ·  town hall, Dundee, Michigan  ·  25 Mar 2024  ·  audio"],
            card_dur=8.0)
    # Haley: "finish them. Finish them." (Hannity), FINISH on bar 38, over her writing on a shell in Israel
    hv = speaker(c, "haley_hannity_finish__finish_them", "finish", bar(38), video=False, oval=False, size=(480, 270),
                 card=["Nikki Haley", "former UN ambassador  ·  Hannity, Fox News  ·  8 Oct 2023",
                       "writing on an Israeli artillery shell, near the Lebanon border  ·  28 May 2024"], card_dur=6.0)
    shell = f"{L.PREACH}/haley_finish_them__shell.mp4"
    c.add({"id": "spk:haley-shell", "tags": ["speaker", "window"], "src": shell, "t0": round(hv["t0"] - 0.2, 4),
           "t1": round(hv["t0"] + 6.2, 4), "time": {"in": 0.0, "speed": 1.0}, "fade": {"in": 0.2, "out": 0.4},
           "size": [430, 250], "crop": L.aspect_crop(shell, 430 / 250, (0.235, 0.0, 0.765, 0.55)),
           "pos": [340, 330], "mask": {"shape": "rect", "feather": 0.03},
           "meta": {"catalog": "preachers", "clip": "haley_finish_them__shell", "seg": 0, "hits_song": [], "z": 3.2}})
    # Ogles, confronted in a Capitol hallway: "that's my taxpayer dollars ... I think we should KILL them all",
    # KILL on bar 42 (the vertical phone video's middle, above its burned-in captions)
    speaker(c, "ogles_kill_them_all__kill_them_all", "kill", bar(42), oval=False, size=(330, 366), pos=[720, 450],
            crop=(0.355, 0.07, 0.64, 0.645), play=False,
            card=["Rep. Andy Ogles (R-TN)", "confronted by CODE PINK activists, US Capitol  ·  Feb 2024"])


# ---------------------------------------------------------------- bars 64-107: the preachers
def preachers(c):
    """After the second rant, over the strikes and the untreated reality: preachers saying it in earnest.
    Over the dead they are still, plain and to one side, framing the victims rather than covering them;
    over strikes, launches and beds they join the play. Rev. Munther Isaac answers them, alone."""
    bar = c.bar
    # 64-65 Hibbs, over the strikes as Hyde's heads fade: "insulting GOD by hamstringing his own people"
    speaker(c, "hibbs_weapons_insulting_god__insulting_god", "God", bar(65), pos=keys([bar(64), [1040, 640]],
            [bar(66), [1080, 660]], ease="smooth"), scale=0.62, play=True, swell=("insulting", "hamstringing"),
            card=["Pastor Jack Hibbs", "Calvary Chapel Chino Hills  ·  Washington Watch (FRC)  ·  14 May 2024"])
    # 68-71 Hagee at the CUFI summit (the broadcast: crowd, then the arena and his pulpit), beside the Reaper
    # countdown: "We must give them the weapons of war to win that FIGHT", FIGHT on the blast, bar 72
    speaker(c, "hagee_cufi2024_weapons__weapons_of_war", "fight", bar(72), k=2, oval=False, size=(600, 338),
            pos=[370, 470], src_in=3.52, gain=2.8, duck=0.5, z=3.4,
            card=["Pastor John Hagee", "founder, Christians United for Israel  ·  CUFI Summit, Washington  ·  29 Jul 2024"])
    # 72-73 Bachmann over the Maghazi families walking out at dusk: "an opportunity to BLESS Israel"
    # (BLESS on bar 73 beat 3, the dark horizon; it is over before that evening's strike lands on bar 74)
    speaker(c, "bachmann_blessed__bless_israel", "bless", bar(73, 2), pos=[1185, 330], scale=0.48, gain=1.3,
            duck=0.18, z=5, card=["Michele Bachmann", "former US Rep. (R-MN)  ·  broadcast interview  ·  4 Mar 2026"])
    # 76-79 Evans, waving his Bible, over Mahmoud Hammad sieving for his family: "I will bless them that
    # bless thee ... America has been blessed because of this" (I on bar 76)
    speaker(c, "evans_bless_thee__bless_thee", "I", bar(76), pos=[1200, 330], scale=0.5, gain=1.3, duck=0.18, z=5,
            card=["Mike Evans", "founder, Friends of Zion  ·  address to Tucker Carlson  ·  31 Oct 2025"])
    # 80-83 Huckabee above the stack of the dead: "Genesis 12, those who bless Israel will be blessed ...
    # I want to be on the blessing side, not the curse side" (GENESIS on bar 80)
    speaker(c, "huckabee_bless_side__blessing_side", "Genesis", bar(80), pos=[755, 330], scale=0.45, gain=1.3,
            duck=0.18, z=5, card=["Mike Huckabee", "Baptist minister, now US ambassador to Israel  ·  "
                                  "The Charlie Kirk Show  ·  14 Nov 2024"])
    # 85 Huckabee again, over the Nasser courtyard graves: "It would be FINE if they took it all"
    speaker(c, "huckabee_tucker_take_it_all__take_it_all", "fine", bar(85), pos=[1200, 320], scale=0.48, gain=2.6,
            duck=0.5, z=5, card=["Mike Huckabee", "US ambassador to Israel  ·  The Tucker Carlson Show  ·  20 Feb 2026"])
    # 88-93 Vaughn sings over the launches, a sung layer under Daso: "What wonderful days these days are
    # before the coming of the Lord" (WHAT on bar 88); then "Oh, the glory" on bar 94's launch, and four
    # silent copies of him wheel round him on the grid
    speaker(c, "vaughn_wonderful_days__wonderful_days", "What", bar(88), pos=keys([bar(88), [1060, 470]],
            [bar(94), [960, 430]], ease="smooth"), scale=0.6, play=True, gain=2.5, duck=0.6,
            card=["Shane Vaughn", "pastor, First Harvest Ministries  ·  his webcast, the night Israel struck Iran"
                  "  ·  13 Jun 2025"])
    g = speaker(c, "vaughn_wonderful_days__glory", "Oh", bar(94), pos=[720, 500], scale=0.62, play=True, gain=2.5,
                duck=0.6, swell=("glory",))
    ring = L.formation_track(c, 4, [("ring", g["t0"], ("beat", 1 / 8))], g["t1"], (720, 500), 330, base_scale=0.3,
                             depth=4.0, tilt=0.35, wobble_bars=2)
    for i, (pos, sc) in enumerate(ring):
        c.add({"id": f"spk:vaughn-ring{i}", "tags": ["head", "speaker", "copy"], "src": g["src"], "t0": g["t0"],
               "t1": g["t1"], "time": {"in": 0.0, "speed": 1.0}, "size": [480, 600],
               "mask": {"shape": "oval", "feather": 0.26}, "pos": pos, "scale": sc, "opacity": 0.85,
               "fade": {"in": 0.3, "out": 0.4}, "fx": L.character([0, 9, 6, 12][i]),
               "meta": {"z": 3.4}})
    # 96-97 Hibbs again over the strike-cam and the walkers: "poking the God of Abraham, Isaac, and Jacob
    # right in the EYE", EYE on bar 98's strike
    speaker(c, "hibbs_weapons_insulting_god__poking_god", "eye", bar(98), pos=[430, 430], scale=0.6, play=True,
            swell=("God",))
    # 100-103 Hagee at the March for Israel, beside the Deir al-Balah tents: "VICTORY was our only aim, and
    # Israel should be afforded that same opportunity" (VICTORY on bar 100 beat 3, after the fireballs)
    speaker(c, "hagee_march_victory__victory", "victory", bar(100, 2), pos=[285, 470], scale=0.55, gain=1.9,
            duck=0.3, z=5, card=["Pastor John Hagee", "March for Israel, National Mall, Washington  ·  14 Nov 2023"])
    # 104-107 Rev. Munther Isaac, alone and not multiplied, over Gaza City's ruins: "Here in Palestine, the
    # Bible is weaponized against us, our very own sacred text" (HERE on bar 104)
    speaker(c, "isaac_bible_weaponized__weaponized", "Here", bar(104), oval=False, size=(520, 439), pos=[720, 520],
            crop=(0.33, 0.0, 0.83, 0.75), gain=2.4, duck=0.3, z=5, opacity=1.0, fade=(0.5, 0.6),
            card=["Rev. Munther Isaac", "Lutheran pastor, Bethlehem  ·  “Christ in the Rubble”"
                  " Christmas liturgy  ·  23 Dec 2023"])


def build_up(c):
    b44, b48, b52, b56, b60, b64, b68, b72 = (c.bar(n) for n in (44, 48, 52, 56, 60, 64, 68, 72))
    # -- supply chain keeps coming --
    gbu = c.seg("weapons:gbu39-load-mq9-night#0")
    L.groove(c, gbu, at=b44, dur=b48 - b44, cycle=1.0, beats=2, src_in=30.0, blend="screen", opacity=0.75,
             fade={"in": 0.2, "out": 0.4}, fx=[{"op": "levels", "black": 0.1}], id="sdb-night", **L.picture(gbu))
    panel_cuts(c, c.seg("weapons:israel-gbu31-prep-oct2023-reedit#1"), 9.0, b48, b52, (0, 2), 480, 300,
               [300, 360], crop=(0, 0.12, 1, 1), fx=ARCHIVE, id="gbu31-rows")   # channel watermark top-left
    panel_cuts(c, c.seg("weapons:israel-gbu31-prep-oct2023-reedit#2"), 38.0, b48, b52, (1, 3), 480, 300,
               [1140, 720], crop=(0, 0.12, 1, 1), fx=ARCHIVE, id="gbu31-forklift")
    panel_cuts(c, c.seg("weapons:iaf-swords-of-iron-loadout-reupload#0"), 40.0, b52, b56, (0, 1, 2, 3), 520, 300,
               keys([b52, [1130, 360]], [b56, [1050, 360]]), fx=ARCHIVE, id="iaf-pylons")

    # -- Gaza from above, under everything, rising with the music (AP drone, bug cropped) --
    for n0, n1, ref, src_in, op, blend in [
            (52, 60, "ground:ap-drone-khanyounis-2025-01-long", 60.0, (0.12, 0.3), "normal"),
            (60, 68, "ground:ap-drone-coast-road-return-2025-01-long", 92.0, (0.45, 0.7), "multiply"),
            (68, 72, "ground:ap-zikim-flour-multitude-2025-07-30", 4.0, (0.35, 0.5), "normal")]:
        clip = next(x for x in c.cat["ground"] if x["id"] == ref.split(":")[1])
        src = clip["file"]
        lay = {"id": f"gaza-bed-{n0}", "tags": ["ground", "bed"], "src": src, "t0": c.bar(n0), "t1": c.bar(n1),
               "time": {"in": src_in, "speed": 1.0}, "opacity": rng(*op, intensity(2.0)), "blend": blend,
               "fade": {"in": 1.0, "out": 0.3}, "fx": [{"op": "sat", "factor": 0.8}],
               "meta": {"catalog": "ground", "clip": clip["id"], "hits_song": [], "z": 0},
               **L.picture(src, crop=AP_CROP)}
        c.add(lay)
    # digging by hand, civil defence (1.1 s per pull, two beats per pull)
    # (ember: Hyde's comic heads stay off the dead, so the civil-defence body recovery that sat under his
    #  formation is gone; the Iowa shell line's workers, one hand-cycle per bar, take its panel)
    iowa = c.seg("weapons:iowa-aap-155mm-line-workers#0")
    L.groove(c, iowa, at=b56, dur=b64 - b56, cycle=3.0, beats=4, src_in=2.0, id="iowa-shell-line",
             fade={"in": 0.2, "out": 0.2}, fx=ARCHIVE + [{"op": "duotone", "dark": [0.05, 0.02, 0.0], "light": [1.0, 0.8, 0.55]}],
             **L.panel(iowa, 440, 300, [1150, 700]))

    # -- strikes, landing on downbeats; denser as the build goes --
    plan = [
        (64, 0, "weapons:idf-gaza-strikes-oct13-2023#0", 0, "normal", 0.35, None),
        (65, 0, "y2026:idf-soldiers-watch-demolition-yellow-line-2026-07-08#0", 0, "screen", None, None),
        (65, 2, "ground:reuters-night-fireballs-2023-10-08#0", 0, "screen", None, None),
        (67, 0, "weapons:hellfire-symphony-tads#8", 0, "screen", None, None),
        (67, 2, "ground:ap-night-flares-explosions-2023-11-09#0", 0, "screen", None, None),
        (68, 0, "ground:newscomau-gaza-city-towers-2025-09#7", 0, "screen", 0.35, None),
        (69, 0, "weapons:idf-beit-hanoun-launcher-2014#1", 1, "multiply", None, None),
        (69, 2, "ground:reuters-explosions-overnight-2023-10-22#3", 0, "screen", None, None),
    ]
    for k, (bar, bb, ref, h, blend, duck, key) in enumerate(plan):
        strike(c, ref, c.bar(bar, bb), hit=h, blend=blend, duck=duck, key=key, k=k,
               after=1.6 if bar < 64 else 1.2, crop=NEWS_CROP if ref.startswith("ground:") else (0, 0, 1, 1),
               id=f"build-strike-{bar}.{bb}")
    # 66-67: a stack. Four strikes on Gaza, untreated, land one per beat of bar 66 into the four
    #        quarters of the picture and stay there, each with its own sound
    quads = [(360, 349), (1080, 349), (360, 731), (1080, 731)]
    for k, (ref, h, crop) in enumerate([("y2026:ap-zeitoun-cemetery-strike-2026-02-06#0", 0, (0, 0.16, 1, 0.8)),
                                        ("ground:reuters-explosions-overnight-2023-10-22#0", 0, (0, 0, 1, 0.62)),
                                        # al-Ansar tent camp, 11 Mar 2026 (Guardian): Guardian logo and the
                                        # caption box (from 4.5 s) cropped; men watching in the street stay
                                        ("ground:guardian-ansar-tent-strike-2026-03#0", 0, (0, 0.09, 1, 0.70)),
                                        ("ground:nbc-night-tower-collapse-2023-10-08#0", 0, NEWS_CROP)]):
        seg = c.seg(ref)
        at = c.bar(66, k)
        untreated(c, seg, at, hit=h, until=c.bar(68), gain=0.45, id=f"stack66-{k}", before=0.08,
                  **L.panel(seg, 720, 382, list(quads[k]), crop=crop, feather=0.0))
    c.duck(c.bar(66), hold=3.0, depth=0.3)
    music_dip(c, c.bar(66), c.bar(68), 0.6)
    # -- countdown: the Reaper monitor's 3, 2, 1 on two-beat steps, the strike on bar 72's downbeat --
    cd = c.seg("weapons:mq9-live-hellfire-holloman#7")
    hs = [x["t"] for x in cd.hits]          # 69.6 "3", 70.62 "2", 71.72 "1", 72.62 blast
    tg = [c.bar(70, 2), c.bar(71), c.bar(71, 2), b72]
    lay = L.map_footage(c, cd, [tg[0] - 0.9] + tg + [b72 + 0.9], [hs[0] - 0.9] + hs + [hs[3] + 0.9], hits_song=tg,
                        id="countdown", fade={"in": 0.2, "out": 0.5},
                        fx=[{"op": "contrast", "factor": 1.3}, {"op": "chroma", "px": rng(0, 14, beat(1, "decay", tau=0.15))}],
                        **L.panel(cd, 640, 360, [1050, 560]))   # right: Hagee's CUFI window is on the left
    lay["meta"]["z"] = 4


Z_DEFAULT = {"bed": 0, "panel": 1, "groove": 1, "strike": 2, "head": 3}


def zsort(layers):
    def z(Ly):
        if "z" in Ly.get("meta", {}):
            return Ly["meta"]["z"]
        return max((Z_DEFAULT.get(t, 1) for t in Ly.get("tags", [])), default=1)
    layers.sort(key=z)


# ---------------------------------------------------------------- bars 72-87: the breakdown
def breakdown(c):
    """The music drops out on bar 72 and the piece lets reality in: untreated, large, with its own sound,
    each shot held for bars. No heads, no effects. The music is dipped further so the real sound leads."""
    b72, b74, b76, b80, b84, b88 = (c.bar(n) for n in (72, 74, 76, 80, 84, 88))
    Y = "y2026:"
    # 72-75: Maghazi camp, 15 Jul 2026 (AP). Families walk out along a rubble road at dusk under an
    #        evacuation order; then, in AP's own sequence, the strike that evening: a ball of flame on the
    #        horizon, on bar 74's downbeat. Two untreated shots of one story, cut on bar 73, their own
    #        sound. (The Zinati killing is shown once, in s2 at bar 204.)
    b73 = c.bar(73)
    walk = c.seg(Y + "ap-maghazi-evacuation-dusk-strikes-2026-07-15#0")
    lay = untreated(c, walk, c.bar(72, 1), src=8.0, until=b73, gain=1.0, id="maghazi-evacuation-walk",
                    **L.picture(walk, crop=AP_CROP))
    lay["meta"]["z"] = 4.5     # above the Reaper countdown's fading tail: no targeting screen over the families
    blast = c.seg(Y + "ap-maghazi-evacuation-dusk-strikes-2026-07-15#1")
    untreated(c, blast, b74, hit=0, before=b74 - b73, until=b74 + 1.6, gain=1.0, id="maghazi-dusk-strike",
              **L.picture(blast, crop=AP_CROP))
    c.duck_music(c.bar(72, 1), hold=b76 - c.bar(72, 1), depth=0.18, attack=0.3, release=2.0)
    # (cut 1.6 s after the fireball, as the cloud climbs; ~0.8 s of Meine alone follows before Hammad)
    # 76-83: Gaza City, Jan 2026 (AP). Mahmoud Hammad sieves the sand of his house for the bones of his
    #        wife and children; one shake of the sieve every two beats; then his fingers lift the fragments
    ham = c.seg(Y + "ap-father-sieves-bones-2026-01-24#0")
    lay = L.groove(c, ham, at=b76, dur=b84 - b76, cycle=1.0, beats=2, src_in=0.5, id="hammad-sieve",
                   blend="normal", audio={"gain": 1.0}, fade={"in": 0.3, "out": 0.4},
                   **L.picture(ham, crop=AP_CROP))
    lay["tags"].append("untreated")
    lay["meta"].update({"z": 2.5, "untreated": True,
                        "people": [{"name": "Mahmoud Hammad", "role": "father; his wife and children were killed",
                                    "source": ham.clip["source_url"]}]})
    c.duck_music(b76, hold=b84 - b76, depth=0.18, attack=0.2, release=2.0)    # Hammad, then the stack
    # 80-83: the stack. Over Hammad, one window per downbeat, each untreated with its own sound:
    #        flag-wrapped remains with photos and names on paper at the Gaza City mass funeral of 105
    #        (AP, 1 Oct 2026), men standing over the shrouded bodies of nine members of one family at
    #        al-Najjar hospital, Rafah (AP, 12 Jan 2024), the Nasser hospital courtyard graves (NBC)
    tiles = [(Y + "ap-mass-funeral-105-2026-10-01#3", 36.0, AP_CROP, (1110, 400), (420, 440)),
             ("ground:ap-rafah-family-shrouds-2024-01#1", 5.5, AP_CROP, (330, 400), (560, 340)),
             ("ground:nbc-nasser-courtyard-graves-2024-01#2", 17.0, (0, 0, 1, 0.84), (720, 720), (560, 340))]
    for k, (ref, src, crop, pos, wh) in enumerate(tiles):
        seg = c.seg(ref)
        untreated(c, seg, c.bar(81 + k), src=src, until=b84, gain=0.6, id=f"stack80-{k}",
                  **L.panel(seg, wh[0], wh[1], list(pos), crop=crop, feather=0.0))
    # 84-87, the riser: the graves fill the picture, still untreated, the music climbing back over them
    graves = c.seg("ground:nbc-nasser-courtyard-graves-2024-01#2")
    #    (the tile's take continues: the tile grows into the picture)
    lay = untreated(c, graves, b84, src=17.0 + (b84 - c.bar(83)), until=b88, gain=0.6, id="graves",
                    **L.picture(graves, crop=(0, 0, 1, 0.84)))


# ---------------------------------------------------------------- bars 88-118: the rise
def rise(c):
    B = {n: c.bar(n) for n in range(86, 120)}
    b88, b96, b104, b112, b116, b118, b119 = B[88], B[96], B[104], B[112], B[116], B[118], B[119]
    # -- the return: he fades in at bar 110 (3:29.7), silent, then "they need more and more MISSILES"
    #    with MISSILES on bar 112's downbeat, in his own voice; on that word he splits again --
    b110, b111 = B[110], B[111]
    ret_src = (9.08, 10.262)                # face.mp4: "They" .. "missiles" (rant words 20-25)
    t_say = b112 - (ret_src[1] - ret_src[0])
    def ret_fn(t):
        gx, gy, gs = L.gaze_offset(t, t_say, ret_src[0], k=0.25)
        return 720 + gx, 520 + gy, 0.75 + 0.2 * (gs - 1)
    pos, sc = L.dense_track(b110, b112 + 0.7, ret_fn)
    c.add(L.head("return-still", b110, t_say, pos, sc, hold=ret_src[0], loop=None, feather=0.28,
                 opacity=keys([b110, 0.0], [b111 + 0.5, 0.75], ease="smooth"), tags=("head", "return")))
    c.add(L.head("return-say", t_say, b112 + 0.75, pos, sc, src_in=ret_src[0], loop=None, feather=0.28,
                 opacity=0.75, fade={"out": 0.25}, audio={"gain": 1.0}, tags=("head", "return"),
                 meta={"hits_song": [round(b112, 3)], "word": "missiles"}))

    # -- layer A (heads): eight burst out of him on MISSILES and bounce, walls on beats, every beat --
    def choices(t):
        return (2, 1) if t < B[114] else (1,)
    for i in range(8):
        K = L.bounce_keys(c, b112 + c.period, b118, BOX, choices, seed=90 + i)
        K = [[b112, [720, 520]]] + K[1:]
        # the last flight of every head ends in the middle on bar 118's downbeat
        K = [k for k in K if k[0] < c.bar(117, 3)] + [[b118, [720, 540]]]
        size = SIZES[i] * 0.8
        sc = mul(rng(size * 0.85, size * 1.3, intensity(2.0)), rng(0.9, 1.22, beat(1, "decay", tau=0.13)),
                 keys([b112, 0.2], [b112 + c.period, 1.0], [c.bar(117, 3), 1.0], [b118, 0.15], ease="smooth"))
        c.add(L.head(f"rise{i}.0", b112, b118, keys(*K), sc, src_in=(i * 3.7 + 9) % 34,
                     fx=L.character(BOUNCE_CHARS[(i + 3) % 8]), rot=rng(-18, 18, beat(2, "sine", offset=i / 8)),
                     opacity=0.95, fade={"in": 0.05, "out": 0.04}, tags=("head", "bounce", "rise")))

    # -- layer B (small heads): sphere then cube, spun on the grid, collapsing on 118 --
    pulse_env = beat_decay(c, 0.12)
    blocks = [("point", b112, ("still", 0)), ("sphere", b112 + 2 * c.period, ("step", 0.25)),
              ("cube", B[114], ("beat", 1 / 8)), ("point", c.bar(117, 2), ("still", 0))]
    tracks = L.formation_track(c, 20, blocks, b118 + 0.04, (720, 530), 300, base_scale=0.09, depth=4.0,
                               morph_beats=2, tilt=0.6, wobble_bars=4, pulse=lambda t: 1 + 0.12 * pulse_env(t))
    for i, (pos, sc) in enumerate(tracks):
        c.add(L.head(f"rform{i}", b112, b118, pos, sc, src_in=(i * 1.7 + 5) % 34, fx=L.character((i + 7) % 14),
                     opacity=0.95, fade={"in": 0.3, "out": 0.05}, tags=("head", "formation", "rise")))

    # -- layer C (beds): the machine and the people, alternating --
    launches = [("weapons:juniper-oak-2023-broll#0", 0), ("weapons:apache-red-sands-uas#0", 0),
                ("weapons:hellfire-yakima-broll#3", None), ("y2026:lockheed-pac3-triple-short-2026-07-29#1", 0)]
    for k, n in enumerate(range(88, 96, 2)):        # a launch on every other downbeat: HIMARS in the Negev,
        tom = c.seg(launches[k][0])                 # then the US arsenal's range shoots
        lay = c.footage(tom, at=B[n], hit=launches[k][1], before=0.4, after=B[n + 2] - B[n] - 0.4 + 0.1,
                        opacity=0.55, fade={"in": 0.08, "out": 0.2}, fx=ARCHIVE, id=f"launch-{n}",
                        **L.picture(tom))
        lay["meta"]["z"] = 0
        c.duck(B[n], hold=0.5, depth=0.5)
    walk = c.seg("ground:ap-drone-return-north-coast-2025-01#1")
    lay = L.groove(c, walk, at=b96, dur=B[100] - b96 + 0.3, cycle=0.55, beats=1, src_in=7.5, blend="multiply",
                   opacity=0.75, fade={"in": 0.3, "out": 0.3}, id="return-north-walk", **L.picture(walk, crop=AP_CROP))
    lay["meta"]["z"] = 0
    # (the Lockheed CGI F-35 line that sat under 104-111 is gone: ember found it confusing.) 104-109: Gaza
    # City's ruins from the air, untreated and silent, under Rev. Munther Isaac and the two strikes after him
    ruins = c.seg("ground:ap-drone-gazacity-ruins-2025-10-long#6")
    lay = c.footage(ruins, at=b104 - 0.6, after=B[110] - b104 + 0.6, id="gaza-city-ruins",
                    fade={"in": 1.2, "out": 0.6}, **L.picture(ruins, crop=AP_CROP))
    lay["time"]["in"] = 128.0
    lay["meta"]["z"] = 0
    # 112-117, under his return: B-2 crews loading bombs into the bay (the Jabaliya dig for victims was
    # here; ember: Hyde's comic heads stay off the dead)
    b2 = c.seg("weapons:b2-jdam-load-whiteman#4")
    lay = c.footage(b2, at=b112, after=b118 - b112, opacity=0.45, fade={"in": 0.2, "out": 0.1}, id="b2-bomb-bay",
                    fx=[{"op": "sat", "factor": 0.6}, {"op": "contrast", "factor": 1.2}],
                    **L.picture(b2, crop=(0, 0.1, 1, 1)))   # a "TV" watermark top-left
    lay["time"]["in"] = 140.0
    lay["meta"]["z"] = 0

    # -- layer D (strikes): on the grid, every bar, then every two beats, then every beat --
    plan = [
        (89, 0, "ground:ap-night-strike-gazacity-2019#0", 0, 0.45),
        (91, 0, "ground:ap-night-eid-bombardment-2014#2", 0, 0.45),
        (93, 0, "ground:ap-ansar-tent-strike-fire-2026-03#0", 0, 0.45),
        (95, 0, "ground:ap-night-blasts-from-israel-2025-09#1", 0, 0.4),
        (97, 2, "y2026:ap-deir-balah-night-strike-2026-05-23#0", 0, None),
        (103, 2, "ground:ap-flares-cloudy-night-2025-12-b#0", 0, None),
        # (104-107: no strikes; Rev. Munther Isaac speaks over the ruins)
        (110, 0, "weapons:hellfire-symphony-tads#6", 0, None),
        (111, 0, "y2026:ap-shati-night-strike-2026-05-28#0", 0, 0.35),
    ]
    for k, (n, bb, ref, h, duck) in enumerate(plan):
        crop = TIGHT_CROP if ref.split(":")[0] in ("ground", "y2026") else (0, 0, 1, 1)
        if "ap-deir-balah-night-strike" in ref:
            crop = (0.0, 0.2, 1.0, 0.72)     # "THE ASSOCIATED PRESS" above, the place caption below
        strike(c, ref, c.bar(n, bb), hit=h, duck=duck, k=k + 3, after=1.5, crop=crop, id=f"rise-strike-{n}.{bb}")
    # the IDF's own strike-camera on Gaza on bar 98, under Hibbs's "right in the EYE"
    strike(c, "weapons:idf-haniyeh-office-2008#2", B[98], hit=0, blend="multiply", duck=0.55, k=8, after=1.6,
           id="idf-strikecam-98", extra_fx=[{"op": "gradmap", "palette": "whitehot", "amount": 0.4}])
    # 100-103: punctured. Deir al-Balah, 26 Mar 2026 (Guardian / AP camera): a row of fireballs behind the
    #          tents lands on bar 100's downbeat; people duck and run; held untreated for four bars with its
    #          own sound, the music pulled down under it. Vertical phone video: a tall frame, Guardian
    #          captions avoided (they sit before 2 s and after 7 s)
    GCROP = (0, 0.17, 0.86, 1.0)    # Guardian logo; the windows below end before each burned-in caption
    dab = c.seg("y2026:guardian-deir-balah-tent-camp-strike-2026-03-26#0")
    untreated(c, dab, B[100], hit=0, before=0.3, until=B[100] + 3.3, gain=1.0, id="deir-al-balah-tents",
              **L.panel(dab, 430, 764, [720, 540], crop=GCROP, feather=0.0))
    # then the smoke over the tents holds, still, to the end of bar 103 (its last caption-free frame)
    hold_ = untreated(c, dab, B[100] + 3.3, src=6.6, until=B[104], gain=0.0, id="deir-al-balah-hold",
                      **L.panel(dab, 430, 764, [720, 540], crop=GCROP, feather=0.0))
    hold_["time"] = {"hold": 6.6}
    hold_.pop("audio")
    c.duck(B[100], hold=B[104] - B[100] - 0.6, depth=0.5)
    c.duck_music(B[100], hold=B[104] - B[100] - 0.3, depth=0.3, release=2.0)   # the shot lingers four bars
    # 109: Gaza City, 28 Jul 2026, the strike on the Dar al-Muttaqin mosque, filmed from a roof above a
    #      street of tents (Reuters, via NBC's vertical edit): the fireball lands on bar 109's downbeat,
    #      people in the street below run, the camera drops to the parapet. Untreated, its own sound.
    #      Only the Reuters picture is used: NBC's title band above it and the REUTERS credit are cropped.
    #      (Bureij, 19 May 2026, is shown once, in s2 at bar 184.)
    mos = c.seg("y2026:nbc-dar-al-muttaqin-mosque-strike-2026-07-28#2")
    #      It ends on bar 110, where his still face begins to fade in, so no head is ever over it.
    untreated(c, mos, B[109], hit=0, before=0.5, until=B[110], gain=1.0, id="dar-al-muttaqin-street",
              **L.panel(mos, 680, 556, [720, 540], crop=(0, 0.345, 1, 0.80), feather=0.0))
    c.duck(B[109], hold=1.5, depth=0.4)
    music_dip(c, B[109], B[110], 0.6)
    # 108: white phosphorus over the tents at night, an orange point blooming into falling gold
    wp = strike(c, "weapons:aj-high-powered-bombs-explainer#6", B[108], hit=0, duck=0.3, after=3.6, k=1,
                id="wp-airburst")
    wp["fade"] = {"in": 0.06, "out": 1.5}
    # 112-117: every two beats, then every beat; short, posterized, each a different place
    fast = ["y2026:ap-short-gaza-city-blasts-2026-07-28#0", "y2026:anadolu-khanyounis-plume-2026-09-09#0",
            "ground:ap-impact-smoke-2014#0", "y2026:ap-shati-strike-plume-2026-09-09#0",
            "ground:ap-explosion-near-camera-2009#1", "y2026:aje-zawayda-warehouse-strike-shrapnel-2026-08-23#0",
            "y2026:roya-afp-tent-strike-black-smoke-2026-03-25#0", "y2026:ap-gaza-city-blast-dusk-2026-07-28#0",
            # 116-117: one per two beats, each stuttered on the second beat
            "weapons:idf-castlead-nightvision-2009#2", "weapons:times-radio-idf-bombardment-oct2023#0",
            "weapons:wsj-gaza-highrise-strike-oct2023#0", "weapons:idf-launcher-strike-2009#1"]
    times = [c.bar(n, b) for n in range(112, 116) for b in (0, 2)] + [c.bar(n, b) for n in (116, 117) for b in (0, 2)]
    for k, (t, ref) in enumerate(zip(times, fast)):
        crop = TIGHT_CROP if ref.split(":")[0] in ("ground", "y2026") else (0, 0, 1, 1)
        if t < b116:
            strike(c, ref, t, hit=0, blend="screen", k=k, after=0.9, duck=0.35 if k % 2 == 0 else None,
                   crop=crop, id=f"rise-fast-{k}")
            continue
        seg = c.seg(ref)
        c.duck(t, hold=0.7, depth=0.35)
        if tuple(crop) == (0, 0, 1, 1):
            crop = next((v for kk, v in CLIP_CROP.items() if seg.clip["id"].startswith(kk)), crop)
        lay = c.stutter(seg, at=t, hit=0, n=2, div=1, slice=0.4, after=0.45, fade={"in": 0.04, "out": 0.3},
                        blend="screen", opacity=0.9, fx=hit_fx(k), id=f"rise-fast-{k}", **L.picture(seg, crop=crop))
        lay["meta"]["z"] = 2
        lay["tags"].append("strike")
    # 118, the handoff: everything has collapsed to the centre; one last white flash that dies out
    # over the bar, leaving only Meine for lane B
    last = strike(c, "ground:ap-night-blasts-from-israel-2025-09#0", b118, hit=0, duck=0.35, after=b119 - b118,
                  before=0.06, k=0, crop=NEWS_CROP, id="handoff-flash", z=4)
    last["fade"] = {"in": 0.04, "out": b119 - b118 - 0.1}


# ---------------------------------------------------------------- the heads speak (c.say like=)
W_ = {"hellfire": 12, "missiles": [13, 25, 29, 36, 50, 57], "more": 22, "and": 23, "more2": 24,
      "as": 34, "many": 35, "as2": 37, "we": 38, "can": 39, "get": 40,
      "thou": 46, "shalt": 47, "give": 48, "israel": 49, "thou2": 51, "shalt2": 52, "give2": 53, "israel2": 54,
      "im": 89, "not": 90, "paying": 91, "enough": 92}


def layer(c, id):
    return next(x for x in c.layers if x.get("id") == id)


def sig_at(spec, t):
    """Value of a dense/keys/const scalar signal at t (python side, for choosing heads)."""
    if isinstance(spec, (int, float)):
        return spec
    if "dense" in spec:
        d = spec["dense"]
        i = int(min(max((t - d["t0"]) / d["dt"], 0), len(d["v"]) - 1))
        return d["v"][i]
    if "mul" in spec:
        r = 1.0
        for x in spec["mul"]:
            v = sig_at(x, t)
            r *= v if isinstance(v, (int, float)) else 1.0
        return r
    return 1.0


def nearest(c, prefix, t, skip=()):
    """The head (id starting with prefix, live at t) closest to camera: the largest scale."""
    cands = [x for x in c.layers if x.get("id", "").startswith(prefix) and x["t0"] <= t < x["t1"] - 0.6
             and x["id"] not in skip and "head" in x.get("tags", []) and "say" not in x.get("tags", [])]
    return max(cands, key=lambda x: sig_at(x["scale"], t))


def say_like(c, head, word, at, gain=0.9, bump=None, z=None, **kw):
    """The moving copy `head` says `word` at `at` (comp.say like=): same place, motion and look, the copy
    hidden while it speaks. bump: scale multiplier while speaking, so a small formation head swells out
    of the shape to be read, then shrinks back into it. z: layer order override (5 = over flashes)."""
    lay = c.say(word, at, like=head, gain=gain, id=f"say:{head['id']}@{at:.2f}", **kw)
    if bump is None:
        bump = 2.4 if head["id"].startswith(("form", "orbit", "rform")) else 1.25
    if bump != 1:
        t0, t1 = lay["t0"], lay["t1"]
        lay["scale"] = mul(lay["scale"], keys([t0, 1.0], [t0 + 0.07, bump], [t1 - 0.1, bump], [t1, 1.0], ease="smooth"))
    if z is not None:
        lay["meta"]["z"] = z
    return lay


def speak(c):
    bar = c.bar
    # bar 116: "missiles" on every beat, a different copy each time; 117: "thou shalt give Israel"
    for b, i in enumerate((0, 6, 3, 7)):
        say_like(c, layer(c, f"rise{i}.0"), W_["missiles"][[4, 5, 0, 1][b]], bar(116, b))
    for b, (i, w) in enumerate(zip((1, 2, 0, 6), ("thou2", "shalt2", "give2", "israel2"))):
        say_like(c, layer(c, f"rise{i}.0"), W_[w], bar(117, b))
    # 118: the chorus where they all vanished, inside the handoff flash
    for k, i in enumerate((0, 1, 2, 3, 6, 7)):
        say_like(c, layer(c, f"rise{i}.0"), W_["missiles"][5], bar(118), gain=0.26, mode="tape",
                 stretch=[1.0, 0.88, 1.15, 0.94, 1.25, 0.8][k], scale=0.42 - 0.04 * k)


def build(c):
    n0 = len(c.layers)
    s0_fade(c)
    opening(c)
    supply_chain(c)
    rant2(c)
    build_up(c)
    breakdown(c)
    rise(c)
    speak(c)
    politicians(c)
    preachers(c)
    mine = c.layers[n0:]
    for x in mine:      # footage stays inside Meine's picture area; heads and lower-thirds may cross the bars
        if not {"head", "say", "voice", "text"} & set(x.get("tags", [])):
            x["clip"] = "picture"
    zsort(mine)
    c.layers[n0:] = mine


if __name__ == "__main__":
    section_main("s1_build", SPAN, build)
