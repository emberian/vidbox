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

# Untreated footage (normal blend, no fx, own sound) is testimony: each clip appears ONCE in the
# whole piece. Sections are written separately, so the check lives here, where they meet.
seen = {}
for L in c.layers:
    m = L.get("meta", {})
    if m.get("catalog") and not L.get("fx") and L.get("blend", "normal") == "normal" and "audio" in L:
        seen.setdefault(f"{m['catalog']}:{m['clip']}", set()).add(round(L["t0"]) // 60)
dups = {k: v for k, v in seen.items() if len(v) > 1}

# Nothing is drawn over an untreated window except the real speakers, their lower-thirds and the
# Meine background: ember caught a strike layer fading in over the MEE remains at bar 179.
untreated = [L for L in c.layers if L.get("meta", {}).get("catalog") in c.cat and not L.get("fx")
             and L.get("blend", "normal") == "normal" and "audio" in L]
over = []
for U in untreated:
    for L in c.layers:
        m = L.get("meta", {})
        if L is U or L in untreated or L.get("id") == "meine" or m.get("catalog") == "preachers" or "text" in L.get("tags", []):
            continue
        if m.get("catalog") in c.cat and L["t0"] < U["t1"] - 0.02 and L["t1"] > U["t0"] + 0.02 \
                and c.layers.index(L) > c.layers.index(U):
            over.append(f"{L['id']} over {U['id']} ({max(L['t0'], U['t0']):.2f}-{min(L['t1'], U['t1']):.2f})")
if over:
    raise SystemExit("footage drawn over untreated footage of the dead:\n  " + "\n  ".join(over))
if dups:
    raise SystemExit("untreated footage used in more than one place (each is shown once): "
                     + "; ".join(f"{k} around minute(s) {sorted(v)}" for k, v in dups.items()))
c.save()
