# s1_build v3: 0:38 to 3:45 (song 38.30-224.97 s)

Bars below are **viewer bars** (counted from 1, as ember counts): viewer bar N = `c.bar(N-1)` in the code.
The v2 notes and script are backed up in the s1v3 scratchpad (`s1_build_NOTES_v2.md`, `s1_build_v2_before.py`).

Build: `uv run python projects/meine/comps/sections/s1_build.py`, which reports 189 layers, 0 repeated
footage pairs and 0 hits off the grid. Viewer: http://127.0.0.1:8765/studio/timeline.html?tl=projects/meine/comps/out/section_s1_build.timeline.json

## v3, from ember's notes on v2

- **Real speakers on top of the scenes.** Politicians come between the rants, preachers after rant 2.
  - Each is named and dated by a lower-third in the letterbox under the picture, so the text never covers a face or a victim.
  - Over the dead they are still, plain (no fx) and to one side.
  - Elsewhere they join the beat play: a pulse, a sway, a light RGB split, and a swell on their key words.
  - Hyde is never on screen with the dead.
- **The F-35 CGI is gone.**
- **No repeated footage in s1.** The IDF crater strike-cam belongs to s2, so s1 doesn't use it.
- **Ducks follow ember's rule** via `music_dip()`: a hold under 4 bars stays at 0.5 or above, deep dips only on holds of 4+ bars, and every release lasts at least a bar.

## Speakers

