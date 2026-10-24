# Footage scope

Every clip in `weapons.json`, `ground.json` and `y2026.json` now has two fields: `scope` and `scope_note`, a one-line reason. A segment whose scope differs from its clip's also has its own `scope` and `scope_note`. If a segment has no `scope`, it inherits the clip's.

Scopes:
- `gaza`: filmed in Gaza, in any war or year. Also footage from southern Israel looking into Gaza, because what it shows is Gaza.
- `israel`: Israel acting, anywhere. This covers IDF/IAF strikes on Gaza, Lebanon, Iran and Yemen, IDF releases, Iranian fire landing on Israel or intercepted over it, and Israeli territory.
- `arms-to-israel`: weapons shipped, airlifted or unloaded to Israel, or US weapons documented as going to Israel.
- `politics-israel`: US politics about arming or funding Israel, and protests against it.
- `us-arsenal`: US weapons outside combat: range firings, tests, production, loading and showcases.
- `region`: other actors' strikes in the wider war around Israel/Gaza: the US Red Sea campaign against the Houthis, and the 2026 US campaign against Iran fought alongside Israel. **Not in the default set.**
- `other`: everything else. That means US combat in unconnected wars (Iraq and Syria against ISIS, the 2008 Apache tape), Ukraine, and footage that isn't about weapons.

Default allowed set: gaza, israel, arms-to-israel, politics-israel, us-arsenal.

## Counts

Clips per clip-level scope:

| scope | weapons | ground | y2026 | total |
|---|---|---|---|---|
| gaza | 6 | 148 | 55 | 209 |
| israel | 32 | 0 | 18 | 50 |
| arms-to-israel | 5 | 0 | 3 | 8 |
| politics-israel | 4 | 0 | 5 | 9 |
| us-arsenal | 28 | 0 | 8 | 36 |
| region | 7 | 0 | 8 | 15 |
| other | 12 | 0 | 0 | 12 |

Segments and minutes by effective scope (a segment's own scope if set, else its clip's):

| scope | weapons | ground | y2026 |
|---|---|---|---|
| gaza | 17 / 7.7 min | 585 / 166.9 min | 215 / 58.8 min |
| israel | 95 / 28.4 min | - | 64 / 14.7 min |
| arms-to-israel | 11 / 3.5 min | - | 16 / 3.0 min |
| politics-israel | 7 / 3.7 min | - | 15 / 9.3 min |
| us-arsenal | 85 / 31.8 min | - | 31 / 5.0 min |
| region | 14 / 4.0 min | - | 31 / 4.9 min |
| other | 31 / 12.0 min | - | 2 / 0.7 min |
| **Default in-scope** (gaza, israel, arms-to-israel, politics-israel, us-arsenal) | **215 / 75.2 min** | **585 / 166.9 min** | **341 / 90.9 min** |
| Default + region | **229 / 79.3 min** | **585 / 166.9 min** | **372 / 95.8 min** |

The minutes are sums of catalogued segment lengths (out minus in). They are not file durations.

## "region" clips (NOT in the default set)

This is the wider war around Israel and Gaza, fought by other actors. Each note gives the link. Including these is ember's call.

### weapons.json (7 clips, 4.0 min)

