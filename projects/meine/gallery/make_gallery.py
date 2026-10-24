"""Looks gallery: every fx_extra op (and a few combinations) on three standard inputs over Meine.

    uv run python projects/meine/gallery/make_gallery.py [--only feedback chromatime ...] [--jobs 3] [--force]

For each look and input (IR strike-cam, daylight Gaza ground, the preacher's head) this writes a
4 s timeline with comp.py, renders it with tl.py at preview size, then builds one contact sheet
per look and out/index.html. Everything lands in projects/meine/gallery/out/ (gitignored).
Clips already rendered are reused unless --force (or their timeline changed).
"""
import argparse
import html
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import cv2
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "render"))
from comp import Comp, beat, rng  # noqa: E402

OUT = HERE / "out"
SONG_BAR = 162          # bar 162 starts ~5:33, the hottest stretch of the main peak
DUR = 4.0

# ---- signals shared by the looks ----
KICK = beat(1, "decay", tau=0.18)        # 1 on every beat, decaying
SNAP = beat(1, "decay", tau=0.07)        # short version, for glitch triggers
BAR_SAW = beat(4, "saw")                 # 0 -> 1 over each bar
TWO_BAR_SINE = beat(8, "sine")

# name -> (fx list, one-line description[, inputs]); inputs default to all three
INPUTS = ("ir", "ground", "head")
HEAD = ("head",)
LOOKS = {
    "feedback": ([{"op": "feedback", "fb": 0.8, "zoom": rng(1.04, 1.12, KICK), "rot": rng(1, 6, KICK),
                   "hue": 25, "tint": [1.0, 0.8, 0.9], "every": 3, "pad": 0.4, "mode": "under"}],
                 "echo tunnel behind the layer: a zoomed, hue-rotated copy stamped every 3 frames "
                 "(mode under, padded so echoes leave the box); zoom and spin kick on the beat"),
    "feedback-smear": ([{"op": "feedback", "fb": 0.82, "zoom": rng(1.01, 1.04, KICK), "rot": rng(0.3, 1.5, KICK),
                         "hue": 6, "tint": [1.0, 0.85, 0.9]}],
                       "continuous zoom feedback (mode max): bright things leave warm, hue-drifting smears"),
    "chromatime": ([{"op": "chromatime", "delay": rng(1, 6, KICK)}],
                   "R now, G and B from 1-6 frames back; the lag swells on every beat"),
    "slitscan": ([{"op": "slitscan", "depth": 18, "axis": "y"}],
                 "each row from a different moment (top = now, bottom = 18 frames ago)"),
    "slitscan-noise": ([{"op": "slitscan", "depth": 20, "axis": "noise", "scale": 260, "speed": 0.25}],
                       "time displacement through an fbm field: regions of the frame lag by different amounts"),
    "flowmosh": ([{"op": "flowmosh", "refresh": rng(0.06, 1.0, beat(2, "pulse", width=0.06)), "gain": 1.3, "px": 16}],
                 "optical-flow datamosh in 16 px macroblocks; a clean 'I-frame' every 2 beats, smear between"),
    "gradmap-thermal": ([{"op": "gradmap", "palette": "ironbow", "beats": 8, "repeat": 0.8}],
                        "ironbow thermal false colour; built-in cycling (beats 8): one ping-pong of the palette "
                        "per 2 bars, stepping forward on every kick"),
    "gradmap-acid": ([{"op": "gradmap", "palette": "acid", "repeat": 2, "cycle": beat(2, "saw")},
                      {"op": "posterize", "levels": 6}],
                     "cyclic acid palette, banded twice, cycling every 2 beats"),
    "mirror": ([{"op": "mirror", "mode": "quad", "shift": rng(-0.08, 0.08, TWO_BAR_SINE)}],
               "quad mirror; the axes sway slowly over two bars"),
    "halftone": ([{"op": "halftone", "period": rng(14, 19, KICK), "mode": "rgb"}],
                 "RGB halftone screens at three angles; dots fatten on the kick"),
    "edgeglow": ([{"op": "edgeglow", "thresh": 0.12, "scale": 3, "px": 8, "base": rng(0.35, 0.7, KICK)}],
                 "neon Sobel outlines with bloom; the picture under them breathes"),
    "glitch": ([{"op": "glitch", "strength": rng(0, 0.8, SNAP), "px": 70, "blocks": 16, "hold": 0.08}],
               "band shifts with RGB split, triggered by the beat"),
    "glitch-blocks": ([{"op": "glitch", "mode": "blocks", "strength": rng(0, 1, SNAP), "px": 90, "scale": 24}],
                      "macroblock corruption on the beat"),
    "radialblur": ([{"op": "radialblur", "strength": rng(0.0, 0.16, KICK)}],
                   "zoom blur punching out from the centre on every beat"),
    "vhs": ([{"op": "vhs", "px": 3, "band": rng(0.15, 0.9, beat(4, "decay", tau=0.5)), "scale": 6, "noise": 0.05}],
            "tape wobble, chroma bleed; the tracking band flares on each downbeat"),
    "bloom": ([{"op": "bloom", "thresh": 0.55, "px": 26, "gain": rng(0.4, 1.1, KICK)}],
              "highlight glow pumping with the kick"),
    "dither": ([{"op": "dither", "levels": 3, "px": 3, "mode": "bayer"}],
               "3-level Bayer dither in chunky 3 px cells"),
    "shock": ([{"op": "shock", "px": 30, "period": 70, "rgb": 0.6}],
              "a chromatic shockwave ring launched on every beat (the default clock: no phase signal needed)"),
    "noise-breathe": ([{"op": "noise", "scale": 70, "mode": "overlay", "color": "rgb", "beats": 2, "amount": 0.6}],
                      "fx.noise, grid-locked: the rgb texture boils a step on every kick and settles (beats 2)"),
    "warp-breathe": ([{"op": "warp", "px": 16, "scale": 140, "beats": 1}],
                     "fx.warp, grid-locked: the field lurches on every kick and eases still before the next"),
    # ---- voronoi: heads only (ember: never on war footage; comp.save enforces it) ----
    "voronoi-crystal": ([{"op": "voronoi", "feature": "cells", "scale": 26, "speed": 0.5, "lines": 0.45}],
                        "crystallize: each Voronoi cell filled flat with the face under it; cells shuffle a step "
                        "per beat", HEAD),
    "voronoi-crackle": ([{"op": "voronoi", "feature": "edge", "scale": 60, "width": 0.06, "mode": "screen",
                          "color": [1.0, 0.25, 0.1], "amount": rng(0.3, 0.9, KICK)}],
                        "F2-F1 crackle lines screened in red over the face, flashing on the beat", HEAD),
    "voronoi-gold-glass": ([{"op": "voronoi", "feature": "cells", "scale": 20, "lines": 0.75, "speed": 0.4},
                            {"op": "gradmap", "palette": "gold", "repeat": 0.78},
                            {"op": "bloom", "thresh": 0.8, "px": 14, "gain": rng(0.1, 0.45, KICK)}],
                           "stained-glass televangelist: fine crystal cells, heavy leading, gold palette, kick bloom",
                           HEAD),
    "voronoi-rainbow": ([{"op": "voronoi", "feature": "random", "scale": 34, "mode": "overlay", "speed": 0.6,
                          "amount": rng(0.35, 0.75, KICK)}],
                        "a random colour per cell overlaid on the face; the mosaic shuffles per beat", HEAD),
    "voronoi-multiply": ([{"op": "voronoi", "feature": "cells", "scale": rng(40, 14, beat(4, "saw")),
                           "lines": 0.5}],
                         "crystals multiply over each bar (cell size 40 -> 14 px), resetting on the downbeat",
                         HEAD),
    "voronoi-soft": ([{"op": "voronoi", "feature": "f1", "scale": 45, "mode": "screen", "color": [0.55, 0.35, 0.9],
                       "beats": 1, "amount": rng(0.4, 0.8, KICK)}],
                     "soft F1 cells screened violet over the face, glowing at the cell walls like a lens of "
                     "bubbles; breathes per beat", HEAD),
    # ---- combinations ----
    "combo-hypno": ([{"op": "feedback", "fb": 0.78, "zoom": rng(1.0, 1.04, KICK), "rot": 0.8, "hue": 6, "pad": 0.3},
                     {"op": "chromatime", "delay": rng(1, 4, KICK)}],
                    "COMBO: feedback tunnel + chromatime. the hypnotic middle"),
    "combo-thermal-judge": ([{"op": "gradmap", "palette": "ironbow", "cycle": rng(0, 0.25, BAR_SAW)},
                             {"op": "edgeglow", "thresh": 0.2, "scale": 4, "px": 6, "base": 0.9,
                              "color": [1.0, 0.85, 0.5], "gain": rng(0.25, 0.7, KICK)},
                             {"op": "bloom", "thresh": 0.8, "px": 20, "gain": 0.4}],
                            "COMBO: thermal false colour + hot edges + bloom (rhymes with the strike-cam)"),
    "combo-mosh-tape": ([{"op": "flowmosh", "refresh": rng(0.08, 1.0, beat(4, "pulse", width=0.03)), "gain": 1.2},
                         {"op": "vhs", "px": 2.5, "band": rng(0.1, 0.7, beat(4, "decay", tau=0.4)), "noise": 0.04}],
                        "COMBO: datamosh smear (I-frame each bar) on a worn tape"),
    "combo-y2k-print": ([{"op": "gradmap", "palette": "y2k", "cycle": beat(4, "saw")},
                         {"op": "halftone", "period": 9, "mode": "rgb", "amount": 0.7},
                         {"op": "glitch", "strength": rng(0, 0.6, SNAP), "px": 50}],
                        "COMBO: chrome y2k palette cycling per bar, half-toned, glitching on the beat"),
    "combo-crystal-dither": ([{"op": "voronoi", "feature": "cells", "scale": 24, "speed": 0.6, "lines": 0.5},
                              {"op": "dither", "levels": 4, "px": 2},
                              {"op": "bloom", "thresh": 0.6, "px": 18, "gain": rng(0.3, 0.9, KICK)}],
                             "COMBO: crystallize + dither + kick bloom: mid-00s Photoshop filter energy", HEAD),
    "combo-judge-shock": ([{"op": "chromatime", "delay": rng(0, 5, KICK), "order": "bgr"},
                           {"op": "shock", "phase": beat(2, "saw"), "px": 22, "period": 60, "rgb": 0.8},
                           {"op": "edgeglow", "color": "source", "thresh": 0.2, "scale": 3, "base": 0.8, "px": 5}],
                          "COMBO: chromatic lag + a shockwave every 2 beats + source-coloured edges"),
}



