# s2_peak: 3:45 to the end (bar 118 to 7:53)

`s2_peak.py` (the section) + `s2_kit.py` (word sampler with pickups, gaze/drift paths re-timed
onto song time, 3D orbit engine for the chorus, `Chorus` whose copies step forward to speak).
Viewer: http://127.0.0.1:8765/studio/timeline.html?tl=projects/meine/comps/out/section_s2_peak.timeline.json
(`section_s2_peak.mp4` is a whole-span render of the current timeline).

`build(c, outro_kind="walkers")`; the other options are `"shroud"` and `"head"` (see Outro).

## What the music does (measured, per bar)

Bar numbers index `beats.json` downbeats (bar 118 = 224.967).

| bars | time | what's there |
|---|---|---|
| 118-119 | 3:45-3:49 | tail of the rise |
| 120-123 | 3:49-3:56 | near silence (intensity 0.03-0.19) |
| 124-131 | 3:56-4:12 | the kick returns alone (strong onset on 124) |
| 132-143 | 4:12-4:34 | peak 1 |
| 144-151 | 4:34-4:50 | lull: hats, intensity about 0.55 (bar 144 is a 1.8 s bar in the grid) |
| 152-166 | 4:50-5:18 | peak 2 |
| 167 | 5:18-5:20 | a one-bar gap |
| 168-195 | 5:20-6:13 | the hottest stretch (0.93-0.98) |
| 196-207 | 6:13-6:36 | cooling |
| 208-237 | 6:36-7:33 | plateau: kick only; every 4th bar dips |
| 238-239 | 7:33-7:37 | last bars. **The beat grid ends at 456.876 s.** Then the music fades to silence at about 472 s |

**Meine is night driving from about 4:15 onward** (dark road, streetlights), and it goes almost
black after 7:00. That decided the blends: multiply turns everything to black, so footage goes on
with screen or lumakey (IR and night clips) or normal (day clips). Black-hot IR is inverted, then
screened, so its ink-blot blasts glow. A duck barely shows on a black background, so for the peak
the footage is what you see and Meine's lights glint through it.

## Bar-by-bar

- **118-119, the handoff.** Lane A collapses its heads to the centre at about 0.15 scale on bar 118
  and has a `handoff-flash` running until 226.87. My preacher **grows out of that point**: two beats
  from (720, 540) at 0.15 into the gaze-steered path (`face_self_gaze`, going where he looks), over
  the last bars of the rise. **On screen at 224.967:** Meine (dusk, the car interior, trucks), lane
  A's flash, and a tiny head at the centre starting to grow. Nothing of mine starts before 224.967.
