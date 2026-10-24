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

SECTIONS = ["s0_rant", "s1_build", "s2_peak"]

c = Comp("meine", "full", range=(0, 473.5), sync="missiles_on_beat")
c.add(c.background())
for name in SECTIONS:
    try:
        mod = importlib.import_module(f"sections.{name}")
    except ModuleNotFoundError:
        print(f"(section {name} not written yet)")
        continue
    mod.build(c)
c.save()
