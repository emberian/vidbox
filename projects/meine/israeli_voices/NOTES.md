# Israeli voices for "Meine"

Catalog: `voices.json` (7 clips, 6 people). Downloads are in `media/israeli_voices/raw/`, word timings
(Whisper large-v3-turbo plus MMS forced alignment, `tools/transcribe.py --language he`) in
`media/israeli_voices/words/`, contact sheets in `media/israeli_voices/sheets/`. Prepared clips:
`uv run python tools/preacher_prep.py --catalog israeli_voices` writes `media/derived/israeli_voices/`
(face-tracked ovals; Weiss is a framed window), each with a sidecar holding its words and its
translated lines in the clip's own clock. Line times in `voices.json` are seconds within the local file.

Sources were found through South Africa's ICJ application (29 Dec 2023, paras 101-107 and footnotes;
copy from courthousenews.com, the ICJ site sits behind a bot check) and then fetched from the original
broadcaster or the outlet's own upload, not from compilations.

## Placed (song time, code bar = viewer bar - 1)

| viewer bar | song s | who | line | under it |
|---|---|---|---|---|
| 109-111 | 206.0-211.2 | Netanyahu, still oval, left | "Remember what Amalek did to you," we were commanded. We remember. (AMALEK on 110) | WP airburst over Gaza City's ruins, then the untreated Dar al-Muttaqin strike; right after Rev. Isaac's "the Bible is weaponized against us" |
| 122-132 | 231.2-247.4 | Gallant, oval, right; still in the breath, beat play from 125 | the whole 9 Oct statement: complete siege on Gaza City / no electricity, no food, no water, no fuel / everything is closed / we are fighting human animals... (SIEGE on 124, WATER on 127; Hyde's MISSILES on 125 falls in Gallant's own pause) | shroud cloth cut in the frozen breath, then the IDF crater strike-cam |
| 133-135 | 252.4-258.1 | Gallant, oval, left, play | No compromises. Gaza won't return to what it was, and Hamas will not exist. We will eliminate everything. (HAMAS on 135) | peak 1 strikes |
| 144-147 | 272.6-278.2 | Dichter, oval, right | We are now actually rolling out the Gaza Nakba, if you like, the Gaza Nakba. (NAKBA on 145 beat 4) | the displaced walking, top-down |
| 147-149 | 278.2-283.8 | Daniella Weiss, window, left | But the purpose is to settle the entire area so that Arabs will not stay here. (ARABS on 149) | the walkers, then the flour multitude |
| 161-164 | 303.8-311.1 | Eiland, small still oval in the letterbox above | ...is to create such a huge pressure on Gaza that Gaza will become an area where people cannot live. (GAZA on 162) | the untreated 2x2 grid: the wounded carried in, rescuers, a stretcher, mourners |
| 179-181 | 339.1-344.2 | Herzog, small still oval in the letterbox above | It's an entire nation out there that is responsible. (NATION on 179 beat 3) | the untreated remains of 112 people from Sabra under flags (MEE; silent) |

Every Hebrew line is subtitled in the letterbox under the lower-third (`comp.subtitle`, tagged
`subtitle`); every first appearance has a lower-third: name, role, venue, date.

## Translations and their checks

- **Gallant, 9 Oct 2023.** Whisper's Hebrew matches the Knesset Channel's own title word for word
  (Whisper misspells נלחמים as נרחמים). Translation: the ICJ application para 101 ("imposing a
  complete siege on Gaza. No electricity, no food, no water, no fuel. Everything is closed. We are
  fighting human animals and we are acting accordingly"), adjusted to this audio: he says העיר עזה,
  "Gaza City". The Times of Israel text omits "no water"; this audio has it.
- **Netanyahu, 28 Oct 2023.** Own translation of the Hebrew: "זכור את אשר עשה לך עמלק", נצטווינו.
  אנו זוכרים (ואנו נלחמים)". The ICJ application quotes the Sky News simultaneous interpretation of the
  same passage ("you must remember what Amalek has done to you, says our Holy Bible. And we do
  remember"); "says our Holy Bible" is the interpreter's rendering of נצטווינו, "we were commanded".
  The cut ends at the pause after "We remember"; "and we are fighting" is left out for time.
- **Gallant, 10 Oct 2023.** Whisper's text of the middle sentence is garbled ("אז זה ... מה שהיא ידעה");
  the reading עזה לא תחזור להיות מה שהייתה follows the Times of Israel / Bloomberg translation cited by
  the ICJ ("Gaza won't return to what it was", "We will eliminate everything") and the audio's syllables.
  **ember: this one is the least certain; a Hebrew speaker should listen to 1:34-1:40 of the source.**
- **Dichter, 11 Nov 2023.** ICJ para 101: "We are now actually rolling out the Gaza Nakba"; Whisper
  writes נקבת for נכבת. The question he answered is in his lower-third.
- Herzog, Eiland and Weiss speak English; their words are checked against the auto captions and the
  forced alignment.

## Context (what each line answers; full notes in voices.json)

- Herzog answered ITV's question about Gaza's 2 million civilians "many of whom have nothing to do
  with Hamas"; he went on "It's not true, this rhetoric about civilians not aware, not involved". Later in
  the same conference: "I agree there are many, many innocent Palestinians who don't agree to this".
- Gallant's office and supporters said "human animals" meant Hamas; the siege he announced covers all
  of Gaza City.
- Dichter went on to give the operational reason ("no way to wage a war ... when the masses are
  between the tanks and the soldiers"). Netanyahu rebuked ministers for the remark the next day.
- Weiss continues: "...because they lost the right to be in Gaza in the massacre of the 7th of October".
- Eiland was a Defence Ministry adviser in the first weeks of the war (ynet, cited by the ICJ).

## Found, not used

- **Netanyahu, MEE/Sky clip** (`preachers.json: netanyahu_amalek_mee`): its English audio is Sky's
  simultaneous interpreter, not Netanyahu (it tracks the Hebrew speech line for line, with the same
  49 s between "Amalek" and "never again is now"). Replaced by his own voice in Hebrew.
- **Ben-Gvir, Channel 12, 11 Nov 2023** ("those who hand out candy... should also be destroyed"; the
  party's own 360p upload): the line is interrupted by the hosts and Whisper's Hebrew is garbled in
  the middle of it; not used until a Hebrew speaker checks it.
- **Col. Yogev Bar-Sheshet, Channel 14, 4 Nov 2023** ("scorched earth... they have no future"): found
  (fqEj3DzadiM), not transcribed in full; a candidate.
- **Eliyahu (nuclear "option")**: radio only (Kol Barama / Kan), no picture.
- **Vaturi, Kallner, Distel-Atbaryan, Gotliv**: their cited statements are posts on X, not video.
- **Smotrich, "justified and moral" to starve 2 million (Aug 2024)**: no original upload found quickly.
- **Tzav 9 / Kerem Shalom blockades** (AP Archive, 9 May 2024 and 25 Aug 2026): the speakers are private
  protesters, so they are left out.
- **The Jan 2024 Jerusalem "settle Gaza" conference**: only news packages and re-uploads turned up.
