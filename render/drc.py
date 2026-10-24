"""Design rule checker: the piece's rules, each with the reason it exists, run over a timeline.

usage: uv run python render/drc.py TIMELINE.json [--strict]

ERROR rules encode ember's explicit decisions; full.py refuses to build on any. WARN rules are
craft lessons from watching the renders. INFO sections are lists for ember's own reviews (the
sensitivity review, the listen list). Bars are VIEWER bars (counted from 1), as ember counts.
"""
import json
import math
import sys
from bisect import bisect_right
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "render"))
from signals import Ctx, Music, compile_signal  # noqa: E402

IN_SCOPE = ("gaza", "israel", "arms-to-israel", "politics-israel", "us-arsenal")
SPEAKER_CATALOGS = ("preachers", "israeli_voices")
HEADS_ONLY_FX = {"voronoi"}
COMIC_FX = {"voronoi", "hue", "chroma", "glitch", "kaleido", "posterize", "dither", "shock", "feedback",
            "chromatime", "gradmap", "noise", "warp"}
REPEAT_ALLOW = {"mq9-countdown-gcs-2026-03", "mq9-countdown"}   # ember: "We can keep that MQ-9"
GRID_TOL = 0.03


class Piece:
    def __init__(self, tl):
        if isinstance(tl, dict):
            self.path, self.tl = Path(f"<{tl.get('project', '?')}>"), tl
        else:
            self.path = Path(tl)
            self.tl = json.loads(self.path.read_text())
        self.L = self.tl["layers"]
        pdir = ROOT / "projects" / self.tl["project"]
        self.music = Music(pdir / "analysis/beats.json")
        self.ctx = Ctx(self.music, pdir)
        self.db = list(self.music.downbeats)
        self.cat = {f.stem: {c["id"]: c for c in json.loads(f.read_text())["clips"]}
                    for f in sorted((pdir / "footage").glob("*.json"))}
        self.period = self.music.period

    # ---- vocabulary ----
    def where(self, t):
        b = bisect_right(self.db, t)   # viewer bar = number of downbeats at or before t
        return f"bar {max(b, 1)} ({int(t // 60)}:{t % 60:04.1f})"

    def seg(self, L):
        m = L.get("meta", {})
        clip = self.cat.get(m.get("catalog"), {}).get(m.get("clip"))
        return (clip, clip["segments"][m.get("seg", 0)]) if clip else (None, None)

    def footage(self, L):
        return self.seg(L)[0] is not None

    def speaker(self, L):
        return L.get("meta", {}).get("catalog") in SPEAKER_CATALOGS or "speaker" in L.get("tags", [])

    def text(self, L):
        return "text" in L.get("tags", []) or "subtitle" in L.get("tags", [])

    def head(self, L):
        return "head" in L.get("tags", []) and not self.speaker(L)

    def untreated(self, L):
        return self.footage(L) and not L.get("fx") and L.get("blend", "normal") == "normal" and "audio" in L

    def visible(self, L, a, b, n=12):
        """Is the layer visible anywhere in [a, b]? (samples its opacity signal)"""
        op = L.get("opacity", 1.0)
        if isinstance(op, (int, float)):
            return op > 0.01
        f = compile_signal(op, self.ctx)
        return any(f(a + (b - a) * i / (n - 1)) > 0.01 for i in range(n))

    def scope(self, L):
        clip, seg = self.seg(L)
        return (seg.get("scope") or clip.get("scope")) if clip else None


def overlap(L, a, b, margin=0.02):
    return L["t0"] < b - margin and L["t1"] > a + margin


# ---- rules: (id, severity, rationale, check(piece) -> [(time, message)]) ----
RULES = []


def rule(rid, sev, why):
    def reg(f):
        RULES.append((rid, sev, why, f))
        return f
    return reg


@rule("scope", "ERROR", 'ember: "the problem isn\'t the strike into people, the problem is that it isn\'t Israel/Gaza at all."')
def r_scope(P):
    allowed = set(IN_SCOPE) | set(P.tl.get("scope_allow", []))
    return [(L["t0"], f"{L['id']}: scope {P.scope(L)}") for L in P.L
            if P.footage(L) and P.scope(L) not in allowed and P.scope(L) is not None]


@rule("voronoi-faces-only", "ERROR", 'ember: "do *not* use the voronoi effect on war footage, but it looks AMAZING on the guys face."')
def r_voronoi(P):
    out = [(L["t0"], f"{L['id']}: {f['op']} on footage") for L in P.L if P.footage(L)
           for f in L.get("fx", []) if f.get("op") in HEADS_ONLY_FX]
    out += [(0.0, f"post: {f['op']} over the whole frame") for f in P.tl.get("post", []) if f.get("op") in HEADS_ONLY_FX]
    return out


@rule("no-decoration-on-the-dead", "ERROR", 'ember: "no decoration on the dead, no mocking juxtaposition, full truth."')
def r_decoration(P):
    out = []
    for L in P.L:
        clip, seg = P.seg(L)
        if seg and seg.get("graphic", 0) >= 2 and (L.get("fx") or L.get("blend", "normal") != "normal"):
            ops = ",".join(f["op"] for f in L.get("fx", [])) or L.get("blend")
            out.append((L["t0"], f"{L['id']}: graphic {seg['graphic']} footage under {ops}"))
    return out


