# y2026 footage: sources

Lane: 2026 footage (Gaza 2026, the US-Iran war, weapons transfers and production, Congress). Catalog: `y2026.json` (97 clips, 374 segments). Files: `media/footage/y2026/raw/` (671 MB, gitignored). Sheets and hit strips: `media/footage/y2026/sheets/`.

## How things were found and checked
- YouTube searches limited to "this year" (`sp=EgIIBQ`), ~90 queries, restricted to an allowlist of wire, news, UN/NGO, government and corporate channels. Every candidate's real `upload_date` and description were then fetched. Clips uploaded in late 2025 were dropped.
- AP Archive items carry a dated shotlist in the description. The **shoot date** (not the upload date) is used as `date`. Several AP stories were shot 3-5 days before they were posted.
- Every clip was viewed on contact sheets. Hits were checked on 5-frame strips (and on 10 fps fine sheets where needed). `refine_hits.py` has been run. **If `y2026.json` is regenerated, run it again.**
- Deduped against `weapons.json` and `ground.json` by video id **and by event**. The 11-12 Mar al-Ansar tent-camp strike, the 27 Jun central-Gaza strikes, the 31 Jul Nuseirat strike and the 2 Mar IMOD first-airlift short are already there, so other uploads of those events were skipped.
- Many AP Archive uploads exist only at **640x360**. That is the source ceiling, not a download fault.

