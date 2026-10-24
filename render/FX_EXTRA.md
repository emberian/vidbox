# Extra effects (`render/fx_extra.py`)

These ops plug into `fx` / `post` lists the same way as the ones in TIMELINE.md. They are
loaded with `fx.py`, so no import is needed. To see each one in motion on strike-cam, Gaza
ground footage and the preacher's head, open the gallery at
`projects/meine/gallery/out/index.html`. Rebuild it with
`uv run python projects/meine/gallery/make_gallery.py [--only NAME ...]`.

## Conventions

- **Lengths** are in canvas px and are always named `px`, `scale` or `period`, so tl.py
  halves them for previews. Other params are unitless.
- **`center`** is `[x, y]` as a fraction of the layer (`[0.5, 0.5]` is the middle). It is a
  vector signal, so it can move.
- **Colours** are `[r, g, b]` in 0..1. Three-element lists pass through as constants. A
  two-element list is read as a vector signal, so custom palettes need at least 3 stops.
- **Let the music drive the strength.** Defaults are deliberately moderate. Put the energy in
  a signal (`rng(lo, hi, beat(...))`, `onset()`, `intensity()`) rather than in a high constant.
- **Layer space, not screen space.** A layer's fx run on the layer image *before* it is placed
  at `pos`. Trails and time effects therefore show what moves *inside* the clip (mouth,
  smoke, drone motion), not the layer's flight across the screen. To get screen-space trails
  of a bouncing head, put the op in `post`, which also hits the background, so use it lightly
  there.
- **Ops may grow the layer.** `feedback` with `pad` returns a larger image, so its echoes can
  leave the clip's box. Later ops in the same list see the larger image.

## Voronoi is heads only

ember: "do *not* use the voronoi effect on war footage, but it looks AMAZING on the guys face."
`comp.save` raises if `voronoi` is in the fx of a footage layer (any layer with a catalog
link) or in `post`. Use it on the preacher's heads. The gallery has seven face variants.

## Grid clock (the default)

Every internal clock runs on the song's beat grid. tl.py hands each op a `fx.Clock` built on
`signals.Music`, which counts beats since the first downbeat: integers are beats and multiples
of 4 are downbeats. It reaches the op as `p["_clock"]`. Ops read it through `fx.cycles(p, t,
per_sec)` or `fx.grid_index(p, t, per_sec)`:

- **Rates snap to musical units.** An old per-second value (`speed`, `roll`, `hold`, `rate`,
  `every`) is converted to cycles per beat and snapped to the nearest 2^k: 1/64 … 16 per beat.
  For example, noise `speed 0.3` becomes 1/8 per beat (one lattice crossfade per 2 bars),
  glitch `hold 0.08` becomes 1/8 beat, and feedback `every 3` becomes 16ths. Old values still
  mean roughly what they did.
- **`beats`** sets the cycle length in beats explicitly and overrides the snapped rate
  (`beats: 4` = once per bar).
- **Phase 0 is on a downbeat**, so cycles complete on beats, bars and phrases.
- **Evolving textures breathe with the kick.** Motion advances in eased steps: 51% of a step
  in the first 16th after the beat, 80% by mid-beat, settled before the next kick. Lattice
  crossfades complete on beats, and fbm octave o runs at 2^o times octave 0's rate, so every
  octave stays on the grid. `snap` (0..1, default 0.8) sets how stepped this is; 0 gives a
  steady locked rate.
- **Opt out with `clock: "seconds"`.** It restores the old free-running behaviour exactly, for
  any op.

