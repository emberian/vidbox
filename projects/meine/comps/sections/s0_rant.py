"""0:00 - the end of the rant (~0:37): the preacher steered by his gaze, a strike's hit frame
landing on every "missiles" (retimed so each is on a beat; Hellfire launch on "Hellfire missiles")."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "render"))
from comp import beat, rng, section_main  # noqa: E402

FACE = "media/derived/face_missiles_on_beat.mp4"
GAZE = "paths/face_self_gaze_synced.json"
SPAN = (0.0, 36.84)


def build(c):
    rant_end = c.sync["map"]["song"][-1]
    launches = c.find("weapons", tags=["hellfire", "launch"], kind="launch")
    blasts = c.find("weapons", tags=["IR", "explosion", "strike"], kind="explosion", min_strength=4, overlay_ok=True)
    for k, w in enumerate(c.words("missiles")):
        seg, h = launches[0] if k == 0 and launches else blasts[k]
        c.footage(seg, at=w["start"], hit=h, before=0.5, after=1.9, blend="screen", fade={"in": 0.15, "out": 0.6},
                  fx=[{"op": "posterize", "levels": 5},
                      {"op": "chroma", "px": rng(2, 16, beat(1, "decay", tau=0.18)), "angle": 30 * k}],
                  opacity=0.9)
    c.add({"id": "preacher", "tags": ["head"], "src": FACE, "t0": 0, "t1": rant_end, "time": {"in": 0, "speed": 1},
           "size": [480, 600], "pos": {"path": GAZE}, "scale": {"pathscale": GAZE},
           "mask": {"shape": "oval", "feather": 0.28}, "opacity": 0.75, "audio": {"gain": 1.0}})


if __name__ == "__main__":
    section_main("s0_rant", SPAN, build)
