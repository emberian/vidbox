"""Candidate hit points in a clip: moments of impact that should land on the music.

usage: uv run python tools/hits.py CLIP [--in S] [--out S] [--top N] [--sheet DIR]

Combines three signals, each normalized per clip:
  audio   sharp transients in the clip's own soundtrack (blasts, gunshots, impacts)
  flash   sudden brightness rise over the last ~0.5 s (explosions, muzzle flash, IR bloom)
  motion  frame-difference spike (shockwave, camera jolt, collapse, a body hitting ground)
Prints JSON candidates sorted by time. These are candidates: confirm by looking.
--sheet writes a 5-frame strip around each candidate (t-0.16 .. t+0.16) for checking.
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
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,avg_frame_rate", "-of", "json", clip],
        capture_output=True, text=True, check=True,
    ).stdout
    streams = json.loads(out)["streams"]
    v = next(s for s in streams if s["codec_type"] == "video")
    num, den = (int(x) for x in v["avg_frame_rate"].split("/"))
    return num / den, any(s["codec_type"] == "audio" for s in streams)


def window(t0, t1):
    return (["-ss", f"{t0}"] if t0 else []) + (["-t", f"{t1 - t0}"] if t1 else [])


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
    fps, has_audio = probe(a.clip)

    # visual signals at native frame rate, tiny grayscale frames, each with its own timestamp
    frames = decode_range(a.clip, a.t0, a.t1 if a.t1 is not None else 1e9, size=(96, 54), gray=True)
    tv = np.array([x[0] for x in frames])
    fr = np.array([x[1] for x in frames], np.float32)
    luma = fr.mean(axis=(1, 2))
    k = max(1, int(fps * 0.5))
    base = np.array([np.median(luma[max(0, i - k):i]) if i else luma[0] for i in range(len(luma))])
    flash = norm(np.maximum(0, luma - base))
    diff = np.r_[0, np.abs(np.diff(fr, axis=0)).mean(axis=(1, 2))]
    motion = norm(diff)

    audio = np.zeros_like(tv)
    if has_audio:
        y = np.frombuffer(subprocess.run(
            ["ffmpeg", "-v", "error", *window(a.t0, a.t1), "-i", a.clip, "-vn", "-ac", "1",
             "-ar", str(SR), "-f", "f32le", "-"], capture_output=True, check=True).stdout, np.float32)
        if len(y) > SR // 2:
            env = librosa.onset.onset_strength(y=y, sr=SR, hop_length=HOP)
            ta = a.t0 + librosa.frames_to_time(np.arange(len(env)), sr=SR, hop_length=HOP)
            # max-pool the audio envelope onto video frame times
            idx = np.clip(np.searchsorted(tv, ta), 0, len(tv) - 1)
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
            t = max(0.0, c["t"] - 0.16)
            subprocess.run(
                ["ffmpeg", "-v", "error", "-y", "-ss", f"{t}", "-i", a.clip, "-vf",
                 f"fps=12.5,scale=200:-1,tile=5x1", "-frames:v", "1",
                 f"{a.sheet}/hit_{c['t']:08.3f}.png"], check=True)
        print(f"strips in {a.sheet}", file=sys.stderr)


if __name__ == "__main__":
    main()
