# vidbox review 2 (branch review/2, from dev 8a19c4c)

The second read-through, 2026-10-24. It follows a runaway that ate hundreds of GB and swap-hung
the machine: a `while t < t1` loop in `signals.compile_time` that could stop advancing on a
float edge (8a19c4c). This pass hunts the same shape everywhere: loops whose progress rests on
float arithmetic or on data, allocations sized by data or parameters with no bound, buffers
multiplied by layers x processes, and processes that outlive their render.

Everything here was diagnosed by reading. Nothing suspected of running away was reproduced. Every
run went through `~/tools/memguard.sh`.

Severity: **runaway** (unbounded memory or a loop that never ends), **leak** (processes, files),
**bug**, **latent** (wrong under conditions not hit today), **perf**. File:line is on this branch
unless the item says otherwise.

## Verification

- **Identity control** (lossless `VIDBOX_CRF=0`, `--full --jobs 1`): section_s0_rant 9-14 and
  full_v2 330-336, rendered before the first change (8a19c4c) and at the branch head. **Video:
  every frame bit-identical (framemd5); audio: bit-identical as PCM** (md5 of the decoded f32
  stream). Same result after the first batch of commits (1249828..afce19b).
- **Seams:** full_v2 52-64 lossless, 1 job against 3 jobs at the head: video and audio identical
  (300 frames).
- **Unit identity**, old code against new on real data:
  - `layer_audio`: all 135 audio layers of full_v2, s1_build.paying, time_ops_demo, fixture and
    s0, bit-identical.
  - `revisit_spans`: every layer of all 11 saved timelines (two start points each), 0
    differences. Over 3000 random seqs there were 103 differences, and each one is the old code
    emitting an inverted interval (see 57e6501).
  - `Comp.groove`: 1675 maps (67 segments x 5 starts x 5 argument sets), identical.
  - credits: raw rgb frame stream (sha256 of 26.2 GB), identical.
  - `tools/hits.py`: candidate JSON on 3 clips, identical.
- **Invariant 6:** all 11 timelines in comps/out compile every layer under the new limits (the
  largest layer drawn is 2.14 canvases; the cap is 16).
- **Supervision:** a chunk that fails at once (s0 0-12, 3 jobs, a missing src in the third)
  ends the render in 1.1 s ("chunk render failed: [None, None, 1]") with nothing left running.
  A parent SIGKILLed mid-render leaves no chunk alive 8 s later.

## Memory (max RSS, one process, `--full`)

| what | before | after |
|---|---|---|
| s0 9-14, 1 job (3 layers) | 1813 MB | 909 MB |
| full_v2 330-336, 1 job (14 layers) | 2186 MB | 1293 MB |
| credits, short | 1378 MB | 281 MB |
| credits, long (every name) | ~8 GB (estimated, not run) | 280 MB |
| hits.py, 471 s 60 fps clip | 2073 MB | 1232 MB |
| hits.py, 799 s clip | 1944 MB | 1480 MB |

CPU is unchanged: full_v2 330-336 in-process, interleaved old/new x2, renderer self CPU
22.96 / 23.26 s old and 22.18 / 23.32 s new. Wall clock was useless here (load average 30-58
from other agents; one head render took 28 s against 14.6 s for base, and the same code under
the in-process probe took 13.5 s).

A render's memory is per chunk process, times `--jobs`: about 0.5 GB of libraries and decoder
threads, plus up to 64 MB of recent frames per open layer (was 120 frames: 560 MB for a
full-canvas layer), plus the span cache (up to 512 MB), plus the mask cache (64 MB, was up
to ~400 MB). The README's `full.timeline.json --full --jobs 8` was 8 x 2-3 GB, and every retry
of a timed-out render stacked another 8 (see L1).

## Findings: runaway and unbounded allocation

