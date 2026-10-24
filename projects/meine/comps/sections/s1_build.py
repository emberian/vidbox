"""0:38 - 3:45 (bars 20-118): the split through the rise.

He finishes speaking; on the next downbeat his head splits into eight characters (chromatic, noise,
posterized...) that hover where they look, then shrink into small heads tracing 3D formations while
the supply chain grooves underneath; they bounce as the build intensifies and strikes land on the
grid; the breakdown thins to one silent head and one image; the rise stacks 3-4 layers at once.
Bar-by-bar map in s1_build_NOTES.md.
"""
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parents[3] / "render"), str(HERE)]
from comp import add, beat, intensity, keys, mul, rng, section_main  # noqa: E402
import s1_lib as L  # noqa: E402

SPAN = (38.301, 224.967)
ORIGIN = (1150, 640)        # where the s0 preacher ends up (gaze path at 36.8 s: ~(1206, 701))
PICTURE_C = (720, 540)
FORM_C = (720, 520)
SIZES = [0.62, 0.47, 0.40, 0.34, 0.30, 0.27, 0.23, 0.20]
HOMES = [(560, 470), (1010, 380), (300, 330), (1230, 560), (720, 760), (420, 700), (930, 690), (1150, 300)]
AP_CROP = [0.0, 0.16, 1.0, 1.0]    # drops AP's top-right bug (x 0.78-0.87, y 0-0.15)
NEWS_CROP = [0.0, 0.16, 1.0, 0.85]  # ground strikes: AP bug, place labels, lower thirds, network bugs


def hit_fx(k, levels=6):
    return [{"op": "posterize", "levels": levels},
            {"op": "chroma", "px": rng(2, 18, beat(1, "decay", tau=0.18)), "angle": 37 * k}]


# ---------------------------------------------------------------- bars 20-27: the split
def split(c):
    b20, b28 = c.bar(20), c.bar(28)
    t_conv = c.bar(27, 1)
    # the detonation the split comes out of: the "Apache in G Major" false-colour fireball
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
    # the copies: peel off the parent one per beat, fly home in a beat, then go where they look
    for i in range(8):
        t_out, t_home = c.bar(20, i + 1), c.bar(20, i + 2)
        src_in = (i * 4.3 + 2.0) % 34
        hx, hy = HOMES[i]
        s_i = SIZES[i]

        def fn(t, i=i, t_out=t_out, t_home=t_home, src_in=src_in, hx=hx, hy=hy, s_i=s_i):
            gx, gy, gs = L.gaze_offset(t, b20, src_in, k=0.22)
            if t < t_out:              # still inside the parent
                return ORIGIN[0], ORIGIN[1], 1.1
            u = L.smooth((t - t_out) / (t_home - t_out))
            x = ORIGIN[0] + (hx + gx - ORIGIN[0]) * u
            y = ORIGIN[1] + (hy + gy - ORIGIN[1]) * u
            s = 1.1 + (s_i * (0.75 + 0.25 * gs) - 1.1) * u
            v = L.smooth((t - t_conv) / (b28 - t_conv))     # gather into the formation's seed
            return x + (FORM_C[0] - x) * v, y + (FORM_C[1] - y) * v, s + (0.1 - s) * v
        pos, sc = L.dense_track(b20, b28, fn)
        # from bar 24 each copy hops on alternate beats, half of them on the off-beat pair
        hop = [0, rng(0, -26 - 30 * s_i, mul(beat(2, "decay", tau=0.22, offset=(i % 2) / 2),
                                            keys([c.bar(24) - 0.5, 0], [c.bar(24), 1], [t_conv, 1], [b28, 0])))]
        c.add(L.head(f"split{i}", b20, b28, add(pos, hop), mul(sc, rng(0.94, 1.12, beat(1, "decay", tau=0.16))),
                     src_in=src_in, fx=L.character(i), opacity=keys([t_out - 0.01, 0], [t_out, 0.95], ease="hold"),
                     tags=("head", "copy", "split")))
    # the parent: plain, shedding a copy on every beat, gone when the last one leaves
    last = c.bar(20, 8)
    c.add(L.head("parent", b20, last + 0.2, [ORIGIN[0], ORIGIN[1]],
                 mul(keys([b20, 1.15], [last, 0.55], ease="linear"), rng(1.0, 1.18, beat(1, "decay", tau=0.12))),
                 src_in=17.5, fx=[{"op": "chroma", "px": rng(0, 26, beat(1, "decay", tau=0.12)), "angle": 0}],
                 fade={"out": 0.2}, tags=("head", "parent")))


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
               blend="normal", speed=1.0):
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
    lay = {"id": id or f"{seg.clip['id']}#{seg.idx}@{t0:.2f}panel", "tags": [seg.catalog, "panel"] + seg.tags[:2],
           "src": seg.file, "t0": round(t0, 4), "t1": round(t1, 4), "time": {"in": src_in, "speed": speed},
           "opacity": mul(cut_keys(None, on, t0, t1), opacity), "blend": blend,
           "fx": list(fx), "meta": {"catalog": seg.catalog, "clip": seg.clip["id"], "seg": seg.idx, "hits_song": []},
           **L.panel(seg, w, h, pos, crop)}
    c.add(lay)
    return lay


ARCHIVE = [{"op": "sat", "factor": 0.55}, {"op": "contrast", "factor": 1.25}, {"op": "posterize", "levels": 7}]


