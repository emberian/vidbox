# s1_build v2: 0:38 to 3:45 (bars 20 to 118)

This is v2, built on ember's direction after watching v1:
- His face is there only while he talks.
- A second rant runs around 85 s.
- He fades back in around 3:30.
- All footage is in scope (Israel and Gaza, arms to Israel, the US arsenal).
- Untreated reality goes in with its own sound: lingering shots and stacks.

Run `uv run python projects/meine/comps/sections/s1_build.py`. The v1 script is kept at `/private/tmp/claude-501/-Users-ember-Downloads/42340d15-64ac-4c01-9187-25feb7131eb1/scratchpad/composeA/s1_build_v1.py` for reference.

Viewer: http://127.0.0.1:8765/studio/timeline.html?tl=projects/meine/comps/out/section_s1_build.timeline.json

`c.save()` reports 159 layers: 90 hits on the beat, 2 on 8ths/16ths (the bar 50 eighth-note stutter, deliberate) and 0 off the grid. No layer is out of scope.

## Rant 2

- `projects/meine/sync/rant2.json` places face.mp4 at start 83.813 s and writes `media/derived/face_rant2.mp4` and `rant2.resolved.json`. The rant runs 84.01 to 120.93.
- Pins:

| word | lands on | song s |
|---|---|---|
| "missiles" #1 | downbeat 47 | 89.73 |
| "missiles" #2 | beat 197 | 94.02 |
| "missiles" #3 | downbeat 50 | 95.45 |
| "missiles" #4 | beat 205 | 97.83 |
| "missiles" #5 | downbeat 54 | 103.06 |
| "missiles" #6 | beat 221 | 105.44 |
| "enough" #1 | beat 244 (downbeat 61) | 116.40 |
| "enough" #2 | beat 248 | 118.31 |

- The motion is `paths/face_rant2_gaze.json` (`selfmotion --mode gaze --sync`).
- The main head is held at 0.72 of the path's scale, because at full scale he and eight copies filled the frame.

## Bar map

