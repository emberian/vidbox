# vidbox review (branch review/cleanup)

Read-through of render/, tools/, studio/ and projects/meine/comps/ on 2026-10-24, rebased
onto dev 778cbca. Severity: **bug**, **latent** (wrong under conditions not hit today),
**perf**, **clean** (duplication, dead code, misleading structure), **docs**.
File:line refers to the file as it is on this branch, unless the item says otherwise.

## Verification

- **Identity control.** Lossless (`VIDBOX_CRF=0`) single-job renders, the dev 778cbca
  render/ against this branch, interleaved. Ranges: section_s0_rant 9-14, split_demo 36-44,
  time_ops_demo 56-64, full_v1 330-336 and full_v1 60-64. **Video: every frame
  bit-identical on all five** (framemd5). Audio: see "Audio changed" below.
- **Seams.** A 1-job and a 3-job render, both lossless, are identical (video and audio) for
  full_v1 52-64 (20 formation heads, chromatime, voronoi, glitch, feedback) and
  time_ops_demo 52-65 (map, stutter, freeze, ramp, reverse).
- **Time ops.** I re-ran the time lane's checkers (copies pointed at this tree) on the
  frame-coded source. check_ops matches on all 7 ops (stutter, freeze, ramp, reverse, multi,
  groove, vari): 0 frame mismatches, tone pitch on target, no clicks. test_long has 0/650
  mismatches with the span cache off (0 MB, which forces the Reader's own seek paths) and on.
- **Audio changed (deliberate, commit "mux_audio: mix constant-speed layers on the
  sample-exact bus").** With the music muted, a cross-correlation against the source puts
  `say4:missiles.d@335.45` (full_v1) 48 samples early on dev and at lag 0 here. Layers
  starting before the range (s0's preacher) are unchanged: I mixed old against new to PCM
  instead of AAC, with music on, and the max difference was 4.7e-4. The AAC-encoded files
  differ by up to ~0.27 on s0/split even so: the AAC encoder does not encode near-identical
  input to near-identical output. Judge audio changes by PCM, not AAC.

## Performance

Single job, lossless, wall = min of 3 and CPU = min of 3 of user+sys including children.
The CPU figure includes ffmpeg's lossless x264 encode and the mux, roughly constant at
8-10 s per range. Two measurement sets: run sequentially early in the session, before and
after the render/ perf commits on 273c36d; and interleaved base/new on dev 778cbca later,
under heavier load from other agents.

| range | sequential wall before -> after | interleaved wall base -> new | interleaved CPU base -> new |
|---|---|---|---|
| section_s0_rant 9-14 | 6.05 -> 7.05 (noise: a1 run 4.90) | 8.33 -> 7.31 | 11.8 -> 11.3 |
| split_demo 36-44 | 16.81 -> 12.50 | 17.44 -> 11.93 | 22.0 -> 19.4 |
| time_ops_demo 56-64 | 11.29 -> 6.43 | 9.86 -> 6.88 | 21.4 -> 15.6 |
| full_v1 330-336 | 31.99 -> 10.49 | 36.46 -> 12.39 | 38.6 -> 21.2 |
| full_v1 60-64 | 31.15 -> 7.11 | 27.20 -> 14.23 | 35.9 -> 18.4 |

Headline (the range the coordinator profiled, full_v1 60-64, 1 job): **31.2 s -> 7.1 s wall (4.4x)** sequentially; 27.2 -> 14.2 s wall and 35.9 -> 18.4 s CPU interleaved under load. render_video alone (no encode wait, no mux) went from 35.7 s to 6.8 s (5.2x).

In-process profile of the same 100 frames (cProfile): **35.7 s before, 6.8 s after**. Where
the time went before:

- **ffprobe per layer: 20.5 s (57%).** render_video built a Layer for all 373 layers of
  full_v1, and each Layer ran ffprobe. That is 373 subprocesses per chunk process, over 73
  distinct files, with 27 layers actually active. The fix memoizes probe() and builds only
  the layers that overlap the chunk.
- **Converting frames nobody sees: about 4.5 s.** media.Reader ran to_array (rgb24, crop and
  INTER_AREA resize) on every decoded frame. That included the whole keyframe-to-target run
  after each seek, and every layer opens with a seek. Opening dvids_976258 (1600x900) 2 s past
  a keyframe converted about 60 frames it never showed, at about 8 ms each. Frames are now
  converted when shown.

Suggestions from the coordinator that I measured and did not take:

- **Sharing decoded frames across copies of face.mp4.** No two of the 21 face copies at
  60-64 s are on the same source frame: their `in` offsets are 2.17 s apart in a loop. A shared
  frame cache would never hit.
- **Decoding Meine (AV1, 1440x1080) at reduced size or from the proxy.** 100 frames decode
  and convert in 0.13 s wall (dav1d threads), so there is nothing to win. The proxy would also
  change pixels.
- **One swscale pass instead of rgb24 + cv2 INTER_AREA.** Per call this is 16x faster on the
  480x600 face (0.095 ms against 1.53 ms). Over the whole range it moves process CPU from 16.1
  to 15.5 s, which is not worth pixels that differ (max 12/255).
- **Dropping the second resize (decode size, then display size).** For constant-scale layers
  the two sizes are equal, and that case now skips the resize. Pulsing layers need it.

What remains on full_v1 60-64: cv2 INTER_AREA at non-integer factors in to_array (about 2.5 s,
mostly the small face copies and the 1600x900 crops), AV decode (0.9 s), compositing (0.5 s)
and fx.

## Findings: render/ (mine)

| # | sev | where | what | status |
|---|---|---|---|---|
| R1 | perf | tl.py probe / render_video (273c36d tl.py:65,267) | ffprobe for every layer of the timeline in every chunk process (373 for full_v1), 57% of a 4 s render | fixed: tl probe once + only in-range layers |
| R2 | perf | media.py Reader._pull (273c36d :123) | every decoded frame converted, including keyframe pre-roll after each seek and frames of >25 fps sources that are skipped | fixed: lazy conversion |
| R3 | perf/bug | media.py Reader.get (273c36d :164) | `t > buf[-1] + 3` forced a seek even at EOF: a layer that outlives its source by >3 s re-decoded the last GOP every frame | fixed (same commit) |
| R4 | bug | tl.py mux_audio constant-speed path (273c36d :465-476) | `adelay=int(ms)` truncates, so the layer lands up to 1 ms (48 samples) early. It also ignored the audio-vs-video stream start offset that layer_audio applies (no current audio source has one, but 41 footage clips do, per the tools lane). It was a second implementation of what layer_audio already does sample-exactly. | fixed: one path; TIMELINE.md audio section updated |
| R5 | bug | comp.py Comp.beat (273c36d :161-166) | past the last beat (456.876 s) it extrapolated from the FIRST beat, so beat(beat_pos(t)) came back 195 ms early in the outro, with a jump at the last beat; every beats_after-based op (stutter, freeze, ramp, say, groove) placed outro material off-grid | fixed |
| R6 | clean | comp.py Comp.word | copy of resolve_word without its error messages | fixed: calls it |
| R7 | latent (ember's rules) | comp.py save (273c36d :565-583) | the voronoi and scope rules only looked at `meta.catalog`; hand-built `c.add` footage (9 layers in s2_peak) skipped both | fixed: Comp.rule_violations matches footage by src too. It flags no head in any saved timeline; a synthetic region clip with voronoi raises both rules |
| R8 | perf | tl.py Layer.draw | same-size cv2.resize on every frame of a constant-scale layer, and a redundant mask copy | fixed |
| R9 | clean | fx_extra.py:27 | `_beat_crossed` sat above the imports | fixed |
| R10 | docs | README.md | described only render.py, the project.json renderer from the path-capture era; tl.py, comp.py and timelines were not mentioned | fixed |
| R11 | docs | FX_EXTRA.md | huekey (a registered op) was undocumented; the voronoi rule text was out of date | fixed |
| R12 | policy conflict | comp.py:212-216 vs save | `find(scope=[..., "region"])` is the documented opt-in for region footage, but save() refuses anything outside IN_SCOPE, so opting in can never be saved. ember has to decide: either a `Comp(scope=...)` that save() honours, or drop the find() parameter. | reported (ember's call) |
| R13 | latent (seams) | fx.py:269 echo | out = max(in, prev * decay) forgets as decay^25 per pre-roll. The default 0.85 leaves 0.017, about 4/255 at a seam. It is unused in today's timelines. The fx_extra recursive ops document this limit (fb ≤ 0.85); echo does not. Suggest saying so in TIMELINE.md, or capping history the way feedback `every > 1` does. | reported |
| R14 | latent | fx_extra.py:23,30,223,654 | 25 fps is hard-coded: HIST_CAP against the 1 s pre-roll, `_beat_crossed` (t - 1/25), feedback's `fno`, vhs's per-frame seed. At another fps, `_beat_crossed` would miss or double grid steps and the frame-based seeds would change rate. Meine is 25 fps. Fix: pass the timeline fps through Clock. | reported |
| R15 | latent | tl.py:224 Layer.open | samples the scale signal at most 4000 times over the layer's life. For a layer over 320 s (the Meine background, a whole-song head) that is coarser than 12.5 Hz, so a tau 0.12 beat pulse can fall between samples. The decode size then undershoots the peak, which upscales and blurs. | reported |
| R16 | latent | comp.py:237-252 footage() | with speed < 0, `pre`/`post` go negative and the hits_song filter `src_in <= x <= src_in + dur*speed` is empty. reverse() is the right tool, but footage() accepts the argument silently. Suggest raising on speed <= 0. | reported |
| R17 | clean | comp.py:520 say() | `layer.update(props)` replaces meta wholesale (hits_song is lost if a caller passes meta). footage() and _timed_layer merge meta instead. | reported |
| R18 | clean | comp.py Comp.beat_pos / period vs signals.Music | two implementations of the beat grid (comp keeps its own beats/period). They agree today; comp could use self.ctx.music. | reported |
| R19 | latent (signals) | signals.py:45 Music.intensity (tools lane finding) | beats.py bins intensity over [k*dt, (k+1)*dt), but the renderer and both viewers read v[k] as the value at k*dt, so the curve is half a bin (0.25 s) early. The fix belongs in signals.py (`x = t/dt - 0.5`) together with tlsignal.js and timeline.js. It shifts every intensity-driven param, so it is ember's call. | reported |
| R20 | env | .venv | cv2 and av each bundle their own libavdevice ("Class AVFFrameReceiver is implemented in both ... may cause spurious casting failures and mysterious crashes" on every run). opencv-python-headless still bundles FFmpeg. If a crash ever looks random, this is the first suspect. | reported |
| R21 | clean | render/render.py | the old project.json renderer duplicates mask, paste and audio logic and has no time ops or canonical clock. Nothing else imports it. It can be deleted once nobody renders project.json; the README now marks it as the old path. | reported |

## Findings: tools/ and studio/ (tools lane, committed on this branch)

| # | sev | where | what | status |
|---|---|---|---|---|
| T1 | **bug (never-early)** | tools/retime.py:59,125-134 | the remap picked source frame `round(t_src*fps)` through cv2's sequential reader, up to half a frame early. Measured against the committed `media/derived/face_missiles_on_beat.mp4`: 450 of 920 frames are one source frame early. cv2's BGR conversion also shifted levels. | fixed in da5f13f (media.Decoder timestamps, latest frame <= t). **The derived file must be regenerated** (`tools/retime.py projects/meine/sync/missiles_on_beat.json`); media/ was read-only for review. s0_rant and split_demo use it. |
| T2 | bug | studio/tlsignal.js | viewer drifted from signals.py: beat offset in the wrong unit (up to 0.96 off), onset min default 0 not 0.3, intensity ignored smooth, mean not median beat interval, other phase origin, unsorted keys, hold at an exact key returned the previous value | fixed; node vs compile_signal on 15 specs x 35k times: max diff 1.0 -> 3.3e-16. bezier.js vs bezier.py: 0 difference on all 7 path files |
| T3 | latent | tools/hits.py | audio envelope on container/audio-stream time instead of the canonical video clock (41 of 339 clips have video starting 21-33 ms after audio: peaks pooled a frame late); pooled to the next frame instead of the one on screen; sheets seeked on the container clock and dropped single-frame flashes at fps=12.5 | fixed; synthetic offset clips now put the audio peak and the flash on the same frame |
| T4 | bug | studio/studio.js:284-289 | capture silently recorded nothing if playback was already running | fixed (Playwright: 4 -> 5 takes) |
| T5 | latent | studio/server.py | every save of a file shared one temp name (concurrent saves could move a half-written file into place); non-JSON body was a 500; `Range: bytes=-` crashed | fixed (4x30 concurrent saves: 49 failures -> 0) |
| T6 | bug (UI) | studio/timeline.js:518-535 | playhead flashed to R0 on every live reload; error listeners piled up | fixed |
| T7 | perf/latent | tools/selfmotion.mjs | O(frames x detections) gap fill; pose/track length mismatch gave NaN paths silently; absolute --out was joined under projects/ | fixed; all 4 modes byte-identical output |
| T8 | bug | tools/facepose.py:35 | default model path relative to cwd | fixed |
| T9 | latent | tools/refine_hits.py:55-62 | not idempotent: a hit moved on an earlier run keeps its moved t even when a later run accepts t_agent | reported (restoring t would clobber hand edits; ember's call) |
| T10 | latent | tools/transcribe.py:70-72 | `max(d)` crashes when no word aligns (after the JSON is written) | reported |
| T11 | latent | tools/prep.sh:15, facecrop.py, facepose.py | rate 160050/5519 hard-coded; cv2 frame-index clock instead of pts (<= 1 ms off for missiles_short.mov) | reported |
| T12 | latent | tools/beats.py:54-62 | `binned` divides by zero on silence; `harm` unused; see R19 for the intensity bin offset | reported |
| T13 | clean | studio/bezier.js splice | neighbouring handles stay fitted to the old segment (overshoot) | reported (changes editing behaviour) |

## Findings: projects/meine/comps (not edited: live; suggested patches)

C1. **bug, sections/s1_build.py:391.** The `fall{i}` heads freeze 16-20 s of source away
from what `bounce{i}` shows at bar 72, so the "freeze mid-word" is a visible jump. The `+33`
ignores that heads 4-7 restart at bar 64 and ignores FACE_LOOP.

```diff
-        c.add(L.head(f"fall{i}", b72, t_drop + 0.9, fall, SIZES[i] * 0.85, hold=(i * 5.1 + 3 + 33) % 34,
+        a_last = c.bar(44) if i < 4 else c.bar(64)     # start of bounce{i}'s last presence
+        c.add(L.head(f"fall{i}", b72, t_drop + 0.9, fall, SIZES[i] * 0.85,
+                     hold=round(L.src_time(b72, a_last, (i * 5.1 + 3) % 34), 3),
```

Related, maybe intended: `bounce{i}.1` restarts the same source stretch at bar 64 instead
of continuing.

C2. **latent, full.py:24.** A ModuleNotFoundError raised *inside* a section (a typo in
s1_lib's imports) prints "not written yet" and drops the section from the full render.

```diff
-    except ModuleNotFoundError:
+    except ModuleNotFoundError as e:
+        if e.name != f"sections.{name}":
+            raise
```

C3. **latent (ember's rules), sections/s2_peak.py:99,358,412,417,452,499,505.** Raw
`c.add()` footage has no meta. R7 now makes save() check these by src anyway. Still add the
link so the viewer groups them and hits show:
`"meta": {"catalog": seg.catalog, "clip": seg.clip["id"], "seg": seg.idx, "hits_song": []}`
(s1_build's gaza-bed already does).

C4. **bug, sections/s2_peak.py:104-106 / s2_kit.py:49.** P-drift plays at `speed: 0.5`, but
`retime_path` samples the drift path at 1x, so his motion is decoupled from his own face.
Give `retime_path` a `speed=1.0` argument, use
`s = a + ((src_in - a) + i * dt * speed) % (b - a)`, and pass `speed=0.5`.

C5. **outro and R5.** s2_peak places outro material after the last beat (456.876 s) through
c.bar/c.beat. With R5 fixed, re-running s2_peak moves anything computed past that point by up
to 0.2 s, onto the grid it asked for. Expect that diff when the section is regenerated.

C6. **clean.**
- s2_peak:380 accounts `pools.take` at `B(b, 2.5)` but places the hit at `B(b, 2)`.
- Unused parameters: `dip_and_reentry(c, P)` and `cut_keys(times, ...)` (s1_build:93).
- split_demo:19 has a redundant comprehension.
- s1_lib `shape16("grid", 1)` divides by zero.
- In s0_rant and split_demo, `blasts[k]` raises IndexError if there are more "missiles" words
  than blasts (today 6 against 23).

C7. **latent, gallery/make_gallery.py:200-208.** `frames_of` seeks with cv2
`CAP_PROP_POS_MSEC`, which is imprecise and not the canonical clock. The sheet times assume
uniform beats.

```diff
-    cap = cv2.VideoCapture(str(mp4)); ... cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
+    fr = decode_range(mp4, 0, max(times) + 0.1); ts = [x[0] for x in fr]
+    return [cv2.cvtColor(fr[max(0, bisect_right(ts, t + 1e-6) - 1)][1], cv2.COLOR_RGB2BGR) if fr else None for t in times]
```

Also `times = [c.beat(c.beat_pos(t0) + b) - t0 + 0.06 ...]`; `--jobs` above 3 is silently
capped (297); `c.layers = []` (154) is redundant.

C8. **saved timelines vs the scope rule.** Every saved timeline in comps/out predates the
scope rule and has out-of-scope layers (full_v1: 48, s1_build: 20, s2_peak: 27, split_demo
3, time_ops_demo 3, s0 1, fixture 2). They still render, since tl.py does not enforce scope.
They fail only when their script saves again.
