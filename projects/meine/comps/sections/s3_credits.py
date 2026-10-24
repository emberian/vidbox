"""After the music (7:53.5): the credits. Who filmed the footage and who published it, who was killed
in it, the journalists killed, and the children of Gaza named by its Ministry of Health. Silent.

credits.mp4 is rendered by tools/credits.py from the clips the timeline actually uses:

    uv run python tools/credits.py data && uv run python tools/credits.py render

so it must be re-rendered whenever the sections change which clips they use. SPAN follows the
rendered file's length.
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "render"))
from comp import section_main  # noqa: E402

SRC = "media/derived/credits.mp4"
MUSIC_END = 473.5


def _duration():
    f = ROOT / SRC
    if f.exists():
        out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(f)],
                             capture_output=True, text=True, check=True).stdout
        return float(out)
    d = ROOT / "projects/meine/credits/credits.durations.json"
    if d.exists():
        return json.loads(d.read_text())["seconds"]
    raise FileNotFoundError(f"{SRC} not rendered yet: uv run python tools/credits.py render")


SPAN = (MUSIC_END, round(MUSIC_END + _duration(), 3))


def build(c):
    """One full-frame, opaque, silent layer from the music's end. credits.mp4 opens on a second of
    black, so the cut from Meine's last frame lands on black, not on text."""
    c.add({"id": "credits", "tags": ["credits"], "src": SRC, "t0": SPAN[0], "t1": SPAN[1],
           "time": {"in": 0.0, "speed": 1.0}, "fit": "native"})


if __name__ == "__main__":
    section_main("s3_credits", SPAN, build)
