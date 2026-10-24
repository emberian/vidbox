"""Record every source media file the project uses, so tools/fetch_sources.py can rebuild media/.

usage: uv run python tools/manifest.py   -> projects/meine/media_manifest.json

media/ is not in git (it is downloaded news footage and music). For each source file this
records where it came from, its duration, sha256, and a brightness fingerprint (mean luma at
5 Hz) so a re-download can be checked, and re-cut when the original was a partial download
(catalog hit times are frame-exact into these specific files).
"""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "render"))
from media import Decoder  # noqa: E402

FP_HZ = 5
KNOWN = {   # sources not described by a catalog
    "media/src/meine.webm": "https://www.youtube.com/watch?v=h7qTI6Njp9g",
    "media/src/missiles_short.mov": "https://www.youtube.com/shorts/_aFaQ-eRuWM",
}


def urls():
    out = dict(KNOWN)
    pdir = ROOT / "projects/meine"
    for cat in (pdir / "footage").glob("*.json"):
        for c in json.loads(cat.read_text()).get("clips", []):
            out[c["file"]] = c.get("source_url")
    pre = pdir / "preachers/preachers.json"
    if pre.exists():
        for c in json.loads(pre.read_text())["clips"]:
            out[c["file"]] = c.get("source_url")
    return out


def fingerprint(path):
    d = Decoder(path)
    vals, next_t = [], 0.0
    for t, f in d.frames(0.0):
        if t + 1e-6 >= next_t:
            vals.append(int(f.to_ndarray(format="gray")[::8, ::8].mean()))
            next_t += 1 / FP_HZ
    d.close()
    return bytes(vals).hex(), (t if vals else 0.0), d.fps


def main():
    src = urls()
    files = sorted({p for p in src if (ROOT / p).exists()})
    missing = sorted(p for p in src if not (ROOT / p).exists())
    entries = []
    for i, rel in enumerate(files):
        p = ROOT / rel
        fp, dur, fps = fingerprint(p)
        entries.append({"file": rel, "url": src[rel], "bytes": p.stat().st_size,
                        "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
                        "duration": round(dur, 3), "fps": round(fps, 3), "luma5hz": fp})
        print(f"\r{i + 1}/{len(files)}", end="", file=sys.stderr)
    out = ROOT / "projects/meine/media_manifest.json"
    out.write_text(json.dumps({"fingerprint_hz": FP_HZ, "files": entries}, indent=1) + "\n")
    print(f"\n{out.relative_to(ROOT)}: {len(entries)} files; {len(missing)} catalogued but absent locally",
          file=sys.stderr)


if __name__ == "__main__":
    main()