def look(name):
    v = LOOKS[name]
    return v[0], v[1], (v[2] if len(v) > 2 else INPUTS)


# looks whose bar-long strips (16 frames, one per 16th note) show the grid lock
STRIPS = [("noise-breathe", "head"), ("warp-breathe", "head"), ("shock", "ground"), ("glitch", "ground"),
          ("feedback", "ground"), ("vhs", "ir"), ("gradmap-thermal", "head"), ("voronoi-crystal", "head"),
          ("voronoi-rainbow", "head")]


def inputs(c, t0):
    """The three standard inputs: name -> layer dict (fx added per look)."""
    ir = c.seg("weapons:hellfire-greece-flir#1")            # FLIR cliff: white impact bloom, smoke
    gz = c.seg("ground:ap-drone-khanyounis-2025-01#3")      # daylight orbit of a shredded block
    hit_at = c.snap(t0 + 0.5)
    box = {"fit": "picture", "scale": 0.82, "pos": [720, 540], "mask": {"shape": "rect", "feather": 0.06}}
    L = {}
    c.layers = []
    # crop the pillarbox bars and the title banner off the FLIR clip
    L["ir"] = c.footage(ir, at=hit_at, hit=0, before=hit_at - t0 + 0.1, after=DUR, id="in-ir",
                        **{**box, "crop": [0.125, 0.15, 0.88, 0.87]})
    L["ground"] = c.footage(gz, at=t0 - 0.1, after=DUR + 0.3, id="in-ground", **box)
    L["head"] = {"id": "in-head", "tags": ["head"], "src": "media/derived/face.mp4", "t0": t0 - 0.1,
                 "t1": t0 + DUR + 0.2, "time": {"in": 6.0, "speed": 1.0}, "size": [480, 600],
                 "pos": [720, 520], "scale": rng(0.9, 1.04, KICK), "mask": {"shape": "oval", "feather": 0.28}}
    c.layers = []
    return L


