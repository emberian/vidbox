# Credits: method, sources, form, open questions

## How it is made

`tools/credits.py` builds everything from the timeline, so the credits follow the sections as they change.

    uv run python tools/credits.py fetch    # source-page metadata for any clip without a yt-dlp info.json, and the lists of the dead
    uv run python tools/credits.py data     # -> credits.json, CREDITS.md
    uv run python tools/credits.py render   # -> media/derived/credits.mp4
    uv run python tools/credits.py render --full    # -> media/derived/credits_full.mp4

All three default to `comps/out/full.timeline.json`; `--tl a.json b.json ...` credits other timelines.

- **Which clips.** A layer counts if `meta.catalog`/`meta.clip` names a catalog clip, or if its `src` is a catalog clip's file. Some s2 layers carry no catalog meta, so the file match matters. Layers whose `src` is neither a catalog file nor a known non-footage source (the Meine video, the preacher's face clips, credits.mp4 itself) are printed as **UNIDENTIFIED** and listed in CREDITS.md, so nothing slips through uncredited.
- **Clip credits** come from the catalog (publisher, date, URL, licence) and from the source page. That is the lane's yt-dlp `info.json` where one exists (ground and weapons), otherwise `credits/meta/<file>.json`, fetched with `yt-dlp -j` (18 y2026 clips). The fields are the source's own title, and AP's dateline place and camera/producer credit, taken verbatim from lines like "AP video shot by ..." or "AP production by ...". Al Jazeera's "...'s X reports from" gives a reporter credit. On-screen credits the lanes recorded in provenance (Storyful, Instagram handles, "IDF via CNN") live in `sources_extra.json`, each with a note of where it came from. That file also holds one title fix (the Israel MoD Facebook post, whose scraped title carried view counts and the whole post) and two translations, each marked "our translation".
- **Title clean-up.** yt-dlp's generic extractor appends " (1)" to DVIDS titles, so that suffix is removed. Emoji are removed because the fonts have no glyphs for them. Nothing else is changed. On screen, DVIDS URLs are shortened to `dvidshub.net/video/<id>`, which resolves to the same page; CREDITS.md keeps the full URLs.
- **People** come from layers' `meta.people` (the section agents add these) and from `people_extra.json`. Each entry in that file is tied to a clip, quotes or paraphrases only its source, carries the source URL, and appears only while its clip is in the timeline. The roles are: killed, a group of the dead (named as the source names them: a family, a count, a place), injured, bereaved, and filmed. Filmed becomes a camera credit on that clip. A bereaved survivor is not repeated on screen when the same clip already credits his family as a group (Mahmoud Hammad).
- **Arabic.** Pillow 13's wheel has raqm (HarfBuzz) but loads FriBiDi at run time. Homebrew's libfribidi is in /opt/homebrew/lib, so the script re-execs itself with `DYLD_FALLBACK_LIBRARY_PATH` set, and it refuses to render if raqm still isn't available. I checked the frames at 2x zoom: the letters join, the order is right to left, and the lam-alef and Allah ligatures are correct ("عبد العزيز بلال خالد الاسي" ↔ "Abdel Aziz Bilal Khaled Al-Asi"). Fonts: Helvetica Neue for text, Avenir Next Condensed for the dense name grids, Geeza Pro for Arabic. These are macOS system fonts. pillow is now a direct dependency in pyproject.toml.
- **Never truncated.** A name too wide for its cell first loses up to 2 pt, then is narrowed horizontally to no less than 72% of its width, and only after that gets smaller.

## What is in the default (credits.mp4, 3:35 at the current clip list)