## Clips (date = event/shoot date)
| date | id | publisher | url | license |
|---|---|---|---|---|
| 2026-01-06 | lockheed-pac3-cgi-accelerating-2026-01-06 | Lockheed Martin (official YouTube) | https://www.youtube.com/watch?v=huUYkh5NHCQ | corporate promo (Lockheed Martin) |
| 2026-01-09 | mee-gaza-is-drowning-storm-2026-01-09 | Middle East Eye (UGC: Rabie Abo Nqaira and others) | https://www.youtube.com/watch?v=QJdKS7lnwno | news (MEE; UGC) |
| 2026-01-11 | reuters-storm-batters-tents-2026-01-11 | Reuters | https://www.youtube.com/watch?v=jGQy8bFImwA | news (Reuters) |
| 2026-01-21 | ap-egyptian-committee-car-journalists-2026-01-21 | AP Archive | https://www.youtube.com/watch?v=LjoChDHzO4s | news (AP) |
| 2026-01-24 | ap-father-sieves-bones-2026-01-24 | AP Archive | https://www.youtube.com/watch?v=XoQWFfNR_M8 | news (AP) |
| 2026-01-28 | ap-rafah-aid-trucks-waiting-2026-01-28 | AP Archive | https://www.youtube.com/watch?v=ohbZvVP5TTo | news (AP) |
| 2026-02-04 | lockheed-camden-munitions-acceleration-center-2026-02-04 | Lockheed Martin (official YouTube) | https://www.youtube.com/watch?v=4ujJigllOOA | corporate promo (Lockheed Martin) |
| 2026-02-06 | ap-zeitoun-cemetery-strike-2026-02-06 | AP Archive | https://www.youtube.com/watch?v=5cwc4YfWnl4 | news (AP) |
| 2026-02-06 | guardian-khanyounis-night-strike-2026-02-06 | Guardian News | https://www.youtube.com/watch?v=wjr8ISPvdh0 | news (Guardian) |
| 2026-02-06 | ap-khanyounis-water-and-kitchen-lines-2026-02-06 | AP Archive | https://www.youtube.com/watch?v=-o-HWB1BAKk | news (AP) |
| 2026-02-15 | mee-drone-tent-strike-bodies-hospital-2026-02-15 | Middle East Eye (footage: m.saed.gaza) | https://www.youtube.com/watch?v=vwPV23gHjMw | news (MEE; local journalist) |
| 2026-02-24 | roya-flooded-tents-muddy-swamps-2026-02-24 | Roya News English (UGC: Rabie Abo Noqaira via Storyful) | https://www.youtube.com/watch?v=qB-dELjA1FM | news (Roya; UGC via Storyful) |
| 2026-02-28 | idf-kermanshah-sa65-illustration-2026-02-28 | Israel Defense Forces (official YouTube) | https://www.youtube.com/watch?v=NHQRyWCPJT4 | IDF release |
| 2026-02-28 | idf-western-iran-launcher-strikes-2026-02-28 | Israel Defense Forces (official YouTube) | https://www.youtube.com/watch?v=lstswzboEcE | IDF release |
| 2026-03-01 | ap-tehran-strike-plumes-2026-03-01 | AP Archive | https://www.youtube.com/watch?v=44wFQte1n5Y | news (AP) |
| 2026-03-01 | idf-tehran-strikes-aerial-2026-03-01 | APT (footage: Israel Defense Forces) | https://www.youtube.com/watch?v=CIwuAr06Xic | IDF release via APT |
| 2026-03-01 | alarabiya-b2-centcom-2026-03-01 | Al Arabiya English (footage: US Air Force/CENTCOM) | https://www.youtube.com/watch?v=I-7I53rMhaA | news (Al Arabiya); USAF b-roll |
| 2026-03-01 | idf-khamenei-dead-roaring-lion-2026-03-01 | Israel Defense Forces (official YouTube) | https://www.youtube.com/watch?v=fX3rHsgnNp8 | IDF release |
| 2026-03-02 | ap-tehran-blast-camera-ducks-2026-03-02 | Associated Press (video: Mohsen Ganji) | https://www.youtube.com/watch?v=7_609uaKADI | news (AP) |
| 2026-03-04 | ap-beirut-dahiyeh-morning-blasts-2026-03-04 | AP Archive | https://www.youtube.com/watch?v=lBv4-FnmSiE | news (AP) |
| 2026-03-07 | cnn-tehran-fuel-depot-blaze-2026-03-07 | CNN | https://www.youtube.com/watch?v=S1CTucfBCR0 | news (CNN; UGC via X/Vahid Online) |
| 2026-03-09 | imod-airlift-expands-50-planes-2026-03-09 | Israel Ministry of Defense (official YouTube) | https://www.youtube.com/watch?v=OMimMjhScWU | government release (Israel MoD) |
| 2026-03-12 | centcom-strikes-planes-boats-trucks-2026-03-12 | Associated Press (footage: US Central Command) | https://www.youtube.com/watch?v=_s_RB3JbQ2o | US government work via AP |
| 2026-03-15 | mee-cctv-iranian-cluster-telaviv-2026-03-15 | Middle East Eye | https://www.youtube.com/watch?v=VB4xjhsBx1Y | news (MEE; CCTV) |
| 2026-03-16 | ap-khanyounis-wall-collapse-tents-2026-03-16 | AP Archive | https://www.youtube.com/watch?v=ahm7E2XSnIY | news (AP) |
| 2026-03-16 | ap-khanyounis-iftar-kitchen-crush-2026-03-16 | AP Archive | https://www.youtube.com/watch?v=_GxOn-Rty3k | news (AP) |
| 2026-03-17 | idf-eliminations-iran-leadership-2026-03-17 | Israel Defense Forces (official YouTube) | https://www.youtube.com/watch?v=8J0ccshILsk | IDF release (contains third-party archive) |
| 2026-03-17 | house-foreign-affairs-defense-sales-hearing-2026-03-17 | Forbes Breaking News (House Foreign Affairs Committee feed) | https://www.youtube.com/watch?v=fRiejhXqTXk | US House committee feed (public) via Forbes |
| 2026-03-22 | sky-dimona-arad-missile-damage-2026-03-21 | Sky News | https://www.youtube.com/watch?v=630tyf5yg64 | news (Sky) |
| 2026-03-25 | roya-afp-tent-strike-black-smoke-2026-03-25 | Roya News English (footage: AFP) | https://www.youtube.com/watch?v=r1XSN4h0DIU | news (AFP via Roya) |
| 2026-03-26 | guardian-deir-balah-tent-camp-strike-2026-03-26 | Guardian News (incl. AP camera angle) | https://www.youtube.com/watch?v=RYOQOwHPlfw | news (Guardian/AP) |
| 2026-03-26 | imod-200th-airlift-plane-2026-03-26 | Israel Ministry of Defense (official YouTube) | https://www.youtube.com/watch?v=blyi1fP3KrY | government release (Israel MoD) |
| 2026-03-31 | dw-isfahan-fireball-2026-03-31 | DW News | https://www.youtube.com/watch?v=6vwqnfSFg2M | news (DW; UGC) |
| 2026-04-08 | idf-spokesman-lebanon-100-strikes-2026-04-08 | Israel Defense Forces (official YouTube) | https://www.youtube.com/watch?v=Nf3VB2SpIiQ | IDF release |
| 2026-04-08 | ap-beirut-barrage-2026-04-08 | Associated Press | https://www.youtube.com/watch?v=A_zAvt-sFxk | news (AP) |
| 2026-04-08 | idf-strike-on-journalist-wishah-car-2026-04-08 | Roya News English (footage: IDF) | https://www.youtube.com/watch?v=RomddJ4qrLU | IDF release via Roya |
| 2026-04-08 | roya-bread-queue-gaza-2026-04-08 | Roya News English | https://www.youtube.com/watch?v=JfqTdqZYhEE | news (Roya) |
| 2026-04-09 | aje-wishah-funeral-press-vest-2026-04-09 | Al Jazeera English | https://www.youtube.com/watch?v=-Ohna38kW3Y | news (AJE) |
| 2026-04-13 | lockheed-pac3-contract-promo-2026-04-13 | Lockheed Martin (official YouTube) | https://www.youtube.com/watch?v=21mFwaCgTxg | corporate promo (Lockheed Martin) |
| 2026-04-14 | aje-nyc-jvp-arms-sales-protest-2026-04-14 | Al Jazeera English | https://www.youtube.com/watch?v=VC55w-N1gZI | news (AJE) |
| 2026-04-15 | zeteo-senate-record-vote-block-arms-2026-04-15 | Zeteo | https://www.youtube.com/watch?v=22lxKeu5kNQ | news (Zeteo) |
| 2026-04-19 | reuters-navy-fires-touska-2026-04-19 | Reuters (footage: US Central Command) | https://www.youtube.com/watch?v=bgqblaNV0gc | US government work via Reuters |
| 2026-04-22 | rtx-tucson-composable-weapons-2026-04-22 | RTX (official YouTube) | https://www.youtube.com/watch?v=22ekkAVLlGY | corporate promo (RTX) |
| 2026-04-29 | imod-ships-ashdod-haifa-munitions-2026-04-30 | Israel Ministry of Defense (official YouTube) | https://www.youtube.com/watch?v=SIgbC6dbXts | government release (Israel MoD) |
| 2026-05-19 | anadolu-bureij-night-blast-street-2026-05-19 | Anadolu English | https://www.youtube.com/watch?v=h1ikSUmcrX8 | news (Anadolu) |
| 2026-05-21 | ajplus-bisan-owda-broken-camera-2026-05-21 | AJ+ | https://www.youtube.com/watch?v=pQDI4qKbfq4 | news (AJ+) |
| 2026-05-22 | lockheed-troy-munitions-groundbreaking-2026-05-22 | Lockheed Martin (official YouTube) | https://www.youtube.com/watch?v=pf85OE2yoBc | corporate promo (Lockheed Martin) |
| 2026-05-23 | ap-deir-balah-night-strike-2026-05-23 | AP Archive | https://www.youtube.com/watch?v=ZCLpNuaEzl8 | news (AP) |
| 2026-05-26 | ap-yellow-line-embed-2026-05-26 | AP Archive | https://www.youtube.com/watch?v=oDHHxJJ1J2U | news (AP) |
| 2026-05-28 | ap-shati-night-strike-2026-05-28 | AP Archive | https://www.youtube.com/watch?v=WIiKD8Mjw1Y | news (AP) |
| 2026-05-28 | reuters-khanyounis-warehouse-fire-2026-05-28 | Reuters | https://www.youtube.com/watch?v=uoZ91TbQ4OI | news (Reuters) |
| 2026-06-05 | ap-zawaida-return-strike-site-2026-06-05 | AP Archive | https://www.youtube.com/watch?v=X42abizC_zw | news (AP) |
| 2026-06-08 | idf-iran-air-defence-strike-2026-06-08 | Israel Defense Forces (official YouTube) | https://www.youtube.com/watch?v=b01T149myxQ | IDF release |
| 2026-06-12 | ap-maghazi-salvage-2026-06-12 | AP Archive | https://www.youtube.com/watch?v=2E2Rv79y7Wg | news (AP) |
| 2026-06-27 | mee-dabit-drone-strike-tent-aftermath-2026-06-27 | Middle East Eye | https://www.youtube.com/watch?v=aNs7wjYPVYo | news (MEE) |
| 2026-06-28 | centcom-hormuz-strikes-2026-06-28 | Associated Press (footage: US Central Command) | https://www.youtube.com/watch?v=vCIbEHKi8M0 | US government work via AP |
| 2026-06-28 | aje-orange-line-displacement-2026-06-28 | Al Jazeera English | https://www.youtube.com/watch?v=Bwcq1WOFjmw | news (AJE) |
| 2026-07-08 | centcom-strikes-iran-2026-07-08-roya | Roya News English (footage: US Central Command) | https://www.youtube.com/watch?v=12dTc8Xu484 | US government work via Roya News |
| 2026-07-08 | idf-soldiers-watch-demolition-yellow-line-2026-07-08 | Roya News English (footage filmed by Israeli soldiers) | https://www.youtube.com/watch?v=v0kPVcvCZO8 | news (Roya; soldier-shot UGC) |
| 2026-07-14 | ap-jabaliya-strike-shifa-arrivals-2026-07-14 | AP Archive | https://www.youtube.com/watch?v=_zps_M-njzw | news (AP) |
| 2026-07-15 | ap-maghazi-evacuation-dusk-strikes-2026-07-15 | AP Archive | https://www.youtube.com/watch?v=qKPvpxpb7MI | news (AP) |
| 2026-07-15 | house-massie-israel-aid-vote-2026-07-15 | Forbes Breaking News (House floor feed) | https://www.youtube.com/watch?v=CVCy59TSHkM | US House floor feed (public) via Forbes |
| 2026-07-16 | mee-bureij-rubble-woman-2026-07-16 | Middle East Eye | https://www.youtube.com/watch?v=NmNiDp22QwA | news (MEE) |
| 2026-07-24 | centcom-13th-night-iran-2026-07-24 | Forbes Breaking News (footage: US Central Command) | https://www.youtube.com/watch?v=R2f9D9M4TQE | US government work via Forbes |
| 2026-07-28 | ap-short-gaza-city-blasts-2026-07-28 | Associated Press | https://www.youtube.com/watch?v=lZHFLf8nVtg | news (AP) |
| 2026-07-28 | ap-gaza-city-blast-dusk-2026-07-28 | AP Archive | https://www.youtube.com/watch?v=y6kQaVWkddo | news (AP) |
| 2026-07-28 | nbc-dar-al-muttaqin-mosque-strike-2026-07-28 | NBC News (footage: WAFA, Reuters) | https://www.youtube.com/watch?v=BTr2lDBjto0 | news (NBC; WAFA/Reuters) |
| 2026-07-29 | ap-khanyounis-morgue-bodies-2026-07-29 | AP Archive | https://www.youtube.com/watch?v=G9EY3rgBcLc | news (AP) |
| 2026-07-29 | lockheed-pac3-triple-short-2026-07-29 | Lockheed Martin (official YouTube) | https://www.youtube.com/watch?v=taalsp6ITII | corporate promo (Lockheed Martin) |
| 2026-07-30 | centcom-heavy-wave-iran-2026-07-30 | Associated Press (footage: US Central Command) | https://www.youtube.com/watch?v=9z1SjPeRGZg | US government work via AP |
| 2026-08-01 | mee-aqsa-medicine-warehouse-crater-2026-08-01 | Middle East Eye (footage: Abd elhkeem Abo riash) | https://www.youtube.com/watch?v=2O1hTbCWinQ | news (MEE; local journalist) |
| 2026-08-01 | idf-gaza-crater-strikecam-2026-08-01 | Forbes Breaking News (footage: IDF via CNN) | https://www.youtube.com/watch?v=JMFVyv-HYM0 | IDF release via CNN/Forbes |
| 2026-08-02 | ap-khanyounis-mourning-overnight-strikes-2026-08-02 | AP Archive | https://www.youtube.com/watch?v=TVneg3n7Ghc | news (AP) |
| 2026-08-03 | mee-112-remains-flags-2026-08-03 | Middle East Eye | https://www.youtube.com/watch?v=4wLmM3v8XH4 | news (MEE; journalist UGC) |
| 2026-08-04 | ap-mass-funeral-hassayna-2026-08-04 | AP Archive | https://www.youtube.com/watch?v=D8BWnIo43Dw | news (AP) |
| 2026-08-23 | aje-zawayda-warehouse-strike-shrapnel-2026-08-23 | Al Jazeera English (UGC: Facebook / Telegram) | https://www.youtube.com/watch?v=KJcRs_-Tx74 | news (AJE; UGC) |
| 2026-08-25 | mee-settlers-block-aid-kerem-shalom-2026-08-25 | Middle East Eye | https://www.youtube.com/watch?v=6KGWs6kmi18 | news (MEE) |
| 2026-09-01 | roya-civil-defence-worker-shifa-2026-09-01 | Roya News English | https://www.youtube.com/watch?v=p0uoWSF1AIw | news (Roya; journalist UGC) |
| 2026-09-02 | ap-gaza-from-israel-border-haze-2026-09-02 | AP Archive | https://www.youtube.com/watch?v=k94C4R6NWmI | news (AP) |
| 2026-09-05 | roya-civil-defence-bones-nuseirat-2026-09-05 | Roya News English | https://www.youtube.com/watch?v=eKwlBuPcmw0 | news (Roya) |
| 2026-09-05 | roya-water-truck-crowd-2026-09-05 | Roya News English | https://www.youtube.com/watch?v=RYfCxBlM1TQ | news (Roya) |
| 2026-09-09 | anadolu-khanyounis-plume-2026-09-09 | Forbes Breaking News (video: Abed Rahim Khatib / Anadolu Agency via Getty Images) | https://www.youtube.com/watch?v=dVPeJx24slc | news (Anadolu/Getty via Forbes) |
| 2026-09-09 | ap-shati-strike-plume-2026-09-09 | AP Archive | https://www.youtube.com/watch?v=2G0ulKRCqLI | news (AP) |
| 2026-09-09 | idf-gaza-weapons-sites-strikecam-2026-09-09 | Roya News English (footage: IDF / AFP) | https://www.youtube.com/watch?v=ILs0UJiqXgw | IDF release via AFP/Roya |
| 2026-09-09 | apt-khanyounis-house-strike-2026-09-09 | APT (news aggregator) | https://www.youtube.com/watch?v=yHnWN-p2G1Q | news aggregator (APT); original camera uncredited |
| 2026-09-15 | guardian-deconstructed-zinati-strike-2026-09-15 | Guardian News (footage: Tamer Labbad) | https://www.youtube.com/watch?v=vQdUgwKtwEY | news (Guardian) |
| 2026-09-16 | reuters-gaza-building-collapse-20-killed-2026-09-16 | Reuters | https://www.youtube.com/watch?v=2f7RROFg6tk | news (Reuters) |
| 2026-09-16 | aje-white-house-40000-bombs-2026-09-16 | Al Jazeera English | https://www.youtube.com/watch?v=ByF_1svMZCo | news (AJE) |
| 2026-09-24 | ap-gaza-city-tent-sea-ruins-2026-09-24 | AP Archive | https://www.youtube.com/watch?v=0ATDQtjezFU | news (AP) |
| 2026-10-01 | ap-mass-funeral-105-2026-10-01 | AP Archive | https://www.youtube.com/watch?v=zC_WjmWdUJk | news (AP) |
| 2026-10-04 | cnn-camden-missile-town-2026-10-04 | CNN | https://www.youtube.com/watch?v=aYFTG9n4PbM | news (CNN) |
| 2026-10-07 | ap-f16-night-smoke-tents-2026-10-07 | AP Archive | https://www.youtube.com/watch?v=bTeYO6is5n4 | news (AP) |
| 2026-10-10 | ap-gaza-city-twin-plumes-2026-10-10 | AP Archive | https://www.youtube.com/watch?v=oEAwkAZBL4U | news (AP) |
| 2026-10-16 | ap-maghazi-rubble-after-strike-2026-10-16 | AP Archive | https://www.youtube.com/watch?v=b8E4cXXxF-c | news (AP) |
| 2026-10-18 | ap-wfp-skau-food-line-deir-balah-2026-10-18 | AP Archive | https://www.youtube.com/watch?v=fVh1r9ibDyU | news (AP) |
| 2026-10-21 | alarabiya-jabalia-demolition-smoke-2026-10-21 | Al Arabiya English | https://www.youtube.com/watch?v=du7HnPd4wiU | news (Al Arabiya) |
| 2026-10-22 | pbs-patriot-production-race-2026-10-22 | PBS NewsHour | https://www.youtube.com/watch?v=bLIuhI03SGg | news (PBS) |

