"""Derive a variant of a rendered-ready timeline without touching its composition script.

usage: uv run python tools/variant.py TIMELINE.json --lowfx [LEVEL] [-o OUT.json]

--lowfx LEVEL (default 0.25): every decorative effect's `amount` is scaled by LEVEL (0 removes
it), on layers and in post. Functional ops are left exactly as they are: they decide WHAT is
shown (keys that cut a blast out of black, the hue key, levels), not how it's dressed up.
Writes NAME.lowfx.timeline.json next to the input by default.
"""
import argparse
import json
from pathlib import Path

FUNCTIONAL = {"lumakey", "huekey", "levels", "invert"}


def scale_fx(fx_list, level):
    out = []
    for f in fx_list:
        if f.get("op") in FUNCTIONAL:
            out.append(f)
            continue
        if level <= 0:
            continue
        g = dict(f)
        amt = g.get("amount", 1.0)
        g["amount"] = amt * level if isinstance(amt, (int, float)) else {"mul": [level, amt]}
        out.append(g)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("timeline")
    ap.add_argument("--lowfx", nargs="?", type=float, const=0.25, required=True)
    ap.add_argument("-o", "--out")
    a = ap.parse_args()
    src = Path(a.timeline)
    tl = json.loads(src.read_text())
    n = 0
    for L in tl["layers"]:
        if L.get("fx"):
            before = len(L["fx"])
            L["fx"] = scale_fx(L["fx"], a.lowfx)
            n += before
    tl["post"] = scale_fx(tl.get("post", []), a.lowfx)
    out = Path(a.out) if a.out else src.with_name(src.name.replace(".timeline.json", ".lowfx.timeline.json"))
    out.write_text(json.dumps(tl, indent=1) + "\n")
    print(f"{out}: {n} layer fx scaled to {a.lowfx:g} (functional ops untouched: {', '.join(sorted(FUNCTIONAL))})")


if __name__ == "__main__":
    main()
