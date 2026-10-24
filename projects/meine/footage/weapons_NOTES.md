# Weapons lane: notes

Catalog: `weapons.json`, with 94 clips, 260 segments and 97 frame-checked hit points. The files total about 1.9 GB in `media/footage/weapons/raw/`. Attribution is in `weapons_SOURCES.md`.
Contact sheets are `media/footage/weapons/sheets/<stem>.png`, which tile row-major, 8 across. The interval is printed by the sheet tool: `max(1, duration/40)` s. Hit strips are `hits_<stem>/` and `hitsheet_<stem>.png`.

## What's here

| group | clips | character |
|---|---|---|
| Hellfire / Apache / MQ-9 | ~12 | DVIDS range shoots (Yakima, Greece, Red Sands), MQ-9 Hellfire loading from crates, ground-control screens showing "TARGET" and a countdown, and a 2008 Iraq gun tape |
| Strike-camera (US) | ~14 | CENTCOM Yemen and Iran 2024-26, OIR Iraq/Syria 2015-18. Grey/white/black-hot IR, green UNCLASSIFIED slates, redaction squares |
| Strike-camera / aerial (IDF) | ~12 | Cast Lead 2008-09, 2011, 2014, and Oct 2023 colour aerial fireballs over the Gaza coast; NV infantry |
| Israeli air force | ~10 | F-35I/F-16I/F-15I takeoffs, bombs in hardened shelters, night afterburner launches for Iran/Yemen |
| Supply chain | ~20 | 155 mm forging (Scranton) and lines (Iowa), JDAM build (Whiteman, Balad, Boeing St Charles), SDB loading, C-17s (incl. the first munitions C-17 into Nevatim, Oct 2023), and the **MK-84 ship unloaded at Ashdod** (IMOD, Feb 2025) |
| Launches / sky | ~14 | Tomahawk night and day (CENTCOM, Philippine Sea 2014), carrier cat shots, HIMARS in the Negev, Iron Dome and Iran-war interceptions over Tel Aviv and Jerusalem 2021-26 |
| Politics / marketing | ~10 | House and Senate aid votes, Blinken with Netanyahu, Lockheed F-35/F-35I marketing (incl. the blue CGI factory), the IDF "Meet the F-35I" infographic, Sky's analysis of IDF strike videos, Forensic Architecture's Rafah bomb ID, and AJ's explainer on high-powered bombs (incl. WP airburst) |

Graphic levels: 192 segments at 0, 64 at 1, 3 at 2 and 1 at 3. This lane is mostly the machine, not the bodies. The ground lane carries the graphic weight. The one graphic-3 segment is the 2008 Apache gun tape: `apache-gun-tape-iraq-2008` 45-74.5, Hellfire into a group of people at **72.12**.

## Top 15 segments

