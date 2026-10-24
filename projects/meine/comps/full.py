"""The whole piece: the background plus every section, in song order, as one timeline.

uv run python projects/meine/comps/full.py && uv run python render/tl.py projects/meine/comps/out/full.timeline.json --jobs 8

Each section lives in sections/<name>.py with SPAN = (t0, t1) in song seconds and
build(c) adding its layers. A section may reach slightly past its span to cross-fade.
Run a section alone with `uv run python projects/meine/comps/sections/<name>.py`.
"""
import importlib
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parents[2] / "render"), str(HERE)]
from comp import Comp  # noqa: E402

SECTIONS = ["s0_rant", "s1_build", "s2_peak", "s3_credits"]

from sections.s3_credits import SPAN as CREDITS  # noqa: E402

c = Comp("meine", "full", range=(0, CREDITS[1]), sync="missiles_on_beat")   # the song, then the credits
c.add(c.background(t1=473.5))
for name in SECTIONS:
    try:
        mod = importlib.import_module(f"sections.{name}")
    except ModuleNotFoundError:
        print(f"(section {name} not written yet)")
        continue
    mod.build(c)

# Head clouds sample from everyone who has spoken so far (ember: "any time there is any 'head
# cloud', we should be sampling from all the heads that have already spoken thus far in the video.
# Instead of just swarms of Hyde. (but Hyde should still be in there for about 1/3rd of the total
# faces)"). Only SILENT copies change; a copy speaking Hyde's words stays Hyde. Each swapped copy
# silently loops one of that speaker's own lines. Face clips share Hyde's 480x600 framing.
import subprocess  # noqa: E402

HYDE = {"media/derived/face.mp4", "media/derived/face_rant2.mp4", "media/derived/face_missiles_on_beat.mp4"}
SPEAKERS = ("preachers", "israeli_voices")


def _dur(src, _cache={}):
    if src not in _cache:
        out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                              str(HERE.parents[2] / src)], capture_output=True, text=True).stdout
        _cache[src] = float(out or 0)
    return _cache[src]


heard = {}   # person -> (first song time heard, [their clips])
for L in sorted(c.layers, key=lambda L: L["t0"]):
    m = L.get("meta", {})
    if m.get("catalog") in SPEAKERS and "audio" in L:
        person = str(m.get("clip", L["id"])).split("__")[0]
        first, clips = heard.setdefault(person, (L["t0"], []))
        if L["src"] not in clips:
            clips.append(L["src"])
copies = sorted((L for L in c.layers if L["src"] in HYDE and "audio" not in L and L.get("size") == [480, 600]),
                key=lambda L: (L["t0"], L["id"]))
swapped = 0
for i, L in enumerate(copies):
    pool = sorted((p for p, (first, _) in heard.items() if first < L["t0"]), key=lambda p: heard[p][0])
    if i % 3 == 0 or not pool:
        continue   # Hyde keeps about a third of the faces (all of them before anyone else has spoken)
    person = pool[(i - i // 3 - 1) % len(pool)]
    src = heard[person][1][(i // len(pool)) % len(heard[person][1])]
    d = _dur(src)
    if d < 1.0:
        continue
    T = L.get("time", {})
    if "hold" in T:
        L["time"] = {"hold": round(d / 2, 3)}
    else:
        L["time"] = {"in": round((i * 0.37) % (d - 0.2), 3), "speed": 1.0, "loop": [0.05, round(d - 0.05, 3)]}
    L["src"] = src
    L.setdefault("tags", []).append("cloud:" + person)
    swapped += 1
print(f"head clouds: {swapped} of {len(copies)} silent copies now real speakers heard by then; "
      f"{len(copies) - swapped} Hyde")

# The design rule checker holds every rule (render/drc.py): footage scope, nothing over the
# dead, untreated footage once, speakers named, hits on the grid... Its errors stop the build.
import drc  # noqa: E402

tmp = c.save(path=HERE / "out" / "full.candidate.timeline.json")
if drc.check(str(tmp)):
    raise SystemExit("DRC errors: fix them before rendering (full.timeline.json left unchanged)")
tmp.replace(HERE / "out" / "full.timeline.json")

