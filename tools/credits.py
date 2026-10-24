"""Credits outro for Meine: who filmed the footage, who published it, who was killed.

    uv run python tools/credits.py fetch               # cache source-page metadata + the lists of the dead
    uv run python tools/credits.py data                # -> projects/meine/credits/credits.json + CREDITS.md
    uv run python tools/credits.py render              # -> media/derived/credits.mp4 (about 3.5 min)
    uv run python tools/credits.py render --full       # -> media/derived/credits_full.mp4 (every name)
    uv run python tools/credits.py render --pages 3    # write a few sample PNGs per section instead

The clip list is derived from the timeline at run time (default comps/out/full.timeline.json; pass
--tl to use others). A clip counts as used if a layer's meta names it OR a layer's src is its file.
People come from layers' meta.people plus projects/meine/credits/people_extra.json (researched,
each with its source URL; an entry only appears while its clip is in the timeline).

Arabic is shaped by Pillow's raqm layout (HarfBuzz + FriBiDi). Pillow's wheel loads FriBiDi at
run time; Homebrew's lives in /opt/homebrew/lib, so the script re-execs itself with
DYLD_FALLBACK_LIBRARY_PATH set when raqm is not available, and refuses to render without it.
"""
import argparse
import csv
import datetime as dt
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PDIR = ROOT / "projects/meine"
CDIR = PDIR / "credits"
META = CDIR / "meta"          # source-page metadata per media file stem (yt-dlp fields we need)
LISTS = CDIR / "lists"        # the lists of the dead, as downloaded, plus RETRIEVED.json
OUT = ROOT / "media/derived"
DEFAULT_TL = [PDIR / "comps/out/full.timeline.json"]
MUSIC_END = 473.5
W, H, FPS = 1440, 1080, 25

LIST_URLS = {
    "killed-in-gaza.min.json": "https://data.techforpalestine.org/api/v3/killed-in-gaza.min.json",
    "summary.json": "https://data.techforpalestine.org/api/v3/summary.json",
    "casualties_daily.json": "https://data.techforpalestine.org/api/v2/casualties_daily.json",
    "press_killed_in_gaza.json": "https://data.techforpalestine.org/api/v2/press_killed_in_gaza.json",
    "cpj_killed.csv": ("https://cpj.org/wp-json/cpj-datamanager/v1/people_list?status=Killed"
                       "&type%5B%5D=Journalist&type%5B%5D=Media%20Worker&motiveConfirmed%5B%5D=Confirmed"
                       "&motiveUnconfirmed%5B%5D=Unconfirmed&sortBy=fullName&limit=-1&export=csv"),
}

# Non-catalog media in the piece, by src prefix
OTHER_SOURCES = {
    "media/src/meine.webm": "music",
    "media/derived/meine_proxy.mp4": "music",
    "media/derived/face": "voice",          # face.mp4, face_missiles_on_beat.mp4, face_rant2.mp4 ...
    "media/src/missiles_short.mov": "voice",
    "media/derived/credits": "self",
}


# ---------------------------------------------------------------- data
def load_catalogs():
    cats, by_file = {}, {}
    for f in sorted((PDIR / "footage").glob("*.json")):
        clips = json.loads(f.read_text())["clips"]
        cats[f.stem] = {c["id"]: c for c in clips}
        for c in clips:
            by_file[c["file"]] = (f.stem, c["id"])
    return cats, by_file


def collect_used(tl_paths, cats, by_file):
    """{(catalog, clip): {"segs", "first", "screen"}}, people from meta, other sources, unknown srcs."""
    used, people, other, unknown = {}, [], {}, set()
    for p in tl_paths:
        tl = json.loads(Path(p).read_text())
        for L in tl["layers"]:
            m = L.get("meta") or {}
            key = None
            if m.get("catalog") in cats and m.get("clip") in cats[m["catalog"]]:
                key = (m["catalog"], m["clip"])
            elif L.get("src") in by_file:
                key = by_file[L["src"]]
            if key:
                u = used.setdefault(key, {"segs": set(), "first": L["t0"], "screen": 0.0})
                if m.get("seg") is not None and key == (m.get("catalog"), m.get("clip")):
                    u["segs"].add(m["seg"])
                u["first"] = min(u["first"], L["t0"])
                u["screen"] += max(0.0, L["t1"] - L["t0"])
            else:
                kind = next((v for k, v in OTHER_SOURCES.items() if L.get("src", "").startswith(k)), None)
                if kind:
                    other.setdefault(kind, set()).add(L["src"])
                else:
                    unknown.add(L.get("src"))
            for person in m.get("people") or []:
                people.append({**person, "clip": key[1] if key else None, "layer": L.get("id")})
    return used, people, other, unknown


def source_meta(clip):
    """Title / uploader / description of the clip's source page: the lane's own yt-dlp info.json if
    it exists, else our cache in credits/meta/."""
    stem = Path(clip["file"]).stem
    lane = Path(clip["file"]).parent.parent
    for p in (ROOT / lane / "raw" / f"{stem}.info.json", ROOT / lane / "sheets/meta" / f"{stem}.info.json",
              META / f"{stem}.json"):
        if p.exists():
            d = json.loads(p.read_text())
            return {k: d.get(k) for k in ("title", "uploader", "upload_date", "description", "webpage_url")}
    return {}


def fetch_meta(clips):
    META.mkdir(parents=True, exist_ok=True)
    for c in clips:
        if source_meta(c):
            continue
        stem = Path(c["file"]).stem
        print(f"fetching {c['id']}  {c['source_url']}", file=sys.stderr)
        r = subprocess.run(["yt-dlp", "-j", "--skip-download", "--no-warnings", c["source_url"]],
                           capture_output=True, text=True, timeout=180)
        if r.returncode != 0:
            print(f"  failed: {r.stderr.strip()[:200]}", file=sys.stderr)
            continue
        d = json.loads(r.stdout)
        keep = {k: d.get(k) for k in ("id", "title", "uploader", "channel", "upload_date", "description",
                                      "webpage_url", "duration")}
        keep["fetched"] = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
        (META / f"{stem}.json").write_text(json.dumps(keep, indent=1, ensure_ascii=False) + "\n")


