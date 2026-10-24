"""0:00 - the end of the rant (~0:37): the preacher steered by his gaze, a strike's hit frame
landing on every "missiles" (retimed so each is on a beat; Hellfire launch on "Hellfire missiles")."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "render"))
from comp import beat, rng, section_main  # noqa: E402
from bezier import Path as Path_  # noqa: E402
import json  # noqa: E402

ROOT = Path(__file__).resolve().parents[4]

FACE = "media/derived/face_missiles_on_beat.mp4"
GAZE = "paths/face_self_gaze_synced.json"
SPAN = (0.0, 36.84)


def aside(strikes, push=380, glide=0.3):
    """Offset for the head during each strike, so he doesn't cover what the footage shows (ember:
    at the Hellfire launch his face sat on the helicopter). He glides toward the side of the
    frame he's already on, holds, and glides back."""
    path = Path_(json.loads((ROOT / "projects/meine" / GAZE).read_text()))
    keys = [[0.0, [0, 0]]]
    for L in sorted(strikes, key=lambda L: L["t0"]):
        x = path((L["t0"] + L["t1"]) / 2)[0]
        dx = -push if x < 720 else push
        a, b = L["t0"], L["t1"]
        if keys[-1][0] > a - glide:   # overlapping or adjacent windows: stay aside
            keys[-1] = [a, [dx, 0]]
        else:
            keys += [[a - glide, [0, 0]], [a, [dx, 0]]]
        keys += [[b, [dx, 0]], [b + glide, [0, 0]]]
    return {"k": keys, "ease": "smooth"}


def build(c, blend="normal", duck=0.4):
    """blend: how the strike footage meets the background; duck: Meine's opacity under each
    strike (None = no dip). Normal + a 40% duck read clearest in a side-by-side of screen,
    normal, lighten, add and difference; screen suits IR whiteouts on black."""
    rant_end = c.sync["map"]["song"][-1]
    strikes = []
    launches = c.find("weapons", tags=["hellfire", "launch"], kind="launch")
    blasts = c.find("weapons", tags=["IR", "explosion", "strike"], kind="explosion", min_strength=4, overlay_ok=True)
    for k, w in enumerate(c.words("missiles")):
        seg, h = launches[0] if k == 0 and launches else blasts[k]
        if duck is not None:
            c.duck(w["start"], hold=1.0, depth=duck)
        # crop the bottom strip where news captions and lower-thirds sit (and, for Al Jazeera's explainer,
        # its logo top-left and its subtitles)
        crop = [0.16, 0.2, 1.0, 0.68] if seg.clip["id"] == "aj-high-powered-bombs-explainer" else [0, 0, 1, 0.82]
        strikes.append(c.footage(seg, at=w["start"], hit=h, before=0.5, after=1.9, blend=blend, fade={"in": 0.15, "out": 0.6},
                  crop=crop, clip="picture",
                  fx=[{"op": "posterize", "levels": 8},
                      {"op": "chroma", "px": rng(2, 16, beat(1, "decay", tau=0.18)), "angle": 30 * k}],
                  opacity=0.85))
    c.add({"id": "preacher", "tags": ["head"], "src": FACE, "t0": 0, "t1": rant_end, "time": {"in": 0, "speed": 1},
           "size": [480, 600], "pos": {"add": [{"path": GAZE}, aside(strikes)]}, "scale": {"pathscale": GAZE},
           "mask": {"shape": "oval", "feather": 0.28}, "opacity": 0.75, "audio": {"gain": 1.0}})


if __name__ == "__main__":
    section_main("s0_rant", SPAN, build)
