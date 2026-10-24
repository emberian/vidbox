# s2_peak: 3:45 to the end (bar 118 to 7:53)

`s2_peak.py` (the section) + `s2_kit.py` (word sampler with pickups, gaze/drift paths re-timed
onto song time, 3D orbit engine for the chorus, `Chorus` whose copies step forward to speak).
Viewer: http://127.0.0.1:8765/studio/timeline.html?tl=projects/meine/comps/out/section_s2_peak.timeline.json
(`section_s2_peak.mp4` is a whole-span render of the current timeline).

`build(c, outro_kind="walkers")`; the other options are `"shroud"` and `"head"` (see Outro).

## Revision 4: ember's v2 notes (2026-10-24); this section overrides everything below where they differ

**Bar numbers.** In this section, "viewer bar" is ember's count, starting at 1. The code and the
older tables below count from 0, so code bar N is viewer bar N+1. Song times are the downbeats in
`analysis/beats.json`.

### Punctures: fewer, longer, soft edges ("too abrupt ... they move on too fast")

The five one-bar punctures (code 171, 175, 179, 187, 191) are replaced by **two three-bar
punctures**, and the morgue after Bureij now holds three bars, not two.
- **In:** over the beat before the downbeat, the hypnosis (beds, strikes, chorus, Meine) recedes
  while the footage fades up. The footage is full on the downbeat.
- **Out:** over the last two beats, the footage fades out and the kaleidoscope and strike-cam close
  back over it. The next strike lands on the following downbeat.
- **His faces:** gone before the footage starts to show, and back only 0.3 s after it has gone.
  No head is ever over the dead.
- **Mechanism:** `real(..., lead=, xout=)`. A window is now `(a, b, xin, xout)`, and the post-pass
  in `build()` ramps every other layer through it.

| viewer bars | code bars | song time | what | music |
|---|---|---|---|---|
| 161-164 | 160-163 | 304.97-312.59 | grid (unchanged, except that it now fades out over its last 2 beats as the strike-cam returns). Tile 1 is now **Roya's rescuers digging by phone light** (`roya-night-rescue-central-gaza-2026-01#3`, src 52, gain 0.12, because its street sound runs about 22 dB hot). The Jabaliya dig is s1's. | 0.3 |
| 172-174 | 171-173 | 325.93-331.64 | **puncture 1**: Khan Younis morgue (AP, 29 Jul 2026). Bodies in bags carried in, then the steel tray. Src 9.76-15.7, all one handheld shot. | 0.4 |
| 179-181 | 178-180 | 339.25-344.97 | **puncture 2**: the remains of 112 under flags, children's photos taped on (MEE). Src 0.76-6.7, segment 0 only. | 0.4 |
| 185 | 184 | 350.68 | Bureij (unchanged) | 0.4 |
| 186-188 | 185-187 | 352.60-358.31 | the Khan Younis morgue arrival, now **3 bars** (src 1.0-6.7, inside shot 0-7.6), soft out | 0.25 |
| 205-208 | 204-207 | 388.78-396.40 | Zinati, then black (unchanged) | 0.05 |
| 209-216 | 208-215 | 396.40-411.63 | the mass funeral: fades up from the black, soft out | 0.3 |
| 225-232 | 224-231 | 426.88-442.11 | the al-Aqsa prayer: soft in and out | 0.3 |

Dropped from the piece (no longer shown anywhere): Roya's torchlight ambulance (old 175), the
Nuseirat bones (old 179) and the Khan Younis women over the shrouds (old 187).

### Music ducks ("too deep/stark ... don't linger")

- **Depth now follows the hold.** The three-bar punctures go to 0.4 (was 0.25 for one bar).
  Bureij plus the morgue is one 4-bar moment: 0.4 under the blast, then 0.25 under the morgue
  (was 0.35, then 0.15 for 2 bars). The 4-bar and 8-bar holds (grid, funeral, al-Aqsa) stay at 0.3.
- **Every release is now at least a bar** (it was 0.5-0.6 s). The music comes back over the bar
  after each window, while the bed is already closing over the footage.
- **Kept:** the deep silence under Zinati and the black bar (0.05). It now comes back over a
  bar, into the funeral, instead of in 0.5 s.