def build(names):
    probe = Comp("meine", "gallery")
    t0 = round(probe.bar(SONG_BAR), 4)
    jobs = []
    for name in names:
        fxl, _, inps = look(name)
        for inp in inps:
            c = Comp("meine", f"gallery_{name}_{inp}", range=(t0, t0 + DUR))
            layer = dict(inputs(c, t0)[inp])
            layer["fx"] = fxl
            c.layers = [c.background(), layer]
            path = OUT / "tl" / f"{name}__{inp}.timeline.json"
            old = path.read_text() if path.exists() else None
            c.save(path)   # comp.save also enforces ember's heads-only rule for voronoi
            jobs.append((name, inp, path, OUT / "clips" / f"{name}__{inp}.mp4", old != path.read_text()))
    return t0, jobs


def render(job, force):
    name, inp, tl, mp4, stale = job
    if mp4.exists() and not stale and not force:
        return f"  reuse {mp4.name}"
    mp4.parent.mkdir(parents=True, exist_ok=True)
    log = OUT / "logs" / f"{name}__{inp}.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    with open(log, "w") as fh:
        r = subprocess.run([sys.executable, str(ROOT / "render/tl.py"), str(tl), "-o", str(mp4)],
                           stdout=fh, stderr=subprocess.STDOUT, cwd=ROOT)
    if r.returncode:
        mp4.unlink(missing_ok=True)   # never leave a half-written clip behind
        return f"  FAILED {name} {inp}: see {log}"
    return f"  rendered {mp4.name}"


