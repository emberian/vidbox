"""The names of the dead, threaded through the film: pages of the Ministry of Health's list
(tools/names_pages.py) flashed or overlaid on the bar grid, in list order, never repeated.

    add_names(timeline_dict, mode)   mode: "text" | "hard" | "continuous"

text        a page flashes on every downbeat (3 frames), white names screened over the picture;
            where the song is intense (> 0.7) also on beats 2-4 (2 frames)
hard        the same schedule, but the page replaces the frame (white on black: a real flash;
            photosensitivity applies)
continuous  the page stays over the picture at low opacity, turning on the beat; all 759 pages,
            in order, spread over the free beats so the list ends with the song

Never during untreated footage of the dead, and not over the credits.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "render"))
from signals import Music  # noqa: E402

SONG_END = 473.5
FPS = 25
PAGES = 759   # pages in the list (tools/names_pages.py)


def untreated_windows(tl):
    out = []
    for L in tl["layers"]:
        m = L.get("meta", {})
        if m.get("catalog") in ("ground", "weapons", "y2026") and not L.get("fx") \
                and L.get("blend", "normal") == "normal" and "audio" in L:
            out.append((L["t0"] - 0.3, L["t1"] + 0.3))
    return out


def schedule(tl, mode, music):
    """[(t0, t1)] song-time spans, one per page, in order."""
    wins = untreated_windows(tl)
    free = lambda a, b: not any(a < w1 and b > w0 for w0, w1 in wins)
    spans = []
    beats = list(music.beats)
    for i, d in enumerate(music.downbeats):
        if d >= SONG_END - 0.1:
            break
        nxt = music.downbeats[i + 1] if i + 1 < len(music.downbeats) else SONG_END
        if mode == "continuous":
            continue   # laid out below, on the beat grid
        hits = [(d, 3)]
        if music.intensity(d, 1.0) > 0.7:
            k = beats.index(min(beats, key=lambda b: abs(b - d)))
            hits += [(beats[k + j], 2) for j in (1, 2, 3) if k + j < len(beats) and beats[k + j] < nxt]
        for t, n in hits:
            if free(t, t + n / FPS):
                spans.append((t, t + n / FPS))
    if mode == "continuous":
        # every page of the list, in order: the free beats (outside untreated windows, before the
        # song ends) shared out evenly, so each page holds one or two beats and the list ends with the song
        slots = [(a, b) for a, b in zip(beats, beats[1:] + [SONG_END]) if a < SONG_END and free(a, b)]
        n = len(slots)
        for k in range(PAGES):
            i0, i1 = k * n // PAGES, max(k * n // PAGES + 1, (k + 1) * n // PAGES)
            for a, b in slots[i0:i1]:   # one span per contiguous run: never bridging a window
                if spans and spans[-1][0] == k and abs(spans[-1][2] - a) < 1e-6:
                    spans[-1] = (k, spans[-1][1], min(b, SONG_END))
                else:
                    spans.append((k, a, min(b, SONG_END)))
        return spans
    return [(k, a, b) for k, (a, b) in enumerate(spans)]


def add_names(tl, mode, first_page=0):
    music = Music(ROOT / "projects/meine/analysis/beats.json")
    spans = schedule(tl, mode, music)
    style = {"text": ("screen", 0.85), "hard": ("normal", 1.0), "continuous": ("screen", 0.3)}[mode]
    for j, (k, a, b) in enumerate(spans):
        tl["layers"].append({
            "id": f"names:{first_page + k:04d}.{j}", "tags": ["names", "text"],
            "src": f"media/derived/names/page_{first_page + k:04d}.png",
            "t0": round(a, 4), "t1": round(b, 4), "time": {"hold": 0.0}, "fit": "native",
            "pos": [720, 540], "blend": style[0], "opacity": style[1]})
    return spans


if __name__ == "__main__":   # write the three test variants of a timeline, and list the pages they need
    src, lo, hi = Path(sys.argv[1]), float(sys.argv[2]), float(sys.argv[3])
    for mode in ("text", "hard", "continuous"):
        tl = json.loads(src.read_text())
        spans = add_names(tl, mode)
        used = [k for k, a, b in spans if a < hi and b > lo]
        out = src.with_name(src.name.replace(".timeline.json", f".names_{mode}.timeline.json"))
        out.write_text(json.dumps(tl) + "\n")
        print(f"{mode}: {len({k for k, _, _ in spans})} pages over the song (of 759); pages {used[0]}-{used[-1]} fall in {lo}-{hi}s")