| bars | song s | on screen |
|---|---|---|
| (s0 tail) | 36.84-40.2 | The s0 preacher's last frame dissolves out, blurring and sinking slightly, over about 3.4 s. |
| 20 | 38.30 | The "Apache in G Major" false-colour fireball on the downbeat (US arsenal), Meine dipped to 40%. No heads. |
| 21-27 | 40-53 | Scranton's red-hot 155 mm noses, hue-keyed (red only) and bloomed, one press stroke per 2 bars. Meine otherwise. |
| 28-31 | 53.5-61.2 | Beat-cut panels: a JDAM fuze screwed home and JDAM kits fitted (Whiteman); bomb noses on the stand from bar 30. |
| 32 | 61.16 | An IDF strike-cam whiteout (Gaza crater, Aug 2026), screened, with a dip. |
| 32-35 | | The MK-84 ship at Ashdod (IMOD), one crane cycle per 2 bars, screened. |
| 36 | 68.78 | An IDF black-hot strike on Gaza (Jan 2014), multiplied. |
| 36-39 | | The first US munitions C-17 into Nevatim (tall window) and apron cuts. |
| 40 | 76.39 | A false-colour Hellfire hit (TADS). Hellfires onto the Reaper rail and out of their crates (panels). |
| 43 | 82.1-84.0 | **He fades in** on his first frame. |
| 44-63 | 84.0-121 | **Rant 2**: the main head is steered by his gaze, chroma-pulsed, with his voice. |
| 44-47 | | Night SDB loading (screened, 1 s to 2 beats). |
| 47 | 89.73 | "Hellfire MISSILES" lands on the downbeat with a Hellfire launch (Apache, US range). **The split**: one copy peels off per beat over bar 47. The 8 copies mouth the rant in unison with him (the same retimed clip, silent) and drift where he looks. |
| 48-51 | | GBU-31 rows and forklifts (Israel, Oct 2023) and IAF pylons, beat-cut. |
| 49.1 | 94.02 | "missiles": the AFP Rafah domes, their hits landed on the grid. |
| 50 | 95.45 | "missiles": the IDF Gaza-shore fireball, stuttered three times on eighths. |
| 51.1 | 97.83 | "missiles": a Reuters night fireball over Gaza City. |
| 52-55 | 99-107 | The heads pass "thou / shalt / give / Israel" (twice): one copy swells on each word, and all of them swell on each "missiles". 54 (103.06): an IDF Oct 2023 aerial fireball, normal blend. 55.1 (105.44): the NBC night tower collapse. |
| 56-59 | 106.9-114.5 | The copies plus 12 more small heads form a ring, then a sphere, around him, spun on the grid, all mouthing the rant. The civil-defence dig panel (Al Jazeera bug cropped) begins. The Khan Younis drone bed is faint underneath. |
| 60-63 | 114.5-122 | The copies bounce off the walls on 2 beats, then every beat. All of them swell on "I'm not paying ENOUGH" (61, 116.40, and 118.31). The coast-road walkers bed. |
| 63 | 120.93 | The rant ends. **Every head falls back into him and fades over about 1.2 s** (gone by 122.1). |
| 64-71 | 122-137 | **No heads.** 64: the IDF crater strike-cam. 65: a Reuters fireball. 66-67: **the stack** (below). 68-69: news.com.au night tower, IDF Beit Hanoun, Reuters. 70 b2-72: the Reaper countdown "3, 2, 1" on two-beat steps, its blast on bar 72 (shortened, so it is gone by 138.3). The flour-crowd bed. |
| 72-75 | 137.4-144.97 | **Untreated** (below). The music is pulled down to 12%. |
| 76-83 | 145-160 | **Untreated**: Hammad, then the stack. |
| 84-87 | 160-167.8 | **Untreated**: the Nasser courtyard graves fill the picture with their sound while the riser climbs. |
| 88-95 | 167.8-183 | Launches on alternate downbeats, each with a dip: HIMARS in the Negev (Juniper Oak), an Apache Hellfire (Red Sands), an Apache Hellfire (Yakima) and a PAC-3 (Lockheed 2026). Night strikes on Gaza on the odd bars. No heads. |
| 96-99 | 183-190.7 | People returning north on the coast road, grooved so each step is a beat. IDF strike-cam on 96 and 98. |
| 100-103 | 190.7-198.3 | **Untreated** Deir al-Balah (below). |
| 104-111 | 198.3-213.5 | The Lockheed CGI F-35 line, screened (its diegetic labels kept). 104: an IDF strike (Times Radio repost, captions cropped). 105-107: strikes. 108: a white-phosphorus airburst over Gaza. 109: **untreated** Bureij (below). |
| 110-111 | 209.7-213.5 | **He fades back in** (still frame, silent), then says "They need more and more MISSILES", landing MISSILES on bar 112's downbeat with his voice (face.mp4 9.08-10.26). |
| 112-117 | 213.5-225 | On MISSILES he splits: 8 copies bounce (2 beats, then every beat) and 20 small heads form a sphere, then a cube. A strike on every 2 beats, then every beat. Jabaliya digging by hand (grooved). 116: "missiles" on each beat, a different copy each time (`c.say like=`). 117: "thou / shalt / give / Israel" passed between copies. |
| 118 | 224.967 | **Handoff.** Every head collapses to the centre and vanishes on the downbeat. A six-voice "missiles" chorus sounds there. One night-blast flash (AP, from Israel) fades out across the bar, ending at 226.871. Clean Meine follows. Lane B may fade in from 223.06; those last two bars are my busiest. |

## Untreated moments, silences, stacks

"Untreated" here means: normal blend, no effects, no key, no heads on top, the footage's own sound, a large frame.

- **137.82-142.77, Zinati, Gaza City, 15 Sep 2026** (Guardian, eyewitness footage by Tamer Labbad).
  - Shown full-picture from 138.3. The second strike lands on bar 74's downbeat, 141.17.
  - The music is ducked to 12% across bars 72-75.
  - It is cut 1.6 s after the strike, before Guardian's split screen and place card. Meine alone follows until 145.
- **144.97-160.0, Mahmoud Hammad sieving the sand of his home for the remains of his wife and children** (AP, Jan 2026).
  - Full picture, one shake every two beats (retimed to the grid), so his fingers lift the fragments on the grid.
  - Sound at gain 1. Music at 15% for bars 76-79.
- **Stack 80-83, over Hammad**, three windows landing one per downbeat (81, 82, 83), each with its own sound (gain 0.6). Music at 20%.
  - The remains of 112 people under flags (MEE, with their photos).
  - Bodies at the Khan Younis morgue (AP).
  - The Nasser courtyard graves (NBC).