| # | sev | where | failure scenario | status |
|---|---|---|---|---|
| A1 | runaway | signals.py compile_time, loop form (8a19c4c cap: `int(passes) + 4`) | The run cap scales with the pass count, so a loop far shorter than a frame (`loop: [5, 5.000001]`) or a huge speed is a *legitimate* list of 10^8+ Run objects (~40 GB) that the cap allows. | fixed 7568402: passes checked against `MAX_RUNS` (100k) before anything is allocated. The progress cap is now 2x passes + 4, since a float edge can add one sliver run per wrap and could trip `+4` on a legitimate timeline. |
| A2 | runaway | signals.py `_seq_runs` | `repeat` is data, and each repeat is up to two Run objects: `stut(..., n=int(span / every))` with a tiny `every` was unbounded. With `every <= 0`, every trigger lands at the same time. | fixed 7568402: same cap; `every <= 0` with repeat > 1 is refused |
| A3 | runaway | tl.py layer_audio tempo path, `_atempo` (8a19c4c :405-412) | The 0.05 s of source context on each side is stretched by 1/speed, and ffmpeg's whole output is captured in memory. Constant speed 1e-5 gives 10^4 s of stereo float32 (3.8 GB) per run; 1e-6 gives 38 GB. A slow `play`, a near-hold `map` piece, or a footage_multi stretch between two nearby hits all qualify. | fixed 3b3ceb6: context ≤ 2 s of song time once stretched (unchanged for \|v\| ≥ 0.025; the slowest saved tempo run is 0.556), and ffmpeg stops 1 s past the samples needed. Bit-identical on all 135 audio layers. |
| A4 | runaway | tl.py atempo_chain | `while f < 0.5: f /= 0.5` never ends at f = 0 (and `f > 2` never ends at inf); it appends filters forever. layer_audio filters speed 0 out today, so it is not reachable now, but it would be the moment a caller passed a held run. | fixed 3b3ceb6: refuses f outside (0, inf) |
| A5 | runaway (O(n^2) memory) | tl.py revisit_spans (8a19c4c :42-63) | Each forward run appended one piece for every earlier overlapping run: n retriggers of one slice build ~n^2 / 2 tuples before the merge (12.5M for n = 5000), in every chunk process. | fixed 57e6501: interval unions, O(n) for retriggers (10k runs: 0.08 s). Old code emitted an inverted `(0.0, negative)` span for material wholly below source time -pad; harmless (never matched), now gone |
| A6 | runaway | tl.py Layer.draw (8a19c4c :247-253) | Display size is base x scale with no bound, followed by float32 img, alpha and mask copies plus fx at that size. Decode is capped at native size, display is not: a scale signal reaching 50 on a 480x600 head is 24000x30000 px, ~8.6 GB per float copy per frame. | fixed caf8353: raises past `MAX_LAYER_AREA` (16 canvases) |
| A7 | runaway | comp.py groove (8a19c4c :440-446) | `while True` until `beat(b0 + k L) >= at + dur`: a NaN or inf `dur`, or a non-positive cycle, appends knots forever. | fixed 8d45fc9: knot count bounded up front from `beat_pos(at + dur)` |
| A8 | runaway | comp.py bounce | `t += nb * period` with nb from `beats_per_crossing`: a 0 there, or an infinite t1, never ends. | fixed 8d45fc9 |
| A9 | runaway (report) | **sections/s1_build.py:123-128** panel_cuts, looped panel | `per = (b - a) / speed`, then `while t < t1: ... t = min(t + per, t1)`. Speed ≤ 0 or an empty loop gives per ≤ 0: an infinite loop appending to `song` / `srcs`, the 8a19c4c shape exactly. Today's calls pass speed 1 and 2.4-2.6 s loops. | reported (live file). Patch below |
| A10 | runaway (report) | **sections/s1_lib.py:148-156** bounce_keys | `tn = c.snap(t + nb * c.period)`: with any nb < 0.5 in `choices(t)`, snap rounds back to t, so t never advances and K grows forever. Today's choices are 1 and 2. | reported (live file). Patch below |
| A11 | unbounded | signals.py Music.intensity | `smooth` sets the pad and kernel length (2 smooth / dt + 1): smooth 1e9 asks numpy for 16 GB per array. | fixed c66cf5a: raises past the song length (saved: 1.0 and 2.0) |
| A12 | unbounded | signals.py compile_time, speed signal | The table is `(t1 - t0) / dt` Python evaluations long: an inf or huge t1 is unbounded. | fixed 7568402: span ≤ 4 h |
| A13 | unbounded | media.py Reader._span | The span size was estimated from the stream's average fps, then decoded into a list with no running check: a mislabelled stream overruns the cache's half-cap. | fixed c66cf5a: gives up past it and streams |
| A14 | multiplier | media.py Reader (8a19c4c :102-184) | It kept the last 120 shown frames converted: a full-canvas layer held 560 MB, per open layer, per chunk process. Measured on s0 9-14: keep=120 at 1726 MB, keep=16 at 971 MB. | fixed 1249828: converted frames ≤ `VIDBOX_READER_MB` (64) per Reader, oldest dropped first (a step back re-seeks). Saved loops are 34-36 s (past the buffer anyway) or 2.4-2.6 s on 430 px panels (27 MB, fits). |
| A15 | multiplier | media.py Reader._pull | During a seek's keyframe pre-roll, the frames pulled past kept their raw source-size frame until get() returned: up to 120 raw frames (1.5 GB for 4K). | fixed 1249828: dropped as the pull passes them (get() dropped them afterwards anyway) |
| A16 | multiplier | tl.py mask cache | Capped at 64 entries, not bytes. A pulsing masked layer misses every frame (new size), so the cache filled with 65 masks: 177 MB measured on s0's preacher, ~400 MB for a full-canvas mask. Also a recompute per frame (perf). | fixed caf8353: 64 MB byte cap. The per-frame recompute remains (perf, see P3) |
| A17 | unbounded | tools/credits.py render | All ~760 name pages of the long version were drawn as PIL images, then copied to numpy, before the first frame was written: ~8 GB in one process (credits_full.mp4 was rendered at 04:57 today). | fixed 8859788: pages drawn when written; 280 MB |
| A18 | unbounded | tools/hits.py | Stacked the whole clip as float32, plus `np.diff` and `abs` copies of the stack: 2 GB on a 471 s 60 fps clip, scaling with clip length (the longest source is 799 s). | fixed 15c8357: 1024-frame blocks, identical output on 3 clips (2073 -> 1232 MB on the 471 s one) |

