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
  "time": {"in": 10.2, "speed": 1.0},     // source time at t0, playback speed (< 0 plays backwards)
       // or {"in": 10.2, "speed": 1.0, "loop": [a, b]}  wrap source time into [a, b)
       // or {"map": {"song": [...], "src": [...]}}       piecewise-linear song->source
       // or {"hold": 12.0}                               freeze frame
       // or {"in": 10.2, "speed": SIGNAL}                speed as any signal, integrated (ramps, surges)
       // or {"seq": [PIECE, ...]}                        stutter / freeze / ramp / reverse pieces
       //    (see "Time ops" below)
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
  "audio": {"gain": 0.8},                 // omit = silent. Any time form; see "Audio" below
  "meta": {"catalog": "ground", "clip": "id", "seg": 3, "hits_song": [97.5]}   // for the viewer
}
```

## Time ops

The frame shown at song time t is the latest source frame with timestamp <= src(t) (never early),
for every form. Hit times in the catalogs are frame timestamps, so a piece that starts at or holds
source time h shows exactly the hit frame.

`seq` pieces play back to back from `t0`; durations are **song** seconds. Past the last piece the
layer continues at that piece's final speed (a hold keeps holding).

| piece | meaning |
|---|---|
| `{"dur": d, "in": s, "speed": v}` | play from source `s` at speed `v` (negative = backwards, 0 = still) |
| `{"dur": d, "hold": s}` | freeze on the frame showing at source `s` (audio silent) |
| `{"dur": d, "in": s, "speed": [v0, v1], "ease": "linear"\|"smooth"}` | speed ramp v0 -> v1 over the piece (source covered = d * mean speed) |
| `{"dur": d, "in": s, "speed": v, "repeat": n, "every": e}` | stutter: n triggers `e` song s apart, each playing `d` from `s`; between triggers the slice's last frame holds; the last trigger plays its full `d` |

Recipes (comp.py builds all of these on the real beat grid, which is not perfectly even, so its
helpers write one piece per trigger rather than `repeat`):

```jsonc
// strike flash 3x on eighths, then on:  play/hold pairs per eighth, then a long play
{"seq": [{"dur": 0.16, "in": 49.08, "speed": 1}, {"dur": 0.078, "hold": 49.24},
         {"dur": 0.16, "in": 49.08, "speed": 1}, {"dur": 0.078, "hold": 49.24},
         {"dur": 1.2,  "in": 49.08, "speed": 1}]}
// freeze on a hit for 2 beats, then continue
{"seq": [{"dur": 1.0, "in": 7.72, "speed": 1}, {"dur": 0.952, "hold": 8.72}, {"dur": 1.5, "in": 8.72, "speed": 1}]}
// slow-mo into an impact (ends exactly on the hit at the end of the ramp)
{"seq": [{"dur": 1.904, "in": 71.43, "speed": [1.0, 0.3], "ease": "smooth"}, {"dur": 1.5, "in": 72.62, "speed": 0.3}]}
// reverse: {"in": 12.0, "speed": -1}      surge on every beat: {"in": 3.0, "speed": {"range": [0.4, 2.2], "of": {"beat": {"div": 1}}}}
```

Several hits of one segment on chosen beats (multi-hit) use `map`; a phase-locked groove (one
motion cycle per musical length) is a `map` with one knot per cycle on the beat grid.

**Decoding**: forward playback streams; source spans a layer plays backwards or revisits (reverse,
stutter slices, a play that re-crosses a stuttered slice) are decoded once into a per-process
cache (`media.SPANS`, LRU, `$VIDBOX_SPAN_CACHE_MB` default 512; a span over half the cap streams).

## Audio

`"audio": {"gain": 1.0, "mode": "tempo", "fade": 0.006}`. The music and every audio layer are mixed
on the song clock (the music track aligns with the picture to ~1 ms; layer audio is sample-exact).

- Constant-speed layers (`in`/`speed` > 0, no loop) stream through ffmpeg (atempo for speed != 1).
- Every other form follows the layer's time map sample by sample, exactly like its frames:
  speed +-1 copies (backwards for reverse); other constant speeds keep pitch (atempo) unless
  `"mode": "tape"`; ramps and speed signals are tape (pitch follows speed); holds are silent.
- Every audio edge (layer start/end, stutter retriggers, cuts into or out of holds) gets a
  `fade` (default 6 ms) so nothing clicks; continuous joins between pieces of different speed
  (map knots) crossfade over +-5 ms.

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
