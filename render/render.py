"""Render a project to video at full quality.

usage: uv run python render/render.py PROJECT [-o out.mp4] [--start S] [--duration D] [--preview]

Frames are composited in numpy: ffmpeg decodes each source to raw RGB on a pipe, and the
result is piped into an encoder that also mixes the audio.
"""
import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from bezier import Path as BezierPath  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


class Reader:
    """Raw RGB frames from a video, resampled to the output fps and size."""

    def __init__(self, src, size, fps, start=0.0):
        self.w, self.h = size
        self.proc = subprocess.Popen(
            ["ffmpeg", "-v", "error", "-ss", f"{start:.4f}", "-i", str(src),
             "-vf", f"fps={fps},scale={self.w}:{self.h}:flags=bicubic",
             "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
            stdout=subprocess.PIPE,
        )
        self.nbytes = self.w * self.h * 3

    def read(self):
        buf = self.proc.stdout.read(self.nbytes)
        if len(buf) < self.nbytes:
            return None
        return np.frombuffer(buf, np.uint8).reshape(self.h, self.w, 3)

    def close(self):
        self.proc.stdout.close()
        self.proc.kill()
        self.proc.wait()


def oval_mask(w, h, feather):
    # pixel-center sampling, same formula as the studio preview
    y, x = np.mgrid[0:h, 0:w].astype(np.float32) + 0.5
    r = np.hypot((x - w / 2) / (w / 2), (y - h / 2) / (h / 2))
    return np.clip((1 - r) / feather, 0, 1)


def paste(dst, src, alpha, cx, cy):
    """Alpha-blend src (h,w,3 float) onto dst (float) centered at (cx, cy), clipped to dst."""
    H, W = dst.shape[:2]
    h, w = src.shape[:2]
    x0, y0 = int(round(cx - w / 2)), int(round(cy - h / 2))
    sx0, sy0 = max(0, -x0), max(0, -y0)
    dx0, dy0 = max(0, x0), max(0, y0)
    dx1, dy1 = min(W, x0 + w), min(H, y0 + h)
    if dx1 <= dx0 or dy1 <= dy0:
        return
    s = src[sy0:sy0 + dy1 - dy0, sx0:sx0 + dx1 - dx0]
    a = alpha[sy0:sy0 + dy1 - dy0, sx0:sx0 + dx1 - dx0, None]
    region = dst[dy0:dy1, dx0:dx1]
    region += (s - region) * a


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("-o", "--out")
    ap.add_argument("--start", type=float, default=0.0)
    ap.add_argument("--duration", type=float)
    ap.add_argument("--preview", action="store_true", help="half size, fast encode")
    args = ap.parse_args()

    pdir = ROOT / "projects" / args.project
    proj = json.loads((pdir / "project.json").read_text())
    fps = proj["fps"]
    W, H = proj["size"]
    k = 0.5 if args.preview else 1.0
    OW, OH = int(W * k) // 2 * 2, int(H * k) // 2 * 2
    dur = args.duration or (proj["duration"] - args.start)
    nframes = round(dur * fps)
    out = Path(args.out) if args.out else ROOT / "out" / f"{args.project}{'_preview' if args.preview else ''}.mp4"
    out.parent.mkdir(parents=True, exist_ok=True)

    bgsrc = ROOT / proj["background"]["src"]
    bg = Reader(bgsrc, (OW, OH), fps, args.start)

    layers = []
    for L in proj["layers"]:
        lw, lh = (int(round(v * k)) for v in L["size"])
        pth = BezierPath(json.loads((pdir / L["path"]).read_text())) if (pdir / L["path"]).exists() else None
        if not pth or not pth.anchors:
            print(f"layer {L['id']}: no path yet, centering", file=sys.stderr)
            pth = lambda t: (W / 2, H / 2)  # noqa: E731
        local0 = args.start - L["start"]
        layers.append(dict(
            L=L, path=pth,
            reader=Reader(ROOT / L["src"], (lw, lh), fps, max(0.0, local0)),
            first=round(max(0.0, -local0) * fps),  # output frame where this layer begins
            alpha=oval_mask(lw, lh, L["mask"]["feather"]) * L["opacity"],
            done=False,
        ))

    # audio: background + each layer, delayed to its start, then limited
    ain = ["-ss", f"{args.start:.4f}", "-i", str(bgsrc)]
    chains = [f"[1:a]volume={proj['background']['gain']}[a0]"]
    for j, l in enumerate(layers):
        L = l["L"]
        lstart = max(0.0, args.start - L["start"])
        ain += ["-ss", f"{lstart:.4f}", "-i", str(ROOT / L["src"])]
        delay = int(max(0.0, L["start"] - args.start) * 1000)
        chains.append(f"[{j + 2}:a]adelay={delay}:all=1,volume={L['gain']}[a{j + 1}]")
    n = len(layers) + 1
    amix = (";".join(chains) + ";" + "".join(f"[a{i}]" for i in range(n))
            + f"amix=inputs={n}:normalize=0:duration=first,alimiter=limit=0.95[aout]")

    enc = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-y",
         "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{OW}x{OH}", "-r", str(fps), "-i", "-",
         *ain, "-filter_complex", amix, "-map", "0:v", "-map", "[aout]", "-t", f"{dur:.4f}",
         "-c:v", "libx264", "-crf", "23" if args.preview else "17",
         "-preset", "veryfast" if args.preview else "medium", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(out)],
        stdin=subprocess.PIPE,
    )

    t_wall = time.time()
    for f in range(nframes):
        frame = bg.read()
        if frame is None:
            print(f"background ended at frame {f}", file=sys.stderr)
            break
        acc = frame.astype(np.float32)
        t = args.start + f / fps
        for l in layers:
            if f < l["first"] or l["done"]:
                continue
            img = l["reader"].read()
            if img is None:
                l["done"] = True
                continue
            cx, cy = l["path"](t)
            paste(acc, img.astype(np.float32), l["alpha"], cx * k, cy * k)
        enc.stdin.write(np.clip(acc + 0.5, 0, 255).astype(np.uint8).tobytes())
        if f % 50 == 0:
            el = time.time() - t_wall
            print(f"\r{f}/{nframes}  {f / el if el else 0:.1f} fps", end="", file=sys.stderr)

    enc.stdin.close()
    enc.wait()
    bg.close()
    for l in layers:
        l["reader"].close()
    print(f"\nwrote {out} in {time.time() - t_wall:.1f}s", file=sys.stderr)
    sys.exit(enc.returncode)


if __name__ == "__main__":
    main()