def frames_of(mp4, times):
    cap = cv2.VideoCapture(str(mp4))
    out = []
    for t in times:
        cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
        ok, f = cap.read()
        out.append(f if ok else None)
    cap.release()
    return out


def _label(img, text, y, scale=0.5, color=(220, 220, 220)):
    cv2.putText(img, text, (6, y), cv2.FONT_HERSHEY_SIMPLEX, scale, color, 1, cv2.LINE_AA)


def sheet(name, period):
    _, _, inps = look(name)
    times = [b * period + 0.06 for b in (0.5, 2, 3, 5, 7)]   # one off-beat, four just after a beat
    tw, th = 288, 216
    rows = []
    for inp in inps:
        fr = frames_of(OUT / "clips" / f"{name}__{inp}.mp4", times)
        tiles = [cv2.resize(f, (tw, th), interpolation=cv2.INTER_AREA) if f is not None
                 else np.zeros((th, tw, 3), np.uint8) for f in fr]
        lab = np.zeros((th, 70, 3), np.uint8)
        _label(lab, inp, th // 2)
        rows.append(np.hstack([lab] + tiles))
    title = np.zeros((34, rows[0].shape[1], 3), np.uint8)
    _label(title, name, 24, 0.7, (255, 255, 255))
    p = OUT / "sheets" / f"{name}.png"
    p.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(p), np.vstack([title] + rows))
    return p


