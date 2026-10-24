# Meine (Daso), structure map

7:53 (473.5s), 25 fps, 1440x1080 with letterbox; picture area is y=158..922.
The video is ONE continuous tracking shot out of a moving vehicle past East German
industrial buildings (single cut at 0.9s), so structure comes from the music.

Loudness is mastered flat (~-11 dB RMS throughout), so intensity is read from
high-band (>2 kHz) energy, `hiband_rms_halfsec.txt` (time_s, dB per 0.5 s):

| time        | section                      | hi-band dB |
|-------------|------------------------------|------------|
| 0:00-0:37   | intro; the preacher's face (speech short, 36.8s) is overlaid here | -32 |
| 0:37-2:15   | slow build                   | -31 -> -28 |
| 2:15-2:45   | breakdown / drop-out         | -31 -> -32.5 |
| 2:45-3:45   | rise                         | -27 -> -26.4 |
| 3:45-4:00   | short dip                    | -31 |
| 4:00-6:15   | main peak (hottest 5:30-6:00) | -25.5 -> -23.8 |
| 6:15-7:30   | plateau, slightly cooler     | -27.5 |
| 7:30-7:53   | outro / fade                 | -33 -> silence |

Plan so far: after the preacher finishes speaking (~0:37) his head splits into many
copies (chromatic pulsing, noise textures, bouncing) that intensify with the music.
War footage is composited over / between / around this, sometimes several scenes at once.
