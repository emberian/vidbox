"""First composition: the rant with strikes on every "missiles", then the split into 8 heads.

uv run python projects/meine/comps/split_demo.py && uv run python render/tl.py projects/meine/comps/out/split_demo.timeline.json --jobs 6
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "render"))
from comp import Comp, beat, bounce, formation, intensity, keys, mul, rng  # noqa: E402

c = Comp("meine", "split_demo", range=(0, 75), sync="missiles_on_beat", seed=3)
c.add(c.background())

FACE = "media/derived/face_missiles_on_beat.mp4"
GAZE = "paths/face_self_gaze_synced.json"
rant_end = c.sync["map"]["song"][-1]

# --- strikes under the preacher: each "missiles" lands a hit frame on the word (on the beat) ---
launches = [s for s in c.find("weapons", tags=["hellfire", "launch"], kind="launch")]
blasts = c.find("weapons", tags=["IR", "explosion", "strike"], kind="explosion", min_strength=4, overlay_ok=True)
for k, w in enumerate(c.words("missiles")):
    seg, h = launches[0] if k == 0 and launches else blasts[k]
    c.footage(seg, at=w["start"], hit=h, before=0.5, after=1.9, blend="screen", fade={"in": 0.15, "out": 0.6},
              fx=[{"op": "posterize", "levels": 5},
                  {"op": "chroma", "px": rng(2, 16, beat(1, "decay", tau=0.18)), "angle": 30 * k}],
              opacity=0.9)

# --- the preacher himself ---
c.add({"id": "preacher", "tags": ["head"], "src": FACE, "t0": 0, "t1": rant_end, "time": {"in": 0, "speed": 1},
       "size": [480, 600], "pos": {"path": GAZE}, "scale": {"pathscale": GAZE},
       "mask": {"shape": "oval", "feather": 0.28}, "opacity": 0.75, "audio": {"gain": 1.0}})

# --- the split: 8 copies, cube formation, then pong ---
split = c.snap(rant_end, 4)
if split < rant_end:
    split = c.bar(c.bar_of(rant_end) + 1)
form_end = c.bar(c.bar_of(split) + 8)
pong_end = c.range[1]
form = formation(c, "cube", 8, split, form_end, center=(720, 520), radius=240, spin_bars=2, base_scale=0.34)

# Gaza strikes on every other downbeat underneath the heads (bright parts keyed in)
gz = c.find("ground", tags=["strike", "explosion", "night", "flash"], kind="any", min_strength=3, overlay_ok=True)
for j, b in enumerate(range(c.bar_of(split), c.bar_of(pong_end), 2)):
    seg, h = gz[j % len(gz)]
    c.footage(seg, at=c.bar(b), hit=h, before=0.8, after=2.6, fit="picture", blend="screen",
              fade={"in": 0.3, "out": 0.8}, opacity=rng(0.5, 0.95, intensity()),
              fx=[{"op": "lumakey", "low": 0.15, "high": 0.55},
                  {"op": "noise", "scale": 260, "mode": "overlay", "speed": 0.5, "seed": j, "amount": 0.5}])

for i in range(8):
    hue0 = i * 45
    common = {
        "tags": ["head", "copy"], "src": FACE, "size": [480, 600], "mask": {"shape": "oval", "feather": 0.3},
        "time": {"in": (i * 4.3) % 30, "speed": 1, "loop": [0.5, 34.5]},   # each mouths a different stretch
        "fx": [{"op": "hue", "deg": rng(hue0, hue0 + 120, beat(2, "sine"))},
               {"op": "posterize", "levels": 3 + i % 4},
               {"op": "noise", "scale": 40 + 12 * i, "mode": "overlay", "color": "rgb", "speed": 0.8,
                "seed": i, "amount": rng(0.2, 0.7, beat(1, "decay", tau=0.2))},
               {"op": "chroma", "px": rng(0, 18, beat(1, "decay", tau=0.12)), "angle": i * 40}],
    }
    pos, sc = form[i]
    c.add({**common, "id": f"copy{i}-cube", "t0": split, "t1": form_end, "pos": pos,
           "scale": mul(sc, rng(0.9, 1.2, beat(1, "decay", tau=0.15))), "opacity": 0.9,
           "fade": {"in": 0.4}})
    c.add({**common, "id": f"copy{i}-pong", "t0": form_end, "t1": pong_end,
           "pos": bounce(c, form_end, pong_end, (130, 260, 1310, 820), seed=i),
           "scale": mul(0.22 + 0.05 * (i % 4), rng(0.9, 1.25, beat(1, "decay", tau=0.15))), "opacity": 0.9,
           "rot": rng(-12, 12, beat(4, "sine", offset=i / 8))})

c.post = [{"op": "noise", "scale": 3, "octaves": 1, "speed": 12, "mode": "overlay", "amount": 0.03}]   # grain: keep it subtle
c.save()
