"""3x3 contact sheets of a render, for close visual review.

usage: uv run python tools/contact.py VIDEO OUTDIR [--from S] [--to S] [--step S]

Each sheet holds 9 frames at 480x360, labelled with song time and VIEWER bar number (bars counted
from 1, as ember counts). Sheets are named by their first time, e.g. sheet_0123.4.png.
"""
import argparse
import json
from bisect import bisect_right
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent.parent


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("outdir")
    ap.add_argument("--from", dest="t0", type=float, default=0.0)
    ap.add_argument("--to", dest="t1", type=float)
    ap.add_argument("--step", type=float, default=1.5)
    a = ap.parse_args()
    db = json.loads((ROOT / "projects/meine/analysis/beats.json").read_text())["downbeats"]
    cap = cv2.VideoCapture(a.video)
    fps = cap.get(cv2.CAP_PROP_FPS)
    end = a.t1 if a.t1 is not None else cap.get(cv2.CAP_PROP_FRAME_COUNT) / fps
    out = Path(a.outdir)
    out.mkdir(parents=True, exist_ok=True)
    times = list(np.arange(a.t0, end, a.step))
    for i in range(0, len(times), 9):
        tiles = []
        for t in times[i:i + 9]:
            cap.set(cv2.CAP_PROP_POS_FRAMES, round(t * fps))
            ok, f = cap.read()
            f = cv2.resize(f if ok else np.zeros((360, 480, 3), np.uint8), (480, 360))
            label = f"{int(t // 60)}:{t % 60:04.1f}  bar {max(1, bisect_right(db, t))}"
            cv2.rectangle(f, (0, 0), (190, 20), (0, 0, 0), -1)
            cv2.putText(f, label, (4, 15), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 255), 1)
            tiles.append(f)
        while len(tiles) < 9:
            tiles.append(np.zeros_like(tiles[0]))
        sheet = np.vstack([np.hstack(tiles[r:r + 3]) for r in (0, 3, 6)])
        cv2.imwrite(str(out / f"sheet_{times[i]:06.1f}.png"), sheet)
    print(f"{(len(times) + 8) // 9} sheets of 9 ({a.step}s apart) in {out}")


if __name__ == "__main__":
    main()
