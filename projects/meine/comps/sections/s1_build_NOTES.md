# s1_build: 0:38 to 3:45 (bars 20 to 118)

Time ops used: `c.say` (including `like=`, so moving heads speak), `c.groove` (through `s1_lib.groove`), `c.footage_multi` (through `s1_lib.land_hits`), `c.stutter` and `c.freeze`.

Files: `s1_build.py` (the section) and `s1_lib.py` (head copies, character fx stacks, gaze and drift tracks, pong keyframes, formation sequences with morphs and bar-locked spin, picture and panel framing). Run `uv run python projects/meine/comps/sections/s1_build.py`, then `uv run python render/tl.py projects/meine/comps/out/section_s1_build.timeline.json --range A B --jobs 3`.

Viewer: http://127.0.0.1:8765/studio/timeline.html?tl=projects/meine/comps/out/section_s1_build.timeline.json

The music shapes the section in four parts. From bar 20 to bar 71 is the slow build. From bar 72 (137.36 s) the high band falls away, and it is almost silent from bar 75 to bar 83. Bars 84 to 87 are a riser. Bar 88 (167.82 s) is the drop into the rise. Measured from beats.json, the breakdown is bars 72 to 87, not 2:15 to 2:45.

Layer order (z) inside the section, from the bottom: beds, then panels and grooves, then strikes, then heads. White-hot flashes (the bar 32 Mosul blast, the countdown monitor and the handoff flash) are placed above the heads on purpose.

## Bar map

