"""Retime a talking clip so chosen words land at chosen moments of the music.

usage: uv run python tools/retime.py projects/<p>/sync/<name>.json

Sync sheet:
{
  "source": "media/derived/face.mp4",          clip with audio (video + voice are retimed together)
  "words": "analysis/rant_words.json",         from tools/transcribe.py (project-relative)
  "start": 0,                                  where the clip's time 0 sits in the song (s)
  "out": "media/derived/face_synced.mp4",
  "pins": [
    {"word": "missiles#3", "beat": 24},        3rd "missiles" starts on beat 24
    {"word": 50, "downbeat": 10},              word index 50 starts on downbeat 10
    {"word": "israel#2", "edge": "end", "at": 12.9},   end of the 2nd "israel" at 12.9 s
    {"src": 30.0, "at": 31.0}                  raw clip time -> song time
  ]
}
Targets (at/beat/downbeat) are song times; beat numbers index analysis/beats.json.
Between pins the clip stretches linearly (pitch-preserving rubberband R3 for the voice,
nearest-frame remap for video). Before the first pin and after the last, speed is 1x.
Writes <out> and <sheet>.resolved.json: the time map and every word's new song time.
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
AUDIO_SR = 48000


def resolve_word(words, ref):
    if isinstance(ref, int):
        return words[ref]
    key, _, n = ref.partition("#")
    hits = [w for w in words if w["key"] == key.lower()]
    if not hits:
        sys.exit(f"no word {key!r} in transcript")
    k = int(n or 1)
    if k > len(hits):
        sys.exit(f"only {len(hits)} x {key!r}, asked for #{k}")
    return hits[k - 1]


def main():
    sheet_path = Path(sys.argv[1]).resolve()
    sheet = json.loads(sheet_path.read_text())
    pdir = sheet_path.parent.parent
    words = json.loads((pdir / sheet["words"]).read_text())["words"]
    beats = json.loads((pdir / "analysis/beats.json").read_text())
    src = ROOT / sheet["source"]
    out = ROOT / sheet["out"]
    start = sheet.get("start", 0.0)

    cap = cv2.VideoCapture(str(src))
    src_fps = cap.get(cv2.CAP_PROP_FPS)
    n_src = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    W, H = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    src_dur = n_src / src_fps

    # pins: (source clip time, destination clip time); destination = song time - start
    pins = []
    for p in sheet["pins"]:
        if "word" in p:
            w = resolve_word(words, p["word"])
            s = w["end"] if p.get("edge") == "end" else w["start"]
            label = f"{w['w']}#{w['i']}"
        else:
            s, label = p["src"], f"src {p['src']}"
        if "at" in p:
            song = p["at"]
        elif "beat" in p:
            song = beats["beats"][p["beat"]]
        else:
            song = beats["downbeats"][p["downbeat"]]
        pins.append((s, song - start, label))
    pins.sort()
    for (s0, d0, l0), (s1, d1, l1) in zip(pins, pins[1:]):
        if d1 <= d0:
            sys.exit(f"pins out of order: {l0} -> {d0 + start:.3f}, {l1} -> {d1 + start:.3f}")
    # 1x before the first pin and after the last
    s_first, d_first, _ = pins[0]
    s_last, d_last, _ = pins[-1]
    m_src = [0.0] + [p[0] for p in pins] + [src_dur]
    m_dst = [d_first - s_first] + [p[1] for p in pins] + [d_last + (src_dur - s_last)]
    if m_dst[0] != 0.0:
        # keep clip time 0 at destination >= 0; a pin may pull the head of the clip earlier
        if m_dst[0] < 0:
            sys.exit(f"first pin needs the clip to start {-m_dst[0]:.2f}s before 'start'; move start earlier")
    dst_dur = m_dst[-1]

    print("segment stretch (1.0 = original speed):", file=sys.stderr)
    for i in range(len(m_src) - 1):
        ds, dd = m_src[i + 1] - m_src[i], m_dst[i + 1] - m_dst[i]
        if ds > 1e-6:
            r = dd / ds
            flag = "  <-- strong" if r < 0.7 or r > 1.5 else ""
            print(f"  src {m_src[i]:6.2f}-{m_src[i + 1]:6.2f} -> song {m_dst[i] + start:6.2f}-{m_dst[i + 1] + start:6.2f}"
                  f"  x{r:.2f}{flag}", file=sys.stderr)

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-vn", "-ac", "1", "-ar", str(AUDIO_SR),
                        tmp / "in.wav"], check=True)
        # The stretched audio starts at destination `lead` (padded with silence below), so its
        # map targets are relative to that, not to the clip's destination time 0.
        lead = m_dst[0]
        (tmp / "map.txt").write_text("".join(f"{round(s * AUDIO_SR)} {round((d - lead) * AUDIO_SR)}\n"
                                             for s, d in zip(m_src[1:-1], m_dst[1:-1])))
        subprocess.run(["rubberband", "-q", "-3", "-M", str(tmp / "map.txt"), "-D", f"{dst_dur - lead:.6f}",
                        tmp / "in.wav", tmp / "st.wav"], check=True)

        fps = sheet.get("fps", 25)
        n_out = int(round(dst_dur * fps))
        enc = subprocess.Popen(
            ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(fps),
             "-i", "-", "-i", str(tmp / "st.wav"), "-af", f"adelay={int(lead * 1000)}:all=1",
             "-c:v", "libx264", "-crf", "14", "-g", "15", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
             "-shortest", "-movflags", "+faststart", str(out)],
            stdin=subprocess.PIPE)
        cur_i, frame = -1, None
        for k in range(n_out):
            t_src = float(np.interp(k / fps, m_dst, m_src))
            want = min(n_src - 1, int(round(t_src * src_fps)))
            while cur_i < want:
                ok, f = cap.read()
                if not ok:
                    break
                frame, cur_i = f, cur_i + 1
            enc.stdin.write(frame.tobytes())
        enc.stdin.close()
        enc.wait()

    new_words = [{**w, "start": round(float(np.interp(w["start"], m_src, m_dst)) + start, 3),
                  "end": round(float(np.interp(w["end"], m_src, m_dst)) + start, 3)} for w in words]
    resolved = {"source": sheet["source"], "out": sheet["out"], "start": start,
                "map": {"src": m_src, "song": [d + start for d in m_dst]},
                "pins": [{"label": l, "src": s, "song": d + start} for s, d, l in pins],
                "words": new_words}
    rpath = sheet_path.with_suffix(".resolved.json")
    rpath.write_text(json.dumps(resolved, indent=1) + "\n")
    print(f"wrote {out.relative_to(ROOT)} ({dst_dur:.2f}s) and {rpath.relative_to(ROOT)}", file=sys.stderr)


if __name__ == "__main__":
    main()