@rule("untreated-once", "ERROR", "Testimony is shown once; a death shown twice becomes a motif.")
def r_once(P):
    seen = {}
    for L in P.L:
        if P.untreated(L):
            m = L["meta"]
            seen.setdefault(f"{m['catalog']}:{m['clip']}", []).append(L["t0"])
    out = []
    for k, ts in seen.items():
        ts.sort()
        if ts[-1] - ts[0] > 60:
            out.append((ts[0], f"{k} untreated at {', '.join(P.where(t) for t in ts)}"))
    return out


@rule("nothing-over-the-dead", "ERROR", "ember caught a strike fading in over the MEE remains at bar 179: \"distasteful\".")
def r_over(P):
    out = []
    idx = {id(L): i for i, L in enumerate(P.L)}
    unt = [L for L in P.L if P.untreated(L)]
    for U in unt:
        for L in P.L:
            if L is U or P.untreated(L) or L.get("id") == "meine" or P.speaker(L) or P.text(L) or P.head(L):
                continue
            if overlap(L, U["t0"], U["t1"]) and idx[id(L)] > idx[id(U)] and \
                    P.visible(L, max(L["t0"], U["t0"]), min(L["t1"], U["t1"])):
                out.append((max(L["t0"], U["t0"]), f"{L['id']} over {U['id']}"))
    return out


@rule("hyde-off-the-dead", "ERROR", "His comic register over the dead reads as mockery; the real speakers are the indictment.")
def r_hyde(P):
    out = []
    for U in (L for L in P.L if P.untreated(L)):
        clip, seg = P.seg(U)
        if not seg or seg.get("graphic", 0) < 2:
            continue
        for H in (L for L in P.L if P.head(L) and overlap(L, U["t0"], U["t1"], 0.3)):
            if P.visible(H, U["t0"] + 0.3, U["t1"] - 0.3):
                out.append((max(H["t0"], U["t0"]), f"{H['id']} over {U['id']}"))
    return out


@rule("speakers-plain-over-the-dead", "ERROR", 'ember wants speakers over the dead ("those people caused **this** to happen to *these people*"), without comic machinery.')
def r_speakers_plain(P):
    out = []
    unt = [U for U in P.L if P.untreated(U) and (P.seg(U)[1] or {}).get("graphic", 0) >= 2]
    for S in (L for L in P.L if P.speaker(L)):
        bad = [f["op"] for f in S.get("fx", []) if f["op"] in COMIC_FX]
        if bad and any(overlap(S, U["t0"], U["t1"], 0.3) for U in unt):
            out.append((S["t0"], f"{S['id']}: {','.join(bad)} while over the dead"))
    return out


@rule("speakers-named", "ERROR", "Real speakers are named and dated on screen; that line separates documentary from satire.")
def r_named(P):
    texts = [L for L in P.L if P.text(L)]
    out, first = [], {}
    for S in sorted((L for L in P.L if P.speaker(L) and "audio" in L), key=lambda L: L["t0"]):
        who = S.get("meta", {}).get("clip") or S.get("meta", {}).get("person") or S["id"]
        person = who.split("__")[0]
        if person in first:
            continue
        first[person] = S["t0"]
        if not any(T["t0"] < S["t0"] + 2.0 and T["t1"] > S["t0"] - 0.5 for T in texts):
            out.append((S["t0"], f"{S['id']}: no lower-third near its first appearance"))
    return out


@rule("hits-on-grid", "ERROR", 'ember: "it\'s important to the integrity of the piece that video motion ends up timed to the music."')
def r_grid(P):
    out = []
    for L in P.L:
        for h in L.get("meta", {}).get("hits_song", []):
            pos = P.music.beat_pos(h)
            err = abs(pos * 4 - round(pos * 4)) / 4 * P.period
            if err > GRID_TOL:
                out.append((h, f"{L['id']}: hit {err * 1000:.0f} ms off the 16th grid"))
    return out


@rule("repeats", "WARN", 'ember: "some of the footage that plays during the car scenes seems repeated?"')
def r_repeats(P):
    by = {}
    for L in P.L:
        T, m = L.get("time", {}), L.get("meta", {})
        if P.footage(L) and "in" in T and isinstance(T.get("speed", 1.0), (int, float)):
            a = T["in"] + (L["t1"] - L["t0"]) * T.get("speed", 1.0)
            by.setdefault(m["clip"], []).append((L["t0"], min(T["in"], a), max(T["in"], a)))
    out = []
    for clip, v in by.items():
        if clip in REPEAT_ALLOW:
            continue
        for i in range(len(v)):
            for j in range(i + 1, len(v)):
                if min(v[i][2], v[j][2]) - max(v[i][1], v[j][1]) > 0.5:
                    out.append((v[j][0], f"{clip}: also at {P.where(v[i][0])}"))
    return out