## Findings: leaks (processes and files)

| # | sev | where | failure scenario | status |
|---|---|---|---|---|
| L1 | leak | tl.py main (8a19c4c :530-540) | `codes = [p.wait() for p in procs]`: one failed chunk left the others rendering to the end. SIGTERM (a tool timeout) killed main() with no cleanup. SIGKILL left every chunk running as an orphan with its full working set until its range was done. So a timed-out render retried a few times stacks jobs x retries chunk processes of 2-3 GB each. | fixed afce19b + 5c9b7a2: `wait_chunks` stops the rest on the first failure; a finally SIGTERMs and reaps them; SIGTERM raises SystemExit in main(); chunks exit within 25 frames once their parent is gone (`VIDBOX_PARENT_PID`, the only defence against SIGKILL) |
| L2 | leak/bug | tl.py render_video | The encoder was closed and waited for only on success. A chunk that raised left ffmpeg finalising its part file while main() deleted the temp dir: `OSError: Directory not empty` instead of "chunk render failed", and the encoder outlived the chunk. | fixed 5c9b7a2: try/finally closes stdin, waits, closes readers |
| L3 | multiplier | tl.py main | `--jobs` above the core count only multiplies memory. | fixed 2dcfcef: capped at `os.cpu_count()` (output is job-count independent) |

## Findings: other, reported