- **Measured** from a music-only render of the new timeline (RMS against the bars around each dip):
  - punctures 1 and 2: -7.5 and -7.4 dB
  - morgue: -11.4 dB
  - funeral and al-Aqsa: -9.7 and -9.8 dB
  - grid: -17.9 dB absolute (about -10 dB)
  - Zinati and the black: -26.4 dB
  - after puncture 1 the level is back to the bed's -7.5 dB by beat 2 of the next bar.
  - (The older "-40 dB" figure for Zinati doesn't match a 0.05 gain: 0.05 is -26 dB.)

### Repeated footage: 0 pairs ("the car scenes ... seems repeated?")

The section now builds with **0 repeated footage pairs**, down from 26 standalone. In full.py
there are 4, listed below. How:
- **Pools are fresh.** `Pools.take(kind, at, before=, after=)` returns only a hit whose source
  window overlaps nothing already placed in the Comp. In full.py that includes s0 and s1. It also
  skips clips shown untreated anywhere: testimony is never reused as spectacle.
  `src_span()` also covers `seq` layers (stutters and freezes), which `Comp._src_span` leaves out.
  A kind that has run dry borrows from its neighbour (ir/fire, gnight/gday).
- **More supply.** There were only about 110 catalogued hits in scope, and the whole piece needs
  more. `s2_kit.onsets()` finds the blasts the catalogue didn't mark: brightness onsets at 50 fps
  (the jump of the brightest 5% of the frame plus the mean; whole-frame changes are skipped as
  cuts). The results are cached in `comps/out/section_s2_peak.onsets.json`. Calibration: it finds
  the Rafah domes at 8.72, 11.56 and 13.72 (catalogue: 8.721, 11.560, 13.721), and black-hot
  2014 at 12.76 (catalogue: 12.761). Onsets count as hits only in footage tagged as a blast
  (`BLAST_TAGS`). The pools now also take y2026 (Israel's strikes; not Iran's strikes on Israel,
  not interceptor promos, not the Wishah strike-cam) and catalogued hits of strength 2 or more.
  Sizes: ir 46, fire 70, gnight 32, gday 24.
- **The odd-bar stutter is now an echo.** It retriggers the bar's own strike (0.3 s, inverted)
  on beats 3, 3-and and 4. This is a deliberate motif and needs no new footage. It overlaps by
  0.3 s, under the 0.5 s that counts as a repeat.
- **Off-grid second blasts.** When a second blast inside a strike's window would land off the
  grid, `strike()` ends the window short of it.
- **Hand-picked takes yield to s1.** The Rafah domes (125-127), the blasts on 129 and the dusk
  fireball on 131 are used only if no earlier section has shown them; otherwise those hits come
  from the pools. In full.py they come from the pools. Other changes to avoid s1's material:
  - lull walkers: now `ap-drone-return-north-coast-2025-01#3`
  - plateau crowd: now the Salah al-Din road crowd (`ap-salahaldin-crossing-return-2025-01#0`,
    grooved at x0.58)
  - Ashdod: s1 has the crane cycle, segment 1; s2 now has segment 0 (the lit port) and
    segment 2 (the convoy)
  - the shroud window at 218: now anchored at 96 (the breath at 120 shows 84-89)
- `RESERVED`: the clips placed by hand later in the section, which the pools leave alone.
- The cooling strike on code bar 204 is gone. It played entirely inside Zinati's window.
- **Left in full.py (4 pairs):**
  1. The MQ-9 **countdown** (`mq9-live-hellfire-holloman#7`) is in both s1 (bars 70-72) and s2
     (code 122-124). I kept it as a deliberate rhyme: the build's countdown and the peak's.
     If ember wants it gone, one of the two sections needs another countdown.
  2. s1 shows three shots from inside the src range of **s2's continuous IDF crater take**
     (code 126-140, src 0.57-29.96): `form-strike0`, `build-strike-65.0` and `idf-strikecam-96`.
     The take is one designed piece (four hits at x1.0), so s1 should give up those shots.

### F-35 removed ("i don't want to use that footage. it confuses me")

The Lockheed CGI factory is gone. At code 232-237 (viewer 233-238, 442.11-453.54) there is now
**the 200th IMOD airlift of the war** (`imod-200th-airlift-plane-2026-03-26#3`, 26 Mar 2026):
on a wet night apron, pallets of munitions come down the scissor loader from the freighter and
trail away on dollies.
- One pallet cycle to two beats; screen plus lumakey, opacity 0.6, under the crowd walking north.
- Crop [0.14, 0.06, 1, 0.8] removes the IMOD logo and the Hebrew subtitles.
- Kept as diegetic: the M.O.D vests, a Hebrew placard on a loader, and the Ashdod port sign
  (code 216-219).

### Captions

New material was checked frame by frame:
- strike takes at 310-386 and 419
- the grid, the punctures, the morgue, the plateau

Fixed: the IMOD camera icon on Ashdod (now x0 0.12) and the airlift subtitles. No other
lower-thirds turned up. The pools pick different takes in full.py than in the standalone build,
so a full-piece render should get the same 1 s sweep.

## Revision 3: "full truth" (ember, 2026-10-24); this section overrides the map below where they differ

The hypnotic bed stays: chorus, kaleidoscope, strike-cam spectacle. It is now **punctured by
untreated reality**.
- **Treatment.** Untreated layers are full frame (or a full-picture grid), normal blend, no fx,
  their own sound, with `c.duck_music` under them.
- **`real()` helper.** It opens a "reality window". Inside it `build()`'s post-pass mutes every
  other layer of the section (chorus, beds, strikes, his head), drops any word he would say, and
  ducks Meine to 0.
- **The preacher near the dead.** He is never on screen over the dead. At Bureij (a living man
  thrown by the blast) he is small, still and at the side.

| bars | song time | what | music |
|---|---|---|---|
| 160-163 | 304.97-312.59 | **stack**: a 2x2 grid of untreated ground takes, one tile per beat, held 4 bars, all four sounds. Tiles: Shifa wounded (y2026), Jabaliya digging by hand, Shifa stretcher with blood (Roya), men kneeling over shrouds (Khan Younis) | 0.3 |
| 171 | 325.93 | puncture: bodies on a steel morgue tray (AP Khan Younis, Jul 2026) | 0.25 |
| 175 | 333.54 | puncture: the wounded lifted into an ambulance by torchlight after an overnight strike in central Gaza (Roya News, 9 Jan 2026; src 5.0, logo/date tag/handle cropped [0.12, 0.14, 1, 0.86], gain 0.2 because its street sound is ~22 dB hotter than the AP takes) | 0.25 |
| 179 | 341.16 | puncture: bones laid on dark cloth (Roya, Nuseirat, Sep 2026) | 0.25 |
| 184 | 350.68 | Bureij: the blast throws a man, portrait frame, own sound; "Hellfire missiles" small at the side | 0.35 |
| 185-186 | 352.60-356.40 | Khan Younis morgue arrival, bodies rushed in, full frame | 0.15 |
| 187 | 356.40 | puncture: women bent over the shrouds (AP Khan Younis, Aug 2026; identifiable mourners) | 0.25 |
| 191 | 364.02 | puncture: the remains of 112 under flags, children's photos taped on (MEE) | 0.25 |
| 204 | 388.78-393.68 | **Zinati** (below), then black to bar 208 | **0.05** (measured: music at about -40 dB in the black) |
| 208-215 | 396.40-411.63 | **linger**: the mass funeral of the Hassayna and Abu Sharia families (AP, 4 Aug 2026), one 15 s take: aerial of the rectangle of bodies, then along the rows | 0.3 |
| 216-223 | 411.63-426.88 | the machine: Ashdod MK-84 cranes; he returns (lines on 217 and 221) | full |
| 224-231 | 426.88-442.11 | **linger**: outside al-Aqsa Martyrs Hospital, Deir al-Balah (AP, 28 Dec 2023), men stand in prayer over white body bags on the pavement, ambulances behind, a boy watching. One 15 s take (src 56.0-71.2, inside the single shot 54.7-79.9), its own quiet sound at gain 3.0 (the source sits ~4 dB under the sieve take) | 0.3 |
| 232-237 | 442.11-453.54 | blueprint factory and walkers; his last lines on 233 and 236 | full |

The cooling strikes and copies of 196-203 still play. Bar 204's chorus copies and strike are
muted by the window.

**Silences.** The music nearly disappears at 204-207: 0.05 under Zinati and the black bar. It dips
to 0.15 under the morgue (185-186), 0.25 under each puncture, and 0.3 under the grid, the funeral
and the al-Aqsa prayer.

**Zinati: included, once.** It is Guardian "Deconstructed", eyewitness footage by Tamer Labbad,
source 2.0-6.9 s: the boy stoops by the wounded paramedic, the second strike, dust.
- It is not a hit. It starts on bar 204 and plays at speed 1 with its own sound, so the strike
  lands wherever it happened (song about 392.3, between beats). It carries no `hits_song`.
- The chorus has already left. His face is gone. The music is almost gone. A bar of black follows,
  then the funeral.
- **Reasoning:** my earlier refusal was about landing a child's death *on a beat*. That would make
  it a device, and that is still out. ember's point is that leaving it out keeps the viewer at the
  perpetrators' distance. Shown once, untreated, held and heard, it is testimony, not decoration.
- Caveat: the Guardian's own forensic circle marking the incoming munition is visible around 4.5 s
  of the source. I kept it, since it's part of the record. The Guardian title card after 7 s is not
  used.

**Names** (`meta.people`, from the catalogue provenance only):
- `real:zinati`:
  - Mohammad Abdul Zinati, 15, killed
  - Sharif Shadi Labad, civil defence paramedic, injured
  - Tamer Labbad, eyewitness who filmed it
  - source https://www.youtube.com/watch?v=vQdUgwKtwEY
- No named individuals in the sources of the other untreated clips. The funeral's provenance names
  the Hassayna and Abu Sharia families, not individuals, so I added no `people` entry.

**Each untreated clip once in the whole piece (2026-10-24).** `full.py` refuses duplicates. s1 and s2
had both used Zinati, Bureij, the Khan Younis morgue, the MEE 112 remains and Hammad. Zinati, Bureij,
the morgue and MEE 112 stay here; Hammad's sieve stays in s1's breakdown, so 224-231 is now the al-Aqsa
prayer take (manufacture against burial: the Ashdod cranes before it, the factory after). Inside this
section no untreated *segment* repeats: puncture 175 used the same Shifa-arrivals shot as grid tile 0
(src 11 vs 12), so it is now the Roya ambulance. The morgue's two uses are different shots (arrival,
src 1.0-4.8, shot 0-7.6; the tray, src 13.0-14.9, shot 7.6-17.2), and so are the Khan Younis mourning
clip's (grid tile src 20.5, puncture 187 src 1.0).