def fetch_lists():
    LISTS.mkdir(parents=True, exist_ok=True)
    rec_path = LISTS / "RETRIEVED.json"
    rec = json.loads(rec_path.read_text()) if rec_path.exists() else {}
    for name, url in LIST_URLS.items():
        tmp = LISTS / (name + ".part")
        subprocess.run(["curl", "-sSfL", "-A", "Mozilla/5.0 (vidbox credits)", "-o", str(tmp), url], check=True)
        if name.endswith(".csv"):   # keep only Israel and the Occupied Palestinian Territory (CPJ's country)
            rows = list(csv.DictReader(tmp.open(encoding="utf-8")))
            keep = [r for r in rows if r["Country"] == "Israel and the Occupied Palestinian Territory"]
            with (LISTS / name).open("w", encoding="utf-8", newline="") as f:
                w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
                w.writeheader()
                w.writerows(keep)
            tmp.unlink()
        else:
            json.loads(tmp.read_text())   # must parse
            tmp.rename(LISTS / name)
        rec[name] = {"url": url, "retrieved": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")}
        print(f"{name}: ok", file=sys.stderr)
    rec_path.write_text(json.dumps(rec, indent=1) + "\n")


# ---- credits fields extracted verbatim from the source page / catalog
CAMERA_PATTERNS = [
    (r"AP [Vv]ideo shot by ([^\n]+)", "Camera"),
    (r"AP [Vv]ideo by ([^\n]+)", "Camera"),
    (r"AP [Cc]amera(?:man|woman|person)? ([A-Z][^\n]+)", "Camera"),
    (r"AP [Pp]roduction by ([^\n]+)", "Producer"),
    (r"AP [Pp]roducer ([A-Z][^\n]+)", "Producer"),
    (r"Al Jazeera[’']s ([A-Z][^\n]+?) reports from", "Reporter"),
]


def credits_from_text(desc):
    out = []
    for pat, role in CAMERA_PATTERNS:
        for m in re.finditer(pat, desc or ""):
            name = m.group(1).strip().rstrip(".").strip()
            if name and (role, name) not in out:
                out.append((role, name))
    return out


def clean_title(t, url):
    """The source's own title, minus scraper artefacts: DVIDS pages read by yt-dlp's html5 extractor
    get ' (1)' appended; emoji and zero-width marks have no glyphs in the credits fonts."""
    if not t:
        return None
    if "dvidshub.net" in url:
        t = re.sub(r" \(\d+\)$", "", t)
    t = "".join(ch for ch in t if not (ord(ch) >= 0x1F000 or 0x2600 <= ord(ch) <= 0x27BF or ch in "\ufe0f\u200b"))
    return re.sub(r"\s+", " ", t).strip()


def ap_datelines(desc):
    """Place lines under 'ASSOCIATED PRESS' in AP shotlists, e.g. 'Gaza City, Gaza Strip - 11 March 2026'."""
    places = []
    for m in re.finditer(r"ASSOCIATED PRESS\s*\n\s*([^\n]+)", desc or ""):
        line = m.group(1).strip()
        place = re.sub(r"\s+,", ",", re.split(r"\s+[-–—]\s+", line)[0]).strip(" ,")
        if place and place not in places and not place.startswith("++"):
            places.append(place)
    return places


OUTLETS = [   # (publisher prefix, outlet group)
    ("AP Archive", "Associated Press"), ("Associated Press", "Associated Press"), ("APT", "Associated Press"),
    ("Reuters", "Reuters"), ("AFP", "AFP"), ("Al Jazeera", "Al Jazeera English"),
    ("NBC News", "NBC News"), ("Guardian", "The Guardian"), ("WSJ", "The Wall Street Journal"),
    ("news.com.au", "news.com.au"), ("Middle East Eye", "Middle East Eye"), ("Roya", "Roya News"),
    ("Anadolu", "Anadolu Agency"), ("Times Radio", "Times Radio"), ("Forbes", "Forbes Breaking News"),
    ("Forensic Architecture", "Forensic Architecture"),
    ("Israel Defense Forces", "Israel Defense Forces"), ("IDF", "Israel Defense Forces"),
    ("Israel Ministry of Defense", "Israel Ministry of Defense"),
    ("DVIDS", "DVIDS (US Department of Defense)"), ("Lockheed", "Lockheed Martin"), ("Boeing", "Boeing"),
]
NEWS_FIRST = ["Associated Press", "Reuters", "AFP", "Al Jazeera English", "Anadolu Agency", "Middle East Eye",
              "Roya News", "The Guardian", "NBC News", "The Wall Street Journal", "news.com.au", "Times Radio",
              "Forbes Breaking News", "Forensic Architecture"]


def outlet(pub):
    for pre, name in OUTLETS:
        if pub.startswith(pre):
            return name
    return "Re-uploads and others"


def build_data(tl_paths):
    cats, by_file = load_catalogs()
    used, meta_people, other, unknown = collect_used(tl_paths, cats, by_file)
    extra_src = json.loads((CDIR / "sources_extra.json").read_text()) if (CDIR / "sources_extra.json").exists() else {}
    clips = []
    for (cat, cid), u in used.items():
        c = cats[cat][cid]
        sm = source_meta(c)
        desc = sm.get("description") or ""
        people_credits = credits_from_text(desc)
        ex = extra_src.get(cid, {})
        for role, name in ex.get("credits", []):
            if (role, name) not in people_credits:
                people_credits.append((role, name))
        clips.append({
            "catalog": cat, "id": cid, "first": round(u["first"], 2), "screen": round(u["screen"], 1),
            "segs": sorted(u["segs"]), "publisher": c["publisher"], "outlet": ex.get("outlet") or outlet(c["publisher"]),
            "title": ex.get("title") or clean_title(sm.get("title"), c["source_url"]), "title_en": ex.get("title_en"),
            "uploader": sm.get("uploader"),
            "date": c.get("date"), "place": ex.get("place") or "; ".join(ap_datelines(desc)) or None,
            "credits": people_credits, "credits_source": ex.get("credits_source"),
            "url": c["source_url"], "license": c.get("license"), "scope": c.get("scope"),
            "provenance": c.get("provenance"),
        })
    clips.sort(key=lambda x: x["first"])

    # people: meta.people in the timeline + researched extras for clips in use
    used_ids = {cid for _, cid in used}
    extras = json.loads((CDIR / "people_extra.json").read_text()) if (CDIR / "people_extra.json").exists() else []
    allp = meta_people + [p for p in extras if p.get("clip") in used_ids]
    people = {}
    for p in allp:
        role = classify(p.get("role", ""))
        if role == "filmed":   # a camera credit, folded into that clip's credits
            for c in clips:
                if c["id"] == p.get("clip") and not any(n == p["name"] for _, n in c["credits"]):
                    c["credits"].append(("Filmed by", p["name"]))
            continue
        k = norm(p["name"])
        q = people.setdefault(k, {"name": p["name"], "kind": role, "roles": [], "age": p.get("age"),
                                  "sources": [], "clips": [], "detail": p.get("detail")})
        if p.get("role") and p["role"] not in q["roles"]:
            q["roles"].append(p["role"])
        if q["age"] is None and p.get("age") is not None:
            q["age"] = p["age"]
        q["detail"] = q["detail"] or p.get("detail")
        if p.get("source") and p["source"] not in q["sources"]:
            q["sources"].append(p["source"])
        if p.get("clip") and p["clip"] not in q["clips"]:
            q["clips"].append(p["clip"])
        if KIND_ORDER.index(role) < KIND_ORDER.index(q["kind"]):
            q["kind"] = role
    people = sorted(people.values(), key=lambda q: (KIND_ORDER.index(q["kind"]),
                                                     min((c["first"] for c in clips if c["id"] in q["clips"]),
                                                         default=1e9)))
    return {"timelines": [str(Path(p).relative_to(ROOT)) for p in tl_paths], "clips": clips, "people": people,
            "other_sources": {k: sorted(v) for k, v in other.items()}, "unknown_sources": sorted(map(str, unknown)),
            "dead": wider_dead()}


KIND_ORDER = ["killed", "group", "injured", "bereaved", "other", "filmed"]


def classify(role):
    r = role.lower()
    if r.startswith("filmed"):
        return "filmed"
    if r.startswith("killed") or r == "dead":
        return "killed"
    if r.startswith("group"):
        return "group"
    if r.startswith("injured") or r.startswith("wounded"):
        return "injured"
    if "bereaved" in r or "father" in r or "mother" in r or "killed" in r:
        return "bereaved"
    return "other"


def norm(name):
    return re.sub(r"[^a-z]", "", name.lower())


def wider_dead():
    rec = json.loads((LISTS / "RETRIEVED.json").read_text())
    summ = json.loads((LISTS / "summary.json").read_text())
    daily = json.loads((LISTS / "casualties_daily.json").read_text())
    last = daily[-1]
    names = json.loads((LISTS / "killed-in-gaza.min.json").read_text())
    hdr, rows = names[0], names[1:]
    ix = {k: hdr.index(k) for k in ("en_name", "ar_name", "age", "sex")}
    # One systematic artefact in the dataset's English: "عبد الله" written as "Abdullahallah" (280 names
    # in the 7 May 2026 list). The Arabic original is unambiguous, so it is written "Abdullah"; nothing
    # else is changed.
    people = [{"en": re.sub(r"\bAbdullahallah\b", "Abdullah", r[ix["en_name"]].strip()), "ar": r[ix["ar_name"]].strip(),
               "age": r[ix["age"]], "sex": r[ix["sex"]]} for r in rows]
    fixed = sum("Abdullahallah" in r[ix["en_name"]] for r in rows)
    people.sort(key=lambda p: (p["age"], p["en"]))
    k = summ["known_killed_in_gaza"]
    children = [p for p in people if p["age"] < 18]
    assert len(children) == k["male"]["child"] + k["female"]["child"], "child count disagrees with T4P summary"
    assert len(people) == k["records"], "name count disagrees with T4P summary"

    def parse(d):
        try:
            return dt.datetime.strptime(d, "%B %d, %Y").date()
        except ValueError:
            return None
    cpj = []
    for r in csv.DictReader((LISTS / "cpj_killed.csv").open(encoding="utf-8")):
        d = parse(r["Date"])
        if d and d >= dt.date(2023, 10, 7):
            cpj.append({"name": r["Name"].strip(), "date": d.isoformat(), "org": re.sub(r"\s*,\s*", ", ", r["Organization"]).strip(),
                        "role": r["Journalist or Media Worker"], "fire": r["Suspected Source of Fire"],
                        "url": r["cpj.org URL"]})
    cpj.sort(key=lambda r: (r["date"], r["name"]))
    by_israel = [r for r in cpj if r["fire"] == "Military Officials"]
    others = [r for r in cpj if r["fire"] != "Military Officials"]
    press_gmo = json.loads((LISTS / "press_killed_in_gaza.json").read_text())
    return {
        "moh": {"killed": last["killed_cum"], "injured": last["injured_cum"], "as_of": last["report_date"],
                "report_source": last["report_source"], "url": "https://data.techforpalestine.org/docs/casualties-daily/",
                "retrieved": rec["casualties_daily.json"]["retrieved"][:10]},
        "names": {"records": len(people), "children": len(children), "infants": sum(p["age"] == 0 for p in people),
                  "includes_until": k["includes_until"], "list_published": k["last_update"], "abdullah_fixed": fixed,
                  "url": "https://data.techforpalestine.org/docs/killed-in-gaza/",
                  "retrieved": rec["killed-in-gaza.min.json"]["retrieved"][:10]},
        "cpj": {"killed_by_israel": by_israel, "others": others,
                "url": "https://cpj.org/data/", "retrieved": rec["cpj_killed.csv"]["retrieved"][:10]},
        "gmo_press": {"records": len(press_gmo), "url": "https://data.techforpalestine.org/docs/press-killed-in-gaza/"},
        "_people": people,
    }


# ---------------------------------------------------------------- CREDITS.md
def write_md(D, path):
    d = D["dead"]
    L = ["# Credits", "",
         f"Derived from `{', '.join(D['timelines'])}` by `tools/credits.py` on "
         f"{dt.date.today().isoformat()}. Every clip that appears in the piece is listed, in order of first "
         "appearance within each outlet.", ""]
    if D["people"]:
        L += ["## Named in the footage", ""]
        for q in D["people"]:
            age = f", {q['age']}" if q.get("age") is not None else ""
            roles = "" if q["kind"] == "group" else ": " + "; ".join(q["roles"])
            L.append(f"- **{q['name']}**{age}{roles}"
                     + (f". {q['detail']}." if q.get("detail") else "")
                     + "".join(f" <{s}>" for s in q["sources"]))
        L.append("")
    L += ["## Footage", ""]
    for o, group in group_clips(D["clips"]):
        L += [f"### {o}", ""]
        for c in group:
            bits = [f"**{c['title'] or c['id']}**" + (f" ({c['title_en']})" if c.get("title_en") else ""),
                    c["publisher"], c["date"] or ""]
            if c["place"]:
                bits.append(c["place"])
            for role, name in c["credits"]:
                bits.append(f"{role}: {name}")
            L.append("- " + ". ".join(b for b in bits if b) + f". <{c['url']}> (licence as catalogued: {c['license']};"
                     f" first at {fmt_t(c['first'])}; catalog id `{c['id']}`)")
        L.append("")
    L += ["## Music, voice, tools", ""] + [f"- {x}" for x in MUSIC_LINES_MD] + [""]
    if D["unknown_sources"]:
        L += ["## UNIDENTIFIED media in the timeline (needs a credit)", ""] + [f"- `{s}`" for s in D["unknown_sources"]] + [""]
    m, n = d["moh"], d["names"]
    L += ["## The dead of Gaza", "",
          f"- Gaza Ministry of Health: {m['killed']:,} killed and {m['injured']:,} injured in Gaza since 7 October 2023, "
          f"as of {m['as_of']}. Via Tech For Palestine's daily casualties dataset <{m['url']}>, retrieved {m['retrieved']}.",
          f"- The ministry's list of the identified dead names {n['records']:,} people (deaths to {n['includes_until']}, "
          f"list published {n['list_published']}); {n['children']:,} of them were under 18 and {n['infants']:,} under one. "
          f"Tech For Palestine dataset (public domain) <{n['url']}>, retrieved {n['retrieved']}. "
          f"English names are the dataset's transliterations, except that its artefact \"Abdullahallah\" "
          f"(for عبد الله, {n['abdullah_fixed']} names) is written \"Abdullah\".",
          f"- Journalists and media workers killed by Israeli forces in Israel and the Occupied Palestinian Territory since "
          f"7 October 2023: {len(d['cpj']['killed_by_israel'])}, Committee to Protect Journalists database <{d['cpj']['url']}>, "
          f"retrieved {d['cpj']['retrieved']}. Gaza's Government Media Office lists {d['gmo_press']['records']} "
          f"<{d['gmo_press']['url']}>.", "",
          "### Journalists and media workers killed by Israeli forces (CPJ)", ""]
    for r in d["cpj"]["killed_by_israel"]:
        L.append(f"- {r['name']}, {r['org']}, {r['date']} ({r['role'].lower()}) <{r['url']}>")
    L += ["", "CPJ also lists, killed by other parties since 7 October 2023:", ""]
    for r in d["cpj"]["others"]:
        L.append(f"- {r['name']}, {r['org']}, {r['date']} (source of fire per CPJ: {r['fire'].lower()}) <{r['url']}>")
    L += ["", f"The {n['records']:,} names are not reproduced here; they are in `projects/meine/credits/lists/"
          "killed-in-gaza.min.json` and at the URL above, and on screen in `media/derived/credits_full.mp4`.", ""]
    path.write_text("\n".join(L))


MUSIC_LINES_MD = [
    "Music: Daso, \"Meine\" (Daso Franke, died 2018), from the *Meine Idee* EP, Spectral Sound (Ghostly International), 2007. "
    "<https://ghostly.bandcamp.com/album/meine-idee>",
    "Background picture: the \"Daso - Meine\" video uploaded to YouTube by discpictures99 on 19 February 2010 "
    "(description: \"Vilnius\"); filmmaker not credited there. <https://www.youtube.com/watch?v=h7qTI6Njp9g>",
    "Voice: Sam Hyde, comedian (Million Dollar Extreme), \"thou shalt give Israel missiles\". The original recording "
    "was not traced; the clip circulates widely, e.g. <https://www.youtube.com/shorts/_aFaQ-eRuWM> (uploaded 14 Sep 2022).",
    "Tools: Whisper (mlx-whisper) for word timing, MediaPipe face tracking, librosa beat analysis, OpenCV, PyAV and "
    "FFmpeg for rendering, Pillow with HarfBuzz/raqm for type.",
]


def group_clips(clips):
    groups = {}
    for c in clips:
        groups.setdefault(c["outlet"], []).append(c)
    order = [o for o in NEWS_FIRST if o in groups] + sorted(o for o in groups if o not in NEWS_FIRST)
    return [(o, groups[o]) for o in order]


def fmt_t(t):
    return f"{int(t // 60)}:{t % 60:04.1f}"


# ---------------------------------------------------------------- render
def ensure_raqm():
    from PIL import features
    if features.check("raqm"):
        return
    if os.environ.get("_CREDITS_REEXEC"):
        sys.exit("Pillow has no raqm layout (needs libfribidi: brew install fribidi). Refusing to render "
                 "Arabic without shaping.")
    env = dict(os.environ, _CREDITS_REEXEC="1",
               DYLD_FALLBACK_LIBRARY_PATH=":".join(x for x in ["/opt/homebrew/lib", "/usr/local/lib",
                                                              os.environ.get("DYLD_FALLBACK_LIBRARY_PATH", "")] if x))
    os.execve(sys.executable, [sys.executable, *sys.argv], env)


class Type:
    """Fonts and text drawing. Latin: Helvetica Neue / Avenir Next Condensed; Arabic: Geeza Pro, via raqm."""
    INK, DIM, FAINT = (236, 233, 226), (160, 156, 148), (104, 101, 96)

    def __init__(self):
        from PIL import ImageFont
        self.IF = ImageFont
        self.cache = {}

    def f(self, face, size):
        key = (face, size)
        if key not in self.cache:
            path, idx = {
                "light": ("/System/Library/Fonts/HelveticaNeue.ttc", 7),
                "regular": ("/System/Library/Fonts/HelveticaNeue.ttc", 0),
                "medium": ("/System/Library/Fonts/HelveticaNeue.ttc", 10),
                "thin": ("/System/Library/Fonts/HelveticaNeue.ttc", 12),
                "cond": ("/System/Library/Fonts/Avenir Next Condensed.ttc", 7),
                "cond_med": ("/System/Library/Fonts/Avenir Next Condensed.ttc", 5),
                "arabic": ("/System/Library/Fonts/GeezaPro.ttc", 0),
            }[face]
            self.cache[key] = self.IF.truetype(path, size, index=idx, layout_engine=self.IF.Layout.RAQM)
        return self.cache[key]

    @staticmethod
    def is_ar(s):
        return bool(re.search(r"[؀-ۿݐ-ݿﭐ-﷿ﹰ-﻿]", s))

    def font_for(self, s, face, size):
        return self.f("arabic", size) if self.is_ar(s) else self.f(face, size)

    def width(self, s, face, size):
        f = self.font_for(s, face, size)
        kw = {"direction": "rtl", "language": "ar"} if self.is_ar(s) and not re.search(r"[A-Za-z]", s) else {}
        return f.getlength(s, **kw)

    def draw(self, d, xy, s, face, size, fill=None, anchor="ls", fit=None):
        """Draw s. With fit=width, a line that is too wide first loses up to two points of size, then
        is narrowed horizontally (never truncated, never below 72% width)."""
        kw = {"direction": "rtl", "language": "ar"} if self.is_ar(s) and not re.search(r"[A-Za-z]", s) else {}
        if fit:
            floor = max(9, size - 2)
            while size > floor and self.width(s, face, size) > fit:
                size -= 1
            w = self.width(s, face, size)
            if w > fit:
                while size > 9 and w * 0.72 > fit:
                    size -= 1
                    w = self.width(s, face, size)
                return self._squeezed(d, xy, s, face, size, fill, anchor, fit / w, kw)
        f = self.font_for(s, face, size)
        d.text(xy, s, font=f, fill=fill or self.INK, anchor=anchor, **kw)
        return size

    def _squeezed(self, d, xy, s, face, size, fill, anchor, sx, kw):
        """Render s at full width into a mask, scale it to sx of its width, and stamp it in place."""
        from PIL import Image, ImageDraw
        f = self.font_for(s, face, size)
        x0, y0, x1, y1 = f.getbbox(s, anchor="ls", **kw)
        pad = 4
        m = Image.new("L", (int(x1 - x0) + 2 * pad, int(y1 - y0) + 2 * pad), 0)
        ImageDraw.Draw(m).text((pad - x0, pad - y0), s, font=f, fill=255, anchor="ls", **kw)
        nw = max(1, round(m.width * sx))
        m = m.resize((nw, m.height), Image.LANCZOS)
        ox = {"l": 0, "r": nw - 2 * pad * sx, "m": (nw - 2 * pad * sx) / 2}[anchor[0]]
        x = round(xy[0] - ox + x0 * sx - pad * sx)
        y = round(xy[1] + y0 - pad)
        d.bitmap((x, y), m, fill=fill or self.INK)
        return size

    def wrap(self, s, face, size, width):
        words, lines, cur = [], [], ""
        for w in s.split():            # a token wider than the column (a URL) is broken by characters
            while self.width(w, face, size) > width and len(w) > 1:
                k = len(w)
                while k > 1 and self.width(w[:k], face, size) > width:
                    k -= 1
                words.append(w[:k])
                w = w[k:]
            words.append(w)
        for w in words:
            t = (cur + " " + w).strip()
            if self.width(t, face, size) <= width or not cur:
                cur = t
            else:
                lines.append(cur)
                cur = w
        if cur:
            lines.append(cur)
        return lines


M_X, TOP, BOTTOM = 110, 120, 1000      # margins; the footer source line sits under BOTTOM


def new_page():
    from PIL import Image, ImageDraw
    im = Image.new("RGB", (W, H), (0, 0, 0))
    return im, ImageDraw.Draw(im)


def header(T, d, title, sub=None):
    T.draw(d, (M_X, 78), title, "light", 30, T.INK)
    if sub:
        T.draw(d, (W - M_X, 78), sub, "light", 18, T.DIM, anchor="rs")


def footer(T, d, text):
    T.draw(d, (M_X, 1046), text, "light", 15, T.FAINT, fit=W - 2 * M_X)


def text_page(T, title, paras, foot=None, gap=18, width=1060, y0=None):
    """A page of wrapped paragraphs, the block centred vertically. paras: [(text, face, size, colour)];
    a paragraph with text "" is an extra gap."""
    im, d = new_page()
    items = []    # ("line", text, face, size, colour) | ("gap", px)
    for text, face, sz, col in paras:
        if text == "":
            items.append(("gap", gap * 5))
            continue
        items += [("line", ln, face, sz, col) for ln in T.wrap(text, face, sz, width)]
        items.append(("gap", gap))
    hgt = sum(x[3] * 1.36 if x[0] == "line" else x[1] for x in items) + (70 if title else 0)
    y = y0 if y0 is not None else max(TOP, (H - hgt) / 2)
    if title:
        T.draw(d, (M_X, y + 30), title, "light", 30, T.INK)
        y += 70
    for x in items:
        if x[0] == "gap":
            y += x[1]
            continue
        _, ln, face, sz, col = x
        y += sz * 1.36
        T.draw(d, (M_X, y), ln, face, sz, col)
    if foot:
        footer(T, d, foot)
    return im


def pages_named(T, D):
    ps = [q for q in D["people"] if q["kind"] in ("killed", "group", "injured", "bereaved")]
    group_clips_ = {c for q in ps if q["kind"] == "group" for c in q["clips"]}
    # a bereaved survivor whose family is already credited as a group from the same clip is not repeated
    ps = [q for q in ps if not (q["kind"] == "bereaved" and set(q["clips"]) <= group_clips_)]
    if not ps:
        return []
    entries = []
    for q in ps:
        age = f", {q['age']}" if q.get("age") is not None else ""
        name_face = "medium" if q["kind"] in ("killed", "group") else "regular"
        e = [(f"{q['name']}{age}", name_face, 25, T.INK)]
        if q["kind"] == "injured" and q["roles"] and not q.get("detail"):
            e.append((q["roles"][0][0].upper() + q["roles"][0][1:], "light", 18, T.DIM))
        elif q["kind"] == "bereaved" and q["roles"]:
            e.append((q["roles"][0][0].upper() + q["roles"][0][1:], "light", 18, T.DIM))
        if q.get("detail"):
            e.append((q["detail"] + ".", "light", 18, T.DIM))
        e.append((" · ".join(short_url(s) for s in q["sources"]), "light", 14, T.FAINT))
        entries.append(e)
    per = 5
    out = []
    for k in range(0, len(entries), per):
        chunk = entries[k:k + per]
        paras = [x for e in chunk for x in e + [("", None, None, None)]]
        n = -(-len(entries) // per)
        sub = f"{k // per + 1}/{n}" if n > 1 else None
        out.append((text_page(T, "In this footage" + (f"  ·  {sub}" if sub else ""), paras, gap=5),
                    3.0 + 2.2 * len(chunk)))
    return out


def short_url(u):
    """URL as shown on screen: scheme and www dropped; DVIDS pages by their numeric id (the slug is
    optional on dvidshub.net, so the short form resolves to the same page)."""
    u = re.sub(r"^https?://(www\.)?", "", u)
    m = re.match(r"(dvidshub\.net/video/\d+)", u)
    return m.group(1) if m else u


def source_blocks(T, D, colw):
    """[(kind, payload, height)] flowed into columns. kind: 'h' outlet header, 'c' clip."""
    blocks = []
    for o, group in group_clips(D["clips"]):
        blocks.append(("h", o, 44))
        for c in group:
            title = c["title"] or c["id"]
            tl = T.wrap(title, "medium", 18, colw)
            if c.get("title_en"):
                tl += T.wrap(c["title_en"], "light", 15, colw)
            meta = " · ".join(x for x in [c["publisher"], c["date"], c["place"]] if x)
            ml = T.wrap(meta, "light", 15, colw)
            cr = [f"{r}: {n}" for r, n in c["credits"]]
            crl = [ln for x in cr for ln in T.wrap(x, "regular", 15, colw)]
            ul = T.wrap(short_url(c["url"]), "light", 13, colw)
            h = len(tl) * 24 + len(ml) * 20 + len(crl) * 20 + len(ul) * 18 + 16
            blocks.append(("c", (tl, ml, crl, ul), h))
    return blocks


def pages_sources(T, D, secs_per_page):
    ncol, gut = 3, 44
    colw = (W - 2 * M_X - gut * (ncol - 1)) / ncol
    blocks = source_blocks(T, D, colw)
    y0, y1 = 140, BOTTOM
    pages, cols, cur, y = [], [], [], y0
    last_header = None
    for kind, payload, h in blocks:
        if kind == "h":
            last_header = payload
        if y + h > y1 or (kind == "h" and y + h + 90 > y1):
            cols.append(cur)
            cur, y = [], y0
            if len(cols) == ncol:
                pages.append(cols)
                cols = []
            if kind == "c" and last_header:   # repeat the outlet header at the top of a new column
                cur.append(("h", last_header + " (cont.)", 44))
                y += 44
        cur.append((kind, payload, h))
        y += h
    if cur:
        cols.append(cur)
    if cols:
        pages.append(cols)
    n = len(D["clips"])
    out = []
    for pi, cols in enumerate(pages):
        im, d = new_page()
        header(T, d, "The footage", f"{n} clips, in order of appearance by outlet · {pi + 1}/{len(pages)}")
        for ci, col in enumerate(cols):
            x, y = M_X + ci * (colw + gut), y0
            for kind, payload, h in col:
                if kind == "h":
                    T.draw(d, (x, y + 26), payload.upper(), "medium", 14, T.DIM)
                    d.line([(x, y + 34), (x + colw, y + 34)], fill=(60, 58, 55), width=1)
                else:
                    tl, ml, crl, ul = payload
                    yy = y
                    for ln in tl:
                        yy += 24
                        T.draw(d, (x, yy), ln, "medium", 18, T.INK)
                    for ln in ml:
                        yy += 20
                        T.draw(d, (x, yy), ln, "light", 15, T.DIM)
                    for ln in crl:
                        yy += 20
                        T.draw(d, (x, yy), ln, "regular", 15, T.INK)
                    for ln in ul:
                        yy += 18
                        T.draw(d, (x, yy), ln, "light", 13, T.FAINT)
                y += h
        footer(T, d, "Titles are each source's own; dates are filming dates where the source gives them. "
                     "News footage is the property of its publishers; US government footage is public domain.")
        out.append((im, secs_per_page))
    return out


def page_music(T):
    paras = [
        ("Music", "medium", 15, T.DIM),
        ("Daso, “Meine”", "medium", 30, T.INK),
        ("Daso Franke (died 2018). From the Meine Idee EP, Spectral Sound / Ghostly International, 2007.", "light", 19, T.DIM),
        ("", None, None, None),
        ("Picture", "medium", 15, T.DIM),
        ("“Daso - Meine”, uploaded to YouTube by discpictures99, 19 February 2010. Filmed in Vilnius "
         "(the upload's description).", "light", 22, T.INK),
        ("youtube.com/watch?v=h7qTI6Njp9g", "light", 15, T.FAINT),
        ("", None, None, None),
        ("Voice", "medium", 15, T.DIM),
        ("Sam Hyde, comedian (Million Dollar Extreme): “In the Bible, it says, thou shalt give Israel missiles.”",
         "light", 22, T.INK),
        ("Original recording not traced; the clip as widely re-posted, e.g. youtube.com/shorts/_aFaQ-eRuWM",
         "light", 15, T.FAINT),
        ("", None, None, None),
        ("Made with", "medium", 15, T.DIM),
        ("Whisper (word timing), MediaPipe (face tracking), librosa (beats), OpenCV, PyAV, FFmpeg, Pillow with "
         "HarfBuzz and FriBiDi (type).", "light", 19, T.DIM),
    ]
    return text_page(T, None, paras, gap=8)


def page_count(T, D):
    m, n, c = D["dead"]["moh"], D["dead"]["names"], D["dead"]["cpj"]
    paras = [
        (f"{m['killed']:,}", "thin", 120, T.INK),
        (f"people killed in Gaza since 7 October 2023, as reported by Gaza's Ministry of Health on "
         f"{long_date(m['as_of'])}. {m['injured']:,} injured.", "light", 26, T.INK),
        ("", None, None, None),
        (f"The ministry has identified {n['records']:,} of the dead by name (deaths to {long_date(n['includes_until'])}). "
         f"{n['children']:,} of them were children under 18; {n['infants']:,} were under one year old.",
         "light", 22, T.DIM),
        ("The ministry has said its lists leave out the missing, the dead still under rubble, the unidentified, "
         "and those buried without passing through a hospital.", "light", 22, T.DIM),
    ]
    foot = (f"Ministry of Health figures via Tech For Palestine (data.techforpalestine.org, public domain), "
            f"retrieved {long_date(m['retrieved'])}. UN OCHA attributes its Gaza casualty figures to the same ministry.")
    return text_page(T, None, paras, foot=foot, gap=6)


def long_date(iso):
    d = dt.date.fromisoformat(iso[:10])
    return f"{d.day} {d.strftime('%B %Y')}"


def pages_journalists(T, D, secs):
    c = D["dead"]["cpj"]
    rows = c["killed_by_israel"]
    ncol, gut, pitch = 3, 40, 46
    colw = (W - 2 * M_X - gut * (ncol - 1)) / ncol
    y0 = 150
    nrow = int((BOTTOM - y0) // pitch)
    per = ncol * nrow
    out = []
    npages = -(-len(rows) // per)
    for pi in range(npages):
        im, d = new_page()
        header(T, d, "Journalists and media workers killed by Israeli forces",
               f"{len(rows)} · since 7 October 2023 · {pi + 1}/{npages}")
        chunk = rows[pi * per:(pi + 1) * per]
        for i, r in enumerate(chunk):
            col, row = divmod(i, nrow)
            x, y = M_X + col * (colw + gut), y0 + row * pitch
            T.draw(d, (x, y + 18), r["name"], "medium", 18, T.INK, fit=colw)
            T.draw(d, (x, y + 37), f"{r['org']} · {long_date(r['date'])}", "light", 13, T.DIM, fit=colw)
        foot = (f"Committee to Protect Journalists database (cpj.org/data), Israel and the Occupied Palestinian Territory, "
                f"retrieved {long_date(c['retrieved'])}. Gaza's Government Media Office lists "
                f"{D['dead']['gmo_press']['records']} journalists killed in Gaza.")
        footer(T, d, foot)
        out.append((im, secs))
    if c["others"]:
        fmt = lambda rs: "; ".join(f"{r['name']} ({r['org']}, {long_date(r['date'])})" for r in rs)
        hamas = [r for r in c["others"] if r["fire"] == "Political Group"]
        armed = [r for r in c["others"] if r["fire"] == "Paramilitary Group"]
        rest = [r for r in c["others"] if r not in hamas and r not in armed]
        paras = [("The Committee to Protect Journalists also documents, in the same period:", "light", 22, T.DIM)]
        if hamas:
            paras += [("Killed in Israel by Hamas", "medium", 15, T.DIM), (fmt(hamas), "light", 20, T.INK)]
        if armed:
            paras += [("Killed by an armed group in Gaza", "medium", 15, T.DIM), (fmt(armed), "light", 20, T.INK)]
        if rest:
            paras += [("Killed by other parties", "medium", 15, T.DIM), (fmt(rest), "light", 20, T.INK)]
        out.append((text_page(T, None, paras, foot="Committee to Protect Journalists database (cpj.org/data); "
                                                   "groupings follow CPJ's source-of-fire classification and summary."),
                    7.0))
    return out


def pages_names(T, D, people, title, ncol, nrow, secs, script="en"):
    """Dense grid of names with ages. script: en | ar | both (two lines per cell)."""
    n = D["dead"]["names"]
    gut = 18
    colw = (W - 2 * M_X - gut * (ncol - 1)) / ncol
    y0 = 140
    pitch = (BOTTOM - y0) / nrow
    per = ncol * nrow
    npages = -(-len(people) // per)

    def page(pi):   # drawn when written: the long version is ~760 pages, ~6 MB each as images
        im, d = new_page()
        chunk = people[pi * per:(pi + 1) * per]
        ages = sorted({p["age"] for p in chunk})
        rng = f"age {ages[0]}" if len(ages) == 1 else f"ages {ages[0]}–{ages[-1]}"
        header(T, d, title, f"{len(people):,} names · {rng} · {pi + 1}/{npages}")
        for i, p in enumerate(chunk):
            col, row = divmod(i, nrow)
            x, y = M_X + col * (colw + gut), y0 + row * pitch
            agew = 26
            if script == "both":
                T.draw(d, (x + colw, y + pitch * 0.42), p["ar"], "arabic", 15, T.INK, anchor="rs", fit=colw)
                T.draw(d, (x, y + pitch * 0.86), p["en"], "cond", 14, T.DIM, fit=colw - agew)
                T.draw(d, (x + colw, y + pitch * 0.86), str(p["age"]), "cond", 14, T.DIM, anchor="rs")
            elif script == "ar":
                T.draw(d, (x + colw - agew, y + pitch * 0.78), p["ar"], "arabic", 15, T.INK, anchor="rs", fit=colw - agew)
                T.draw(d, (x, y + pitch * 0.78), str(p["age"]), "cond", 14, T.DIM)
            else:
                T.draw(d, (x, y + pitch * 0.78), p["en"], "cond", 15, T.INK, fit=colw - agew)
                T.draw(d, (x + colw, y + pitch * 0.78), str(p["age"]), "cond", 15, T.DIM, anchor="rs")
        footer(T, d, f"Gaza Ministry of Health list of the identified dead, deaths to {long_date(n['includes_until'])}, "
                     f"as published by Tech For Palestine (data.techforpalestine.org). English names are its "
                     f"transliterations. Youngest first.")
        return im
    return [(lambda pi=pi: page(pi), secs) for pi in range(npages)]


def page_end(T, D):
    m, n = D["dead"]["moh"], D["dead"]["names"]
    paras = [
        ("Sources for the names and figures", "medium", 15, T.DIM),
        (f"Gaza Ministry of Health: daily reports (to {long_date(m['as_of'])}) and lists of the identified dead "
         f"(to {long_date(n['includes_until'])}), compiled by Tech For Palestine, data.techforpalestine.org, "
         "released into the public domain.", "light", 21, T.INK),
        ("Committee to Protect Journalists, cpj.org/data.", "light", 21, T.INK),
        ("UN OCHA reported-impact snapshots, ochaopt.org.", "light", 21, T.INK),
        ("", None, None, None),
        (f"Every one of the {n['records']:,} names is in the long version of these credits.", "light", 19, T.DIM),
    ]
    return text_page(T, None, paras, gap=8)


def build_sequence(T, D, full=False):
    """[(section, [(PIL image or a function drawing it, seconds)], dense)]"""
    people = D["dead"]["_people"]
    seq = [("named", pages_named(T, D), False),
           ("sources", pages_sources(T, D, 7.0), False),
           ("music", [(page_music(T), 10.0)], False),
           ("count", [(page_count(T, D), 11.0)], False),
           ("journalists", pages_journalists(T, D, 9.0), False)]
    if full:
        seq.append(("all", pages_names(T, D, people, "Killed in Gaza, named by the Ministry of Health",
                                       4, 24, 2.5, script="both"), True))
    else:
        kids = [p for p in people if p["age"] < 18]
        seq.append(("children", pages_names(T, D, kids, "Children killed in Gaza, named by the Ministry of Health",
                                            5, 44, 0.8, script="en"), True))
    seq.append(("end", [(page_end(T, D), 9.0)], False))
    return [(s, p, dense) for s, p, dense in seq if p]


def render(D, out, full=False, sample_pages=0):
    import numpy as np
    T = Type()
    seq = build_sequence(T, D, full)
    if sample_pages:
        sd = Path(out).with_suffix("")
        sd.mkdir(parents=True, exist_ok=True)
        for s, pages, _ in seq:
            for i, (im, _) in enumerate(pages[:sample_pages]):
                (im() if callable(im) else im).save(sd / f"{s}_{i:03d}.png")
        print(f"wrote samples to {sd}", file=sys.stderr)
        return
    fade = 10        # frames: fade from/to black at section edges and between readable pages
    total = 0
    plan = []        # (page, frames, fade_in, fade_out); a page becomes pixels only when written
    lead = 25        # one second of black after the music ends
    for s, pages, dense in seq:
        for i, (im, secs) in enumerate(pages):
            n = max(1, round(secs * FPS))
            first, last = i == 0, i == len(pages) - 1
            fi = fade if (first or not dense) else 0
            fo = fade if (last or not dense) else 0
            plan.append((im, n, fi, fo))
            total += n
    total += lead + 25
    out = Path(out)
    tmp = out.with_suffix(".part.mp4")
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
           "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "14", "-tune", "stillimage",
           "-pix_fmt", "yuv420p", "-g", "50", "-movflags", "+faststart", str(tmp)]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    black = np.zeros((H, W, 3), np.uint8).tobytes()
    for _ in range(lead):
        p.stdin.write(black)
    for k_page in range(len(plan)):
        im, n, fi, fo = plan[k_page]
        plan[k_page] = None   # drop each page once written (the eager pages too)
        arr = np.asarray(im() if callable(im) else im, dtype=np.uint8)
        raw = arr.tobytes()
        for k in range(n):
            a = 1.0
            if fi and k < fi:
                a = (k + 1) / (fi + 1)
            if fo and k >= n - fo:
                a = min(a, (n - k) / (fo + 1))
            p.stdin.write(raw if a >= 1.0 else (arr.astype(np.float32) * a).astype(np.uint8).tobytes())
    for _ in range(25):
        p.stdin.write(black)
    p.stdin.close()
    if p.wait():
        sys.exit("ffmpeg failed")
    tmp.rename(out)
    secs = total / FPS
    durs = {s: round(sum(round(x[1] * FPS) for x in pages) / FPS, 1) for s, pages, _ in seq}
    print(f"wrote {out.relative_to(ROOT)}: {secs:.1f} s ({int(secs // 60)}:{secs % 60:04.1f}); sections {durs}",
          file=sys.stderr)
    (CDIR / f"{out.stem}.durations.json").write_text(json.dumps(
        {"file": str(out.relative_to(ROOT)), "seconds": round(secs, 2), "frames": total, "sections": durs},
        indent=1) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["fetch", "data", "render"])
    ap.add_argument("--tl", nargs="+", type=Path, help="timeline(s) to credit (default full.timeline.json)")
    ap.add_argument("--full", action="store_true", help="name every identified person (long version)")
    ap.add_argument("--pages", type=int, default=0, help="write N sample PNGs per section, no video")
    ap.add_argument("-o", "--out", type=Path)
    a = ap.parse_args()
    tls = [p.resolve() for p in (a.tl or DEFAULT_TL)]
    if a.cmd == "fetch":
        cats, by_file = load_catalogs()
        used, *_ = collect_used(tls, cats, by_file)
        fetch_meta([cats[k][c] for k, c in used])
        fetch_lists()
        return
    D = build_data(tls)
    if D["unknown_sources"]:
        print("WARNING: media in the timeline with no credit:", *D["unknown_sources"], sep="\n  ", file=sys.stderr)
    if a.cmd == "data":
        CDIR.mkdir(parents=True, exist_ok=True)
        dump = {k: v for k, v in D.items() if k != "dead"}
        dump["dead"] = {k: v for k, v in D["dead"].items() if not k.startswith("_")}
        (CDIR / "credits.json").write_text(json.dumps(dump, indent=1, ensure_ascii=False) + "\n")
        write_md(D, CDIR / "CREDITS.md")
        print(f"{len(D['clips'])} clips, {len(D['people'])} people named; wrote {CDIR.relative_to(ROOT)}/credits.json "
              f"and CREDITS.md", file=sys.stderr)
        return
    ensure_raqm()
    out = a.out or OUT / ("credits_full.mp4" if a.full else "credits.mp4")
    render(D, out, a.full, a.pages)


if __name__ == "__main__":
    main()