## Attribution caveats worth knowing
- **IDF / CENTCOM strike-cam** reaches us through AP, Reuters, Roya, Forbes and APT reposts. The original is the military release; publisher fields name both.
- `idf-soldiers-watch-demolition-yellow-line-2026-07-08`: filmed by Israeli soldiers and posted socially, carried by Roya. The scene (soldiers on a berm watching a demolition) is consistent, but there is no wire confirmation of the exact date beyond Roya's tag.
- `apt-khanyounis-house-strike-2026-09-09`: APT is an aggregator and does not credit the camera. The event and date match AP/Anadolu coverage of 9 Sep.
- `aje-white-house-40000-bombs-2026-09-16`: the Gaza ruins inside it are **undated archive cover shots**. Do not present them as Sep 2026.
- `alarabiya-b2-centcom-2026-03-01`: the B-2 shots are generic USAF b-roll, not mission footage.
- `idf-eliminations-iran-leadership-2026-03-17` and `idf-khamenei-dead-roaring-lion-2026-03-01` contain third-party archive (France 24-branded clips, Iranian state footage) inside IDF edits.
- `sky-dimona-arad-missile-damage-2026-03-21`: the night impact clips are pillarboxed UGC within Sky's package.
- UGC carried by wires/news (MEE, Roya, AJE, Anadolu) is credited on screen to local journalists (e.g. m.saed.gaza, Abd elhkeem Abo riash, Rabie Abo Noqaira via Storyful, Tamer Labbad). Those credits are in `provenance`.