| bars | song s | what happens |
|---|---|---|
| 20 | 38.30 | The "Apache in G Major" false-colour fireball (`hellfire-symphony-tads#5`, hit 32.07) lands on the downbeat, screened over Meine, which ducks to 40%. A plain parent head sits where the s0 preacher ended (1150, 640) and silently mouths "thou shalt give Israel missiles" (face.mp4 at 17.5 s). |
| 20-21 | 38.3-42.1 | The split. One copy peels off on every beat (beats 1 to 8) and flies home over one beat. The parent shrinks with each copy and is gone when the eighth leaves. There are 8 copies of graded sizes (0.62 down to 0.20), each with its own character (below). |
| 21-27 | 40-53 | The copies hover where their own face looks (the `face_self_gaze` path, sampled at each copy's source time, so each goes where he looks) and grow on eye contact (the path's scale channel). From bar 24 they hop on alternate beats, half on the off-pair. Underneath, Scranton's red-hot 155 mm noses (`scranton-155mm-nosing-redhot#0`) are hue-keyed (the new `huekey` op: red only, so greys and darks drop out), bloomed and grooved to one 4 s press cycle per 2 bars. |
| 27 b1-28 | 51.6-53.5 | All eight gather into one point at the centre. |
| 28-31 | 53.5-61.2 | A formation of 20 small heads (scale about 0.1) bursts from the point into a wireframe **cube** (8 vertices plus 12 edge midpoints) that snaps a quarter turn on every downbeat. Panels cut on the beat: a fuze screwed into a JDAM (Whiteman) on beats 1-2 left, blue-gloved hands seating a sensor (Balad) on beats 3-4 right, and bomb noses on the build stand from bar 30. |
| 32 | 61.16 | A white-hot Mosul detonation (`oir-mosul-vbied-facility-2017#0`, hit 0) with a duck. The flash whites out the frame for about 0.25 s on purpose and goes over the heads. The cube morphs into a **sphere** (smooth, one turn per 2 bars). A bigger gaze-steered "core" head sits at the centre of his own globe. |
| 32-35 | 61-69 | The MK-84 ship at Ashdod (`imod-mk84-ashdod-feb2025#1`) is screened over the picture, grooved to one 5 s crane cycle per 2 bars. |
| 36 | 68.78 | A black-hot blast (`idf-strikes-jan2014-blackhot#1`) is **multiplied** over Meine, so an ink cloud spreads over the sky. The formation becomes a double **helix** at one turn per bar. |
| 36-39 | 68.8-76.4 | The first US munitions C-17 into Nevatim (Oct 2023, vertical phone video) lands in a tall window on the right. The apron close-ups cut on beats from bar 37, left. |
| 40 | 76.39 | A false-colour TADS hit (`#4`, 21.37) with a duck. The formation becomes a **ring** that steps 1/16 turn per beat and wanders. Hellfires: a night hand guides one onto the Reaper rail on beats 1-2 (Holloman, text cards cropped off); crates on beat 3 and the carry onto the rail on beat 4 (Gulfport). |
| 43 b3-44 | 83.5-84.0 | The ring collapses to a point. |
| 44 | 84.01 | A night Tomahawk launch from the deck (`tomahawk-night-philippine-sea-2014#1`, 5.04) with a duck. The eight big copies burst out of the collapse point and **bounce** pong-style with every wall contact on a beat. Crossings take 4 beats in bars 44-47, then 2 or 4 beats in 48-55, 2 or 3 in 56-63, 1 or 2 in 64-67, and mostly 1 in 68-71. Sizes swell with intensity. |
| 44-47 | | Night SDB loading on the Reaper flightline is screened, grooved at 1 s to 2 beats. |
| 46, 48, 50, 54 | | Strikes on downbeats. 48 is the IDF's own Oct 2023 fireball on the Gaza shore, **stuttered** (`c.stutter`, 3 triggers on eighths: 48 b0, b0.5, b1) with a duck. 54 is the CENTCOM black ink-blot frame, multiplied. |
| 48-71 | 91.6-137 | **Drift mode**: one big preacher wanders along `face_self_drift`, chroma-split and noise-textured. |
| 48-55 | | Panels: endless rows of GBU-31s and forklifts (Oct 2023), then bombs on IAF pylons. |
| 52 | 99.25 | The AFP Rafah night strikes, three orange domes, landed on consecutive grid points (`footage_multi`, with the speed kept within 1 ± 0.35) under a 3 s duck. The Gaza ground layer begins: AP drone orbit of Khan Younis rubble as a faint bed (opacity 0.12-0.3). |
| 56-63 | 106.9-122.1 | A strike on every bar: alternating ground night fireballs and strike-cam hits, plus the GBU-39 "OVER 46 MILE RANGE" promo fireball (58). Twenty small heads orbit the drift head as a ring, then as a torus (60). Panel: civil defence digging by hand (`aje-civil-defence-body-recovery-2025-12#1`, not identifiable), grooved at 1.1 s per pull to 2 beats, in sepia duotone. |
| 60-67 | | Bed: AP drone over the coast road, the people returning north, multiplied at 0.45-0.7. |
| 64 | 122.11 | A night sky over Gaza goes white (`ap-night-blasts-from-israel-2025-09#0`, 3.6) and **freezes** for two beats (`c.freeze`), then plays on. Duck 35%. |
| 64-71 | 122.1-137.4 | All eight copies again, crossing on 1-2 beats. Strikes come every bar plus an extra on beat 3 of odd bars. Ducks on the even bars. Bed: the Zikim flour-sack multitude. |
| 70 b2-72 | 134.5-137.4 | **The countdown**: the Reaper ground-station monitor's "3", "2", "1" (`mq9-live-hellfire-holloman#7`) land on two-beat steps (70 b2, 71, 71 b2), and its strike lands on bar 72's downbeat, exactly where the music drops out. It is retimed by a piecewise map, a centred 760x430 window above everything. |
| 72-73 | 137.4-141 | Every head freezes mid-word, desaturates and drops out of frame, two per beat. |
| 72 b2-80 | 138-153 | A golden dusk with smoke columns over Gaza seen from Israel (`ap-dusk-smoke-from-israel-2023-10#1`) at 55%. Meine has turned into a car interior at dusk here, and it stays in view. |
| 74-84 | 141-160 | **One head**: small, grey, slow-motion (speed 0.5), drifting. It sits where Meine's rear-view mirror is, so the preacher watches from the mirror. This was an accident, and I kept it. |
| 76-79 | 145-152.3 | One image, small, centred: a morgue worker cuts white shroud cloth (`ap-aqsa-shroud-laundry-2023-10#3`), one cut every 3 beats. |
| 80-83 | 152.3-160 | The same window: white shrouds laid out on the pavement outside al-Aqsa hospital (slow, 0.6x, desaturated). |
| 84-87 | 160-167.8 | Riser: the Nasser courtyard graves, with hands smoothing the sand (`nbc-nasser-courtyard-graves-2024-01#2`, graphic 3 but not identifiable). The window grows 1.0 to 1.6 and the colour returns. Copies come back two per bar (2, 4, 6, 8), orbiting faster and faster (quadratic), and gather to the centre on the last two beats. |
| 87 | 165.7 | `c.say`: he stutters "mi-, mi-, mi-, mi-" one per beat across the last riser bar, in his own voice. |
| 88 | 167.82 | **"MISSILES"** on the drop, with a daytime Tomahawk launch from a destroyer. Eight heads burst out bouncing on 1-2 beat crossings. Twenty small heads come out of a point into a double helix (1 turn per bar). |
| 88-95 | | Bed: the destroyer's launches (`centcom-epic-fury-tomahawks#1`), cut so a launch lands on every other downbeat, each with a duck to 50%. Ground night strikes on the odd bars. |
| 96-103 | 183.1-198.3 | Bed: people returning north on the coast road, **grooved so every step lands on a beat** (0.55 s to 1 beat), multiplied. The sphere formation, quarter turn per bar. The CENTCOM strike-camera montage has all six hits landed on two-beat grid points through the whole 8 bars (multi-hit, whitehot gradmap), each with a short duck. Ground fireballs on beat 3 of odd bars. |
| 104-111 | 198.3-213.5 | Bed: Lockheed's blue CGI F-35 assembly line, screened ("WING BUILD", "FINAL ASSEMBLY" drift past) through a y2k palette cycle. A torus formation steps 1/16 turn per beat. A strike on every bar. **108: white phosphorus airburst** over tents at night (`aj-high-powered-bombs-explainer#6`), falling gold, with a 3.6 s tail and a duck to 30%. |
| 112-115 | 213.5-221.2 | Strikes every two beats (12 rotating sources, posterized, ducks on alternate hits). Bed: Jabaliya, men tearing at concrete by hand, grooved 1 s to 2 beats, 45%. A cube formation stepping 1/8 turn per beat. Heads cross on every beat. |
| 116-117 | 221.2-225.0 | Strikes on **every beat**. Bar 116: "missiles" on every beat, each from a different bouncing copy. Bar 117: "thou / shalt / give / Israel" passed between copies, one per beat. On 117 b2 the small heads collapse to a point. On 117 b3 the bouncing heads' last flights all end in the centre. |
| 118 | 224.97 | **Handoff.** Every head arrives at the centre and vanishes on the downbeat (scale 0.15). One last night blast flash (`ap-night-blasts-from-israel-2025-09#0`, 3.6) lands on the downbeat, framed to the picture, with a duck to 35%. |