| op | was free-running | now |
|---|---|---|
| noise, warp (fx.py) | fbm boil and drift at `speed`/s, octaves at 1 + 0.37·o | eased steps per beat; `speed` snapped (or `beats`); octaves at 2^o |
| slitscan `axis: noise` | fbm at `speed`/s | as noise. New: `depth_beats` (depth in beats; 1 ≈ 12 frames) |
| voronoi | point orbits at `speed`·0.5/s | eased steps per beat; `beats` overrides |
| vhs | wobble 0.7/s, tracking band 0.23/s over a 1.3 cycle | wobble 1/4 per beat, band one pass per 2 bars (`roll` snapped), launched on a downbeat |
| glitch | new pattern every `hold` s | new pattern every 2^k beat fraction (0.08 s → 1/8 beat), on the grid |
| dither `noise` | pattern at `rate` Hz | pattern on 32nds (`rate` snapped) |
| feedback `every > 1` | stamp every N frames | stamp on grid steps (`every 3` → 16ths), or one per `beats` |
| flowmosh | refresh only from your signal | also a built-in clean I-frame every `iframe` beats (default 2; 0 = off). This also makes seams exact by default |
| shock | `phase` default 0 (static) | with no `phase` given: a wave per `beats` (default 1), launched on the beat |
| gradmap | `cycle` only from your signal | optional `beats`: built-in palette turn per `beats`, stepping on the kicks |
| chromatime | `delay` in frames | still frames; new `delay_beats` (0.25 = a 16th) |
| feedback `every = 1`, echo, kaleido, chroma, hue and other param-driven ops | no internal clock | unchanged: drive them with beat signals |

Per-frame tape noise (the vhs streaks and row jitter) still changes every frame, deliberately.

## Chunked renders: determinism

tl.py renders chunks in parallel, each with 1 s of pre-roll (25 frames).

- Random patterns (glitch, dither `noise`, vhs) are pure functions of `(seed, t)`.
- History ops keep at most 24 frames, so a chunk has rebuilt the identical history by its
  first visible frame.
- A jump in `t` resets state: a seek, a layer re-entering, or the layer skipped while its
  opacity is 0.

I checked this by rendering each look's 12 frames after a seam both continuously and cold
from the pre-roll, through tl.py's own `Layer.draw`, and comparing raw canvases:

| op | seam result |
|---|---|
| chromatime, slitscan (y / x / noise), flowmosh (default `iframe: 2`), feedback `every > 1`, glitch, vhs, voronoi, noise (all re-checked on the grid clock, 2026-10-24, footage and head inputs) | bit-exact (max diff 0) |
| feedback `every = 1` (recursive) | max 1/255 at fb 0.78-0.82. The leftover is fb^25: keep fb ≤ 0.85 |
| flowmosh with `iframe: 0` and `refresh` never reaching 1 | leftover (1-refresh)^25: keep refresh ≥ 0.17 or spike it to 1 at least once a second |

## Ops

ms/frame are medians over 25 frames of Meine on the shared 12-core box, measured while it was
heavily loaded (load average 30-90). Expect them to be faster when it is quiet. Head layers
(480×600 or smaller) cost a fraction of the 720×540 preview figure.

### Time and feedback

**feedback**: zoom/rotate feedback, the hypnotic tunnel. *Stateful.*

| param | default | |
|---|---|---|
| fb | 0.8 | how much of each echo survives a step (max 0.97) |
| zoom | 1.03 | scale per step (>1 trails expand outward) |
| rot | 0 | degrees per step |
| px | [0, 0] | drift per step `[dx, dy]` (a bare number drifts vertically) |
| center | [0.5, 0.5] | zoom/rotation centre |
| hue | 0 | hue rotation per step, in degrees. Grey footage stays grey unless you also `tint` |
| tint | none | `[r, g, b]` multiplied in per step, so echoes age toward that colour (e.g. `[1, .8, .9]` → pink) |
| mode | max | `max` (bright things smear), `screen`, `mix`, `under` (current frame on top, echoes only where it is see-through; the one for masked heads) |
| every | 1 | 1 = continuous recursive smear. N > 1 = a discrete echo stamped every N song frames, which is seam-exact |
| echoes | 6 | max echoes when `every > 1` (all within the last 24 frames) |
| pad | 0 | grow the layer by this fraction per side so echoes can leave the box (heads: 0.3-0.4) |

