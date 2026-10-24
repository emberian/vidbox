# vidbox

A small, code-first video composition toolkit, and the project it was built for: **Meine**, an
anti-war piece cut to Daso's "Meine" (7:53, 126 BPM). In it, a satirical rant ("thou shalt give
Israel missiles") is answered by the war it describes: Israel/Gaza footage, US arsenal footage,
and real preachers and politicians, all locked to the music's beat grid. A credits outro names
the sources, the dead shown in the footage, the journalists killed, and the children of Gaza
named by its Ministry of Health.

The piece contains graphic footage of war and its dead. Everything here is code, catalogs and
analysis; the footage itself is not in this repository (see "Rebuilding media").

## Layout

| path | what |
|---|---|
| `render/` | the renderer and composition library. `TIMELINE.md` is the format; `tl.py` renders a timeline (layers, blends, masks, effects, audio, parallel chunks; `VIDBOX_CRF=0` renders losslessly, for frame comparisons); `comp.py` writes timelines in musical terms (beats, bars, words, hit-aligned footage); `signals.py` makes any parameter music-driven; `fx.py`/`fx_extra.py` (+ `FX_EXTRA.md`) are the effects, beat-locked by default; `media.py` decodes frames on one exact clock. `render.py` is the original single-background renderer from the path-capture studio, superseded by timelines |
| `tools/` | analysis and prep: beat map (`beats.py`), word timing (`transcribe.py`: Whisper + forced alignment), rant retiming (`retime.py`), face tracking (`facecrop.py`, `facepose.py`), head motion (`selfmotion.mjs`), impact detection (`hits.py`, `refine_hits.py`), credits (`credits.py`), variants (`variant.py`), media rebuild (`manifest.py`, `fetch_sources.py`) |
| `studio/` | browser tools, served by `server.py` (HTTP Range for video seeking; saves limited to `projects/**.json`): `index.html` captures and edits motion paths, `timeline.html` shows a composition over the beat grid, synced to its render. `uv run python studio/server.py`, then http://127.0.0.1:8765/ |
| `projects/meine/` | the piece: `analysis/` (beat map, structure, rant words), `footage/` (catalogs with provenance, scope, frame-exact impact times), `preachers/`, `credits/`, `sync/` (rant retiming sheets), `paths/` (timed Bezier motion paths; format at the top of `studio/bezier.js`), `comps/` (section scripts and generated timelines) |

## Rebuilding media

`media/` is not in git. `projects/meine/media_manifest.json` records every source file: URL,
duration, checksum and a brightness fingerprint.

```sh
uv sync
uv run python tools/fetch_sources.py           # downloads and verifies every source (yt-dlp)
uv run python tools/refine_hits.py projects/meine/footage/*.json   # only if anything was re-cut
./tools/prep.sh                                 # face-tracked clip, proxies, face track
uv run python tools/retime.py projects/meine/sync/missiles_on_beat.json
uv run python tools/retime.py projects/meine/sync/rant2.json
uv run python tools/credits.py data && uv run python tools/credits.py render
```

Downloads are checked against the manifest. A file that was originally downloaded in part is
located inside the full video by fingerprint and re-cut. Sources go offline; whatever can't be
fetched is listed with its URL. Some derived media (face-tracked preacher clips, text cards) is
generated on demand by the section scripts and tools.

## Rendering

```sh
uv run python projects/meine/comps/full.py                      # assemble the piece
uv run python render/tl.py projects/meine/comps/out/full.timeline.json --jobs 8   # half-size preview
uv run python render/tl.py projects/meine/comps/out/full.timeline.json --full --jobs 8
uv run python tools/variant.py projects/meine/comps/out/full.timeline.json --lowfx   # low-effect variant
```

`full.py` and `comp.py` enforce the piece's rules when saving:
- footage must be in scope: Israel/Gaza, arms to Israel, the US arsenal (`footage/SCOPE.md`);
- untreated footage of the dead is shown once;
- the voronoi effect is used only on faces;
- impacts must land on the beat grid.

## Sources and credit

Footage is credited per clip in `projects/meine/footage/*.json` and `*_SOURCES.md`, and in
`projects/meine/credits/CREDITS.md`. The ranting voice is Sam Hyde, a comedian, in a 2022
satire clip; the real speakers are named and dated on screen.
