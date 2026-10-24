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

# Head clouds sample from everyone who has spoken so far, Hyde keeping about a third (clouds.py).
from clouds import mix_clouds  # noqa: E402

n_sw, n_cloud, n_silent = mix_clouds(c.layers, HERE.parents[2])
print(f"head clouds: {n_sw} of {n_cloud} cloud copies now real speakers heard by then "
      f"({n_silent - n_cloud} lone Hyde heads untouched)")

# The design rule checker holds every rule (render/drc.py): footage scope, nothing over the
# dead, untreated footage once, speakers named, hits on the grid... Its errors stop the build.
import drc  # noqa: E402

tmp = c.save(path=HERE / "out" / "full.candidate.timeline.json")
if drc.check(str(tmp)):
    raise SystemExit("DRC errors: fix them before rendering (full.timeline.json left unchanged)")
tmp.replace(HERE / "out" / "full.timeline.json")