## Speaking heads (`c.say(..., like=head)`)

The mechanism is `comp.say` with `like=layer` (an additive extension). The word's face layer copies the moving copy's size, crop, mask, pos, scale, rot, fx, blend, opacity and tags. The copy itself is gated to opacity 0 for the word's span (a hold-keyed multiply), so the speaking mouth sits exactly where the head is, in the same motion and with the same effects.

`s1_build.say_like` adds two things:
- `bump`, a scale swell while speaking: x2.4 for small formation, orbit and rise-formation heads, so the mouth is readable; x1.25 for big copies; x1 for the lone head.
- `z`, a layer-order override.

`speak(c)` holds all of them:

| bar | song s | who says what |
|---|---|---|
| 32, 36, 40 | 61.16, 68.78, 76.39 | The small formation head nearest the camera says "missiles" as each strike lands. At 32 it is drawn over the white-hot flash (z 5), so it is the one face left in the whiteout. |
| 51 b0-b3 | 97.35-98.78 | Call and response across bouncing copies: "thou", "shalt", "give", "Israel" (bounce 0, 5, 2, 7). |
| 52 | 99.25 | **Chorus**: all 8 bouncing copies plus the drift head say "missiles" on the Rafah domes' downbeat. They use tape-mode stretch 0.8-1.3, so nine preachers speak at nine pitches from one onset, each at gain 0.24. |
| 61 | 116.40, 117.34 | The drift head: "Hellfire" on the TADS strike, then "missiles" on beat 3. |
| 63 b0-b2, 64 | 120.21-122.11 | Orbit ring heads pass "more / and / more" round, then a bouncing copy says "MISSILES" into the bar 64 white-sky freeze. |
| 102-103 | 194.49-197.82 | "as many missiles / as we can get", a word a beat across rise copies. |
| 105, 107, 109, 111 | 200.2-211.6 | A small spinning formation head swells out of the torus and says "missiles" on each odd-bar strike. |
| 116-117 | 221.16-224.49 | "missiles" on each beat of 116, then "thou shalt give Israel" across 117, a different copy each beat. |
| 118 | 224.97 | A six-voice tape chorus "missiles" at the vanishing point. The faces sit under the handoff flash, so they are ghosts. The voices run about 0.6 s past 224.97, inside the allowed cross-fade bar. |

