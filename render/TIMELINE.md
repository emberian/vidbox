# Timeline format (v1)

A timeline is the render input: JSON written by a composition script (`projects/<p>/comps/*.py`,
using `render/comp.py`), rendered by `render/tl.py`, viewed in `studio/timeline.html`.
All times are **song seconds** (Meine's clock). Paths are repo-relative unless noted.

```jsonc
{
  "version": 1,
  "project": "meine",
  "size": [1440, 1080], "fps": 25,
  "range": [0, 473.5],                    // song time span this timeline renders
  "music": {"src": "media/src/meine.webm", "gain": 1.0},
  "layers": [ /* bottom first */ ],
  "post": [ /* fx applied to the finished frame */ ]
}
```

## Layer

```jsonc
{
  "id": "strike-07", "tags": ["ground", "strike"],   // tags are free-form (viewer groups by them)
  "src": "media/footage/ground/raw/x.mp4",
  "t0": 96.3, "t1": 99.8,                 // active song-time span
  "time": {"in": 10.2, "speed": 1.0},     // source time at t0, playback speed
       // or {"in": 10.2, "speed": 1.0, "loop": [a, b]}  wrap source time into [a, b)
       // or {"map": {"song": [...], "src": [...]}}       piecewise-linear song->source
       // or {"hold": 12.0}                               freeze frame
  "fit": "cover",                         // base size: cover | contain | picture (cover Meine's
                                          // letterboxed picture area) | native
  "size": [480, 600],                     // explicit base size in canvas px (overrides fit)
  "crop": [0, 0, 1, 0.9],                 // normalized source crop x0 y0 x1 y1 (e.g. drop a logo)
  "pos": [720, 540],                      // vector signal: layer center in canvas px
  "scale": 1, "rot": 0, "opacity": 1,     // signals; rot in degrees
  "blend": "normal",                      // normal screen add multiply difference lighten darken overlay
  "mask": {"shape": "oval", "feather": 0.28},   // or {"shape": "rect", "feather": 0.05}; omit = none
  "fade": {"in": 0.2, "out": 0.5},        // seconds, multiplies opacity
  "fx": [ {"op": "posterize", "levels": 4} ],   // applied to the layer image, in order
  "audio": {"gain": 0.8},                 // omit = silent. constant speed or map-free layers only
  "meta": {"catalog": "ground", "clip": "id", "seg": 3, "hits_song": [97.5]}   // for the viewer
}
```

## Signals

Any numeric parameter (layer props and fx params) may be a **signal**, evaluated per frame at song time t:

| form | meaning |
|---|---|
| `0.7` | constant |
| `{"k": [[t, v], ...], "ease": "linear"\|"smooth"\|"hold"}` | keyframes (v may be a number or [x, y]) |
| `{"dense": {"t0": s, "dt": s, "v": [...]}}` | sampled values (numbers or [x, y]), linear between |
| `{"path": "paths/face_self_gaze.json"}` | vector: Bezier path position (project-relative) |
| `{"pathscale": "paths/face_self_gaze.json"}` | number: that path's scale channel |
| `{"beat": {"div": 1, "shape": "decay", "tau": 0.12, "width": 0.25, "offset": 0}}` | 0..1 locked to the beat grid. `div` in beats (0.5 = eighths, 4 = bar, 16 = 4 bars), phase 0 on downbeats. shapes: decay (exp, `tau` s), pulse (`width` of the period), saw, ramp (1-saw), sine, tri |
| `{"intensity": {"smooth": 1.0}}` | the song's intensity curve, 0..1 |
| `{"onset": {"tau": 0.15, "min": 0.3}}` | envelope that jumps to each onset's strength (>= min) and decays |
| `{"range": [lo, hi], "of": S}` | lo + (hi - lo) * S |
| `{"add": [S, ...]}`, `{"mul": [S, ...]}` | arithmetic |
| `{"clamp": [lo, hi], "of": S}` | clamp |
| `[Sx, Sy]` | vector from two signals |

## Effects (`fx` / `post`)

Each is `{"op": name, ...params}`; params are signals unless noted. `amount` (default 1) mixes
the effect over its input.

| op | params |
|---|---|
| posterize | levels |
| chroma | px, angle (RGB channel split, px at canvas scale) |
| noise | scale (feature px), octaves, speed, mode (mul\|screen\|add\|overlay\|luma), color ([r,g,b] or "rgb"), seed (const) |
| warp | scale, px (displacement), speed, octaves, seed |
| threshold | level, soft |
| duotone | dark [r,g,b], light [r,g,b] (consts) |
| invert | |
| hue | deg |
| sat | factor |
| contrast | factor (around 0.5), bright (add) |
| levels | black, white, gamma |
| lumakey | low, high: alpha *= smoothstep(low, high, luma). Bright-on-black footage keys itself |
| kaleido | segments (const), angle |
| pixelate | px |
| blur | px |
| scanlines | period, dark |
| echo | decay: trails, out = max(in, prev * decay) (stateful) |
| tint | color [r,g,b] (const), amount |