- **159.99-167.82, the Nasser courtyard graves** fill the picture, with their sound, while the music climbs back.
- **Stack 66-67 (125.84-129.73)**: four strikes on Gaza land one per beat into the four quarters of the picture and stay there, each with its sound (gain 0.45). Meine dipped to 30%, music to 45%.
  - Zeitoun cemetery (AP, Feb 2026)
  - Reuters, 22 Oct 2023
  - Maghazi dusk (AP, Jul 2026)
  - NBC night tower
- **190.38-198.30, Deir al-Balah tent camp, 26 Mar 2026** (Guardian / AP). A tall untreated window.
  - The fireballs land on bar 100's downbeat; people duck and run; the sound is at gain 1.
  - It then holds still on the smoke over the tents to bar 104.
  - Music at 25% for about 3.5 s.
- **207.33-210.33, Bureij camp, 19 May 2026** (Anadolu, eyewitness phone). A night blast on bar 109's downbeat knocks a man in the street off his feet. Tall window, its own sound, music at 30%.
- **No heads over any of these.** The head-free stretch runs 122.1 to 209.7. He returns only at 210, after the Bureij window ends.

## People named (`meta.people`, from source provenance only)

- **Mohammad Abdul Zinati**, 15, killed. Source: https://www.youtube.com/watch?v=vQdUgwKtwEY (Guardian).
- **Sharif Shadi Labad**, civil defence paramedic, injured. Same source.
- **Tamer Labbad**, filmed the footage. Same source.
- **Mahmoud Hammad**, father; his wife and children were killed. Source: https://www.youtube.com/watch?v=XoQWFfNR_M8 (AP).

The MEE 112 tile shows photos of the dead, but no names are in its provenance, so none are given. The morgue, graves, stack and strike clips name no one.

## What was swapped for scope

| v1 clip (out of scope) | used for | replaced by |
|---|---|---|
| OIR Mosul (other) | strikes at 32, 50, 63, 107 and fast strikes | IDF Gaza crater strike-cam (y2026) |
| CENTCOM Iran (region) | ink blot at 54; montage 96-103; fast strikes | IDF crater strike-cam, IDF Haniyeh office (2008), IDF Beit Hanoun, Times Radio IDF repost |
| CENTCOM Tomahawks (region) | launches 88-95 | HIMARS Juniper Oak, Apache Red Sands, Apache Yakima, PAC-3 |
| Tomahawk Philippine Sea (other) | strike 104 | IDF aerial fireball (Times Radio) |
| JDAM Balad (other) | panel | JDAM build Whiteman #1 |
| SDB feature (other) | fast strike | A-10 bomb at Nellis (US arsenal range) |
| AP flares (cloudy night) | strike | AP flares and explosions, Nov 2023 (no lower-third) |

## Caption sweep (two passes, a frame every 2 s, offset by 1 s)

| leak | fix |
|---|---|
| Guardian burned-in captions at 194-197 ("This video shows an explosion...", "At least one person was killed") | Window ends before them and holds a clean frame. |
| Guardian place card at 143 | Zinati cut earlier. |
| "Secondary Explosions" label on IDF Beit Hanoun at 132 | Top crop 0.24. |
| IMOD camera icon (Ashdod) | Cropped. |
| Al Jazeera bug (civil-defence dig) | Cropped. |
| NBC NEWS NOW bug (graves) | Cropped. |
| Telegram-style watermark on the GBU-31 rows and forklift | Top crop. |
| DVIDS caption (Gulfport carry) | Cropped. |
| Holloman night text card ("This is the largest") | Panel loops before it. |
| Green UNCLASSIFIED banners | Gone with the CENTCOM footage. |
| "OVER 46 MILE RANGE" ad copy | Bar 58 strike removed in the restructure. |
| News lower-thirds on ground strikes | NEWS_CROP. |
| IDF releases rebroadcast with bugs | `idf-` crop. |

- Kept on purpose: reticles and sight data, Lockheed's CGI factory labels, the Guardian forensic circle in the Zinati shot (it is the analysis of the killing), and Meine's own signs.
- Every footage layer has `"clip": "picture"`. Only heads cross the letterbox.

## Open

- The tools/variant.py low-fx variant was not run here.
- Two of my scratch audit processes (srcaudit.py, PIDs 59376/59378 and 63194/63196) hung while the load average was about 28. They have no PID files, so I have not killed them. ember should stop them.