def strip(name, inp, period):
    """One bar (the clip's second, so state has built), a frame per 16th note, beats marked."""
    times = [(4 + i / 4) * period + 0.02 for i in range(16)]
    fr = frames_of(OUT / "clips" / f"{name}__{inp}.mp4", times)
    tw, th = 180, 135
    tiles = []
    for i, f in enumerate(fr):
        tile = cv2.resize(f, (tw, th), interpolation=cv2.INTER_AREA) if f is not None else np.zeros((th, tw, 3), np.uint8)
        bar = np.zeros((22, tw, 3), np.uint8)
        on = i % 4 == 0
        _label(bar, (f"beat {i // 4 + 1}" if on else ["", "e", "+", "a"][i % 4]), 16, 0.5,
               (80, 220, 255) if on else (150, 150, 150))
        if on:
            bar[:, :3] = (80, 220, 255)
        tiles.append(np.vstack([bar, tile]))
    rows = [np.hstack(tiles[:8]), np.hstack(tiles[8:])]
    title = np.zeros((30, rows[0].shape[1], 3), np.uint8)
    _label(title, f"{name} on {inp}: one bar, a frame per 16th", 21, 0.6, (255, 255, 255))
    p = OUT / "strips" / f"{name}__{inp}.png"
    p.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(p), np.vstack([title] + rows))
    return p


def index(t0):
    css = """:root{color-scheme:dark}body{background:#111;color:#ddd;font:14px/1.4 system-ui,sans-serif;
margin:0 auto;max-width:1500px;padding:16px}h1{font-size:20px}section{border-top:1px solid #333;padding:14px 0}
h2{font-size:17px;margin:0 0 4px;color:#fff}p{margin:0 0 8px;color:#aaa}pre{background:#1b1b1b;padding:8px;
overflow-x:auto;font-size:12px;color:#9cd}.vids{display:grid;grid-template-columns:repeat(3,1fr);gap:8px}
video{width:100%;background:#000}img{max-width:100%;margin-top:6px}nav a{color:#9cd;margin-right:10px}
@media (max-width:700px){.vids{grid-template-columns:1fr}}"""
    secs, nav = [], []
    for name in LOOKS:
        fxl, desc, inps = look(name)
        have = [i for i in inps if (OUT / "clips" / f"{name}__{i}.mp4").exists()]
        if not have:
            continue
        nav.append(f'<a href="#{name}">{name}</a>')
        vids = "".join(f'<figure style="margin:0"><video src="clips/{name}__{i}.mp4" controls loop preload="metadata">'
                       f'</video><figcaption>{i}</figcaption></figure>' for i in have)
        strips = "".join(f'<img src="strips/{n}__{i}.png" loading="lazy" alt="{n} strip">'
                         for n, i in STRIPS if n == name and (OUT / "strips" / f"{n}__{i}.png").exists())
        secs.append(f'<section id="{name}"><h2>{html.escape(name)}</h2><p>{html.escape(desc)}</p>'
                    f'<div class="vids">{vids}</div><img src="sheets/{name}.png" loading="lazy" alt="{name}">'
                    f'{strips}<pre>{html.escape(json.dumps(fxl, indent=1))}</pre></section>')
    page = (f"<!doctype html><meta charset=utf-8><meta name=viewport content='width=device-width'>"
            f"<title>Meine looks</title><style>{css}</style><h1>Meine looks gallery</h1>"
            f"<p>4 s at song {t0:.2f}s (bar {SONG_BAR}), preview size. Every op's internal clock is locked to "
            f"the beat grid; contact sheets sample just after beats, strips show one bar per 16th note. "
            f"Voronoi looks are heads only (ember's rule). Ops are documented in render/FX_EXTRA.md.</p>"
            f"<nav>{' '.join(nav)}</nav>{''.join(secs)}")
    (OUT / "index.html").write_text(page)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--jobs", type=int, default=3)
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    names = a.only or list(LOOKS)
    t0, jobs = build(names)
    with ThreadPoolExecutor(max_workers=max(1, min(a.jobs, 3))) as ex:
        for msg in ex.map(lambda j: render(j, a.force), jobs):
            print(msg, flush=True)
    period = Comp("meine", "gallery").period
    for n in names:
        if all((OUT / "clips" / f"{n}__{i}.mp4").exists() for i in look(n)[2]):
            print("  sheet", sheet(n, period).relative_to(ROOT))
    for n, i in STRIPS:
        if n in names and (OUT / "clips" / f"{n}__{i}.mp4").exists():
            print("  strip", strip(n, i, period).relative_to(ROOT))
    index(t0)
    print("wrote", (OUT / "index.html").relative_to(ROOT))


if __name__ == "__main__":
    main()