Cost: `every 1` takes 9 ms full and 2 ms preview. The echo mode takes 49 ms full-frame (echoes
are drawn at half res above 0.5 MP) and 30 ms preview. A padded head is cheap, but `pad` on a
full-frame layer is 150 ms, so don't. Good for heads in `under` mode with `every 3, pad 0.4`.
That gives hue-aging rings that kick on the beat with `zoom: rng(1.04, 1.12, beat)`. On
footage it makes a tunnel frame around the clip.

**chromatime**: each RGB channel from a different moment: R now, G `delay` frames back,
B 2×`delay` back. This is literally "pulsating chromatically". *Stateful.*
`delay` (4, fractional is fine, max 12) and `order` ("rgb": first letter = now, last =
oldest, so try "bgr" or "gbr"). Alpha is the max over the frames used. Cost: 17 ms full,
4 ms preview. Good for talking heads, where the mouth goes rainbow; drive it with
`delay: rng(0, 6, beat(1, "decay"))`.

**slitscan**: every row, column, ring or noise region comes from a different moment.
*Stateful.*
`depth` (16 frames, max 24), `axis` (`y` | `x` | `radial` | `noise`), `reverse` (0/1),
`center` (radial). For the noise axis: `scale` (240 px feature size), `speed` (0.2), `seed`.
Cost: y/x take 17 ms full and 4 ms preview; radial/noise take 65 ms full and 16 ms preview
(per-pixel gather). Good on moving material: Meine's tracking shot, the head, smoke. It is
invisible on static shots.

**flowmosh**: datamosh-ish. Each frame, the previous *output* is dragged along the current
frame's optical flow (Farneback at low res), and only `refresh` of the real frame leaks back.
*Stateful.*
`refresh` (0.15; 1 = a clean "I-frame", so spike it on beats:
`rng(0.06, 1, beat(2, "pulse", width=0.06))`), `gain` (1.0, flow exaggeration), `px`
(0 = smooth flow, 16 = one vector per 16 px macroblock, the codec look), `res` (192: long
side of the flow computation). Cost: 16 ms full, 6 ms preview. Good on drone and tracking
footage between hits.

### Colour

**gradmap**: luma mapped through a palette.
`palette`: `ironbow` (FLIR thermal), `whitehot`, `blackhot`, `nightvision`, `blood`, `gold`,
and the cyclic ones `y2k` (chrome cyan/pink), `acid`, `rainbow`. It also accepts a list of
≥3 `[r, g, b]` stops (add `cyclic: 1` to wrap). Further params: `cycle` (0: offset into the
palette, so drive it with `beat(4, "saw")`; ramps ping-pong, cyclic palettes wrap), `repeat`
(1: bands the palette N times across the luma range), `gamma` (1). Cost: 23 ms full, 6 ms
preview. **ironbow is the strongest single look here**: it turns the preacher and the Gaza
footage into the same false-colour as the strike-cam.

**dither**: posterize with dithering.
`levels` (4 per channel), `mode` (`bayer` ordered | `noise`), `px` (2: chunky cell size),
`rate` (12.5 Hz: how often the `noise` pattern changes), `seed`. Cost: 4 ms full, 3 ms
preview. Pairs well after gradmap.

### Geometry

**mirror**: `mode` `h` (left half reflected onto the right) | `v` | `quad` | `tile`,
`shift` (−0.5..0.5, slides the mirror axis), `tiles` (2, for tile). Cost: 12 ms full, 3 ms
preview. Quad on a face gives the four-eyed judge.

**radialblur**: zoom blur (and/or spin blur) about `center`.
`strength` (0.08: zoom fraction; 0 = off, so beat-drive it), `spin` (degrees), `passes`
(3 → 8 samples; 4 → 16). Cost: 17 ms full, 6 ms preview.

**shock**: a ring of radial displacement expanding from `center` as `phase` goes 0 → 1.
With no `phase`, it launches a wave every `beats` (default 1, so one per kick). Give `phase`
yourself to key it to a strike's hit time.
`px` (24: push), `period` (80 px ring width), `decay` (1.5: fades as it grows), `rgb` (0:
>0 splits the channels across the ring). Cost: 21 ms full, 6 ms preview.

### Print and screen