**Captions.** All of the new material was swept at 1 s. AP bugs are cropped (top 0.16), along with
the funeral's subtitles and "ASSOCIATED PRESS", MEE's Instagram credit, and the Guardian logo and
title. The low-fx variant is left to `tools/variant.py --lowfx`.

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
  falls away. A close night blast in Khan Younis (Guardian, 6 Feb 2026; it whites out the frame) lands on the same
  downbeat. **The tracking shot freezes**
  (`meine-freeze` holds Meine's frame of bar 120, then desaturates, blurs and dims) for the breath.
  This is the only time the spine of the piece stops.
- **120-123, the breath.** A morgue worker cuts shroud cloth (one cut about every 3 beats). It is
  screened over the frozen road while the preacher drifts across it small (the drift path). From
  122.5 the MQ-9 monitor shows TARGET, then **3, 2, 1 every two beats** (122.5, 123, 123.5), and the
  strike lands on **124 as the kick returns**, as he says "MISSILES" big in the centre.
- **124-131, re-entry.** The eight-head chorus splits off him, **one copy per bar**, each gliding
  into a slowly turning cube. One continuous IDF strike-cam take over Gaza ("leaving crater", 1 Aug 2026) sits in a
  feathered window with **four hits on bars 126, 132, 135 and 140**, all at about x1.0. It is a
  hand-built time map, because the hits span three catalogue segments of one file. Israel's strikes
  fill the bars the take leaves open: the IDF air-defence strike in Iran (8 Jun 2026) on 128, and
  the IDF "weapons sites" strike-cam over Gaza (9 Sep 2026) on 130.
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
  - **Bar 184, the human cost:** "Hellfire MISSILES" (his face moved to the right, so it doesn't
    cover the picture) lands on Bureij, 19 May 2026 (Anadolu phone video, portrait, in its own
    frame): a night street, the blast behind a man throws him off his feet, on the downbeat.
  - **Bars 185-186:** bagged bodies rushed from an ambulance into the Khan Younis morgue (AP, 29 Jul
    2026; graphic 3, no faces of the dead, `identifiable_victims: false`). Two bars, normal blend,
    no effects.
  - **Why these two:** the human cost of one strike as cause and effect, a person thrown by the
    blast, then the dead arriving. I passed over the Guardian Zinati clip (the moment a
    15-year-old is killed). It is identifiable, and landing a child's death on a downbeat is
    exactly the gimmick to avoid. I also passed over the MEE tent-strike bodies (a caption runs
    throughout) and the mass funerals (used elsewhere in spirit, and slower).
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

- **Scope (ember's rule):** all footage is Israel/Gaza or US arsenal; `c.save()` passes. Three
  layers were swapped out:
  - `mosul-into-dip` (OIR, bar 120, 3:48.8) became Guardian Khan Younis 2026.
  - `iran-take` (CENTCOM Iran, bars 126-136) became the IDF Gaza crater strike-cam (126, 132, 135,
    140), plus IDF strikes on 128 and 130.
  - `gun-tape` (Apache 2008, bar 184, 5:50.7) became Bureij plus the Khan Younis morgue (bars 184-186).
- **Graphic 3:** the Khan Younis morgue arrival, bars 185-186 (5:52.6-5:56.4). The prayer over the shrouded (`ap-aqsa-children-mourned-2024-08#3`)
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
  - After the scope swap, a second sweep (every 1 s across the whole span) found:
    - a vertical "IDF / AFP" credit on the weapons-sites strike-cam at 4:08. Fixed by cropping
      x0 to 0.14.
    - IDF "Secondary Explosions" labels at 5:27 and 5:50, from `idf-beit-hanoun-launcher-2014`.
      That clip is now in `CAPTIONED`.
  - The crater take's Forbes lower third, "VIDEO: IDF VIA CNN" and date are cropped away
    ([0.05, 0.09, 0.87, 0.7]). So are the Guardian logo on Khan Younis and the AA logo and
    location tag on Bureij.
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
