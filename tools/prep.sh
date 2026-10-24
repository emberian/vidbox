#!/bin/zsh
# Build derived media from media/src. Re-runnable; skips outputs that already exist.
set -euo pipefail
cd "${0:A:h}/.."
D=media/derived

# Studio preview proxies: h264, short GOP so scrubbing is snappy.
[[ -f $D/meine_proxy.mp4 ]] || ffmpeg -v error -stats -i media/src/meine.webm \
  -vf scale=960:720 -c:v libx264 -crf 23 -preset veryfast -g 12 -pix_fmt yuv420p \
  -c:a aac -b:a 160k -movflags +faststart $D/meine_proxy.mp4

# Face-tracked crop of the short, with his voice muxed back in.
if [[ ! -f $D/face.mp4 ]]; then
  uv run python -I tools/facecrop.py media/src/missiles_short.mov 480 600 --track $D/face_track.json \
    | ffmpeg -v error -f rawvideo -pix_fmt bgr24 -s 480x600 -r 160050/5519 -i - \
      -i media/src/missiles_short.mov -map 0:v -map 1:a \
      -c:v libx264 -crf 12 -g 15 -pix_fmt yuv420p -c:a aac -b:a 160k -shortest \
      -movflags +faststart $D/face.mp4
fi
[[ -f $D/face_track.json ]] || uv run python -I tools/facecrop.py media/src/missiles_short.mov 480 600 --track $D/face_track.json --track-only
ls -la $D