| section | content | seconds |
|---|---|---|
| lead | black after the music | 1 |
| In this footage | the people killed or injured in clips the piece uses, as their sources name or count them (3 pages) | 33 |
| The footage | every clip used: source title, publisher, filming date, AP dateline place, camera/producer/reporter where the source gives one, URL; grouped by outlet, news first; 74 clips on 4 pages | 28 |
| Music, picture, voice, tools | | 10 |
| The count | 74,498 killed (MoH, 22 Oct 2026), 175,616 injured; 72,835 named (deaths to 7 May 2026), 21,637 children, 1,072 under one; what the lists leave out | 11 |
| Journalists | all 191 journalists and media workers CPJ records as killed by Israeli forces since 7 Oct 2023, each with outlet and date (4 pages), then a page for the 5 CPJ records as killed by others | 43 |
| Children | all 21,637 named children, youngest first, name and age, 220 per page, 0.8 s per page (99 pages) | 79 |
| Sources for the names and figures | | 9 |
| tail | black | 1 |

Every page carries its source in the footer. Readable pages dip through black (0.4 s); the dense name pages cut hard, page to page.

## The wider dead: forms considered

| form | duration | |
|---|---|---|
| Every name, one per line, read aloud pace (~3 names/s) | ~6 h 45 min | impossible in a credit roll |
| **Every name, paged, Arabic + English + age, 96 per page, 2.5 s per page** | **33:38** (759 pages, 2.48 s each) | built: `credits_full.mp4` |
| Every child, readable pace (220 per page, 4 s) | ~6.6 min | |
| **Every child, dense (220 per page, 0.8 s)** | **79 s** | **the default** |
| The 1,072 under one year old, readable | ~20 s | names a fraction; the rest only counted |
| A count card alone | ~10 s | names no one |
| Journalists named in full (CPJ) | ~36 s + 7 s | in both versions |

**Why this one.** The default names every child the ministry has identified, and none is left out to fit the length. At 0.8 s a page the eye can't read them, and that is the scale made visible. Every frame is still a clean, legible page, so anyone who pauses can read every name. Youngest first, because the ministry's own data makes that the most direct truth: the first page is all newborns, and age 0 runs for five pages. The count card before it states the total, including the dead the lists do not name. The journalists are named in full at reading pace, with outlet and date, because the piece is made from journalists' footage. The full version names all 72,835 in Arabic (the ministry's original) and English.

The default's children list is English only, for density. To show Arabic in the default as well, use `pages_names(..., script="both")` or `"ar"` in `build_sequence` (4 columns, about 2.3x as many pages).

## Sources for every name and figure

