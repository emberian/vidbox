# s2_peak: continuation notes (lane B, written mid-task, 2026-10-24)

## State (revision 4, 2026-10-24: ember's v2 notes; see s2_peak_NOTES.md "Revision 4")
- Punctures are now two 3-bar ones (code 171-173, 178-180) with soft edges (`real(lead=, xout=)`, 4-tuple windows); the morgue holds 3 bars; ducks deepen only with length, and every release lasts at least a bar.
- Pools are fresh (`Pools.take` checks source overlap against the whole Comp), with detected onsets added (`s2_kit.onsets`, cached in comps/out/section_s2_peak.onsets.json). 0 repeated pairs standalone; 4 in full.py (the countdown motif plus 3 s1 shots inside the crater take).
- The F-35 CGI is replaced by the IMOD 200th airlift.

## Earlier state (revision 3)
- `s2_peak.py` builds and `c.save()` passes: in scope, 0 hits off the grid.
- `section_s2_peak.mp4` is a full render of the current timeline.
- **Current task: ember's "full truth" direction.** Untreated reality windows, source audio, music
  ducks, lingering holds, stacks, Zinati. These are implemented; the caption sweep and the notes
  update were in progress.

## Mechanism
- `real(c, ref, t0, t1, src_in, ...)` in `s2_peak.py` adds an untreated layer:
  - normal blend, no fx, `clip: picture`
  - its own audio
  - `meta.people` for names
  - `c.duck_music` underneath
- It also opens a "reality window". `build()`'s post-pass merges the windows. Inside them it:
  - mutes every non-`real` layer of the section (chorus, beds, strikes, his head)
  - drops any spoken-word layer
  - ducks Meine to 0
- To add an untreated moment, call `real()`. Nothing else needs changing.

## Untreated moments (bar: song time)
- 160-163 (304.97-312.59): a 2x2 grid of ground takes, one tile per beat, held, all their sounds.
  Music ducked to 0.3.
- (superseded by revision 4) Punctures, one bar each, full frame, music to 0.25:
  - 171 (325.93): morgue tray
  - 175 (333.54): Shifa wounded
  - 179 (341.16): bones on cloth
  - 187 (356.40): women over shrouds
  - 191 (364.02): MEE 112 remains
- 184 (350.68): Bureij blast. Portrait window, untouched, own audio, music to 0.35. His "Hellfire
  missiles" is small and still at the side.
- 185-186 (352.60-356.40): Khan Younis morgue arrival, full frame, music to 0.15.
- 204 (388.78): Zinati. Guardian eyewitness footage, src 2.0-6.9, own sound, music to 0.05. Then
  black until bar 208, music nearly silent (measured -40 dB).
- 208-215 (396.40-411.63): the Hassayna/Abu Sharia mass funeral, one 15 s take, music to 0.3.
- 224-231 (426.88-442.11): Mahmoud (was Hammad; now the al-Aqsa hospital prayer over body bags, see s2_peak_NOTES.md) sieving, one 15 s take, music to 0.3.

## Named people (meta.people)
- Mohammad Abdul Zinati (15, killed)
- Sharif Shadi Labad (paramedic, injured)
- Tamer Labbad (filmed it)
- Mahmoud (was Hammad; now the al-Aqsa hospital prayer over body bags, see s2_peak_NOTES.md) (bereaved father)

## Left to do
- Nothing. Revision 3 is complete: rendered, caption-swept at 1 s, and in the notes.
