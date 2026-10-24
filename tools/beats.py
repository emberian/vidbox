"""Beat map of a track: tempo, beats, downbeats, onsets with strengths, and an intensity curve.

usage: uv run python tools/beats.py AUDIO_OR_VIDEO OUT.json

Everything downstream that should land "on the music" (head bounces, footage hit points)
syncs to this file. Times are seconds from the start of the source.
"""
import json
import subprocess
import sys

import librosa
import numpy as np

SR = 22050
HOP = 256


def decode(src):
    raw = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", src, "-vn", "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
        capture_output=True, check=True,
    ).stdout
    return np.frombuffer(raw, np.float32)


def main():
    src, out = sys.argv[1], sys.argv[2]
    y = decode(src)
    harm, perc = librosa.effects.hpss(y)

    env = librosa.onset.onset_strength(y=perc, sr=SR, hop_length=HOP)
    tempo, beat_frames = librosa.beat.beat_track(onset_envelope=env, sr=SR, hop_length=HOP)
    beats = librosa.frames_to_time(beat_frames, sr=SR, hop_length=HOP)

    # Downbeat phase: of the 4 possible bar phases, the one whose beats carry the most
    # low-frequency (kick) onset energy.
    low = librosa.onset.onset_strength(y=perc, sr=SR, hop_length=HOP, fmax=200, n_mels=32)
    low_at = low[np.minimum(beat_frames, len(low) - 1)]
    phase = int(np.argmax([low_at[p::4].mean() for p in range(4)]))
    downbeats = beats[phase::4]

    on_frames = librosa.onset.onset_detect(onset_envelope=env, sr=SR, hop_length=HOP, units="frames")
    on_str = env[on_frames] / env.max()
    onsets = librosa.frames_to_time(on_frames, sr=SR, hop_length=HOP)

    # Intensity: percussive RMS + high-band energy, 0.5 s bins, normalized to 0..1.
    dt = 0.5
    n = int(len(y) / SR / dt)
    rms = librosa.feature.rms(y=perc, hop_length=HOP)[0]
    S = np.abs(librosa.stft(y, hop_length=HOP))
    hi = S[librosa.fft_frequencies(sr=SR) > 2000].mean(axis=0)
    ft = librosa.frames_to_time(np.arange(len(rms)), sr=SR, hop_length=HOP)
    bins = np.minimum((ft / dt).astype(int), n - 1)

    def binned(x):
        v = np.bincount(bins, weights=x[: len(bins)], minlength=n) / np.maximum(np.bincount(bins, minlength=n), 1)
        v = 20 * np.log10(v + 1e-9)
        lo_, hi_ = np.percentile(v, 5), np.percentile(v, 99)
        return np.clip((v - lo_) / (hi_ - lo_), 0, 1)

    intensity = 0.5 * binned(rms) + 0.5 * binned(hi)

    data = {
        "src": src,
        "tempo": round(float(np.atleast_1d(tempo)[0]), 2),
        "beats": [round(float(t), 3) for t in beats],
        "downbeats": [round(float(t), 3) for t in downbeats],
        "onsets": [[round(float(t), 3), round(float(s), 3)] for t, s in zip(onsets, on_str)],
        "intensity": {"dt": dt, "values": [round(float(v), 3) for v in intensity]},
    }
    with open(out, "w") as f:
        json.dump(data, f)
    print(f"tempo {data['tempo']} bpm, {len(beats)} beats, {len(downbeats)} downbeats "
          f"(phase {phase}), {len(onsets)} onsets -> {out}", file=sys.stderr)


if __name__ == "__main__":
    main()