**halftone**: dots on a rotated grid; dot area follows brightness.
`period` (10 px cell; 14-19 reads clearly at preview), `angle` (45), `mode` (`rgb`: three
screens at angle +15/+75/+0, the pop-art/LED look | `mono`: luma dots in `ink` on `paper`),
`invert`. Cost: rgb takes 27 ms full and 9 ms preview; mono takes 41 / 11 ms. Animating
`angle` or `period` rebuilds the grid cache, which adds a few ms.

**vhs**: per-row wobble, a rolling tracking band, chroma bleed and streaky noise.
`px` (3: wobble), `period` (140: wobble wavelength in rows), `band` (0.4: tracking-band
strength, so flare it on downbeats), `roll` (0.23: band passes per second), `scale` (6: chroma
bleed width), `noise` (0.06), `seed`. Cost: 28 ms full, 8 ms preview.

### Light

**bloom**: glow from the highlights.
`thresh` (0.65), `knee` (0.15), `px` (24: radius), `gain` (0.8), `color` (tint the glow).
Cost: 24 ms full, 6 ms preview.

**edgeglow**: neon outlines. Sobel edges of luma, coloured, bloomed and screened over the
image dimmed to `base`.
`thresh` (0.12), `scale` (2 px pre-blur: **raise it to 3-4 on busy texture like rubble**, or
everything outlines), `color` (`[0.35, 1, 0.9]`, or `"source"` to use the image's own colour),
`px` (8: glow radius), `glow` (1.5), `gain` (1), `base` (0.6; 0 = lines on black). Cost:
38 ms full, 10 ms preview. It is very good on the head.

### Glitch and texture

**glitch**: block-shift glitch. Off unless `strength` > 0, so drive it with a short beat decay
or an onset (`rng(0, 0.8, beat(1, "decay", tau=0.07))`).
`mode` (`bands`: horizontal bands shifted with an RGB split | `blocks`: macroblocks copied from
elsewhere, some posterized or channel-swapped), `px` (60: shift distance), `blocks` (14:
band count, or block count factor), `scale` (32: block size), `rgb` (0.5: channel split),
`hold` (0.08 s: how long a pattern holds), `seed`. Cost: 1-2 ms.

**voronoi** (**heads only**: see above): animated Worley/Voronoi texture, in the spirit of
Blender's Voronoi Texture.
`feature`: `f1` (soft cells) | `edge` (F2−F1 crackle lines) | `cells` ("crystallize": each
cell filled flat with the picture under it) | `random` (a random colour per cell).
Further params: `scale` (80 px cell), `speed` (0.4: points orbit inside their cells),
`width` (0.08, edge), `lines` (stained-glass borders: 0.4 for `cells`), `color` (for
f1/edge), `mode` (blend as in `noise`, plus `replace`; the default is `replace` for cells and
`overlay` otherwise), `seed`. For a recognisable face in `cells` mode, use `scale` 22-30.
Cost: 60 ms full, 14-21 ms preview (computed at reduced res).

## Recipes (all in the gallery)

| name | stack | where |
|---|---|---|
| hypno | feedback (fb .78, zoom beat 1.0-1.04, hue 6, pad .3) → chromatime (delay beat 1-4) | heads in the hypnotic middle |
| thermal-judge | gradmap ironbow (cycle bar-saw 0-.25) → edgeglow (thresh .2, scale 4, warm, beat gain) → bloom (thresh .8) | heads and ground, rhyming with strike-cam |
| echo tunnel | feedback mode under, every 3, zoom beat 1.04-1.12, rot beat 1-6, hue 25, tint [1,.8,.9], pad .4 | single head copies, framed footage |
| mosh-tape | flowmosh (I-frame per bar, px 16) → vhs (band flares on downbeats) | drone/aftermath footage between hits |
| y2k-print | gradmap y2k (cycle per bar) → halftone rgb (amount .7) → glitch on the kick | short bursts at peaks |
| judge-shock | chromatime bgr → shock every 2 beats (rgb .8) → edgeglow source | the preacher at full intensity |