- **Gaza Ministry of Health, daily cumulative**: 74,498 killed, 175,616 injured, report of 22 Oct 2026 (`report_source: mohtel`, the ministry's Telegram). Via Tech For Palestine's Daily Casualties dataset, <https://data.techforpalestine.org/api/v2/casualties_daily.json>, retrieved 2026-10-24.
- **Gaza Ministry of Health, list of the identified dead**: 72,835 records, deaths to 7 May 2026, published by T4P on 27 Jul 2026 (records carry list updates 1 to 10). Via Tech For Palestine's Killed in Gaza dataset, <https://data.techforpalestine.org/api/v3/killed-in-gaza.min.json>, docs at <https://data.techforpalestine.org/docs/killed-in-gaza/>, retrieved 2026-10-24. **Licence:** the repository's LICENSE is a public-domain dedication (Unlicense-style) for software and data. **Provenance:** the ministry's PDF lists (Telegram; later lists via Iraq Body Count), plus public submissions and judicial-committee records, transliterated to English by T4P. The script checks the counts against T4P's summary.json: 21,637 under 18 = 12,803 boys + 8,834 girls.
- **Ministry caveat** ("the missing, the dead under rubble, the unidentified, those buried without passing through a hospital"): the ministry's January 2024 note on its first list, quoted on T4P's docs page, which says these constraints "have mostly held true". That is why the screen says "the ministry has said".
- **Journalists**: the Committee to Protect Journalists database, exported from `cpj.org/wp-json/cpj-datamanager/v1/people_list` (the CSV behind cpj.org/data) and filtered to country "Israel and the Occupied Palestinian Territory", dated on or after 7 Oct 2023: 196 records. 191 give "Military Officials" as the source of fire. This matches CPJ's own summary (<https://cpj.org/2023/10/journalist-casualties-in-the-israel-gaza-war/>, as of 24 Sep 2026): 189 Palestinians killed by Israel in Gaza, plus 2 in Israeli detention centres. The other five are the 4 Israeli journalists CPJ says were killed by Hamas and 1 Palestinian killed by an armed group in Gaza; they are named on their own page, using CPJ's wording. Retrieved 2026-10-24. CPJ's text is CC BY-NC-ND; the names, outlets and dates are facts, credited to CPJ.
- **Gaza Government Media Office**: 262 journalists (T4P press list, <https://data.techforpalestine.org/api/v2/press_killed_in_gaza.json>). Shown in the journalists footer as the second count.
- **UN OCHA**: its reported-impact snapshots (e.g. 14 Oct 2026, <https://www.ochaopt.org/content/reported-impact-snapshot-gaza-strip-14-october-2026>) say "Casualty numbers have been provided by the Ministry of Health (MoH) and the Israeli authorities". Hence "UN OCHA attributes its Gaza casualty figures to the same ministry". No OCHA figure is shown, because its fatality breakdowns stop at 31 Dec 2025.
- **In this footage**: each line's source is the clip's own source page (AP shotlist/storyline, Guardian, NBC, Roya, MEE); the URL is on screen under it. See people_extra.json.

## Uncertain, or ember's call

1. **The "preacher" is Sam Hyde, a comedian (Million Dollar Extreme), doing a bit.** Every re-post found credits him: the YouTube short "thou shalt give Israel missiles" (uploaded 14 Sep 2022, description "Sam Hyde and his infinite wisdom..."), r/copypasta, 24vids ("- Sam Hyde"), and the transcript matches the copypasta word for word. I did not trace the original recording (show, stream, or date). Two things follow. The piece frames him as a preacher, but the credits name a comedian. And his comedy circle is widely associated with the online far right, which is worth knowing before putting his name on an anti-war piece. The credit on screen is plain: "Sam Hyde, comedian (Million Dollar Extreme)". Change or remove it as you see fit, but the voice should be credited somehow.
2. **The background video.** `media/src/meine.webm` (1440x1080, 473.54 s) matches YouTube `h7qTI6Njp9g`, "Daso - Meine", uploaded by **discpictures99** on 19 Feb 2010 (36M views; the whole description is "Vilnius"). No filmmaker is credited, and it is not an official label upload as far as I can tell. `analysis/STRUCTURE.md` calls the setting "East German industrial buildings", but the uploader says Vilnius. Rights to the picture are unclear.
3. **Music.** Daso (Daso Franke), "Meine", Meine Idee EP, Spectral Sound (Ghostly International), released 31 Oct 2007; Franke died in April 2018 (Ghostly's Bandcamp text). Bandcamp says he was 26 in autumn 2007, so his birth year is 1980 or 1981; it is not stated, and the screen says only "died 2018".
4. **Which timeline.** `full.timeline.json` (03:51) is stale. It still contains the Iraq/ISIS and Yemen clips that `Comp.save` now rejects as out of scope. So the current credits.mp4 was rendered from the three section timelines (s0 03:59, s1 04:44, s2 04:43), which give 74 clips, all in the default scope. **After the rework lands, run `data` and `render` with no `--tl`** (and `render --full` too, if you want the long version to match).
5. **Children figure.** I use the names list (21,637 under 18, deaths to 7 May 2026), not the ministry's daily cumulative child count (20,179), which was last reported on 7 Oct 2025 and has been carried forward since. The two disagree because they are different products at different dates.
6. **One correction to the dataset's English.** 280 names carry the transliteration artefact "Abdullahallah" (for عبد الله, e.g. "Yusri Mousa Abdullahallah Ghaben" / "يسرى موسى عبد الله غبن"). They are shown as "Abdullah". Nothing else in the names is altered, and the Arabic is untouched.
7. **Sabra, November 2023**: AP gives 22 Nov and "more than 300"; MEE (citing civil defence) gives 23 Nov and 308. The screen says "November 2023" and "some 300".
8. **Sharif Shadi Labad** is credited as an injured civil defence paramedic. The Israeli military's claim that he was a Hamas militant who had been targeted is included, attributed, because the Guardian reports both.
9. **Jabaliya, 14 Jul 2026.** AP reports that Gaza's interior ministry named Colonel Mohamad Marwan Salem, head of the Jabaliya police station, among the seven dead. He is named because the source names him. Whether he is among the bodies in the shots used is not known.
10. **Mahmoud Hammad's family.** AP does not give their names. I did not search the ministry list by surname, because a match would be a guess.
11. **Scope of "the dead".** The credits count and name the dead of Gaza, the journalists CPJ records in Israel and the Occupied Palestinian Territory (including the 4 Israeli journalists CPJ says Hamas killed), and those shown in the footage. Not included: about 1,200 people killed in Israel on 7 Oct 2023 (AP storylines), the West Bank (1,124 killed per T4P/MoH, 22 Oct 2026), Lebanon (8,433, T4P, 25 Sep 2026), and Iran. If you want any of them, it is one more card.
12. **Out-of-scope footage.** If the Iraq clips came back (`apache-gun-tape-iraq-2008`, `oir-habbaniyah-convoy-2016`), the people they show being struck are covered in people_extra.json in their releases' own terms. Comp.save's scope rule currently keeps them out.
13. **Licences** are as catalogued. The footer says "News footage is the property of its publishers; US government footage is public domain". It makes no fair-use claim; that is yours to make.

## Placing it in the piece (not edited: full.py, render/tl.py)

`comps/sections/s3_credits.py` has `SPAN = (473.5, 473.5 + duration of credits.mp4)`, read with ffprobe, and one opaque, silent, full-frame layer.

**full.py** (three changes):

```python
SECTIONS = ["s0_rant", "s1_build", "s2_peak", "s3_credits"]
from sections.s3_credits import SPAN as CREDITS          # after the sys.path lines
c = Comp("meine", "full", range=(0, CREDITS[1]), sync="missiles_on_beat")
c.add(c.background(t1=473.5))                             # Meine's picture ends with its music
```

Without `t1=473.5`, `c.background()` spans the whole range. Past the file's end (473.54 s) the reader holds Meine's last frame. That would be invisible under the opaque credits, but it wastes decode time and would show if the credits ever had transparency.

**render/tl.py, `mux_audio`.** amix uses `duration=first`, and its first input is the music. I tested the exact filter graph on a 10 s black video with the music started at -ss 470: **the audio stream ends at 3.53 s and the video runs to 10 s.** A full render would therefore end its audio at 7:53.5 while the picture runs another 3.5 min (or 34 min). Many players handle a short audio track by playing silence, but some editors and platforms don't, and any audio layer placed after the music would be cut off too. The fix is to pad the music with silence to the render's length:

```python
# constant gain
chains = [f"[1:a]asetpts=PTS-STARTPTS,volume={mg},apad=whole_dur={r1 - r0:.4f}[a0]"]
# envelope (signal) gain: pad after the multiply, since amultiply stops at its shorter input
chains.append(f"[{...}:a]aresample={SR},pan=stereo|c0=c0|c1=c0,"
              f"aformat=sample_fmts=flt:channel_layouts=stereo[env];[mus][env]amultiply,apad=whole_dur={r1 - r0:.4f}[a0]")
```

Confirmed through the real renderer as well: a test timeline (background clamped to 473.5 + s3_credits) rendered with `tl.py --range 471 478 --full` came out as video 7.000 s, audio 2.526 s. With the change, the same isolated test gives audio 10.000 s and video 10.000 s. `-t` already bounds the output. The music envelope (`env`) is already computed for the whole of `r0..r1`, so a ducking signal keeps working.

**Silence over the credits** is what this gives: credits.mp4 has no audio, and the layer has no `audio` key. If you would rather have sound, the only true options I see are silence or room tone; that is your decision.