- **120, the drop-out.** He says "give Israel MISSILES" with the word on the downbeat, as the music
  falls away. A white-hot Mosul blast lands on the same downbeat. **The tracking shot freezes**
  (`meine-freeze` holds Meine's frame of bar 120, then desaturates, blurs and dims) for the breath.
  This is the only time the spine of the piece stops.
- **120-123, the breath.** A morgue worker cuts shroud cloth (one cut about every 3 beats). It is
  screened over the frozen road while the preacher drifts across it small (the drift path). From
  122.5 the MQ-9 monitor shows TARGET, then **3, 2, 1 every two beats** (122.5, 123, 123.5), and the
  strike lands on **124 as the kick returns**, as he says "MISSILES" big in the centre.
- **124-131, re-entry.** The eight-head chorus splits off him, **one copy per bar**, each gliding
  into a slowly turning cube. One continuous CENTCOM Iran strike-cam take sits in a feathered window
  with **six hits on bars 126, 128, 130, 132, 134 and 136** (`footage_multi`; speeds 0.93 to 1.27).
  Rafah's three night domes land on 125, 126.5 and 127.5, two blasts on 129 and 129.5, and a dusk
  fireball on 131.
- **132-143, peak 1.** Three copies say "missiles" together on 132 (three different takes, a little
  choir). After that, one copy at a time on 136 and 140, and "more and more missiles" on 142.5.
  Ground strikes land on the odd bars and weapons on 138, 140 and 142. Bar 143 has IR accents on
  beats 2, 3 and 4. The cube spins one turn every 2 bars, with radius and scale pulsing on the beat.
- **144-151, lull: the displaced.** The formation **scatters into drift mode**. Top-down walkers on
  the coast road and the Zikim flour multitude are both grooved, so steps land on the beat. On 149 a
  drifting copy says "...ripped from me" over the hungry crowd. No strikes.
- **152-166, peak 2.** The copies regroup into a ring, then a helix, then a sphere. There is a hit on
  every downbeat, cycling IR, ground night, weapons fireball and ground day, each with a short
  feedback tunnel. A copy speaks every 2 bars, and on 165.5 one says "mi-mi-missiles" (`c.say`
  stutter).
- **167, the gap bar.** The chorus stops turning. The last IR strike **freezes** in a blood
  gradmap. His big face says "I should be paying seventy-five percent", ending just before the drop.
- **168-195, the hottest stretch** ("atrocity atrocity atrocity, music music music"):
  - Under everything, a **kaleidoscope bed** of rubble-field drone footage, palette-cycling and
    changing every 8 bars (ironbow, blood, acid, nightvision). Its opacity breathes from 0.12 to
    0.42 on each bar.
  - A hit on **every downbeat**, with feedback trails. On odd bars an IR stutter (3 triggers on
    eighths) fills beat 3. On 194-195 there is a hit on every beat, into a whiteout.
  - The chorus moves in a figure-eight about the screen at 0.105 scale, cube to helix to ring, one
    turn per bar. A word comes every 2 bars, and every 8th-bar phrase end is "mi-mi-mi-missiles".
  - **Bar 184 is the single graphic-3 moment:** the 2008 Apache gun tape, a Hellfire into a group of
    people, lands on the downbeat as his face (whitehot) says "Hellfire MISSILES".
- **196-207, cooling.** The copies fly outward and leave one every 6 beats. Strikes come every 2
  bars and run longer. The Ansar tent camp burns (keyed fire). From 205 to 208 men pray over
  shrouded bodies: normal blend, desaturated, no effects.
- **208-237, plateau: manufacture and burial.** He is alone again, gaze-steered at about 0.36 scale,
  with a sentence on each 8-bar phrase:
  - 212 "they need more missiles"
  - 220 "thou shalt give Israel missiles"
  - 228 "I'm not paying enough"
  - 236 "missiles"

  Each phrase has one quiet strike (212, 220, 228). Grooved against each other:
  - 208-215: 155 mm shell noses pressed red-hot, with a grave dug by hand at Nasser in a window
    (one shovel stroke every 3 beats).
  - 216-223: the MK-84 containers craned off at Ashdod, with shroud cloth cut in a window.
  - 224-231: the crowd returning north.
  - 230-237: Lockheed's blueprint F-35 factory.
- **238 to the end, outro.** On bar 239 his head starts shrinking, slowed to half speed, and is gone
  2 s after the last beat (458.9). The misty coast road, the river of people walking north, fades in
  from 236. It is the last image, fading out with the music.

## Outro options (`outro_kind`)

1. **walkers** (default): he disappears and the people outlast him. It is the least didactic, and it
   closes on the displaced, not the weapon or the man.
2. **shroud**: white cloth unfolding, desaturated, fading with the music. Quieter and more funereal;
   it rhymes with the breath at 3:49.
3. **head**: nothing but the night road and his shrinking, half-speed face. It ends on him, which
   makes the piece about him.
4. (not built) He says one last "missiles" after the grid ends, into the silence, with no music
   under it. This would land off-grid by definition.

## Ducks and blends

- Event ducks are at 0.3 to 0.45 per hit/word. The hottest stretch has a held duck at 0.6, the gap
  bar 0.15, and the prayer 0.25. During the freeze the live background is ducked to 0, so only the
  frozen frame shows.
- Blends:
  - IR (white-hot): lumakey(0.3, 0.7), then screen.
  - Black-hot: invert, levels, screen.
  - Night ground: lumakey, then screen.
  - Day ground: normal with posterize 7.
- Heads carry their own hue cycle, posterize, overlay rgb noise and chroma (the noise textures ember
  wanted). **There is no full-frame grain or post at all.**

## Footage choices and cautions (for the sensitivity review)

- **Graphic 3:** only `apache-gun-tape-iraq-2008` at 72.12, bar 184 (Iraq 2008, not Gaza; it's
  there for the Hellfire). The prayer over the shrouded (`ap-aqsa-children-mourned-2024-08#3`)
  shows no faces of the dead.
- **Identifiable victims:** pools exclude `identifiable_victims: true`. Pre-2023 *ground* material
  (`-war`, 2019, May-2023 tags) is excluded. Some *weapons* clips are older IDF/OIR strike-cam
  (2009-2018) and `ap-iron-dome-chase-may2021`. They show the machine, not a dated Gaza event.
- **Captions (swept 2026-10-24).** Every 1 s of the render was checked: two sweeps, each with a
  frame every 2 s, offset by 1 s. Fixes:
  - Weapons crop is now `WEAPONS_CROP` [0.06, 0.16, 0.94, 0.76]. This removes the AP credit at 4:24
    and 5:26, the corner logos at 5:34 and 5:42, and "ISRAEL DEFENSE FORCES HANDOUT" at about 5:31
    (`times-radio-idf-bombardment`).
  - OIR tapes use `OIR_CROP` (bottom at 0.68), which removes their typed description at 5:22.
  - Captioned clips are kept out of the pools (`CAPTIONED`):
    - `aj-high-powered-bombs-explainer` (subtitles; it remains only as the 7:14 WP airburst, cropped
      [0.16, 0.2, 1, 0.68])
    - `ap-interceptions-telaviv-jlm-feb2026`
    - `ap-flares-cloudy-night-2025-12-b` (the "SOUTHERN ISRAEL OVERLOOKING THE GAZA STRIP"
      lower-third at 5:43)
    - `fa-rafah-bomb-identification` (white page with text at 6:12)
  - Ashdod crane: cropped away the IMOD camera icon (6:52-7:05).
  - Deliberately kept: the redaction boxes in CENTCOM strike-cam, the sight's "FLIR"/reticle data,
    the diegetic labels in Lockheed's CGI factory ("FORWARD FUSELAGE", "FINAL ASSEMBLY", "WING
    BUILD"), and a lit shop sign in Meine itself (6:14).
- **Letterbox:** every footage layer now has `"clip": "picture"`. Only the floating heads may cross
  into the bars.

## Verification

- `c.save()`: **26 "off-grid" hits, all deliberate subdivisions**: IR stutter triggers on eighths
  and "mi-mi-missiles" fragments on sixteenths. I checked every hit lands on the 16th grid
  (|error| < 30 ms against beats subdivided in 4). Every downbeat/beat hit is on the grid.
- The whole span was rendered (`--jobs 3`) and checked on contact sheets across it. Fixed along the
  way: multiply going black over night Meine, a grey IR wash, kaleido beds swamping the strikes, a
  plateau head that was too big, and caption leaks.
- Tested in the full assembly (`s0_rant` + `s1_build` + `s2_peak` into a Comp, not saved): it
  builds 373 layers. Pools use `shuffle=False` and their own rotation, so the section doesn't
  depend on other sections' random calls.

## What I'd try next

- Lane A ends with many heads at the centre and I start with one. A crossfade where their copies
  are literally the first chorus copies (shared ids) would be smoother.
- The hottest stretch could use `mirror` (quad) on the strike layers during 176-183, and `shock`
  rings driven by a beat saw on the downbeats.
- `c.say(..., video=False, repeat=4, every=1)`: a voice-only "missiles" chant under 188-195.
- The 2 s of silence after his head vanishes may want the WP airburst embers falling (screened)
  before the walkers take the frame.
