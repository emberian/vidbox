"""Snap catalogued hit points to the exact first frame of the impact.

usage: uv run python tools/refine_hits.py projects/meine/footage/{weapons,ground}.json [--dry]

Agents placed hits by eye to about +-1 frame. For each hit, look at the frames within +-2
of it and move it to the frame where the flash starts: the EARLIEST frame whose brightness
rise over the frame before is at least 25% of the biggest rise nearby (the eye syncs to the
first perceptible change, not the peak). Only brightness counts: frame difference also fires
on camera moves, so hits without a real flash (collapses, falls, shoves) keep the agent's
eyeballed time. The agent's frame is the one nearest their time, and it is kept whenever it
is itself a plausible onset; a hit moves only when it plainly isn't (e.g. the second white
frame of a whiteout). The refined time is that frame's
timestamp plus 1 ms, so "latest frame at or before t" lookup lands on it.
The agent's original is kept as "t_agent". Times are on the canonical clock
of render/media.py (seconds from the stream's first frame).
"""
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "render"))
from media import Decoder, decode_range  # noqa: E402


def main():
    paths, dry = [p for p in sys.argv[1:] if not p.startswith("--")], "--dry" in sys.argv
    for path in paths:
        cat = json.loads(Path(path).read_text())
        moved = same = weak = 0
        shifts = []
        for clip in cat["clips"]:
            src = str(ROOT / clip["file"])
            d = Decoder(src)
            fps = d.fps
            d.close()
            for seg in clip["segments"]:
                for h in seg.get("hits", []):
                    t = h.get("t_agent", h["t"])
                    frames = decode_range(src, t - 3.5 / fps, t + 2.5 / fps, size=(96, 54), gray=True)
                    if len(frames) < 4:
                        continue
                    ts = [x[0] for x in frames]
                    fr = np.array([x[1] for x in frames], np.float32)
                    luma = fr.mean(axis=(1, 2))
                    jump = np.r_[0, np.maximum(0, np.diff(luma))] / 255
                    k_agent = int(np.argmin([abs(x - t) for x in ts]))   # the frame the agent meant
                    lo, hi = max(1, k_agent - 2), min(len(fr) - 1, k_agent + 2)
                    if not (lo <= k_agent <= hi):
                        continue
                    peak = jump[lo:hi + 1].max()
                    k_best = next(k for k in range(lo, hi + 1) if jump[k] >= 0.25 * peak)
                    if k_best == k_agent:
                        same += 1
                        continue
                    if jump[k_agent] >= 0.25 * peak:
                        same += 1   # the agent's frame is itself an onset: trust it
                        continue
                    if jump[k_best] < 1.5 * jump[k_agent] or peak < 0.03:   # no real flash here
                        weak += 1
                        continue
                    new_t = round(ts[k_best] + 0.001, 4)
                    shifts.append(k_best - k_agent)
                    h.setdefault("t_agent", t)
                    h["t"] = new_t
                    moved += 1
        hist = {d: shifts.count(d) for d in sorted(set(shifts))}
        print(f"{path}: moved {moved} (frame shifts {hist}), already exact {same}, left alone (no clear onset) {weak}")
        if not dry:
            Path(path).write_text(json.dumps(cat, indent=1) + "\n")


if __name__ == "__main__":
    main()
