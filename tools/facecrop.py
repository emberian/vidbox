"""Track the largest face in a video and stream a face-centered crop as raw BGR24 to stdout.

usage: facecrop.py INPUT OUT_W OUT_H > raw
Crop box is a fixed size (from the median face size) so the face scale stays steady;
only its center follows the smoothed track.
"""
import sys

import cv2
import numpy as np

src, out_w, out_h = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

# pass 1: detect
cap = cv2.VideoCapture(src)
dets = []
while True:
    ok, frame = cap.read()
    if not ok:
        break
    H, W = frame.shape[:2]
    gray =cv2.equalizeHist(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY))
    faces = cascade.detectMultiScale(gray, 1.1, 6, minSize=(80, 80))
    if len(faces):
        x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
        dets.append((x + w / 2, y + h / 2, w))
    else:
        dets.append(None)
cap.release()

n = len(dets)
hit = [i for i, d in enumerate(dets) if d is not None]
print(f"frames={n} detected={len(hit)}", file=sys.stderr)
idx = np.arange(n)
cx = np.interp(idx, hit, [dets[i][0] for i in hit])
cy = np.interp(idx, hit, [dets[i][1] for i in hit])

# smooth the path (centered moving average, ~0.5s)
k = 15
kern = np.ones(k) / k
cx = np.convolve(np.pad(cx, k // 2, mode="edge"), kern, "valid")
cy = np.convolve(np.pad(cy, k // 2, mode="edge"), kern, "valid")

fs = float(np.median([dets[i][2] for i in hit]))
# box wide enough for hat-to-beard; nudge down since the Haar box sits eyes-to-mouth
bw = fs * 1.25
bh = bw * out_h / out_w
cy = cy + fs * 0.05
print(f"face_size={fs:.0f} box={bw:.0f}x{bh:.0f} src={W}x{H}", file=sys.stderr)

# pass 2: crop (pad with edge pixels if the box runs off-frame)
cap = cv2.VideoCapture(src)
pad = int(max(bw, bh))
out = sys.stdout.buffer
for i in range(n):
    ok, frame = cap.read()
    if not ok:
        break
    big = cv2.copyMakeBorder(frame, pad, pad, pad, pad, cv2.BORDER_REPLICATE)
    x0 = int(round(cx[i] - bw / 2)) + pad
    y0 = int(round(cy[i] - bh / 2)) + pad
    crop = big[y0 : y0 + int(bh), x0 : x0 + int(bw)]
    out.write(cv2.resize(crop, (out_w, out_h), interpolation=cv2.INTER_AREA).tobytes())