## Rejected and why
- `4-Hs8mdpnQE` (AP short, Zeitoun strike, 6 Feb): vertical crop of `ap-zeitoun-cemetery-strike-2026-02-06`. Downloaded, then deleted.
- `KxVNZOvybA0` (TRT "Made in USA, 40,000 bombs"): a designed graphic built on undated photos plus an illustrated bomb. Not footage. Downloaded, then deleted.
- `TF_dFA1C_CY` (AP short, Shati 28 May) and `VO7BB_OHvaA` (AP short, Shati 9 Sep): duplicates of AP Archive stories that are catalogued.
- `BiWDgCo52oo`, `y2Pio-5THxo` (AP, 27 Jun central Gaza): same event as `ap-deir-balah-strikes-dawn` in weapons.json.
- `_ho5be-TaV8` (AP, Nuseirat 31 Jul): same as `ap-nuseirat-night-strike-2026-07` in ground.json.
- `63xg_uQ0ahg`, `tP4W6iKXBHs`, `p2zcL82Rin8`, `FaV5Z2euhvA`, `4w7Kpuywjzc` (11-12 Mar al-Ansar tent camp): already covered three times in ground.json.
- `hoSkNfNjA3o` (IMOD first airlift, 2 Mar): the same footage as `imod-airlift-pixelated-2026` in weapons.json.
- `BOTOfHlMqa8` (APT, Pentagon Tomahawk barrage from USS Bainbridge): overlaps the DVIDS Epic Fury Tomahawk release already in weapons.json.
- `ObO3ZxJ6HSs` (AP, cold rain in Deir al-Balah): shot 27 Dec 2025.
- `BpbTh6_7vVk` (AP, bread queue in rain, Apr): same story as `ap-bread-queue-rain-2026-04`.
- `q0NYe6k-uIE` (AP, strike near reporter live in Lebanon): the footage is Al Manar TV (Hezbollah-controlled). Excluded under the no-militant-media rule.
- `lb9tKbeJlUw` (Hezbollah attack video via AP): militant group production. Excluded.
- `ypJD3_0Ihu0` (Roya, "one-way drones hit Gaza City"): "footage shared by Palestinian media", with no camera credit. Unattributable.
- `Rsc91DFGlPA` (IDF drone footage alleging a child carrying weapons): an IDF claim that is unverified and would mislabel a child in the edit. Excluded.
- `6NG15Nnby4w` (IDF "terrorist eliminated"): Nov 2025.
- `9LJZ8HUPth8`, `_jztaYYsxGA`, `ucOSVjJrZmg` (IMOD 1,000th plane, D9 bulldozer shipment, airlift): Nov, Jul and Jun 2025. They are relevant but not 2026. The **D9 bulldozer shipment (`_jztaYYsxGA`, 10 Jul 2025)** is worth a look for the weapons catalog.
- Indian and other aggregator channels (India Today, ET, WION, "WorldGeopoliticx" etc.) reposting the IMOD airlift: used the IMOD originals instead.
- No AI-looking or synthetic material was found among the candidates that were kept. Fan "news" channels with sensational titles were filtered out by the allowlist.

## Wanted, needs login
- None hit an age gate in this lane. These Israel MoD **Facebook** originals are reachable without login and are higher-res than YouTube, but were not downloaded (the YouTube copies are used):
  - https://www.facebook.com/IsraelMOD/videos/2329998237486176/ (200th aircraft, 26 Mar 2026, 1080p)
  - https://www.facebook.com/IsraelMOD/videos/1333243675294430/ (airlift expands, 9 Mar 2026)