Lines are cut by `tools/preacher_prep.py` into `media/derived/preachers/<clip>__<line>.mp4` (+ a `.json` sidecar with words in the clip's clock):
- **Heads:** facecrop'd ovals.
- **Windows:** the plain cut, as a framed window.
- **Audio:** gently compressed and normalised to -14 LUFS.

`speaker()` in s1_build.py lands one word on a grid time.

| viewer bars | song s | speaker | line (key word on the grid) | under it |
|---|---|---|---|---|
| 22-27 | 41.6-51.2 | Sen. Lindsey Graham, oval, play | "...Hiroshima and Nagasaki... the right decision. Give Israel the BOMBS..." (BOMBS on 26) | Scranton forge |
| 27-29 | 51.1-54.6 | Speaker Mike Johnson, oval, play | "God will BLESS the nation that blesses Israel..." (28) | Scranton / JDAM panels |
| 29-31 | 54.8-58.8 | Sen. Ted Cruz, oval, play | "...those who BLESS Israel will be blessed" (31) | JDAM panels |
| 32 | 59.1-60.0 | Tucker Carlson, window | "WHERE is that?" (32) | JDAM panels |
| 32-37 | 60.0-69.0 | Rep. Tim Walberg, voice only | "...not a dime on humanitarian aid... like Nagasaki and Hiroshima. Get it over QUICK" (QUICK on the bar-37 strike) | strike 33, Ashdod MK-84 ship |
| 37-39 | 69.4-74.7 | Nikki Haley, Hannity voice + window of her writing on a shell | "FINISH them. Finish them." (39) | C-17 at Nevatim |
| 40-43 | 74.8-80.8 | Rep. Andy Ogles, window | "that's my taxpayer dollars... I think we should KILL them all" (43) | Hellfires |
| 65-66 | 121.9-126.5 | Pastor Jack Hibbs, oval, play | "We are actually insulting GOD by hamstringing his own people" (66) | strikes as Hyde's heads fade |
| 69-72 | 129.7-137.4 | Pastor John Hagee, CUFI broadcast window (left) | "...We must give them the weapons of war to win that FIGHT" (FIGHT on the bar-73 blast) | Reaper countdown (moved right), flour crowd |
| 73-74 | 137.6-141.1 | Michele Bachmann, still oval in the sky | "an opportunity to BLESS Israel" (74 beat 3; over before the bar-75 fireball) | **untreated** Maghazi families, dusk |
| 77-80 | 144.8-152.4 | Mike Evans, still oval top-right, waving his Bible | "I will bless them that bless thee... America has been blessed because of this" (I on 77) | **untreated** Mahmoud Hammad sieving |
| 81-84 | 152.2-160.4 | Mike Huckabee, still oval in the gap above the stack | "GENESIS 12, those who bless Israel will be blessed... blessing side, not the curse side" (81) | **untreated** stack of the dead |
| 86 | 161.4-163.1 | Mike Huckabee, still oval top-right | "It would be FINE if they took it all" (86) | **untreated** Nasser courtyard graves |
| 89-94 | 167.6-178.7 | Shane Vaughn, oval, play, sung | "WHAT wonderful days these days are before the coming of the Lord" (89) | launches, night strikes |
| 95 | 179.1-181.6 | Shane Vaughn + 4 silent copies in a ring | "OH, the glory" (95) | launch |
| 97-99 | 182.6-187.2 | Pastor Jack Hibbs, oval, play | "poking the God of Abraham, Isaac, and Jacob right in the EYE" (EYE on the bar-99 strike-cam) | coast-road walkers |
| 101-104 | 191.5-198.4 | Pastor John Hagee, still oval left | "VICTORY was our only aim..." (101 beat 3, after the fireballs) | **untreated** Deir al-Balah window |
| 105-108 | 198.2-206.2 | Rev. Munther Isaac, window, alone, not multiplied, no fx | "HERE in Palestine, the Bible is weaponized against us, our very own sacred text" (105) | untreated drone shot of Gaza City's ruins |

Lower-third texts are in `politicians()` and `preachers()`. Every first appearance gets one; Hibbs's second line doesn't.
Each speaker layer carries `meta.people` (name, role, date, source).

## Other changes from v2

- **Bars 33-37:** the strike is now the Times Radio IDF bombardment (screen).
- **Bar 66:** the IDF soldiers watching a demolition (both strikes were the crater strike-cam, which is s2's).
- **Bars 57-64:** the panel under Hyde's formation is now the Iowa 155 mm shell-line workers (grooved). It used to be the civil-defence body recovery.
- **Bar 51 (m6):** AP's 2014 Gaza City night blast. The NBC tower is shown untreated in the bar-67 stack.
- **Bars 89-95 launches:** HIMARS, Apache Red Sands, Apache Yakima #3 (the old #1 was s0's), PAC-3 triple.
- **Bars 105-110:** the ruins bed replaces the F-35 CGI. The strikes at 105-108 are gone.
- **Bars 113-118:** under Hyde's return, the B-2 bomb-bay loading bed replaces the Jabaliya dig for victims.
- **The fast strikes are all different segments.** The bars 117-118 hits stutter twice, on the beat.
- **Caption crops:** the rise's ground strikes use TIGHT_CROP (0.18-0.72), plus per-clip crops (AP Deir al-Balah night strike, WSJ high-rise, B-2 watermark).
- **Looped panels** are explicit maps, so `repeats()` reads their true source span.

## Ducks (music level relative to raw Meine, measured from a music-only render)

| where | music |
|---|---|
| politicians, Hibbs, Hagee CUFI, Huckabee "take it all", stack 66 (short) | 0.52-0.59 |
| Vaughn | 0.63 |
| Maghazi, Hammad, stack 77-84 (4+ bars) | 0.19 |
| Deir al-Balah, Isaac (4 bars each) | 0.31 |
| Dar al-Muttaqin (short) | 0.63 |

Voice over music (speech-active RMS), at the final gains:
- **Shallow dips:** about +6.5 to +9 dB. Computed from a measurement at 2 dB lower gain, not re-measured.
- **Over the dead:** +16 dB.
- **Hagee at Deir al-Balah:** +10 dB.
- **Isaac:** about +10 dB.

## Open

- **Scope:** comp.save accepts the speaker layers. Their `meta.catalog` "preachers" is not a footage catalog, so scope is not checked for them. Checking it would need comp.py to load preachers.json as a catalog with scope politics-israel.
- **The MQ-9 countdown** is in s1 (bars 71-73) and s2 (123-125), on purpose: ember decides.
- **`full.py`:** 2 repeated pairs: the countdown, and ap-nuseirat-night-strike between 242.7 and 418.6 (both s2 or later, not s1).
- **Questions for ember:**
  - Should Isaac move to the very end of the section?
  - Should Graham's lower-third carry his death year?
  - Bachmann's line and Vaughn's song come from the Iran strikes (Bachmann is dated, Vaughn's card says so). Is Bachmann over Maghazi OK?