# ---------------------------------------------------------------- bars 28-43: formations + supply chain
def formations(c):
    t_conv, b28, b32, b36, b40, b44 = c.bar(27, 1), c.bar(28), c.bar(32), c.bar(36), c.bar(40), c.bar(44)
    N = 20
    pulse_env = beat_decay(c, 0.14)
    radius = {"cube": 270, "sphere": 290, "helix": 230, "ring": 400}

    def rad(t):
        if t < b32:
            return radius["cube"]
        if t < b36:
            return radius["sphere"]
        if t < b40:
            return radius["helix"]
        return radius["ring"]

    def ctr(t):
        if t < b40:
            return FORM_C
        u = (t - b40) / (b44 - b40)          # the ring wanders while it spins
        return (720 + 140 * math.sin(2 * math.pi * u), 520 + 50 * math.sin(4 * math.pi * u))

    blocks = [("point", t_conv, ("still", 0)), ("cube", b28, ("step", 0.25)), ("sphere", b32, ("smooth", 2)),
              ("helix", b36, ("smooth", 1)), ("ring", b40, ("beat", 1 / 16)), ("point", c.bar(43, 3), ("still", 0))]
    tracks = L.formation_track(c, N, blocks, b44 + 0.04, ctr, rad, base_scale=0.1, depth=4.0, morph_beats=2,
                               pulse=lambda t: 1 + 0.07 * pulse_env(t))
    for i, (pos, sc) in enumerate(tracks):
        c.add(L.head(f"form{i}", t_conv, b44, pos, sc, src_in=(i * 2.17 + 1) % 34,
                     fx=L.character(i % 14), opacity=0.95, fade={"in": 0.6, "out": 0.1},
                     tags=("head", "formation")))
    # the preacher at the centre of his own globe (sphere and ring), steered by his gaze
    def core(t):
        gx, gy, gs = L.gaze_offset(t, b32, 8.0, k=0.12)
        cx, cy = ctr(t)
        return cx + gx, cy + gy, 0.3 + 0.12 * (gs - 1)
    pos, sc = L.dense_track(b32, b44, core)
    c.add(L.head("form-core", b32, b44, pos, mul(sc, rng(0.95, 1.15, beat(1, "decay", tau=0.15))), src_in=8.0,
                 fx=[{"op": "chroma", "px": rng(2, 20, beat(1, "decay", tau=0.15)), "angle": 0},
                     {"op": "hue", "deg": rng(0, 360, beat(16, "saw"))}],
                 fade={"in": 0.5, "out": 0.3}, tags=("head", "core")))

    # -- supply chain, cut and grooved to the grid --
    # 28-31: JDAM build. A fuze screwed home (Whiteman) / blue-gloved hands seating a sensor (Balad)
    panel_cuts(c, c.seg("weapons:jdam-build-whiteman#2"), 27.0, b28, b32, (0, 1), 460, 330, [270, 540],
               fx=ARCHIVE, id="jdam-fuze")
    panel_cuts(c, c.seg("weapons:jdam-build-balad-2007#0"), 7.0, b28, b32, (2, 3), 460, 330, [1170, 540],
               fx=ARCHIVE, id="jdam-hands")
    panel_cuts(c, c.seg("weapons:jdam-build-whiteman#3"), 36.0, c.bar(30), b32, (2, 3), 460, 330, [270, 540],
               fx=ARCHIVE, id="jdam-noses")
    # 32-35: the MK-84 ship at Ashdod, crane cycle (5 s) to two bars, screened over Meine
    ash = c.seg("weapons:imod-mk84-ashdod-feb2025#1")
    L.groove(c, ash, at=b32, dur=b36 - b32, cycle=5.0, beats=8, src_in=11.0, blend="screen", opacity=0.7,
             fade={"in": 0.3, "out": 0.4}, fx=[{"op": "levels", "black": 0.12, "white": 0.85}],
             id="ashdod", **L.picture(ash))
    # 36-39: the first US munitions C-17 into Nevatim (vertical phone video: a tall window)
    c17 = c.seg("weapons:c17-first-us-munitions-israel-oct2023#0")
    lay = c.footage(c17, at=b36, after=b40 - b36, speed=1.0, id="c17-nevatim",
                    fade={"in": 0.15, "out": 0.3}, fx=[{"op": "contrast", "factor": 1.15}],
                    **L.panel(c17, 340, 600, keys([b36, [1180, 540]], [b40, [1120, 540]]), crop=(0.23, 0, 0.77, 1)))
    lay["time"]["in"] = 6.0
    c17b = c.seg("weapons:c17-first-us-munitions-israel-oct2023#1")
    panel_cuts(c, c17b, 34.0, c.bar(37), b40, (0, 1, 2, 3), 380, 300, [270, 470], fx=ARCHIVE, id="c17-apron")
    # 40-43: Hellfires out of their crates and onto the rail
    panel_cuts(c, c.seg("weapons:mq9-live-hellfire-holloman#1"), 13.4, b40, b44, (0, 1), 430, 330, [270, 560],
               crop=(0.42, 0, 1, 1), id="hellfire-rail-night")
    panel_cuts(c, c.seg("weapons:mq9-hellfire-reload-gulfport#1"), 10.0, b40, b44, (2,), 430, 330, [1170, 480],
               fx=ARCHIVE, id="hellfire-crates")
    panel_cuts(c, c.seg("weapons:mq9-hellfire-reload-gulfport#2"), 12.8, b40, b44, (3,), 430, 330, [1170, 480],
               crop=(0, 0, 1, 0.7), fx=ARCHIVE, id="hellfire-carry")

    # -- strikes on the four-bar downbeats --
    for k, (ref, h, blend, depth) in enumerate([("weapons:oir-mosul-vbied-facility-2017#0", 0, "screen", 0.5),
                                                ("weapons:idf-strikes-jan2014-blackhot#1", 0, "multiply", None),
                                                ("weapons:hellfire-symphony-tads#4", 0, "screen", 0.45)]):
        seg = c.seg(ref)
        at = [b32, b36, b40][k]
        if depth:
            c.duck(at, hold=0.6, depth=depth)
        key = [{"op": "lumakey", "low": 0.55, "high": 0.85}] if k == 0 else []   # white-hot only
        lay = c.footage(seg, at=at, hit=h, before=0.1, after=1.8, blend=blend, opacity=0.9,
                        fade={"in": 0.08, "out": 0.9}, fx=key + hit_fx(k + 1, 6), id=f"form-strike{k}", **L.picture(seg))
        lay["meta"]["z"] = 4 if k == 0 else 2     # the white-hot flash goes over the heads


