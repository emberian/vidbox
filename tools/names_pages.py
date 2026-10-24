"""Render pages of the names of the dead (the credits' full list) as stills, for use in the film.

usage: uv run python tools/names_pages.py FIRST COUNT   -> media/derived/names/page_NNNN.png

Same pages as credits_full.mp4's "all" section (tools/credits.py: every person named by Gaza's
Ministry of Health, Arabic and English, with age, in list order), white on black. Pages already
written are skipped.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import credits as C  # noqa: E402

OUT = C.ROOT / "media/derived/names"


def pages():
    D = C.build_data(C.DEFAULT_TL)
    return C.pages_names(C.Type(), D, D["dead"]["_people"], "Killed in Gaza, named by the Ministry of Health",
                         4, 24, 2.5, script="both")


def main():
    first, count = int(sys.argv[1]), int(sys.argv[2])
    C.ensure_raqm()
    P = pages()
    OUT.mkdir(parents=True, exist_ok=True)
    made = 0
    for k in range(first, min(first + count, len(P))):
        f = OUT / f"page_{k:04d}.png"
        if not f.exists():
            im = P[k][0]
            (im() if callable(im) else im).save(f)
            made += 1
    print(f"{len(P)} pages in the list; wrote {made} to {OUT.relative_to(C.ROOT)}", file=sys.stderr)


if __name__ == "__main__":
    main()
