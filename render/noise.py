"""Animated fractal noise (in the spirit of Blender's Noise Texture), cheap enough per frame.

Each octave is a coarse random lattice upsampled with bicubic interpolation (smooth value
noise); time crossfades between lattices and drifts them, so the field both boils and flows.
"""
from functools import lru_cache

import cv2
import numpy as np


TABLE = 256   # lattice period in cells


@lru_cache(maxsize=256)
def _table(seed, octave, k):
    return np.random.default_rng((seed, octave, k)).random((TABLE, TABLE), dtype=np.float32)


def _lattice(seed, octave, k, cy, cx, gh, gw):
    """gh x gw window of an endless (periodic) lattice, starting at cell (cy, cx)."""
    T = _table(seed, octave, k)
    return T[np.ix_((cy + np.arange(gh)) % TABLE, (cx + np.arange(gw)) % TABLE)]


def fbm(h, w, t, scale=200.0, octaves=4, speed=0.3, seed=0, lacunarity=2.0, gain=0.5, clock=None):
    """Noise field in [0, 1], shape (h, w). scale = feature size of the first octave in px.
    clock: if given, the first octave's cycle count (replaces t * speed; see fx.cycles), and
    octave o runs at 2**o times it, so every octave's crossfades complete on the beat grid."""
    out = np.zeros((h, w), np.float32)
    amp, total = 1.0, 0.0
    for o in range(int(octaves)):
        s = max(2.0, scale / lacunarity ** o)
        gh, gw = int(h / s) + 4, int(w / s) + 4
        tt = t * speed * (1 + 0.37 * o) if clock is None else clock * 2 ** o
        k = int(np.floor(tt))
        f = tt - k
        f = f * f * (3 - 2 * f)
        # drift: each octave slides continuously in its own direction (whole cells move the
        # lattice window, the remainder shifts the upsampled crop)
        ang = 2.4 * o + seed
        Dx, Dy = np.cos(ang) * tt * s * 0.5, np.sin(ang) * tt * s * 0.5
        cx, cy = int(np.floor(Dx / s)), int(np.floor(Dy / s))
        g = (_lattice(seed, o, k, cy, cx, gh, gw) * (1 - f)
             + _lattice(seed, o, k + 1, cy, cx, gh, gw) * f)
        # crossfading two independent lattices lowers contrast mid-way; restore it
        g = (g - 0.5) / np.sqrt((1 - f) ** 2 + f ** 2) + 0.5
        up = cv2.resize(g, (int(gw * s), int(gh * s)), interpolation=cv2.INTER_CUBIC)
        dx, dy = int(Dx - cx * s), int(Dy - cy * s)
        out += amp * up[dy:dy + h, dx:dx + w]
        total += amp
        amp *= gain
    out /= total
    # value noise clusters near 0.5; stretch it to use the range
    return np.clip((out - 0.5) * 2.2 + 0.5, 0, 1)