1. **`hellfire-symphony-tads` 30-35.5**: false-colour Apache sight with a pink/orange/blue fireball (hit 32.14). Its title card at 0-4.5 reads "Apache in G Major" (the Army's own irony).
2. **`centcom-iran-strikes-jul2026` 43.4-69**: six strike-cam hits in 25 s (44.90, 49.12, 53.97, 57.83, 61.27, 65.97). The black ink-blot on white at 53.97 is the strongest single frame. It is made for beat-locked cutting.
3. **`idf-gaza-strikes-oct13-2023` 14-30**: orange fireball at the Gaza shore (14.88), then a long drift over a row of smoke columns. There are more fireballs at 12.32 and 31.40.
4. **`imod-mk84-ashdod-feb2025` 8.5-28**: the actual 2,000 lb bomb shipment, craned off a ship at night under sodium light.
5. **`scranton-155mm-nosing-redhot` 0-32**: red-hot shell noses descending into a press in the dark, with a ~4 s cycle. It keys on black.
6. **`tomahawk-night-philippine-sea-2014` 4.5-40**: a ship deck erupts orange to white in total darkness (5.02, 40.66).
7. **`oir-mosul-vbied-facility-2017` 3-53**: white-hot detonations one after another (9.66, 16.28, 23.95, 30.16), about 7 s apart.
8. **`gbu39-sdb-promo-nellis` 9.5-14.2**: a fireball under the ad copy "GBU-39 / OVER 46 MILE RANGE" (10.96). The SDB is the bomb in many Gaza strikes.
9. **`israel-gbu31-prep-oct2023-reedit` 7.5-30**: endless rows of 2,000 lb bombs with JDAM kits. Its provenance is caveated.
10. **`ap-interceptions-telaviv-jun2025` 21.5-41**: the Tel Aviv skyline as a screen of light; the sky flashes white at 33.77 and 38.87.
11. **`aj-high-powered-bombs-explainer` 156.4-163**: a white-phosphorus airburst unfolding into falling gold embers on black (157.22).
12. **`idf-strikes-jan2014-blackhot` 8-17**: an inverted, black-hot blast spreading like ink (9.60, then a secondary at 12.84).
13. **`ap-interceptions-jerusalem-mar2026` 23.5-34**: a white intercept burst with corkscrew contrails on deep blue.
14. **`mq9-live-hellfire-holloman` 56-80**: a drone monitor with a red "TARGET" box, then "3, 2, 1" (69.60/70.62/71.72) and the strike (72.64). The countdown lands on beats almost by itself.
15. **`lm-f35-factory-animation` 0-105**: Lockheed's glowing blue wireframe assembly line on black. It is the cleanest overlay for the preacher's multiplying heads.

Honourable mentions:
- `oir-habbaniyah-convoy-2016`: convoy strike, black-hot.
- `f35i-nevatim-takeoffs`
- `mq9-hellfire-reload-gulfport` 10-12.4: Hellfires in their crates.
- `apache-red-sands-uas` 22-28.6: three stacked Apache silhouettes, good for tiling.
- `hellfire-yakima-broll` 9.8-26.5: an Apache hovering head-on, a "face" that echoes the preacher.

## Keying candidates

- **Bright on black** (screen/add): `tomahawk-night-philippine-sea-2014`, `centcom-iran-strikes-jul2026` 15-42, `iaf-night-launch-feb2026` 10-21.5, `iaf-rising-lion-shelters-jun2025` 25.5-33.5, `centcom-houthi-night-cat-launches`, `centcom-sanaa-night-launch-dec2024`, `ynet-iaf-takeoff-iran-jun2025` 9-25, `ap-interceptions-jerusalem-mar2026` 12-22.5, `ap-jerusalem-night-streaks-jun2025` 13-18.5, `ap-telaviv-intercepts-may2023`, `aj-high-powered-bombs-explainer` 156.4-163, `scranton-155mm-nosing-redhot`, `lm-f35-factory-animation`, `idf-castlead-nightvision-2009` (round green vignette)
- **White-hot IR flashes** (hard strobes on beats):
  - `dvids_504731` (`oir-bayji-vehicle-2017`): 11.34, 14.13
  - `mq9-strike-yemen-2024`: 2.38
  - `oir-strike-feb2015`: 9.11
  - `hellfire-symphony-tads`: 8.90, 41.91, 44.98, 50.58
  - `oir-mosul-vbied-facility-2017`
- **Black-hot / white backgrounds** (multiply/darken): `idf-strikes-jan2014-blackhot`, `oir-ramadi-bridge-2015`, `oir-susah-fuel-truck-2018`, `centcom-iran-strikes-jul2026` 53.97, `idf-weapons-storage-2011`, and the Forensic Architecture white pages.
- **Sky-only** (luma key): `f35i-nevatim-takeoffs` 30-41, `mq9-nevada-flying`, `reuters-interceptor-contrail-feb2026` 0-7.5.

## Rhythmic material (`motion_tempo`)

- 155 mm press: ~4.0 s
- Iowa line hands: ~3 s
- Ashdod crane cycle: ~5 s
- Carrier launch cycle: ~4.5 s
- Countdown: 1.05 s/step, which is close to 2 beats at 126 BPM (0.952 s)
- Apache rotor: ~0.25 s
- NV infantry walk: ~0.6 s

The Tomahawk volleys in `centcom-epic-fury-tomahawks` come every ~5 s: 10.88, 19.85, 24.56, 40.0, 45.2, 49.8, 54.96.

## Text and slates worth using as graphics

- Green "UNCLASSIFIED" OIR slates in five clips. Their typed descriptions read: "COALITION STRIKES DA'ESH FIGHTERS FLEEING IN A CONVOY".
- "Apache in G Major".
- "OVER 46 MILE RANGE".
- "ARTIFICIAL INTELLIGENCE USED TO GENERATE KILL LISTS".
- The IDF "TARGETS STRUCK 4,000+" infographic.
- The 2008 gun-tape card, which reads "engage individuals with 1 x hellfire missile".

## Gaps

- **No Hellfire production line.** Lockheed has no first-party Troy/Ocala footage online that I could find. The factory material is artillery shells, JDAM kits, SDBs and F-35 airframes instead.
- **No R9X footage**, only animations.
- **IDF strike footage from 2024-25 Gaza** is thin. The Oct 2023 IDF aerial and the Sky grid are the closest. More could come from the IDF Telegram/X; I did not search there.
- **US Congress**: no vote-tally board close-up, only floor wides and speakers.
- **A Hellfire launch from an MQ-9 on camera**: `mq9-nevada-flying` should contain one per its title, but the 6.7 s sampling missed it. Scan it at 1 s to find it.
- Hits are recorded only where I looked at frames. Mostly static segments (factories, politics, flights) have `hits: []` on purpose. Several long clips (`juniper-oak-2023-broll`, `f16-gbu39-sortie-cockpit`, `c17-onload-deployed`, `gbu39-load-mq9-night`, `iaf-swords-of-iron-loadout-reupload`) are catalogued in broad ranges and deserve a finer pass before use.

## For the merge step

- `id`s are unique slugs; `file` paths are repo-relative.
- Hit `t` is absolute in the file and refers to the visual frame (±0.04 s unless a note says ±0.08).
- The scratch tools I used (sheet, hit-strip stacker, frame rows with timestamps) are in this session's scratchpad. The frame-row tool (PIL plus ffmpeg, timestamps in yellow) is worth promoting to `tools/` if the merge needs more checking.
