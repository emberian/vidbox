"""Word-level transcript: Whisper for the words, forced alignment for the timing.

usage: uv run python tools/transcribe.py MEDIA OUT.json [--model mlx-community/whisper-large-v3-turbo]

Whisper's own word times are good to roughly +-80 ms, and in connected speech there is no
clean energy onset to snap to (words run together; "missile" starts on a soft nasal). So the
Whisper transcript is force-aligned against the audio with torchaudio's MMS aligner, which
places each character's sound to ~20 ms. Words with no alignable letters (e.g. "75%") keep
Whisper's times.
Each word: {i, w, key, start, end, start_whisper, end_whisper, prob, aligned}.
"""
import argparse
import json
import re
import subprocess
import sys

import mlx_whisper
import numpy as np
import torch
import torchaudio

SR = 16000


def decode(src):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", src, "-vn", "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32)


def align(y, words):
    """Set start/end on each word that has letters, via MMS forced alignment."""
    bundle = torchaudio.pipelines.MMS_FA
    model, tokenizer, aligner = bundle.get_model(with_star=False), bundle.get_tokenizer(), bundle.get_aligner()
    alignable = [w for w in words if w["key"].replace("'", "")]
    wav = torch.from_numpy(y.copy()).unsqueeze(0)
    with torch.inference_mode():
        emission, _ = model(wav)
    spans = aligner(emission[0], tokenizer([w["key"] for w in alignable]))
    sec_per_frame = wav.size(1) / emission.size(1) / SR
    for w, sp in zip(alignable, spans):
        w["start"] = round(sp[0].start * sec_per_frame, 3)
        w["end"] = round(sp[-1].end * sec_per_frame, 3)
        w["aligned"] = True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("media")
    ap.add_argument("out")
    ap.add_argument("--model", default="mlx-community/whisper-large-v3-turbo")
    a = ap.parse_args()

    y = decode(a.media)
    res = mlx_whisper.transcribe(y, path_or_hf_repo=a.model, word_timestamps=True, language="en")
    words = []
    for seg in res["segments"]:
        for w in seg.get("words", []):
            text = w["word"].strip()
            words.append({
                "i": len(words), "w": text, "key": re.sub(r"[^a-z']", "", text.lower()).strip("'"),
                "start": round(w["start"], 3), "end": round(w["end"], 3),
                "start_whisper": round(w["start"], 3), "end_whisper": round(w["end"], 3),
                "prob": round(w.get("probability", 0), 3), "aligned": False,
            })
    align(y, words)
    with open(a.out, "w") as f:
        json.dump({"media": a.media, "text": res["text"].strip(), "words": words}, f, indent=1)
    d = [abs(w["start"] - w["start_whisper"]) for w in words if w["aligned"]]
    print(f"{len(words)} words, {len(d)} aligned; |aligned - whisper| start: median {np.median(d) * 1000:.0f} ms, "
          f"max {max(d) * 1000:.0f} ms -> {a.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