# ---------------------------------------------------------------- bars 44-71: the build
BOX = (170, 300, 1270, 800)       # head centres stay inside the picture area
BOUNCE_K = {}
BOUNCE_CHARS = [0, 1, 2, 9, 10, 5, 12, 13]


def strike(c, ref, at, hit=0, blend="screen", duck=None, before=0.12, after=1.9, key=None, k=0, opacity=0.9,
           z=2, full=False, crop=(0, 0, 1, 1), extra_fx=(), **kw):
    seg = c.seg(ref)
    if duck:
        c.duck(at, hold=0.7, depth=duck)
    fx = ([{"op": "lumakey", "low": key[0], "high": key[1]}] if key else []) + hit_fx(k) + list(extra_fx)
    frame = {"fit": "cover", "crop": list(crop)} if full else L.picture(seg, crop=crop)
    lay = c.footage(seg, at=at, hit=hit, before=before, after=after, blend=blend, opacity=opacity,
                    fade={"in": 0.06, "out": 0.8}, fx=fx, **frame, **kw)
    lay["meta"]["z"] = z
    lay["tags"].append("strike")
    return lay


def build_up(c):
    b44, b48, b52, b56, b60, b64, b68, b72 = (c.bar(n) for n in (44, 48, 52, 56, 60, 64, 68, 72))
    # -- the eight burst back out of the formation's collapse and bounce, walls on beats --
    def choices(t):
        if t < b48:
            return (4,)
        if t < b56:
            return (2, 4)
        if t < b64:
            return (2, 3)
        if t < c.bar(68):
            return (1, 2)
        return (1, 1, 2)
    present = {i: [(b44, b72)] if i < 4 else [(b44, b56), (b64, b72)] for i in range(8)}
    for i in range(8):
        K = L.bounce_keys(c, b44 + 4 * c.period, b72, BOX, choices, seed=40 + i)
        K = [[b44, list(FORM_C)]] + K[1:]          # first flight starts from the collapse point
        BOUNCE_K[i] = K
        pos = keys(*K)
        size = SIZES[i] * 0.85
        sc = mul(rng(size * 0.8, size * 1.25, intensity(2.0)), rng(0.92, 1.18, beat(1, "decay", tau=0.15)),
                 keys([b44, 0.2], [b44 + c.period, 1.0], ease="smooth"))
        for j, (a, b) in enumerate(present[i]):
            c.add(L.head(f"bounce{i}.{j}", a, b, pos, sc, src_in=(i * 5.1 + 3) % 34, fx=L.character(BOUNCE_CHARS[i]),
                         rot=rng(-14, 14, beat(4, "sine", offset=i / 8)), opacity=0.95,
                         fade={"in": 0.1 if j == 0 else 0.4, "out": 0.4 if b < b72 else 0.05},
                         tags=("head", "bounce")))

    # -- drift mode: one big preacher wandering where his drift path takes him (48-71); from 56 he is
    #    the hub of a spinning ring of small heads --
    drift_in = 4.0

    def drift_fn(t):
        gx, gy, _ = L.gaze_offset(t, b48, drift_in, name="face_self_drift", k=0.55)
        return 720 + gx, 540 + gy * 0.8, 0.5 if t < b56 else 0.36
    dpos, dsc = L.dense_track(b48, b72, drift_fn)
    c.add(L.head("drift", b48, b72, dpos, mul(dsc, rng(0.95, 1.2, beat(1, "decay", tau=0.15))), src_in=drift_in,
                 fx=[{"op": "chroma", "px": rng(3, 28, beat(1, "decay", tau=0.15)), "angle": 0},
                     {"op": "noise", "scale": 90, "octaves": 3, "mode": "overlay", "color": "rgb", "speed": 0.4,
                      "seed": 21, "amount": 0.35}],
                 fade={"in": 0.3, "out": 0.05}, tags=("head", "drift")))

    def hub(t):
        x, y, _ = drift_fn(t)
        return (x, y)
    pulse_env = beat_decay(c, 0.14)
    blocks = [("ring", b56, ("beat", 1 / 16)), ("torus", b60, ("smooth", 1)), ("point", c.bar(63, 3), ("still", 0))]
    tracks = L.formation_track(c, 20, blocks, b64 + 0.04, hub, lambda t: 300, base_scale=0.1, depth=4.0,
                               morph_beats=2, tilt=0.9, wobble_bars=4, pulse=lambda t: 1 + 0.1 * pulse_env(t))
    for i, (pos, sc) in enumerate(tracks):
        c.add(L.head(f"orbit{i}", b56, b64, pos, sc, src_in=(i * 1.9 + 2) % 34, fx=L.character((i + 4) % 14),
                     opacity=0.95, fade={"in": 0.5, "out": 0.1}, tags=("head", "formation")))

    # -- supply chain keeps coming --
    gbu = c.seg("weapons:gbu39-load-mq9-night#0")
    L.groove(c, gbu, at=b44, dur=b48 - b44, cycle=1.0, beats=2, src_in=30.0, blend="screen", opacity=0.75,
             fade={"in": 0.2, "out": 0.4}, fx=[{"op": "levels", "black": 0.1}], id="sdb-night", **L.picture(gbu))
    panel_cuts(c, c.seg("weapons:israel-gbu31-prep-oct2023-reedit#1"), 9.0, b48, b52, (0, 2), 480, 300,
               [300, 360], fx=ARCHIVE, id="gbu31-rows")
    panel_cuts(c, c.seg("weapons:israel-gbu31-prep-oct2023-reedit#2"), 38.0, b48, b52, (1, 3), 480, 300,
               [1140, 720], fx=ARCHIVE, id="gbu31-forklift")
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
    dig = c.seg("ground:aje-civil-defence-body-recovery-2025-12#1")
    L.groove(c, dig, at=b56, dur=b64 - b56, cycle=1.1, beats=2, src_in=38.0, id="dig-civil-defence",
             fade={"in": 0.2, "out": 0.2}, fx=ARCHIVE + [{"op": "duotone", "dark": [0.05, 0.02, 0.0], "light": [1.0, 0.8, 0.55]}],
             **L.panel(dig, 440, 300, [1150, 700]))

    # -- strikes, landing on downbeats; denser as the build goes --
    plan = [
        (44, 0, "weapons:tomahawk-night-philippine-sea-2014#1", 0, "screen", 0.4, None),
        (46, 0, "weapons:hellfire-symphony-tads#7", 0, "screen", None, None),
        (50, 0, "weapons:oir-mosul-vbied-facility-2017#0", 1, "screen", None, (0.5, 0.8)),
        (54, 0, "weapons:centcom-iran-strikes-jul2026#3", 2, "multiply", None, None),
        (56, 0, "ground:reuters-explosions-overnight-2023-10-22#2", 0, "screen", 0.4, None),
        (57, 0, "weapons:centcom-iran-strikes-jul2026#3", 0, "screen", None, None),
        (58, 0, "weapons:gbu39-sdb-promo-nellis#0", 0, "normal", 0.45, None),
        (59, 0, "ground:ap-night-explosion-flares-2025-12#0", 0, "screen", None, None),
        (60, 0, "ground:nbc-night-tower-collapse-2023-10-08#0", 0, "screen", 0.35, None),
        (61, 0, "weapons:hellfire-symphony-tads#2", 0, "screen", None, None),
        (62, 0, "ground:ap-ansar-tent-strike-fire-2026-03#0", 0, "screen", 0.45, None),
        (63, 0, "weapons:oir-mosul-vbied-facility-2017#0", 2, "screen", None, (0.5, 0.8)),
        (65, 0, "weapons:centcom-iran-strikes-jul2026#3", 3, "screen", None, None),
        (65, 2, "ground:reuters-night-fireballs-2023-10-08#0", 0, "screen", None, None),
        (66, 0, "weapons:idf-gaza-strikes-oct13-2023#4", 0, "normal", 0.4, None),
        (67, 0, "weapons:hellfire-symphony-tads#8", 0, "screen", None, None),
        (67, 2, "ground:ap-flares-cloudy-night-2025-12-b#0", 0, "screen", None, None),
        (68, 0, "ground:newscomau-gaza-city-towers-2025-09#7", 0, "screen", 0.35, None),
        (69, 0, "weapons:centcom-iran-strikes-jul2026#3", 4, "screen", None, None),
        (69, 2, "ground:reuters-explosions-overnight-2023-10-22#3", 0, "screen", None, None),
    ]
    for k, (bar, bb, ref, h, blend, duck, key) in enumerate(plan):
        strike(c, ref, c.bar(bar, bb), hit=h, blend=blend, duck=duck, key=key, k=k,
               after=1.6 if bar < 64 else 1.2, crop=NEWS_CROP if ref.startswith("ground:") else (0, 0, 1, 1),
               id=f"build-strike-{bar}.{bb}")
    # 48: the IDF's own fireball on the Gaza shore, retriggered three times on eighths (c.stutter)
    shore = c.seg("weapons:idf-gaza-strikes-oct13-2023#3")
    c.duck(b48, hold=1.4, depth=0.4)
    lay = c.stutter(shore, at=b48, hit=0, n=3, div=0.5, slice=0.14, after=1.6, fade={"in": 0.05, "out": 0.8},
                    fx=hit_fx(48), id="shore-stutter", **L.picture(shore))
    lay["meta"]["z"] = 2
    lay["tags"].append("strike")
    # 64: the whole night sky goes white over Gaza and holds there for two beats (c.freeze)
    sky = c.seg("ground:ap-night-blasts-from-israel-2025-09#0")
    c.duck(b64, hold=1.2, depth=0.35)
    lay = c.freeze(sky, at=b64, hit=0, beats=2, before=0.15, then="continue", after=1.0, blend="screen",
                   fade={"in": 0.05, "out": 0.6}, fx=hit_fx(64), id="sky-freeze", **L.picture(sky, crop=NEWS_CROP))
    lay["meta"]["z"] = 2
    lay["tags"].append("strike")
    # Gaza strikes from the ground, three domes of light landed on consecutive grid points (bars 52-53)
    rafah = c.seg("ground:afp-rafah-night-strikes-flares-2023-12#0")
    c.duck(c.bar(52), hold=3.0, depth=0.45)
    lay = L.land_hits(c, rafah, c.bar(52), div=1, before=0.5, after=1.5, blend="screen", opacity=0.95,
                      fade={"in": 0.2, "out": 0.6}, fx=hit_fx(5), id="rafah-domes", **L.picture(rafah))
    lay["meta"]["z"] = 2

    # -- countdown: the Reaper monitor's 3, 2, 1 on two-beat steps, the strike on bar 72's downbeat --
    cd = c.seg("weapons:mq9-live-hellfire-holloman#7")
    hs = [x["t"] for x in cd.hits]          # 69.6 "3", 70.62 "2", 71.72 "1", 72.62 blast
    tg = [c.bar(70, 2), c.bar(71), c.bar(71, 2), b72]
    lay = L.map_footage(c, cd, [tg[0] - 0.9] + tg + [b72 + 3.0], [hs[0] - 0.9] + hs + [hs[3] + 3.0], hits_song=tg,
                        id="countdown", fade={"in": 0.2, "out": 1.5},
                        fx=[{"op": "contrast", "factor": 1.3}, {"op": "chroma", "px": rng(0, 14, beat(1, "decay", tau=0.15))}],
                        **L.panel(cd, 760, 430, [720, 540]))
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
    b72, b74, b76, b80, b84, b88 = (c.bar(n) for n in (72, 74, 76, 80, 84, 88))
    # the blast lands on 72: every head freezes mid-word and drops out of frame, one per beat
    for i in range(8):
        x0, y0 = L.interp_keys(BOUNCE_K[i], b72)
        t_drop = c.bar(72, i // 2)
        fall = keys([b72, [x0, y0]], [t_drop, [x0, y0]], [t_drop + 0.9, [x0 + (i - 3.5) * 30, 1250]], ease="smooth")
        c.add(L.head(f"fall{i}", b72, t_drop + 0.9, fall, SIZES[i] * 0.85, hold=(i * 5.1 + 3 + 33) % 34,
                     fx=L.character(BOUNCE_CHARS[i]) + [{"op": "sat", "factor": 0.3}], rot=keys([t_drop, 0], [t_drop + 0.9, 40 * (1 if i % 2 else -1)]),
                     opacity=0.95, tags=("head", "fall")))
    # golden dusk, smoke columns over Gaza seen from Israel; the music has gone, so has the colour
    dusk = c.seg("ground:ap-dusk-smoke-from-israel-2023-10#1")
    lay = c.footage(dusk, at=c.bar(72, 2), after=b80 + 1.0 - c.bar(72, 2), id="dusk-smoke", blend="normal",
                    opacity=0.55, fade={"in": 1.5, "out": 2.0}, fx=[{"op": "sat", "factor": 0.7}],
                    **L.picture(dusk, crop=AP_CROP))
    lay["time"]["in"] = 58.0
    lay["meta"]["z"] = 0
    # one image, small, in the middle: cloth cut for shrouds (1.4 s a cut, three beats a cut) -> the
    # shrouds laid out -> the graves in the Nasser courtyard, hands smoothing the sand
    cloth = c.seg("ground:ap-aqsa-shroud-laundry-2023-10#3")
    L.groove(c, cloth, at=b76, dur=b80 - b76 + 0.5, cycle=1.4, beats=3, src_in=80.0, id="shroud-cloth",
             fade={"in": 1.2, "out": 0.5}, fx=[{"op": "sat", "factor": 0.25}, {"op": "contrast", "factor": 1.1}],
             **L.panel(cloth, 560, 320, [720, 560], crop=AP_CROP))
    bags = c.seg("ground:ap-aqsa-body-bags-prayer-2023-12#2")
    lay = c.footage(bags, at=b80, after=b84 - b80 + 0.5, speed=0.6, id="shrouds-laid", fade={"in": 0.5, "out": 0.5},
                    fx=[{"op": "sat", "factor": 0.25}], **L.panel(bags, 560, 320, [720, 560], crop=AP_CROP))
    lay["time"]["in"] = 60.0
    graves = c.seg("ground:nbc-nasser-courtyard-graves-2024-01#2")
    lay = c.footage(graves, at=b84, after=b88 - b84, id="graves", fade={"in": 0.4, "out": 0.05},
                    fx=[{"op": "sat", "factor": rng(0.25, 1.0, keys([b84, 0], [b88, 1]))}],
                    **L.panel(graves, 560, 320, [720, 560], crop=(0, 0, 1, 0.9)))
    lay["time"]["in"] = 21.0
    lay["scale"] = keys([b84, 1.0], [b88, 1.6], ease="smooth")
    # one head left: small, grey, mouthing in slow motion where his drift path takes him
    def lone(t):
        gx, gy, _ = L.gaze_offset(t, b74, 20.0, speed=0.5, name="face_self_drift", k=0.3)
        return 720 + gx, 330 + gy * 0.4, 0.24
    pos, sc = L.dense_track(b74, b84, lone)
    c.add(L.head("lone", b74, b84 + 0.5, pos, sc, src_in=20.0, speed=0.5,
                 fx=[{"op": "sat", "factor": 0.0}, {"op": "contrast", "factor": 1.2}],
                 opacity=0.85, fade={"in": 1.5, "out": 0.5}, tags=("head", "lone")))
    # the riser: the copies come back one more per bar (2, 4, 6, 8), circling the graves faster and
    # faster, gathering in the middle on the last two beats before the drop
    for i in range(8):
        n_in = 84 + i // 2
        t_in = c.bar(n_in, 2 * (i % 2))
        t_gather = c.bar(87, 2)
        ph0 = i / 8

        def orbit(t, ph0=ph0, t_in=t_in, t_gather=t_gather, i=i):
            beats_in = (t - b84) / c.period
            ang = 2 * math.pi * (ph0 + (beats_in / 16) ** 2 * 4)     # accelerating
            r = 420 - 60 * (i % 2)
            x, y = 720 + r * math.cos(ang), 540 + 0.55 * r * math.sin(ang)
            v = L.smooth((t - t_gather) / (b88 - t_gather))
            return x + (720 - x) * v, y + (540 - y) * v, (0.16 + 0.02 * i) * (1 - 0.6 * v)
        pos, sc = L.dense_track(t_in, b88, orbit)
        c.add(L.head(f"riser{i}", t_in, b88, pos, mul(sc, rng(0.9, 1.25, beat(1, "decay", tau=0.12))),
                     src_in=(i * 4.3 + 2.0) % 34, fx=L.character(i), opacity=0.95, fade={"in": 0.25},
                     tags=("head", "riser")))


# ---------------------------------------------------------------- bars 88-118: the rise
def rise(c):
    B = {n: c.bar(n) for n in range(86, 120)}
    b88, b96, b104, b112, b116, b118, b119 = B[88], B[96], B[104], B[112], B[116], B[118], B[119]
    # across the last riser bar he stutters it, one "mi-" a beat, and MISSILES on the drop
    c.say("missiles#1", at=c.bar(87), stutter=4, div=1, gain=1.0, pos=[720, 540], scale=0.75,
          fx=[{"op": "chroma", "px": rng(4, 30, beat(0.5, "decay", tau=0.08)), "angle": 0}],
          mask={"shape": "oval", "feather": 0.3}, id="say-missiles-drop")

    # -- layer A (heads): eight burst out of the drop and bounce, walls on beats, ever faster --
    def choices(t):
        if t < b96:
            return (2, 2, 1)
        if t < b112:
            return (1, 2)
        return (1,)
    counts = {i: [(b88, b118)] if i < 4 or i >= 6 else [(b88, b96), (b104, b118)] for i in range(8)}
    for i in range(8):
        K = L.bounce_keys(c, b88 + c.period, b118, BOX, choices, seed=90 + i)
        K = [[b88, [720, 540]]] + K[1:]
        # the last flight of every head ends in the middle on bar 118's downbeat
        K = [k for k in K if k[0] < c.bar(117, 3)] + [[b118, [720, 540]]]
        size = SIZES[i] * 0.8
        sc = mul(rng(size * 0.85, size * 1.3, intensity(2.0)), rng(0.9, 1.22, beat(1, "decay", tau=0.13)),
                 keys([b88, 0.2], [b88 + c.period, 1.0], [c.bar(117, 3), 1.0], [b118, 0.15], ease="smooth"))
        for j, (a, b) in enumerate(counts[i]):
            c.add(L.head(f"rise{i}.{j}", a, b, keys(*K), sc, src_in=(i * 3.7 + 9) % 34,
                         fx=L.character(BOUNCE_CHARS[(i + 3) % 8]), rot=rng(-18, 18, beat(2, "sine", offset=i / 8)),
                         opacity=0.95, fade={"in": 0.05 if j == 0 else 0.4, "out": 0.4 if b < b118 else 0.04},
                         tags=("head", "bounce", "rise")))

    # -- layer B (small heads): helix, sphere, torus, cube, spun on the grid, collapsing on 118 --
    pulse_env = beat_decay(c, 0.12)
    blocks = [("point", b88, ("still", 0)), ("helix", b88 + 2 * c.period, ("smooth", 1)),
              ("sphere", b96, ("step", 0.25)), ("torus", b104, ("beat", 1 / 16)), ("cube", b112, ("beat", 1 / 8)),
              ("point", c.bar(117, 2), ("still", 0))]
    rad = lambda t: 230 if t < b96 else 300 if t < b104 else 330 if t < b112 else 300
    tracks = L.formation_track(c, 20, blocks, b118 + 0.04, (720, 530), rad, base_scale=0.09, depth=4.0,
                               morph_beats=2, tilt=0.6, wobble_bars=4, pulse=lambda t: 1 + 0.12 * pulse_env(t))
    for i, (pos, sc) in enumerate(tracks):
        c.add(L.head(f"rform{i}", b88, b118, pos, sc, src_in=(i * 1.7 + 5) % 34, fx=L.character((i + 7) % 14),
                     opacity=0.95, fade={"in": 0.3, "out": 0.05}, tags=("head", "formation", "rise")))

    # -- layer C (beds): the machine and the people, alternating --
    tom = c.seg("weapons:centcom-epic-fury-tomahawks#1")
    for k, n in enumerate(range(88, 96, 2)):        # a destroyer's launch on every other downbeat
        lay = c.footage(tom, at=B[n], hit=[0, 1, 2, 4][k], before=0.3, after=B[n + 2] - B[n] - 0.3 + 0.1,
                        opacity=0.5, fade={"in": 0.08, "out": 0.2}, fx=ARCHIVE, id=f"tomahawk-day-{n}",
                        **L.picture(tom))
        lay["meta"]["z"] = 0
        c.duck(B[n], hold=0.5, depth=0.5)
    walk = c.seg("ground:ap-drone-return-north-coast-2025-01#1")
    lay = L.groove(c, walk, at=b96, dur=b104 - b96, cycle=0.55, beats=1, src_in=7.5, blend="multiply",
                   opacity=0.75, fade={"in": 0.3, "out": 0.3}, id="return-north-walk", **L.picture(walk, crop=AP_CROP))
    lay["meta"]["z"] = 0
    f35 = c.seg("weapons:lm-f35-factory-animation#0")
    lay = c.footage(f35, at=b104, after=b112 - b104, speed=1.0, blend="screen", opacity=0.85,
                    fade={"in": 0.2, "out": 0.4}, id="f35-factory",
                    fx=[{"op": "gradmap", "palette": "y2k", "cycle": beat(4, "saw"), "amount": 0.4}],
                    **L.picture(f35))
    lay["time"]["in"] = 20.0
    lay["meta"]["z"] = 0
    dig = c.seg("ground:ap-jabaliya-dig-for-victims-2025-03#1")
    lay = L.groove(c, dig, at=b112, dur=b118 - b112, cycle=1.0, beats=2, src_in=20.0, opacity=0.45,
                   fade={"in": 0.2, "out": 0.1}, id="jabaliya-dig",
                   fx=[{"op": "sat", "factor": 0.6}, {"op": "contrast", "factor": 1.2}], **L.picture(dig, crop=AP_CROP))
    lay["meta"]["z"] = 0

    # -- layer D (strikes): on the grid, every bar, then every two beats, then every beat --
    plan = [
        (89, 0, "ground:reuters-explosions-overnight-2023-10-22#3", 0, 0.45),
        (91, 0, "ground:afp-rafah-night-strikes-flares-2023-12#0", 1, 0.45),
        (93, 0, "ground:ap-ansar-tent-strike-fire-2026-03#0", 0, 0.45),
        (95, 0, "ground:ap-night-blasts-from-israel-2025-09#1", 0, 0.4),
        (97, 2, "ground:reuters-night-fireballs-2023-10-08#0", 0, None),
        (99, 2, "ground:ap-night-explosion-flares-2025-12#0", 0, None),
        (101, 2, "ground:nbc-night-tower-collapse-2023-10-08#0", 0, 0.4),
        (103, 2, "ground:ap-flares-cloudy-night-2025-12-b#0", 0, None),
        (104, 0, "weapons:tomahawk-night-philippine-sea-2014#2", 0, 0.4),
        (105, 0, "weapons:hellfire-symphony-tads#5", 0, None),
        (106, 0, "ground:reuters-explosions-overnight-2023-10-22#2", 0, 0.4),
        (107, 0, "weapons:oir-mosul-vbied-facility-2017#0", 3, None),
        (109, 0, "ground:newscomau-gaza-city-towers-2025-09#7", 0, 0.4),
        (110, 0, "weapons:hellfire-symphony-tads#6", 0, None),
        (111, 0, "ground:ap-night-blasts-from-israel-2025-09#0", 0, 0.35),
        (111, 2, "weapons:idf-gaza-strikes-oct13-2023#2", 0, None),
    ]
    for k, (n, bb, ref, h, duck) in enumerate(plan):
        strike(c, ref, c.bar(n, bb), hit=h, duck=duck, k=k + 3, after=1.5,
               key=(0.5, 0.8) if "mosul" in ref else None,
               crop=NEWS_CROP if ref.startswith("ground:") else (0, 0, 1, 1), id=f"rise-strike-{n}.{bb}")
    # the strike-camera montage: its six hits landed on the grid through bars 96-103
    cent = c.seg("weapons:centcom-iran-strikes-jul2026#3")
    lay = L.land_hits(c, cent, b96, div=2, before=0.3, after=1.2, blend="screen", opacity=0.75,
                      fade={"in": 0.2, "out": 0.6}, fx=[{"op": "gradmap", "palette": "whitehot", "amount": 0.5}] + hit_fx(7),
                      id="centcom-montage", **L.picture(cent, crop=(0, 0.08, 1, 0.92)))
    lay["meta"]["z"] = 2
    for t in lay["meta"]["hits_song"]:
        c.duck(t, hold=0.3, depth=0.55)
    # 108: white phosphorus over the tents at night, an orange point blooming into falling gold
    wp = strike(c, "weapons:aj-high-powered-bombs-explainer#6", B[108], hit=0, duck=0.3, after=3.6, k=1,
                id="wp-airburst")
    wp["fade"] = {"in": 0.06, "out": 1.5}
    # 112-117: every two beats, then every beat; short, posterized, each a different place
    fast = ["ground:afp-rafah-night-strikes-flares-2023-12#0", "weapons:oir-mosul-vbied-facility-2017#0",
            "ground:reuters-explosions-overnight-2023-10-22#0", "weapons:hellfire-symphony-tads#8",
            "ground:ap-night-blasts-from-israel-2025-09#2", "weapons:hellfire-symphony-tads#2",
            "ground:nbc-missile-hits-building-2023-10#0", "weapons:idf-strikes-jan2014-blackhot#1",
            "ground:ap-bank-strike-fireball-2023-10-08#0", "weapons:sdb-feature-deployed-2017#4",
            "ground:reuters-national-bank-strike-2023-10#0", "weapons:centcom-iran-strikes-jul2026#3"]
    hit_of = {"weapons:oir-mosul-vbied-facility-2017#0": 2, "ground:afp-rafah-night-strikes-flares-2023-12#0": 2,
              "ground:ap-night-blasts-from-israel-2025-09#2": 1, "weapons:centcom-iran-strikes-jul2026#3": 5}
    times = [c.bar(n, b) for n in range(112, 116) for b in (0, 2)] + [c.bar(n, b) for n in (116, 117) for b in range(4)]
    for k, t in enumerate(times):
        ref = fast[k % len(fast)]
        blend = "multiply" if "blackhot" in ref else "screen"
        strike(c, ref, t, hit=hit_of.get(ref, 0), blend=blend, k=k, after=0.9 if t < b116 else 0.45,
               duck=0.35 if k % 2 == 0 else None, key=(0.5, 0.8) if "mosul" in ref else None,
               crop=NEWS_CROP if ref.startswith("ground:") else (0, 0, 1, 1), id=f"rise-fast-{k}")
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


def speak(c, paying=False):
    bar = c.bar
    # bars 32 / 36 / 40: the small formation head nearest the camera says "missiles" as the strike lands
    for n, w in zip((32, 36, 40), W_["missiles"][:3]):
        say_like(c, nearest(c, "form", bar(n), skip=("form-core",)), w, bar(n), z=5)   # over the white-hot flash
    # bar 51 call and response across the bouncing copies, bar 52 the whole chorus on the Rafah domes
    for b, (i, w) in enumerate(zip((0, 5, 2, 7), ("thou", "shalt", "give", "israel"))):
        say_like(c, layer(c, f"bounce{i}.0"), W_[w], bar(51, b))
    chorus = [layer(c, f"bounce{i}.0") for i in range(8)] + [layer(c, "drift")]
    for k, h in enumerate(chorus):    # tape-mode stretches: nine preachers at nine pitches, one onset
        say_like(c, h, W_["missiles"][4], bar(52), gain=0.24, stretch=[1.0, 0.9, 1.12, 0.95, 1.2, 0.85, 1.06, 1.3, 0.8][k],
                 mode="tape")
    # bar 61: the drift head, on the TADS strike: "Hellfire ... missiles"
    say_like(c, layer(c, "drift"), W_["hellfire"], bar(61))
    say_like(c, layer(c, "drift"), W_["missiles"][0], bar(61, 2))
    # bar 63: the orbiting ring, "more / and / more" passed round, "MISSILES" on 64 (the white sky)
    used = []
    for b, w in enumerate(("more", "and", "more2")):
        h = nearest(c, "orbit", bar(63, b), skip=used)
        used.append(h["id"])
        say_like(c, h, W_[w], bar(63, b))
    say_like(c, layer(c, "bounce0.0"), W_["missiles"][1], bar(64))
    # bars 102-103: "as many missiles / as we can get" bounced between copies, a word a beat
    seq = [(102, 0, "as"), (102, 1, "many"), (102, 2, "missiles"), (103, 0, "as2"), (103, 1, "we"), (103, 2, "can"),
           (103, 3, "get")]
    heads = [0, 6, 1, 7, 2, 3, 0]
    for (n, b, w), i in zip(seq, heads):
        say_like(c, layer(c, f"rise{i}.0"), W_["missiles"][3] if w == "missiles" else W_[w], bar(n, b))
    # bars 105-111: a small spinning head says it as each odd-bar strike lands
    for k, n in enumerate((105, 107, 109, 111)):
        say_like(c, nearest(c, "rform", bar(n)), W_["missiles"][k % 4], bar(n), gain=0.8)
    # bar 116: "missiles" on every beat, a different copy each time; 117: "thou shalt give Israel"
    for b, i in enumerate((0, 6, 3, 7)):
        say_like(c, layer(c, f"rise{i}.0"), W_["missiles"][[4, 5, 0, 1][b]], bar(116, b))
    for b, (i, w) in enumerate(zip((1, 2, 0, 6), ("thou2", "shalt2", "give2", "israel2"))):
        say_like(c, layer(c, f"rise{i}.0"), W_[w], bar(117, b))
    # 118: the chorus where they all vanished, inside the handoff flash
    for k, i in enumerate((0, 1, 2, 3, 6, 7)):
        say_like(c, layer(c, f"rise{i}.0"), W_["missiles"][5], bar(118), gain=0.26, mode="tape",
                 stretch=[1.0, 0.88, 1.15, 0.94, 1.25, 0.8][k], scale=0.42 - 0.04 * k)
    if paying:
        # variant: in the breakdown the lone grey head mutters "I'm not paying enough", slowed
        lone = layer(c, "lone")
        for b, w in enumerate(("im", "not", "paying")):
            say_like(c, lone, W_[w], bar(78, b), stretch=1.5, gain=1.0, bump=1)
        say_like(c, lone, W_["enough"], bar(79), stretch=1.8, gain=1.0, bump=1)


def build(c, paying=False):
    n0 = len(c.layers)
    split(c)
    formations(c)
    build_up(c)
    breakdown(c)
    rise(c)
    speak(c, paying=paying)
    mine = c.layers[n0:]
    zsort(mine)
    c.layers[n0:] = mine


if __name__ == "__main__":
    if "--paying" in sys.argv:     # variant: section_s1_build.paying.timeline.json
        section_main("s1_build.paying", SPAN, lambda c: build(c, paying=True))
    else:
        section_main("s1_build", SPAN, build)