- `centcom-iran-strikes-jul2026` (1.1 min): US CENTCOM launches and strike-cam on Iran, July 2026: the resumed phase of the 2026 US-Israel war on Iran; Israel was striking Iran in the same weeks (IDF air-defence strikes, 8 Jun 2026) and PBS calls it 'the US-Israel war with Iran'.
- `mq9-strike-yemen-2024` (0.2 min): US CENTCOM MQ-9 strike on Houthi weapons storage in Yemen, Nov 2024: the US Red Sea campaign against the Houthis, which began after the Houthis attacked shipping in declared solidarity with Gaza (from Nov 2023).
- `centcom-sanaa-night-launch-dec2024` (0.2 min): US carrier launches for strikes on Houthi missile storage in Sana'a, Dec 2024: the US Red Sea campaign against the Houthis, which began after the Houthis attacked shipping in declared solidarity with Gaza (from Nov 2023).
- `centcom-yemen-dec2024-carrier-ship` (0.5 min): US carrier and ship launches for strikes on the Houthis, Dec 2024: the US Red Sea campaign against the Houthis, which began after the Houthis attacked shipping in declared solidarity with Gaza (from Nov 2023).
- `centcom-houthi-carrier-day` (0.6 min): US carrier launches as strikes on the Houthis began, 15 Mar 2025: the US Red Sea campaign against the Houthis, which began after the Houthis attacked shipping in declared solidarity with Gaza (from Nov 2023) (resumed after the Houthis renewed their threats over Israel's Gaza aid blockade).
- `centcom-houthi-night-cat-launches` (0.4 min): US carrier night launches against the Houthis, Mar 2025: the US Red Sea campaign against the Houthis, which began after the Houthis attacked shipping in declared solidarity with Gaza (from Nov 2023).
- `centcom-epic-fury-tomahawks` (1.0 min): US CENTCOM Tomahawk and carrier launches opening Operation Epic Fury on 28 Feb 2026: part of the same 2026 Iran war Israel fought alongside the US (Epic Fury ran in parallel with Israel's Roaring Lion from 28 Feb 2026).

### y2026.json (8 clips, 4.9 min)

- `alarabiya-b2-centcom-2026-03-01` (0.4 min): Al Arabiya package on B-2 strikes on Iran on 1 Mar 2026 (generic USAF B-2 b-roll inside): part of the same 2026 Iran war Israel fought alongside the US (Epic Fury ran in parallel with Israel's Roaring Lion from 28 Feb 2026).
- `centcom-strikes-planes-boats-trucks-2026-03-12` (0.9 min): US CENTCOM strike-cam on day 12 of the US campaign on Iran: part of the same 2026 Iran war Israel fought alongside the US (Epic Fury ran in parallel with Israel's Roaring Lion from 28 Feb 2026).
- `dw-isfahan-fireball-2026-03-31` (0.5 min): Explosions over Isfahan after US strikes on 31 Mar 2026: part of the same 2026 Iran war Israel fought alongside the US (Epic Fury ran in parallel with Israel's Roaring Lion from 28 Feb 2026); the closing Bnei Brak shot carries its own israel scope.
- `reuters-navy-fires-touska-2026-04-19` (0.3 min): US Navy firing on an Iranian-flagged ship enforcing the blockade, Apr 2026: part of the same 2026 Iran war Israel fought alongside the US (Epic Fury ran in parallel with Israel's Roaring Lion from 28 Feb 2026).
- `centcom-hormuz-strikes-2026-06-28` (0.6 min): US CENTCOM strikes on Iran near Hormuz, 28 Jun 2026: the resumed phase of the 2026 US-Israel war on Iran; Israel was striking Iran in the same weeks (IDF air-defence strikes, 8 Jun 2026) and PBS calls it 'the US-Israel war with Iran'.
- `centcom-strikes-iran-2026-07-08-roya` (0.8 min): US CENTCOM strike-cam on Iran, 8 Jul 2026: the resumed phase of the 2026 US-Israel war on Iran; Israel was striking Iran in the same weeks (IDF air-defence strikes, 8 Jun 2026) and PBS calls it 'the US-Israel war with Iran'.
- `centcom-13th-night-iran-2026-07-24` (0.8 min): US CENTCOM strike-cam from the 13th night of strikes on Iran, Jul 2026: the resumed phase of the 2026 US-Israel war on Iran; Israel was striking Iran in the same weeks (IDF air-defence strikes, 8 Jun 2026) and PBS calls it 'the US-Israel war with Iran'.
- `centcom-heavy-wave-iran-2026-07-30` (0.6 min): US CENTCOM strikes on Iran after an Iranian missile attack on a US base in Jordan, Jul 2026: the resumed phase of the 2026 US-Israel war on Iran; Israel was striking Iran in the same weeks (IDF air-defence strikes, 8 Jun 2026) and PBS calls it 'the US-Israel war with Iran'.

## "us-arsenal" clips (in the default set)

US weapons shown as the arsenal itself: range firings, tests, production, loading and showcases.

### weapons.json (28 clips, 31.8 min)

- `scranton-155mm-nosing-redhot` (0.7 min): US Army 155 mm shell production at Scranton (arsenal at home); the provenance's 'supplied Ukraine and Israel' is uncited and not tied to these shells, so not arms-to-israel.
- `iowa-aap-155mm-line-workers` (0.4 min): US 155 mm production line at Iowa AAP: the arsenal at home, no Israel tie.
- `iowa-aap-paint-line` (0.2 min): US 155 mm paint line at Iowa AAP: the arsenal at home.
- `f16-gbu39-sortie-cockpit` (1.8 min): USAF F-16 GBU-39 sortie cockpit GoPro, with no combat theatre named: weapons footage on a training or test sortie.
- `ah1z-hellfire-lejeune-2016` (1.5 min): USMC Hellfire range shoot at Camp Lejeune: range firing.
- `a10-bomb-load-nellis` (0.5 min): USAF A-10 loading and range impact at Nellis: training and range.
- `sdb-feature-deployed-2017` (1.3 min): USAF showcase of the GBU-39 build and loading at Al Dhafra; its one combat strike clip (155.5-163, an anti-ISIS-era strike) is scoped other.
- `gbu39-sdb-promo-nellis` (0.3 min): USAF GBU-39 showcase promo on a Nevada range; the bomb type is used by Israel in Gaza, but these bombs and this footage have no Israel tie.
- `mq9-live-hellfire-holloman` (1.1 min): USAF MQ-9 Hellfire live-fire training at White Sands: range firing.
- `apache-rising-thunder` (0.7 min): US and Japanese Apaches in exercise Rising Thunder at Yakima: training.
- `hellfire-yakima-broll` (0.6 min): US Army Apache Hellfire range shoot at Yakima: range firing.
- `hellfire-symphony-tads` (0.7 min): US Army 'Apache in G Major' Hellfire range shoot at Yakima: range firing.
- `hellfire-greece-flir` (0.3 min): US Army Apache Hellfire range shoot in Greece (DEFENDER 23): range firing.
- `mq9-nevada-flying` (4.5 min): USAF MQ-9 carrying Hellfires on a test flight over Nevada.
- `c17-munitions-onload-selfridge` (1.1 min): Domestic US exercise munitions onload at Selfridge; the provenance says it is NOT a shipment to Israel.
- `iowa-aap-rounds-moving` (0.1 min): US 155 mm production at Iowa AAP: the arsenal at home.
- `scranton-finish-turn` (0.1 min): US 155 mm shell lathe work at Scranton AAP: the arsenal at home.
- `apache-red-sands-uas` (0.5 min): US Army Apaches in the Red Sands 24.2 counter-drone exercise in Saudi Arabia: range firing.
- `f35-gbu31-release` (0.1 min): US F-35 test drop of an inert GBU-31: a weapons test.
- `b52-refuel-centcom-2025` (0.3 min): US B-52 task-force presence flight refuelling over the Middle East; no strike: arsenal showcase.
- `gbu39-load-mq9-night` (5.0 min): USAF crew loading GBU-39s onto an MQ-9: weapons handling.
- `jdam-build-whiteman` (1.5 min): USAF JDAM assembly at Whiteman AFB: the arsenal at home.
- `b2-jdam-load-whiteman` (2.1 min): USAF loading JDAMs into a B-2 at Whiteman: the arsenal at home.
- `c17-night-patriot-delivery` (3.2 min): USAF C-17 delivering Patriot components in the CENTCOM AOR; this is weapons logistics rather than combat, and the provenance says it is not Israel-specific.
- `mq9-hellfire-reload-gulfport` (0.5 min): US Air National Guard Hellfire reload exercise in Mississippi: weapons handling in training.
- `boeing-jdam-400k-stcharles` (0.5 min): Boeing JDAM kit production at St. Charles, 2019; the provenance says the plant supplies Israel's JDAMs, but no Israel-bound weapons are shown (a borderline call; it could flip to arms-to-israel).
- `lm-f35-factory-animation` (1.7 min): Lockheed Martin CGI of the F-35 production line: manufacturer showcase, not about Israel.
- `lm-plant4-f16-f35` (0.3 min): Lockheed Martin F-16/F-35 factory video: manufacturer showcase, not about Israel.

### y2026.json (8 clips, 5.0 min)

- `lockheed-pac3-cgi-accelerating-2026-01-06` (0.4 min): Lockheed PAC-3 production CGI: manufacturer showcase.
- `lockheed-camden-munitions-acceleration-center-2026-02-04` (0.7 min): Lockheed THAAD production expansion and test launches: the arsenal at home.
- `lockheed-pac3-contract-promo-2026-04-13` (0.8 min): Lockheed PAC-3 production and test-launch promo: manufacturer showcase.
- `rtx-tucson-composable-weapons-2026-04-22` (0.5 min): RTX/Raytheon missile production showcase in Tucson.
- `lockheed-troy-munitions-groundbreaking-2026-05-22` (0.8 min): Lockheed THAAD munitions plant groundbreaking and production line: the arsenal at home.
- `lockheed-pac3-triple-short-2026-07-29` (0.3 min): Lockheed PAC-3 production and launch promo: manufacturer showcase.
- `cnn-camden-missile-town-2026-10-04` (0.5 min): CNN on Camden, Arkansas as a hub of US missile production (Lockheed line, Patriot launches): the arsenal at home.
- `pbs-patriot-production-race-2026-10-22` (1.0 min): PBS inside Lockheed's PAC-3 line, with Patriot test launches; the studio intro and Ukraine night-sky segments are scoped other.

## "other" clips (excluded)

These have no link to Israel or Gaza.

### weapons.json (12 clips, 11.8 min)

- `jdam-build-balad-2007` (0.8 min): USAF building JDAMs at Balad, Iraq, 2007, in theatre for the Iraq war, a war unconnected to Israel.
- `tomahawk-night-philippine-sea-2014` (1.9 min): US Navy Tomahawk launches for the first US strikes on ISIL in Syria, 2014.
- `apache-gun-tape-iraq-2008` (1.6 min): US Army Apache gun tape from Iraq, 2008.
- `oir-strike-feb2015` (0.4 min): Coalition (OIR) airstrike on ISIL in Iraq, 2015.
- `oir-ramadi-bridge-2015` (1.0 min): Coalition (OIR) strikes on a bridge near Ramadi, Iraq, 2015.
- `oir-hit-weapons-storage-2016` (0.4 min): Coalition (OIR) strike near Hit, Iraq, 2016.
- `oir-habbaniyah-convoy-2016` (1.0 min): Coalition (OIR) convoy strike near Habbaniyah, Iraq, 2016.
- `oir-bayji-vehicle-2017` (0.2 min): Coalition (OIR) strike near Bayji, Iraq, 2017.
- `oir-mosul-vbied-facility-2017` (0.8 min): Coalition (OIR) strike near Mosul, Iraq, 2017.
- `oir-raqqa-artillery-2017` (0.2 min): US Marine artillery strike near Raqqa, Syria, 2017 (OIR).
- `oir-susah-fuel-truck-2018` (0.5 min): Coalition (OIR) strike on an ISIS fuel truck in as-Susah, Syria, 2018.
- `c17-onload-deployed` (2.8 min): Generic USAF C-17 cargo palletizing and takeoff; no munitions are shown and it isn't about weapons.

## Segments that carry their own scope

- weapons: `sdb-feature-deployed-2017` 155.5-163.0: **other** (clip is us-arsenal). A US combat strike clip from a deployed anti-ISIS-era base, not arsenal footage.
- weapons: `ap-ashkelon-intercept-day-oct2023` 84.6-158.4: **gaza** (clip is israel). Long lens from Ashkelon looking at smoke over Gaza: it depicts Gaza.
- weapons: `aj-high-powered-bombs-explainer` 110.0-116.0: **other** (clip is gaza). Stock F-16 formation with no stated air force; nothing ties it to Israel.
- weapons: `aj-high-powered-bombs-explainer` 156.4-163.0: **israel** (clip is gaza). Unlabelled night WP airburst; Israel's WP use over Gaza and Lebanon is documented but this shot's location is not stated, so it is scoped to Israel as actor, not Gaza.
- weapons: `aj-high-powered-bombs-explainer` 169.5-174.0: **israel** (clip is gaza). Control-room graphic about Israel's AI kill lists.
- weapons: `aj-high-powered-bombs-explainer` 212.4-218.0: **israel** (clip is gaza). Labelled Israeli army strike-cam video.
- y2026: `dw-isfahan-fireball-2026-03-31` 28.0-34.8: **israel** (clip is region). Bnei Brak, Israel: roof damaged by Iranian fire.
- y2026: `ap-yellow-line-embed-2026-05-26` 10.0-14.0: **israel** (clip is gaza). Israeli soldiers on the Yellow Line: the IDF itself on camera.
- y2026: `guardian-deconstructed-zinati-strike-2026-09-15` 60.0-80.0: **israel** (clip is gaza). Screenshot of an IDF statement.
- y2026: `aje-white-house-40000-bombs-2026-09-16` 10.0-22.0: **gaza** (clip is politics-israel). Archive cover shots of Gaza ruins (undated).
- y2026: `pbs-patriot-production-race-2026-10-22` 0.0-32.0: **other** (clip is us-arsenal). Studio anchor intro, 'Arming Ukraine'.
- y2026: `pbs-patriot-production-race-2026-10-22` 66.0-74.0: **other** (clip is us-arsenal). Ukraine night sky with an interceptor: the Ukraine war.
## Borderline calls and which way they went

Weapons and supply line:
- `boeing-jdam-400k-stcharles` went to **us-arsenal**, not arms-to-israel. The provenance says this plant makes the JDAM kits supplied to Israel, which is true of the plant in general. But this clip is the 2019 400,000th-kit ceremony, and no Israel-bound weapons appear in it. It is the strongest candidate to flip to arms-to-israel.
- `scranton-155mm-nosing-redhot` went to **us-arsenal**. The provenance's "supplied Ukraine and Israel" is an uncited aside about the plant.
- `gbu39-sdb-promo-nellis` went to **us-arsenal**. The GBU-39 type is documented in Gaza strikes (Rafah, May 2024), but these bombs are on a US range.
- `c17-munitions-onload-selfridge` went to **us-arsenal**. Its provenance says explicitly that it is not a shipment to Israel.
- `c17-night-patriot-delivery` went to **us-arsenal**: Patriot logistics in the CENTCOM AOR, "not Israel-specific".
- `c17-onload-deployed` went to **other**. It shows generic pallets and no weapons.
- `jdam-build-balad-2007` went to **other**. The bombs are assembled in theatre for the Iraq war, not at home or in training.
- `israel-gbu31-prep-oct2023-reedit` went to **arms-to-israel**. Its attribution is caveated (a probable IMOD/IDF original, re-edited by a third party).
- `lm-f35i-combat-capable-2017` went to **arms-to-israel**: Lockheed selling the F-35I to Israel. It would be `israel` just as well.
- `juniper-oak-2023-broll` went to **israel**: a joint US-IDF exercise in the Negev. The HIMARS in it are American.
- `f16-gbu39-sortie-cockpit` went to **us-arsenal**. DVIDS names no combat theatre, so I read it as a training or test sortie.

Iran, Yemen and Lebanon:
- `ap-tehran-blast-camera-ducks-2026-03-02` went to **israel**. The provenance names no attacker, but AP's own title for that day's Tehran video reads "after several US-Israeli strikes" (Kagi search, apnews.com). If joint strikes should count as region, flip it.
- `ap-tehran-strike-plumes-2026-03-01` went to **israel**. Its AP shotlist says Israel is targeting the capital, and the campaign was joint with the US.
- `ap-beirut-dahiyeh-morning-blasts-2026-03-04` went to **israel**. The provenance doesn't name the attacker, but Israel was the only power bombing Dahiyeh in 2026.
- The July 2026 CENTCOM Iran clips went to **region**: `centcom-iran-strikes-jul2026`, `centcom-strikes-iran-2026-07-08-roya`, `centcom-13th-night-iran-2026-07-24` and `centcom-heavy-wave-iran-2026-07-30`, plus `centcom-hormuz-strikes-2026-06-28`. Their link to the Israel war is weaker than for the Feb-Mar clips. They come from the resumed phase after the April ceasefire, and their trigger was Iranian attacks on shipping and a US base. The link I relied on is that Israel was striking Iran in the same weeks (`idf-iran-air-defence-strike-2026-06-08`) and that PBS calls it "the US-Israel war with Iran". If that is too thin, flip them to other.
- `alarabiya-b2-centcom-2026-03-01` went to **region**. The B-2 shots themselves are generic USAF b-roll, which would be us-arsenal, but the package presents them as the 1 Mar strike on Iran.
- `reuters-navy-fires-touska-2026-04-19` went to **region**: the US blockade of Iran during the 2026 war.
- `mq9-strike-yemen-2024` and the four CENTCOM Houthi carrier clips went to **region**, as part of the Red Sea campaign that followed Gaza.

Gaza edges:
- `ap-rafah-aid-trucks-waiting-2026-01-28` went to **gaza**. It was filmed on the Egyptian side of the Rafah crossing, but its subject is aid queuing to enter Gaza under Israeli inspection.
- `mee-settlers-block-aid-kerem-shalom-2026-08-25` went to **israel**: Israeli activists on the Israeli side of the crossing, blocking aid to Gaza.
- Every "from southern Israel" AP clip went to **gaza**: 12 in ground.json and 1 in y2026, plus the second segment of `ap-ashkelon-intercept-day-oct2023`. They show Gaza being struck. Some have Israeli rooftops in the foreground, as the ground notes say.
- `idf-soldiers-watch-demolition-yellow-line-2026-07-08` went to **gaza**: soldier-shot footage inside Gaza. It would be `israel` just as well.
- 21 ground.json clips come from earlier Gaza wars: 2009, 2012, 2014, 2019, May 2021 and May 2023. They are all **gaza**, because the rule counts any war in Gaza. Their scope_note says so, and their `-war` tags still mark them.
- In `aj-high-powered-bombs-explainer`, the night WP airburst at 156.4-163 has no stated location. Israel used WP over both Gaza and Lebanon, so I gave the segment **israel**, with Israel as the actor, rather than gaza. The stock F-16 formation at 110-116 got **other**, since it is unidentified.

ground.json: all 148 clips are Gaza, so no clip or segment needed another scope. I grepped every segment for Israel, tank, rocket, studio, border and similar words. The rocket volleys and the IDF insert that the ground notes flag were never catalogued as segments.