**Variant, not the default.** `uv run python projects/meine/comps/sections/s1_build.py --paying` writes `section_s1_build.paying.timeline.json`. In it, the lone grey head in the breakdown says "I'm / not / paying" on bar 78 beats 0-2 and "enough" on bar 79, slowed (stretch 1.5-1.8), over the shroud cloth. A rendered preview of 147.5-154.5 is next to that timeline.

### How they were verified
- **By eye:** crop strips around each speaker from 0.16 s before the word, generated with the scratch script `saycrop.py`. They cover the formation heads at 32, the bar 51 call and response, the drift head at 61, the orbit heads at 63, bar 64, the rise formation heads at 105 and 107, and the lone-head variant. The copy vanishes and the speaking face appears in the same spot on the beat, and the mouth opens on the word.
- **By ear:** a voice-only render (music gain 0, faces hidden) over 96.5-123, with onsets taken from a 5 ms RMS envelope. Errors against the target beat:

| word | error |
|---|---|
| "shalt" | +8 ms |
| "give" | +6 ms |
| "Israel" | +2 ms |
| "missiles" (bar 61) | 0 ms |
| "more", "and", "more" | +1 to +3 ms |
| "MISSILES" (bar 64) | +1 ms |
| "thou" | +35 ms |
| "Hellfire" | +59 ms |

  The "thou" and "Hellfire" lags come from breathy onsets (th, h), which have little energy at the start; the word timing is aligned. The bar 52 chorus could not be measured that way, because "Israel" (0.6 s) is still sounding on the downbeat.

## At the boundary (for lane B)

- At 224.967 (bar 118) every s1 head and formation layer ends.
- The only s1 layer after 224.967 is `handoff-flash`. It ends at 226.871 (bar 119), with its fade-out running the whole bar.
- The last duck (35%, at 224.97) releases by about 226.3.
- From 226.871 there is clean Meine (a dusk street seen from the car) with nothing of mine on it.
- Lane B can fade in from 223.062. Over 223.06 to 224.97, s1 is at its busiest: strikes on every beat, "missiles" on every beat, heads converging.

## Characters (`s1_lib.character`)

Each head has its own fx stack, and most pulse on the beat:

