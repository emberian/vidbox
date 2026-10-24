"""Render a timeline (render/TIMELINE.md).

usage: uv run python render/tl.py TIMELINE.json [--full] [--range A B] [--jobs N] [-o OUT]

Default is a half-size preview written next to the timeline as NAME.mp4 (what the studio's
timeline viewer plays); --full renders 1:1 to NAME.full.mp4. --jobs splits the range into
chunks rendered in parallel processes (each with a short pre-roll so trails settle).
"""
import argparse
import json
import math
import os
import subprocess
import sys
import tempfile
import time as wall
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import fx as FX  # noqa: E402
from media import Reader  # noqa: E402
from signals import Ctx, Music, compile_signal  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
PICTURE = (0, 158, 1440, 922)   # Meine's letterboxed picture area (canvas px)
LENGTH_PARAMS = {"px", "scale", "period"}   # fx params in canvas px: scaled with the preview
PREROLL = 1.0


def probe(src):
    out = json.loads(subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
         "stream=width,height,avg_frame_rate", "-of", "json", str(src)],
        capture_output=True, text=True, check=True).stdout)["streams"][0]
    num, den = (int(x) for x in out["avg_frame_rate"].split("/"))
    return out["width"], out["height"], num / den


_mask_cache = {}


def mask(spec, w, h):
    if not spec:
        return None
    key = (spec.get("shape"), spec.get("feather", 0.2), w, h)
    if key not in _mask_cache:
        y, x = np.mgrid[0:h, 0:w].astype(np.float32) + 0.5
        f = max(spec.get("feather", 0.2), 1e-3)
        if spec["shape"] == "oval":
            r = np.hypot((x - w / 2) / (w / 2), (y - h / 2) / (h / 2))
            m = np.clip((1 - r) / f, 0, 1)
        elif spec["shape"] == "rect":
            dx = np.minimum(x, w - x) / (w / 2)
            dy = np.minimum(y, h - y) / (h / 2)
            m = np.clip(np.minimum(dx, dy) / f, 0, 1)
        else:
            raise ValueError(f"mask shape {spec['shape']!r}")
        if len(_mask_cache) > 64:
            _mask_cache.clear()
        _mask_cache[key] = m.astype(np.float32)
    return _mask_cache[key]


BLENDS = {
    "normal": lambda b, l: l,
    "screen": lambda b, l: 1 - (1 - b) * (1 - l),
    "add": lambda b, l: np.minimum(1, b + l),
    "multiply": lambda b, l: b * l,
    "difference": lambda b, l: np.abs(b - l),
    "lighten": np.maximum,
    "darken": np.minimum,
    "overlay": lambda b, l: np.where(b < 0.5, 2 * b * l, 1 - 2 * (1 - b) * (1 - l)),
}


