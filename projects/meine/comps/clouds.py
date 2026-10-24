"""Head clouds sample from everyone who has spoken so far (ember: "any time there is any 'head cloud',
we should be sampling from all the heads that have already spoken thus far in the video. Instead of
just swarms of Hyde. (but Hyde should still be in there for about 1/3rd of the total faces)").

mix_clouds(layers, root): only SILENT Hyde copies that are part of a cloud (at least 3 other silent
copies on screen at the same moment) change; a lone head stays Hyde (ember caught the re-emerging
preacher at bar 120 turned into an unreadable Haley window). Only speakers who appeared as
face-tracked ovals are drawn from. Each swapped copy silently loops one of that speaker's own lines.
"""
import subprocess

HYDE = {"media/derived/face.mp4", "media/derived/face_rant2.mp4", "media/derived/face_missiles_on_beat.mp4"}
SPEAKERS = ("preachers", "israeli_voices")


def _dur(root, src, _cache={}):
    if src not in _cache:
        out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                              str(root / src)], capture_output=True, text=True).stdout
        _cache[src] = float(out or 0)
    return _cache[src]


def mix_clouds(layers, root):
    heard = {}   # person -> (first song time heard, [their face-tracked clips])
    for L in sorted(layers, key=lambda L: L["t0"]):
        m = L.get("meta", {})
        if m.get("catalog") in SPEAKERS and "audio" in L and L.get("mask", {}).get("shape") == "oval":
            person = str(m.get("clip", L["id"])).split("__")[0]
            first, clips = heard.setdefault(person, (L["t0"], []))
            if L["src"] not in clips:
                clips.append(L["src"])
    silent = [L for L in layers if L["src"] in HYDE and "audio" not in L and L.get("size") == [480, 600]]

    def in_cloud(L):
        mid = (L["t0"] + L["t1"]) / 2
        return sum(1 for o in silent if o is not L and o["t0"] <= mid < o["t1"]) >= 3

    copies = sorted((L for L in silent if in_cloud(L)), key=lambda L: (L["t0"], L["id"]))
    swapped = 0
    for i, L in enumerate(copies):
        pool = sorted((p for p, (first, _) in heard.items() if first < L["t0"]), key=lambda p: heard[p][0])
        if i % 3 == 0 or not pool:
            continue   # Hyde keeps about a third of the faces (all of them before anyone else has spoken)
        person = pool[(i - i // 3 - 1) % len(pool)]
        src = heard[person][1][(i // len(pool)) % len(heard[person][1])]
        d = _dur(root, src)
        if d < 1.0:
            continue
        if "hold" in L.get("time", {}):
            L["time"] = {"hold": round(d / 2, 3)}
        else:
            L["time"] = {"in": round((i * 0.37) % (d - 0.2), 3), "speed": 1.0, "loop": [0.05, round(d - 0.05, 3)]}
        L["src"] = src
        L.setdefault("tags", []).append("cloud:" + person)
        swapped += 1
    return swapped, len(copies), len(silent)