- 0: hue cycle and RGB split
- 1: RGB fbm noise overlay
- 2: blood duotone, posterized
- 3: threshold cracked by Voronoi edges
- 4: pixelate kick
- 5: liquid warp with green noise
- 6: negative
- 7: cyan/magenta duotone with scanlines
- 8: gold posterize with noise burn
- 9: ironbow thermal (his face through the strike camera's palette)
- 10: Voronoi crystallize
- 11: halftone
- 12: acid palette with neon edges
- 13: chromatime with beat glitch

Characters 3 and 9-13 use the looks lane's `fx_extra` ops. There is no full-frame grain anywhere (`post` is empty). Noise is only on heads.

## Footage choices and why

- **Supply chain during the build**, in order of the chain: forging (Scranton) → JDAM assembly (Whiteman, Balad) → MK-84 ship at Ashdod → C-17 into Nevatim → Hellfires onto the Reaper rail → SDB loading → GBU-31 rows (Israel, Oct 2023) → IAF pylons. Daylight factory material goes in beat-cut inset panels (desaturated, posterized "archive") so Meine stays visible. Night material is screened over the full picture.
- **Strikes**: each lands its catalogued hit frame on a downbeat (later on every 2 beats, then every beat).
  - Black-hot and white-page material is multiplied (ink on Meine's sky).
  - Night fireballs are screened.
  - The IDF's own colour aerials are normal-blended with a duck, because they need their colour.
- **Ground (Gaza)** grows through the build:
  - Bars 52-71: a faint drone bed, then a multiplied one.
  - Bars 56-63: hands digging in a panel.
  - 72-87: it carries the breakdown.
  - In the rise: the people walking, the hands, alongside the strikes.
- **Identifiable victims**: none are used. Every graphic-3 choice is shrouds, bags or graves, seen without faces (catalog `identifiable_victims: false`). The dig and walking footage shows rescuers and crowds, not victims. Pre-2023 material: `idf-strikes-jan2014-blackhot` (2014), `oir-*` (Iraq 2015-17) and `tomahawk-night-philippine-sea-2014` are weapons-side footage used as "the machine", not presented as Gaza 2023+.
- **Crops**: AP sources lose the top 16% (their bug). Ground strikes also lose the bottom 15% (lower thirds, network bugs). Everything except the TADS fireball is framed to Meine's picture area (y 158..922), so the letterbox stays black.

## Ducks

- Meine dips to 40% on the split fireball, the big four-bar strikes in the build and the Rafah domes (3 s hold).
- It dips to 50% on each Tomahawk launch in 88-95, and to 55% (short) on each CENTCOM montage hit.
- It dips to 30-35% on the WP airburst, the tower collapses, the fast strikes in 112-117 and the handoff flash.
- The breakdown has no ducks: Meine is the "nothing".

## Verification

- `c.save()` reports 251 layers: 131 hits on the beat, 1 on an eighth (the bar 48 stutter, deliberate) and 0 off the grid. The 131 include every speaking-head onset.
- The bar 87 stutter is on quarter notes. Eighths read better but are off-grid by the checker's standard, so I chose beats.
- Frames I looked at (contact sheets): the split (38.3-53), the formations (53-84), the build (84-137), the breakdown (136-168), the rise and handoff (166-227), and the whole-span sheet.

## Library notes (not edited)

- `section_main` uses `Comp(...)`, whose `project.json` duration is 36.8. Harmless, since the range is explicit.
- The `meta` overwrite in `footage()` is fixed upstream (cf1aeb3).
- A layer-level "clip to picture area" option would save the per-source aspect-crop arithmetic (`s1_lib.picture`).
- Added: the `huekey` op in `render/fx_extra.py` (hue, width, soft, sat, val, soft_sv, invert). It still needs a line in FX_EXTRA.md or TIMELINE.md.
- Added: `comp.say(..., like=layer)`. It is additive: s0 and s1 timelines were byte-identical before the s1 say layers were added.

## What I'd try next

- Give formation heads depth sorting. Layer order is fixed, so far heads can draw over near ones in spins. One way is to split each formation into front and back layers per half-turn.
- Use more `c.ramp` (a slow-mo into the countdown blast) and `c.reverse` (an explosion un-exploding into the breakdown at 72).
- Try `feedback`/`slitscan` on the bouncing heads in 112-117 for trails.
- Make speakers in the orbit ring (bar 63) pick a readable character. The pixelate and chromatime heads swell but are hard to lip-read.
- Nudge breathy onsets (`nudge=-0.03` on "thou", `-0.05` on "Hellfire").
- Decide whether the bar 118 chorus faces should sit above the handoff flash (z 5) or stay a ghost under it, as now.
- Try a longer or more varied handoff with lane B once its first bars exist.
