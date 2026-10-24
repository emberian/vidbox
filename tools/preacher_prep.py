"""Cut the real speakers' lines (projects/meine/preachers/preachers.json) into derived clips.

usage: uv run python tools/preacher_prep.py [KEY ...]      (no keys: every entry in SPECS)

For each spec:
  oval    the line's span cut with ffmpeg (optionally pre-cropped to one pane), face-tracked by
          tools/facecrop.py into a 480x600 head (the same framing as media/derived/face.mp4), with
          its own audio muxed back in
  window  the span cut as-is (scaled to 1280 wide) for a framed window or voice-only use
Audio is compressed gently and loudness-normalised (EBU R128, -14 LUFS, two-pass) so every speaker
sits at one level against the music. Writes media/derived/preachers/<clip>__<label>.mp4 plus a sidecar
<clip>__<label>.json: the cut's span in the source file and its words, re-timed to the clip's
own clock (0 = first frame), so a comp can land a word on the beat.
Re-runnable; skips outputs that exist (delete one to rebuild it).
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CAT = ROOT / "projects/meine/preachers/preachers.json"
OUT = ROOT / "media/derived/preachers"

# Pre-crops keep Haar on the speaker: Johnson's colleague and the House seal, Cruz's hands (his face is
# at ~30 deg yaw), Bachmann's host pane (the broadcast dissolves between two-pane and full frame).
# key: (clip id, label, start s, end s in the raw file, mode, pre-crop x0 y0 x1 y1 or None)
SPECS = {
    # politicians, between rant 1 and rant 2
    "graham": ("graham_mtp_bombs", "hiroshima_bombs", 9.10, 18.62, "oval", None),
    "johnson": ("johnson_bible_bless", "bless_curse", 22.52, 25.95, "oval", (0.25, 0.0, 0.72, 0.72)),
    "cruz": ("cruz_tucker_bless", "taught_bless", 7.18, 11.20, "oval", (0.2, 0.0, 0.7, 0.65)),
    "tucker": ("cruz_tucker_bless", "where_is_that", 26.62, 27.50, "window", None),
    "walberg": ("walberg_nagasaki", "nagasaki_quick", 21.88, 31.05, "window", None),
    "haley_voice": ("haley_hannity_finish", "finish_them", 7.80, 13.10, "window", None),
    "haley_shell": ("haley_finish_them", "shell", 0.0, 6.4, "window", None),
    "ogles": ("ogles_kill_them_all", "kill_them_all", 14.45, 20.45, "window", None),
    # preachers, after rant 2
    "hibbs": ("hibbs_weapons_insulting_god", "insulting_god", 12.36, 16.98, "oval", None),
    "hagee_weapons": ("hagee_cufi2024_weapons", "weapons_of_war", 11.0, 22.80, "window", None),
    "bachmann": ("bachmann_blessed", "bless_israel", 60.80, 64.30, "oval", (0.42, 0.0, 1.0, 0.85)),
    "evans": ("evans_bless_thee", "bless_thee", 9.36, 16.95, "oval", None),
    "huckabee": ("huckabee_bless_side", "blessing_side", 9.72, 17.98, "oval", None),
    "huckabee_all": ("huckabee_tucker_take_it_all", "take_it_all", 30.00, 31.70, "oval", None),
    "vaughn": ("vaughn_wonderful_days", "wonderful_days", 0.20, 11.30, "oval", None),
    "vaughn_glory": ("vaughn_wonderful_days", "glory", 34.50, 37.00, "oval", None),
    "hibbs_eye": ("hibbs_weapons_insulting_god", "poking_god", 36.58, 41.15, "oval", None),
    "hagee_march": ("hagee_march_victory", "victory", 15.40, 22.30, "oval", (0.3, 0.0, 0.85, 0.62)),
    "isaac": ("isaac_bible_weaponized", "weaponized", 42.90, 50.95, "window", None),
}


def run(cmd, **kw):
    return subprocess.run(cmd, check=True, **kw)


def probe_rate(f):
    return subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=r_frame_rate",
                           "-of", "csv=p=0", str(f)], capture_output=True, text=True, check=True).stdout.strip()


# a gentle compressor first lowers speech's crest factor, so a voice can sit well above Meine (a mastered
# track around -11.5 LUFS) without the mix's limiter squashing its peaks
COMP = "acompressor=threshold=-28dB:ratio=4:attack=5:release=150:makeup=6dB"


def loudnorm_args(f):
    """Measure pass of EBU R128 loudnorm (after COMP); returns the af chain for the linear second pass."""
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(f), "-af",
                        f"{COMP},loudnorm=I=-14:TP=-1.0:LRA=7:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True, check=True).stderr
    m = json.loads(r[r.rindex("{"):r.rindex("}") + 1])
    if m["input_i"] in ("-inf", "inf"):      # silent clip (a visual insert): leave it silent
        return "anull"
    return (f"{COMP},loudnorm=I=-14:TP=-1.0:LRA=7:linear=true:"
            f"measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}:"
            f"measured_thresh={m['input_thresh']}:offset={m['target_offset']}")


def prep(key, cat):
    cid, label, a, b, mode, pre = SPECS[key]
    clip = next(c for c in cat["clips"] if c["id"] == cid)
    raw = ROOT / clip["file"]
    out = OUT / f"{cid}__{label}.mp4"
    side = out.with_suffix(".json")
    OUT.mkdir(parents=True, exist_ok=True)
    words = json.loads((ROOT / clip["lines"][0]["words_json"]).read_text())["words"] if clip["lines"] else []
    side.write_text(json.dumps({
        "key": key, "clip": cid, "label": label, "mode": mode, "src": clip["file"], "span": [a, b],
        "person": clip["person"], "role": clip["role"], "venue": clip.get("venue"), "date": clip["date"],
        "publisher": clip.get("publisher"), "source_url": clip.get("source_url"),
        "words": [{"w": w["w"], "start": round(w["start"] - a, 3), "end": round(w["end"] - a, 3)}
                  for w in words if a - 0.05 <= w["start"] and w["end"] <= b + 0.05]}, indent=1) + "\n")
    if out.exists():
        print(f"{out.relative_to(ROOT)} exists")
        return
    rate = probe_rate(raw)
    with tempfile.TemporaryDirectory() as td:
        cut = Path(td) / "cut.mp4"
        vf = []
        if pre:
            x0, y0, x1, y1 = pre
            vf.append(f"crop=iw*{x1 - x0}:ih*{y1 - y0}:iw*{x0}:ih*{y0}")
        if mode == "window":
            vf.append("scale=1280:-2")
        # frame-accurate cut (re-encode), audio as lossless PCM for the loudness passes
        run(["ffmpeg", "-v", "error", "-y", "-ss", f"{a}", "-i", str(raw), "-t", f"{b - a}",
             *(["-vf", ",".join(vf)] if vf else []), "-c:v", "libx264", "-crf", "12", "-pix_fmt", "yuv420p",
             "-c:a", "pcm_s16le", str(cut.with_suffix(".mov"))])
        cut = cut.with_suffix(".mov")
        af = loudnorm_args(cut)
        if mode == "window":
            run(["ffmpeg", "-v", "error", "-y", "-i", str(cut), "-c:v", "libx264", "-crf", "14", "-g", "15",
                 "-pix_fmt", "yuv420p", "-af", af, "-ar", "48000", "-c:a", "aac", "-b:a", "192k",
                 "-movflags", "+faststart", str(out)])
        else:
            fc = subprocess.Popen(["uv", "run", "python", "-I", str(ROOT / "tools/facecrop.py"), str(cut), "480", "600"],
                                  stdout=subprocess.PIPE, cwd=ROOT)
            run(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", "480x600", "-r", rate,
                 "-i", "-", "-i", str(cut), "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-crf", "12", "-g", "15",
                 "-pix_fmt", "yuv420p", "-af", af, "-ar", "48000", "-c:a", "aac", "-b:a", "192k", "-shortest",
                 "-movflags", "+faststart", str(out)], stdin=fc.stdout)
            fc.stdout.close()
            if fc.wait():
                raise SystemExit(f"facecrop failed on {key}")
    print(f"{out.relative_to(ROOT)}  ({mode}, {b - a:.2f} s)")


if __name__ == "__main__":
    cat = json.loads(CAT.read_text())
    for k in sys.argv[1:] or SPECS:
        prep(k, cat)
