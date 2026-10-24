"""Rebuild media/ from the internet, using projects/meine/media_manifest.json.

usage: uv run python tools/fetch_sources.py [--only SUBSTRING] [--dry]

For each manifest entry whose file is missing (or differs), download its URL with yt-dlp and
check it against the recorded duration and brightness fingerprint. A partial original (some
clips were fetched as sections) is located inside the full download by fingerprint and re-cut
to the recorded length. Re-cut files are good to ~0.1 s; afterwards run
`uv run python tools/refine_hits.py projects/meine/footage/*.json` to re-snap flash onsets.
Then rebuild derived media: `tools/prep.sh`, `tools/retime.py projects/meine/sync/<sheet>.json`
for each sync sheet, and `tools/credits.py data && tools/credits.py render`.

Sources go offline. Anything that can't be fetched is listed at the end, with its URL.
"""
import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from manifest import fingerprint  # noqa: E402


def download(url, outdir, keep_format):
    fmt = [] if keep_format else ["-S", "res:720,ext:mp4:m4a", "--merge-output-format", "mp4"]
    r = subprocess.run(["yt-dlp", "-q", "--no-playlist", *fmt, "-o", str(outdir / "dl.%(ext)s"), url],
                       capture_output=True, text=True)
    got = sorted(outdir.glob("dl.*"))
    return (got[0] if got else None), r.stderr.strip().splitlines()[-1:] if r.returncode else []


def locate(want_hex, have_hex, hz):
    """Offset (s) of the recorded fingerprint inside the downloaded one, and its mean error."""
    a = np.frombuffer(bytes.fromhex(want_hex), np.uint8).astype(np.float32)
    b = np.frombuffer(bytes.fromhex(have_hex), np.uint8).astype(np.float32)
    if len(b) < len(a):
        return None, 1e9
    errs = [np.abs(b[k:k + len(a)] - a).mean() for k in range(len(b) - len(a) + 1)]
    k = int(np.argmin(errs))
    return k / hz, float(errs[k])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only")
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()
    man = json.loads((ROOT / "projects/meine/media_manifest.json").read_text())
    hz = man["fingerprint_hz"]
    done, recut, failed = [], [], []
    for e in man["files"]:
        if a.only and a.only not in e["file"]:
            continue
        dest = ROOT / e["file"]
        if dest.exists() and dest.stat().st_size == e["bytes"]:
            continue
        print(f"fetch {e['file']} <- {e['url']}", file=sys.stderr)
        if a.dry:
            continue
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            got, err = download(e["url"], tmp, keep_format=e["file"].startswith("media/src/"))
            if not got:
                failed.append((e["file"], e["url"], " ".join(err)))
                continue
            fp, dur, _ = fingerprint(got)
            dest.parent.mkdir(parents=True, exist_ok=True)
            if abs(dur - e["duration"]) < 0.15:
                shutil.move(got, dest.with_suffix(got.suffix) if got.suffix != dest.suffix else dest)
                done.append(e["file"])
                continue
            off, err_v = locate(e["luma5hz"], fp, hz)
            if off is None or err_v > 12:
                failed.append((e["file"], e["url"], f"downloaded {dur:.1f}s doesn't contain the recorded "
                                                    f"{e['duration']:.1f}s (fingerprint error {err_v:.1f})"))
                continue
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(got), "-ss", f"{off:.3f}", "-t",
                            f"{e['duration']:.3f}", "-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p",
                            "-c:a", "aac", "-b:a", "192k", str(dest)], check=True)
            recut.append((e["file"], off))
    print(f"\nfetched {len(done)}, re-cut {len(recut)} from longer downloads, failed {len(failed)}", file=sys.stderr)
    for f, off in recut:
        print(f"  re-cut {f} at +{off:.1f}s (run tools/refine_hits.py afterwards)", file=sys.stderr)
    for f, url, why in failed:
        print(f"  FAILED {f}  {url}  {why}", file=sys.stderr)


if __name__ == "__main__":
    main()