def composite(canvas, img, alpha, cx, cy, rot, mode):
    H, W = canvas.shape[:2]
    h, w = img.shape[:2]
    blend = BLENDS[mode]
    if rot == 0 and w * h > 0.6 * W * H:   # big layer: integer placement is fine
        x0, y0 = int(round(cx - w / 2)), int(round(cy - h / 2))
        L, A = img, alpha
    else:   # small or rotated: sub-pixel, rotated warp into its bounding box
        th = math.radians(rot)
        c, s = math.cos(th), math.sin(th)
        bw, bh = abs(w * c) + abs(h * s), abs(w * s) + abs(h * c)
        x0, y0 = int(math.floor(cx - bw / 2)), int(math.floor(cy - bh / 2))
        bw_i, bh_i = int(math.ceil(bw)) + 2, int(math.ceil(bh)) + 2
        # layer px -> bbox px: rotate about the layer centre, place centre at (cx, cy)
        M = np.float32([[c, s, 0], [-s, c, 0]])
        M[:, 2] = np.array([cx - x0, cy - y0]) - M[:, :2] @ np.array([w / 2, h / 2])
        L = cv2.warpAffine(img, M, (bw_i, bh_i), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
        A = cv2.warpAffine(alpha, M, (bw_i, bh_i), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    h, w = L.shape[:2]
    sx0, sy0 = max(0, -x0), max(0, -y0)
    dx0, dy0, dx1, dy1 = max(0, x0), max(0, y0), min(W, x0 + w), min(H, y0 + h)
    if dx1 <= dx0 or dy1 <= dy0:
        return
    Ls = L[sy0:sy0 + dy1 - dy0, sx0:sx0 + dx1 - dx0]
    As = A[sy0:sy0 + dy1 - dy0, sx0:sx0 + dx1 - dx0, None]
    base = canvas[dy0:dy1, dx0:dx1]
    base += (blend(base, Ls) - base) * As


class Params:
    """Compiled-signal cache. Keys are tuples ending in the parameter name."""

    def __init__(self, ctx, k):
        self.ctx, self.k, self._sig = ctx, k, {}

    def sig(self, key, spec, default):
        if key not in self._sig:
            self._sig[key] = compile_signal(spec if spec is not None else default, self.ctx)
        return self._sig[key]

    def param(self, spec, key, t):
        """Evaluate an fx param; strings and colour triples pass through as constants."""
        if isinstance(spec, str) or (isinstance(spec, list) and len(spec) != 2):
            return spec
        v = self.sig(key, spec, None)(t)
        return v * self.k if key[-1] in LENGTH_PARAMS else v

    def run_fx(self, fx_list, img, alpha, t, state, scope):
        return FX.apply(fx_list, img, alpha, t, state, lambda spec, key: self.param(spec, (scope,) + key, t))


class Layer(Params):
    def __init__(self, spec, ctx, W, H, k, fps):
        super().__init__(ctx, k)
        self.s = spec
        self.id = spec.get("id", "?")
        self.t0, self.t1 = spec["t0"], spec["t1"]
        self.src = ROOT / spec["src"]
        self.reader, self.state = None, {}
        sw, sh, self.src_fps = probe(self.src)
        crop = spec.get("crop")
        if crop:
            sw, sh = sw * (crop[2] - crop[0]), sh * (crop[3] - crop[1])
        self.native = (sw, sh)
        if "size" in spec:
            bw, bh = spec["size"]
        else:
            fit = spec.get("fit", "cover")
            if fit == "native":
                f = 1.0
            elif fit == "contain":
                f = min(W / sw, H / sh)
            elif fit == "picture":
                f = max((PICTURE[2] - PICTURE[0]) / sw, (PICTURE[3] - PICTURE[1]) / sh)
            else:
                f = max(W / sw, H / sh)
            bw, bh = sw * f, sh * f
        self.base = (bw * k, bh * k)
        T = spec.get("time", {"in": 0.0, "speed": 1.0})
        if "map" in T:
            song, src = T["map"]["song"], T["map"]["src"]
            self.src_time = lambda t: float(np.interp(t, song, src))
        elif "hold" in T:
            self.src_time = lambda t: T["hold"]
        else:
            tin, sp, loop = T.get("in", 0.0), T.get("speed", 1.0), T.get("loop")
            if loop:
                a, b = loop
                self.src_time = lambda t: a + ((tin - a) + (t - self.t0) * sp) % (b - a)
            else:
                self.src_time = lambda t: tin + (t - self.t0) * sp
        fade = spec.get("fade", {})
        self.fin, self.fout = fade.get("in", 0.0), fade.get("out", 0.0)

    def open(self, t0, t1):
        # decode at the largest size this layer reaches (but never above the source's own)
        scales = [self.sig("scale", self.s.get("scale"), 1)(t) for t in np.linspace(t0, t1, 24)]
        smax = max(1e-3, max(abs(x) for x in scales))
        w, h = self.base[0] * smax, self.base[1] * smax
        f = min(1.0, self.native[0] / w, self.native[1] / h)
        size = (max(2, int(w * f)) // 2 * 2, max(2, int(h * f)) // 2 * 2)
        self.reader = Reader(self.src, self.s.get("crop"), size)

    def close(self):
        if self.reader:
            self.reader.close()
            self.reader = None

    def draw(self, canvas, t):
        s = self.s
        op = self.sig("opacity", s.get("opacity"), 1)(t)
        if self.fin > 0:
            op *= min(1.0, (t - self.t0) / self.fin)
        if self.fout > 0:
            op *= min(1.0, (self.t1 - t) / self.fout)
        sc = self.sig("scale", s.get("scale"), 1)(t)
        if op <= 0.002 or sc <= 0.002:
            return
        frame = self.reader.get(self.src_time(t))
        dw, dh = max(2, int(round(self.base[0] * sc))), max(2, int(round(self.base[1] * sc)))
        interp = cv2.INTER_AREA if dw < frame.shape[1] else cv2.INTER_LINEAR
        img = cv2.resize(frame, (dw, dh), interpolation=interp).astype(np.float32) * (1 / 255)
        m = mask(s.get("mask"), dw, dh)
        alpha = (m.copy() if m is not None else np.ones((dh, dw), np.float32)) * op
        if s.get("fx"):
            img, alpha = self.run_fx(s["fx"], img, alpha, t, self.state, "fx")
        H, W = canvas.shape[:2]
        pos = self.sig("pos", s.get("pos"), [W / self.k / 2, H / self.k / 2])(t)
        rot = self.sig("rot", s.get("rot"), 0)(t)
        composite(canvas, img, alpha, pos[0] * self.k, pos[1] * self.k, rot, s.get("blend", "normal"))


def render_video(tl, frames, k, out, ctx, warm=0):
    """Render frame indices `frames` (song frame numbers); the first `warm` are pre-roll."""
    W, H = (int(tl["size"][0] * k) // 2 * 2, int(tl["size"][1] * k) // 2 * 2)
    fps = tl["fps"]
    layers = [Layer(L, ctx, *tl["size"], k, fps) for L in tl["layers"]]
    post = Params(ctx, k) if tl.get("post") else None
    enc = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(fps),
         "-i", "-", "-c:v", "libx264", "-crf", "17" if k == 1 else "22", "-preset", "medium" if k == 1 else "veryfast",
         "-pix_fmt", "yuv420p", "-an", str(out)],
        stdin=subprocess.PIPE)
    post_state = {}
    t_start = wall.time()
    for j, fno in enumerate(frames):
        t = fno / fps
        canvas = np.zeros((H, W, 3), np.float32)
        for L in layers:
            if L.t0 <= t < L.t1:
                if L.reader is None:
                    L.open(t, L.t1)
                L.draw(canvas, t)
            elif L.reader is not None and t >= L.t1:
                L.close()
        if post:
            ones = np.ones((H, W), np.float32)
            canvas, _ = post.run_fx(tl["post"], canvas, ones, t, post_state, "post")
        if j >= warm:
            enc.stdin.write((np.clip(canvas, 0, 1) * 255 + 0.5).astype(np.uint8).tobytes())
        if j % 50 == 0 and j:
            el = wall.time() - t_start
            print(f"\r  {out.name}: {j}/{len(frames)} {j / el:.1f} fps", end="", file=sys.stderr)
    enc.stdin.close()
    enc.wait()
    for L in layers:
        L.close()
    print(file=sys.stderr)
    return enc.returncode


def mux_audio(tl, video, out, r0, r1):
    ins = ["-i", str(video), "-ss", f"{r0:.4f}", "-i", str(ROOT / tl["music"]["src"])]
    chains = [f"[1:a]volume={tl['music'].get('gain', 1.0)}[a0]"]
    n = 1
    for L in tl["layers"]:
        if "audio" not in L or L["t1"] <= r0 or L["t0"] >= r1:
            continue
        T = L.get("time", {"in": 0.0, "speed": 1.0})
        if "map" in T or "hold" in T or "loop" in T:
            print(f"  audio skipped for {L.get('id')}: only constant-speed layers carry audio", file=sys.stderr)
            continue
        sp = T.get("speed", 1.0)
        start = max(L["t0"], r0)
        sin = T.get("in", 0.0) + (start - L["t0"]) * sp
        dur = (min(L["t1"], r1) - start) * sp
        ins += ["-ss", f"{sin:.4f}", "-t", f"{dur:.4f}", "-i", str(ROOT / L["src"])]
        tempo, f = [], sp
        while f > 2.0:
            tempo.append("atempo=2.0"); f /= 2
        while f < 0.5:
            tempo.append("atempo=0.5"); f /= 0.5
        if abs(f - 1) > 1e-3:
            tempo.append(f"atempo={f:.5f}")
        chain = ",".join(tempo + [f"adelay={int((start - r0) * 1000)}:all=1", f"volume={L['audio'].get('gain', 1.0)}"])
        chains.append(f"[{n + 1}:a]{chain}[a{n}]")
        n += 1
    graph = ";".join(chains) + ";" + "".join(f"[a{i}]" for i in range(n)) + \
        f"amix=inputs={n}:normalize=0:duration=first,alimiter=limit=0.95[aout]"
    subprocess.run(["ffmpeg", "-v", "error", "-y", *ins, "-filter_complex", graph, "-map", "0:v", "-map", "[aout]",
                    "-t", f"{r1 - r0:.4f}", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart",
                    str(out)], check=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("timeline")
    ap.add_argument("--full", action="store_true")
    ap.add_argument("--range", nargs=2, type=float)
    ap.add_argument("--jobs", type=int, default=1)
    ap.add_argument("-o", "--out")
    ap.add_argument("--chunk", help=argparse.SUPPRESS)   # internal: "a b warm out" frame range
    a = ap.parse_args()

    tl_path = Path(a.timeline).resolve()
    tl = json.loads(tl_path.read_text())
    pdir = ROOT / "projects" / tl["project"]
    ctx = Ctx(Music(pdir / "analysis/beats.json"), pdir)
    k = 1.0 if a.full else 0.5
    fps = tl["fps"]

    if a.chunk:
        f0, f1, warm, out = a.chunk.split()
        sys.exit(render_video(tl, range(int(f0), int(f1)), k, Path(out), ctx, int(warm)))

    r0, r1 = a.range or tl["range"]
    base = tl_path.name.removesuffix(".timeline.json").removesuffix(".json")
    out = Path(a.out) if a.out else tl_path.parent / f"{base}{'.full' if a.full else ''}.mp4"
    F0, F1 = round(r0 * fps), round(r1 * fps)
    t_wall = wall.time()
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        jobs = max(1, min(a.jobs, (F1 - F0) // (fps * 4) or 1))
        bounds = np.linspace(F0, F1, jobs + 1).round().astype(int)
        procs, parts = [], []
        for i in range(jobs):
            s, e = int(bounds[i]), int(bounds[i + 1])
            warm = int(PREROLL * fps) if i > 0 else 0
            part = tmp / f"part{i:03d}.mp4"
            parts.append(part)
            procs.append(subprocess.Popen([sys.executable, __file__, str(tl_path), *(["--full"] if a.full else []),
                                           "--chunk", f"{s - warm} {e} {warm} {part}"]))
        codes = [p.wait() for p in procs]
        if any(codes):
            sys.exit(f"chunk render failed: {codes}")
        (tmp / "list.txt").write_text("".join(f"file '{p}'\n" for p in parts))
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", tmp / "list.txt",
                        "-c", "copy", tmp / "video.mp4"], check=True)
        mux_audio(tl, tmp / "video.mp4", out, r0, r1)
    print(f"wrote {out} ({r1 - r0:.1f}s of song) in {wall.time() - t_wall:.1f}s with {jobs} job(s)",
          file=sys.stderr)


if __name__ == "__main__":
    main()