@rule("dips-match-holds", "WARN", 'ember: "many of the music ducks are too deep/stark, that don\'t linger on a scene for a good long while."')
def r_dips(P):
    g = P.tl["music"].get("gain", 1.0)
    if isinstance(g, (int, float)):
        return []
    f, dt = compile_signal(g, P.ctx), 0.05
    r0, r1 = P.tl["range"][0], min(P.tl["range"][1], 473.5)
    out, t, bar = [], r0, 4 * P.period
    while t < r1:
        if f(t) < 0.5:
            a, low = t, f(t)
            while t < r1 and f(t) < 0.95:
                low, t = min(low, f(t)), t + dt
            held = t - a
            if held < 4 * bar and low < 0.45:
                out.append((a, f"music dips to {low:.2f} for {held / bar:.1f} bars (holds under 4 bars stay >= 0.5)"))
        t += dt
    return out


@rule("untreated-lingers", "WARN", 'ember: "the scenes at/around bar 172 ... are too abrupt and don\'t hit because they move on too fast."')
def r_linger(P):
    bar = 4 * P.period
    spans = sorted((L["t0"], L["t1"], L["id"]) for L in P.L if P.untreated(L))
    merged = []   # back-to-back untreated shots are one moment
    for a, b, i in spans:
        if merged and a <= merged[-1][1] + 0.3:
            merged[-1] = (merged[-1][0], max(b, merged[-1][1]), merged[-1][2])
        else:
            merged.append((a, b, i))
    return [(a, f"{i}: {(b - a) / bar:.1f} bars") for a, b, i in merged if (b - a) < 2 * bar - 0.2]


@rule("grain", "WARN", 'ember: "we should calm down on the \'full-scene noise\' a bit!"')
def r_grain(P):
    out = []
    for f in P.tl.get("post", []):
        amt = f.get("amount", 1.0)
        if f.get("op") == "noise" and isinstance(amt, (int, float)) and amt > 0.04:
            out.append((0.0, f"post noise at {amt}"))
    return out


@rule("captions", "WARN", "Burned-in captions and logos leaked repeatedly; captioned clips need a crop.")
def r_captions(P):
    return [(L["t0"], f"{L['id']}: catalog marks overlay_ok false and the layer has no crop")
            for L in P.L if P.footage(L) and P.seg(L)[1].get("overlay_ok", True) is False and not L.get("crop")]


@rule("letterbox", "WARN", "Footage stays inside Meine's picture; only heads cross the bars.")
def r_letterbox(P):
    return [(L["t0"], f"{L['id']}: fit {L.get('fit', 'cover')} without clip") for L in P.L
            if P.footage(L) and not L.get("clip") and L.get("fit", "cover") in ("cover", "picture") and not L.get("size")]


@rule("subtitled", "WARN", "Speech not in English needs a faithful subtitle.")
def r_subs(P):
    subs = [L for L in P.L if "subtitle" in L.get("tags", [])]
    return [(S["t0"], f"{S['id']}: {S['meta'].get('lang')} speech without subtitles") for S in P.L
            if P.speaker(S) and S.get("meta", {}).get("lang", "en") != "en"
            and not any(overlap(T, S["t0"], S["t1"]) for T in subs)]


def info_sections(P):
    ident, g3, listen = [], [], []
    for L in P.L:
        clip, seg = P.seg(L)
        if not seg:
            continue
        if seg.get("identifiable_victims"):
            ident.append((L["t0"], f"{clip['id']}: {seg.get('desc', '')[:80]}"))
        if seg.get("graphic", 0) >= 3:
            g3.append((L["t0"], f"{clip['id']}: {seg.get('desc', '')[:80]}"))
        if P.untreated(L) and L.get("audio", {}).get("gain", 1) > 0 and \
                not any(k in (clip.get("publisher", "") + clip.get("provenance", "")).lower()
                        for k in ("raw", "shotlist", "shot list", "unedited", "natural sound")):
            listen.append((L["t0"], f"{clip['id']} ({clip.get('publisher', '?')})"))
    return [("sensitivity review: identifiable victims", ident),
            ("sensitivity review: graphic 3", g3),
            ("listen list: untreated sound from produced sources (check for music beds)", listen)]


def check(tl, strict=False, quiet=False):
    P = Piece(tl)
    errors = warns = 0
    lines = []
    for rid, sev, why, f in RULES:
        hits = sorted(f(P), key=lambda x: x[0])
        if not hits:
            continue
        errors += sev == "ERROR" and len(hits)
        warns += sev == "WARN" and len(hits)
        lines.append(f"\n{sev} {rid} ({len(hits)})  {why}")
        lines += [f"  {P.where(t)}  {msg}" for t, msg in hits[:12]]
        if len(hits) > 12:
            lines.append(f"  ... and {len(hits) - 12} more")
    for title, items in info_sections(P):
        if items:
            lines.append(f"\nINFO {title} ({len(items)})")
            lines += [f"  {P.where(t)}  {msg}" for t, msg in sorted(items)[:40]]
    if not quiet:
        print(f"DRC {P.path.name}: {errors} errors, {warns} warnings", *lines, sep="\n")
    return errors + (warns if strict else 0)


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    sys.exit(1 if check(args[0], strict="--strict" in sys.argv) else 0)