| # | sev | where | what | why not fixed |
|---|---|---|---|---|
| R1 | latent | tools/fetch_sources.py:75 | When yt-dlp's extension differs from the manifest's, the file is moved to `dest.with_suffix(got.suffix)`. Renders and the next run look for `dest`, so the source is "missing" forever and re-downloaded on every run. It applies to media/src/ (keep_format). Fix: remux into `dest`'s container (`ffmpeg -i got -c copy dest`), or fail loudly. | changes fetched media; ember's call on remux vs fail |
| P1 | perf | media.py:21 `thread_type = "AUTO"` | Every open Reader gets its own frame-thread pool, so threads = jobs x open layers x cores (full_v2 has 14 active layers). Measured ~100 MB on s0 at 3 layers. Mostly CPU oversubscription. | changes decode speed per layer; needs a timing pass on an idle machine |
| P2 | perf | signals.py:367 speed signals | Tabulated with one Python call per 1 ms, in Layer() of every chunk process, in layer_audio and in comp: a whole-song varispeed is ~470k calls (1-2 s) each time. | bounded now (A12); speed only |
| P3 | perf | tl.py mask(); fx_extra.py `_Ring.push` | A layer whose scale changes every frame recomputes its mask every frame. Under chromatime/slitscan it rebuilds a 25-frame stack (24 resizes, 155 MB at full canvas) every frame. | bounded; speed only |
| P4 | perf | tl.py source_audio | Decodes from the file start to `until` + 1 s each time a later layer needs more of the same source (the cache keeps only the longest), and `_audio_cache` holds every source's prefix with no cap. Bounded by source length: 26 MB is the largest today; a 799 s source would be 300 MB. | fine today |
| P5 | latent | fx_extra.py:753 glitch blocks | `nblk = int(strength * blocks * 2)`, with strength a signal: a mis-scaled strength (100) is 2800 block copies per frame. CPU only. | changes output for strength > 1 if clamped |
| C | sections | s1_build, s1_lib | A9, A10 above. REVIEW.md C1-C8 are still open; this pass did not touch them. | live files |

### Patches for the live section files (not applied)

A9, `sections/s1_build.py` panel_cuts:

```diff
     if loop:    # a looped panel as an explicit map: one linear piece per pass, a 1 ms jump back between them
         a, b = loop
         per = (b - a) / speed
+        if not per > 0.002:   # else the loop below never advances (speed <= 0, empty loop)
+            raise ValueError(f"panel_cuts loop {loop} at speed {speed}")
         song, srcs, t = [], [], t0
```

A10, `sections/s1_lib.py` bounce_keys:

```diff
         nb = r.choice(choices(t))
         tn = c.snap(t + nb * c.period)
+        if tn <= t + 1e-6:   # nb < 0.5 snaps back onto t: K would grow forever
+            raise ValueError(f"bounce_keys: {nb} beats from {t:.3f} does not reach the next beat")
```

## What could also have caused the hundreds-of-GB incident

Ranked by likelihood. None was reproduced.

1. **The compile_time loop (8a19c4c).** It grows without bound in one process, and it is the
   only shape found that needs no degenerate input, only an unlucky float.
2. **Stacked chunk processes (L1).** Each chunk was 2-3 GB at --full (and over 3 GB at the
   busiest stretches of full_v2, by my static estimate: 1.9 GB of Reader buffers alone at t=95 s),
   and `--jobs 8` is the documented command. Two things stacked them: a tool timeout that
   SIGTERMs or SIGKILLs the parent leaves the chunks running, and an agent that retries does it
   again. 3 retries x 8 jobs x 3 GB is 72 GB, and two agents doing this is past 100 GB. This
   needs no bug in the timeline at all.
3. **The same loop shape in section code being written live (A9, A10, A7, A8).** A degenerate
   argument at composition time (speed 0 in panel_cuts, a 0.25-beat choice in bounce_keys, an inf
   dur in groove) is an infinite append, exactly like the original. These run in the composing
   agent's own process, outside any render.
4. **Slow tempo audio (A3).** One run at speed below about 1e-5 is several GB to tens of GB in the
   mux, and it needs only one slow, near-hold piece with `audio`. No saved timeline has one.
5. **Contributors, not causes:** credits_full (~8 GB, rendered today), hits.py over long clips
   (2 GB each, often run in parallel), a runaway scale signal (A6).

## For the root at merge

- No timeline needs regenerating and no media changes. Renders are bit-identical.
- The section patches A9 and A10 are for whoever owns s1_build / s1_lib now.
- New knobs: `VIDBOX_READER_MB` (64). New limits that raise: `signals.MAX_RUNS`,
  `tl.MAX_LAYER_AREA`, smooth > song, speed-signal span > 4 h. `--jobs` is capped at the core
  count.
- `media` in the worktree is a symlink to the main checkout's media/ (untracked, not committed).
