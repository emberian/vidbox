"""Frame-exact video decoding on one canonical clock.

Canonical time of a frame = (pts - stream start) * time_base: seconds from the stream's first
frame, the same clock a browser's video.currentTime uses. Catalog hit times, the hit tools and
the renderer all use it. (Inferring frame times from ffmpeg -ss positions is off by 1-2 frames
in ways that vary per file; every frame here carries its own timestamp instead.)
"""
import os
from bisect import bisect_right
from collections import OrderedDict, deque

import av
import cv2
import numpy as np


class Decoder:
    def __init__(self, src):
        self.c = av.open(str(src))
        self.s = self.c.streams.video[0]
        self.s.thread_type = "AUTO"
        self.tb = self.s.time_base
        self.st = self.s.start_time or 0
        self.fps = float(self.s.average_rate or self.s.guessed_rate or 25)
        self.width, self.height = self.s.width, self.s.height

    def frames(self, t_from):
        """(t, av.VideoFrame) from the keyframe at or before t_from onwards."""
        self.c.seek(max(0, int((t_from - 0.25) / self.tb)) + self.st, stream=self.s, backward=True)
        for f in self.c.decode(self.s):
            if f.pts is None:
                continue
            yield float((f.pts - self.st) * self.tb), f

    def close(self):
        self.c.close()


def to_array(f, crop=None, size=None, gray=False):
    a = f.to_ndarray(format="gray" if gray else "rgb24")
    if crop:
        h, w = a.shape[:2]
        x0, y0, x1, y1 = crop
        a = a[int(y0 * h):int(y1 * h), int(x0 * w):int(x1 * w)]
    if size and (a.shape[1], a.shape[0]) != tuple(size):
        interp = cv2.INTER_AREA if size[0] < a.shape[1] else cv2.INTER_LINEAR
        a = cv2.resize(a, tuple(size), interpolation=interp)
    return np.ascontiguousarray(a)


def decode_range(src, t0, t1, size=None, gray=False):
    """[(t, array)] for every frame with t0 <= t <= t1."""
    d = Decoder(src)
    out = []
    for t, f in d.frames(t0):
        if t > t1 + 1e-6:
            break
        if t >= t0 - 1e-6:
            out.append((t, to_array(f, size=size, gray=gray)))
    d.close()
    return out


class SpanCache:
    """Process-wide, size-capped LRU of decoded source spans for revisited material (reverses,
    stutters, repeated slices): key (src, crop, size, a, b) -> (times, frames). Capped at
    $VIDBOX_SPAN_CACHE_MB (default 512) per process; a span larger than half the cap is never
    cached (the Reader's forward path serves it instead)."""

    def __init__(self, cap_mb=None):
        self.cap = int(float(cap_mb if cap_mb is not None else os.environ.get("VIDBOX_SPAN_CACHE_MB", 512)) * 2 ** 20)
        self.d = OrderedDict()
        self.bytes = 0

    def get(self, key):
        v = self.d.get(key)
        if v is not None:
            self.d.move_to_end(key)
        return v

    def fits(self, nbytes):
        return nbytes <= self.cap // 2

    def put(self, key, value, nbytes):
        self.d[key] = (value, nbytes)
        self.bytes += nbytes
        while self.bytes > self.cap and len(self.d) > 1:
            _, (_, nb) = self.d.popitem(last=False)
            self.bytes -= nb


SPANS = SpanCache()


class Reader:
    """Frame shown at time t = the latest frame with timestamp <= t (never early).
    Decodes forward, keeps a short buffer so small backward steps (stutters, loop wraps
    into the recent past) don't re-seek. `spans`: source intervals [(a, b)] that will be
    revisited or played backwards; times inside one are served from SPANS (decoded once, by a
    separate decoder, so the forward position is kept)."""

    def __init__(self, src, crop, size, keep=120, spans=None):
        self.src, self.crop, self.size, self.keep = src, crop, size, keep
        self.d = Decoder(src)
        self.fps = self.d.fps
        self.gen, self.eof = None, False
        self.buf = deque()   # (t, array), increasing t
        self.times = []
        self.spans = sorted(spans or [])
        self.too_big = set()

    def _seek(self, t):
        self.gen = self.d.frames(t)
        self.eof = False
        self.buf.clear()

    def _pull(self):
        try:
            t, f = next(self.gen)
        except StopIteration:
            self.eof = True
            return
        self.buf.append((t, to_array(f, self.crop, self.size)))
        while len(self.buf) > self.keep:
            self.buf.popleft()

    def _span(self, a, b):
        key = (str(self.src), tuple(self.crop) if self.crop else None, tuple(self.size), round(a, 4), round(b, 4))
        hit = SPANS.get(key)
        if hit is not None:
            return hit[0]
        if key in self.too_big:
            return None
        est = (b - a + 2 / self.fps) * self.fps * self.size[0] * self.size[1] * 3
        if not SPANS.fits(est):
            self.too_big.add(key)
            return None
        d = Decoder(self.src)
        times, frames, prev = [], [], None
        for t, f in d.frames(a):
            if t > b + 1e-6:
                break
            if t <= a + 1e-6:
                prev = (t, f)   # the frame showing at a (latest with timestamp <= a)
                continue
            if prev is not None:
                times.append(prev[0]); frames.append(to_array(prev[1], self.crop, self.size)); prev = None
            times.append(t); frames.append(to_array(f, self.crop, self.size))
        if prev is not None:
            times.append(prev[0]); frames.append(to_array(prev[1], self.crop, self.size))
        d.close()
        val = (times, frames)
        SPANS.put(key, val, sum(x.nbytes for x in frames))
        return val

    def get(self, t):
        for a, b in self.spans:
            if a - 1e-6 <= t <= b + 1e-6:
                sp = self._span(a, b)
                if sp is not None and sp[0]:
                    i = bisect_right(sp[0], t + 1e-6) - 1
                    return sp[1][max(i, 0)]
                break
        if self.gen is None or not self.buf or t < self.buf[0][0] - 1e-6 or t > self.buf[-1][0] + 3.0:
            self._seek(t)
        while not self.eof and (not self.buf or self.buf[-1][0] <= t + 1e-6):
            self._pull()
        times = [x[0] for x in self.buf]
        i = bisect_right(times, t + 1e-6) - 1
        if i < 0:   # t precedes the first decodable frame (or the stream is empty)
            if not self.buf:
                return np.zeros((self.size[1], self.size[0], 3), np.uint8)
            i = 0
        return self.buf[i][1]

    def close(self):
        self.d.close()
