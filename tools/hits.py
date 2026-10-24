"""Candidate hit points in a clip: moments of impact that should land on the music.

usage: uv run python tools/hits.py CLIP [--in S] [--out S] [--top N] [--sheet DIR]

Combines three signals, each normalized per clip:
  audio   sharp transients in the clip's own soundtrack (blasts, gunshots, impacts)
  flash   sudden brightness rise over the last ~0.5 s (explosions, muzzle flash, IR bloom)
  motion  frame-difference spike (shockwave, camera jolt, collapse, a body hitting ground)
Prints JSON candidates sorted by time. These are candidates: confirm by looking.
--sheet writes a strip of the 5 native frames around each candidate (it is the middle one).
Candidate times are on the canonical clock (render/media.py): each frame's own timestamp.
"""
import argparse
import json
import subprocess
import sys

import librosa
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "render"))
from media import decode_range  # noqa: E402

SR = 22050
HOP = 256


def probe(clip):
    """fps, has_audio, and where canonical time 0 (the video stream's first frame) sits on the
    container clock that ffmpeg's -ss counts from (format start = 0)."""
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,avg_frame_rate,start_time:format=start_time",
         "-of", "json", clip],
        capture_output=True, text=True, check=True,
    ).stdout
    info = json.loads(out)
    streams = info["streams"]
    v = next(s for s in streams if s["codec_type"] == "video")
    num, den = (int(x) for x in v["avg_frame_rate"].split("/"))
    fmt0 = float(info.get("format", {}).get("start_time", 0) or 0)
    v0 = float(v.get("start_time", fmt0) or fmt0)
    return num / den, any(s["codec_type"] == "audio" for s in streams), v0 - fmt0


def window(t0, t1, offset):
    """ffmpeg input seek for canonical [t0, t1): canonical time t is container time t + offset."""
    return ["-ss", f"{t0 + offset:.6f}"] + (["-t", f"{t1 - t0:.6f}"] if t1 is not None else [])


def norm(x):
    lo, hi = np.percentile(x, 50), np.percentile(x, 99.5)
    return np.clip((x - lo) / (hi - lo + 1e-9), 0, None)


def peaks(x, t, min_gap, thresh):
    out = []
    for i in np.argsort(-x):
        if x[i] < thresh:
            break
        if all(abs(t[i] - t[j]) >= min_gap for j in out):
            out.append(i)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("clip")
    ap.add_argument("--in", dest="t0", type=float, default=0.0)
    ap.add_argument("--out", dest="t1", type=float)
    ap.add_argument("--top", type=int, default=20)
    ap.add_argument("--sheet")
    a = ap.parse_args()
    fps, has_audio, offset = probe(a.clip)

    # visual signals at native frame rate, tiny grayscale frames, each with its own timestamp
    frames = decode_range(a.clip, a.t0, a.t1 if a.t1 is not None else 1e9, size=(96, 54), gray=True)
    tv = np.array([x[0] for x in frames])
    u8 = [x[1] for x in frames]
    del frames
    # per-frame luma and mean |frame difference|, in float32 blocks: one float32 stack of the whole
    # clip (plus np.diff and abs copies of it) was 1.6 GB for a 13-minute source
    luma = np.empty(len(u8), np.float32)
    diff = np.zeros(len(u8))
    for i in range(0, len(u8), 1024):
        o = 1 if i else 0   # blocks after the first start one frame early, for the difference
        blk = np.array(u8[i - o:i + 1024], np.float32)
        luma[i:i + len(blk) - o] = blk[o:].mean(axis=(1, 2))
        d = np.abs(np.diff(blk, axis=0)).mean(axis=(1, 2))
        diff[i + 1 - o:i + 1 - o + len(d)] = d
    k = max(1, int(fps * 0.5))
    base = np.array([np.median(luma[max(0, i - k):i]) if i else luma[0] for i in range(len(luma))])
    flash = norm(np.maximum(0, luma - base))
    motion = norm(diff)

    audio = np.zeros_like(tv)
    if has_audio:
        y = np.frombuffer(subprocess.run(
            # first_pts=0 pads with silence if the audio starts after the seek point, so sample 0
            # is canonical time t0 either way
            ["ffmpeg", "-v", "error", *window(a.t0, a.t1, offset), "-i", a.clip, "-vn", "-ac", "1",
             "-af", "aresample=first_pts=0", "-ar", str(SR), "-f", "f32le", "-"],
            capture_output=True, check=True).stdout, np.float32)
        if len(y) > SR // 2:
            env = librosa.onset.onset_strength(y=y, sr=SR, hop_length=HOP)
            ta = a.t0 + librosa.frames_to_time(np.arange(len(env)), sr=SR, hop_length=HOP)
            # max-pool the audio envelope onto the frame on screen at each envelope time
            # (latest frame with timestamp <= ta, the renderer's rule)
            idx = np.clip(np.searchsorted(tv, ta + 1e-6, side="right") - 1, 0, len(tv) - 1)
            pooled = np.zeros_like(tv)
            np.maximum.at(pooled, idx, env)
            audio = norm(pooled)

    score = 0.45 * audio + 0.30 * flash + 0.25 * motion
    picks = sorted(peaks(score, tv, 0.25, 0.35)[: a.top])
    cands = [{"t": round(float(tv[i]), 3), "score": round(float(score[i]), 2),
              "audio": round(float(audio[i]), 2), "flash": round(float(flash[i]), 2),
              "motion": round(float(motion[i]), 2)} for i in picks]
    print(json.dumps({"clip": a.clip, "fps": round(fps, 3), "has_audio": has_audio, "candidates": cands}, indent=1))

    if a.sheet:
        Path(a.sheet).mkdir(parents=True, exist_ok=True)
        for c in cands:
            # seek half a frame before the frame 2 back: accurate seek keeps frames from there on.
            # (An fps= resample here would drop single-frame flashes from the strip.)
            t = max(0.0, c["t"] - 2.5 / fps) + offset
            subprocess.run(
                ["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.6f}", "-i", a.clip, "-vf",
                 "scale=200:-1,tile=5x1", "-frames:v", "1",
                 f"{a.sheet}/hit_{c['t']:08.3f}.png"], check=True)
        print(f"strips in {a.sheet}", file=sys.stderr)


if __name__ == "__main__":
    main()
