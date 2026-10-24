"""Per-frame face pose and gaze, in image space, via MediaPipe Face Landmarker.

usage: uv run python tools/facepose.py VIDEO OUT.json [--model media/models/face_landmarker.task]

Per frame (null when no face):
  face_h, face_v  where the face points, as seen in the picture: nose tip offset from the
                  cheek/brow-chin midpoints, in face widths/heights. +h = toward image right,
                  +v = toward image bottom. Measured in the image, so no mirror/sign guessing.
  gaze_h, gaze_v  iris offset within the eye opening (both eyes averaged), same signs.
  yaw, pitch, roll  degrees from the model's facial transformation matrix (cross-check).
  cx, cy, size    face center (px) and inter-ocular distance (px).
"""
import argparse
import json
import math
import sys
from pathlib import Path

import cv2
import mediapipe as mp
import numpy as np
from mediapipe.tasks.python import BaseOptions, vision

ROOT = Path(__file__).resolve().parent.parent

# MediaPipe face mesh indices
NOSE, CHEEK_A, CHEEK_B, BROW, CHIN = 1, 234, 454, 10, 152
EYES = [  # (outer corner, inner corner, upper lid, lower lid, iris center)
    (33, 133, 159, 145, 468),
    (263, 362, 386, 374, 473),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("out")
    ap.add_argument("--model", default=str(ROOT / "media/models/face_landmarker.task"))
    a = ap.parse_args()

    lm = vision.FaceLandmarker.create_from_options(vision.FaceLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=a.model),
        running_mode=vision.RunningMode.VIDEO,
        num_faces=1,
        output_facial_transformation_matrixes=True,
    ))
    cap = cv2.VideoCapture(a.video)
    fps = cap.get(cv2.CAP_PROP_FPS)
    frames = []
    i = 0
    while True:
        ok, bgr = cap.read()
        if not ok:
            break
        H, W = bgr.shape[:2]
        img = mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB))
        res = lm.detect_for_video(img, int(round(i * 1000 / fps)))
        i += 1
        if not res.face_landmarks:
            frames.append(None)
            continue
        P = np.array([[p.x * W, p.y * H] for p in res.face_landmarks[0]])
        a_, b_ = P[CHEEK_A], P[CHEEK_B]
        width = np.linalg.norm(b_ - a_)
        height = np.linalg.norm(P[CHIN] - P[BROW])
        # signed offsets along image axes, normalized by face size
        face_h = (P[NOSE][0] - (a_[0] + b_[0]) / 2) / width
        face_v = (P[NOSE][1] - (P[BROW][1] + P[CHIN][1]) / 2) / height
        gh, gv = [], []
        for outer, inner, up, low, iris in EYES:
            ew = abs(P[inner][0] - P[outer][0])
            eh = abs(P[low][1] - P[up][1])
            gh.append((P[iris][0] - (P[inner][0] + P[outer][0]) / 2) / max(ew, 1))
            gv.append((P[iris][1] - (P[up][1] + P[low][1]) / 2) / max(eh, 1))
        M = np.array(res.facial_transformation_matrixes[0])[:3, :3]
        yaw = math.degrees(math.atan2(-M[2, 0], math.hypot(M[2, 1], M[2, 2])))
        pitch = math.degrees(math.atan2(M[2, 1], M[2, 2]))
        roll = math.degrees(math.atan2(M[1, 0], M[0, 0]))
        center = P.mean(axis=0)
        frames.append({k: round(float(v), 4) for k, v in dict(
            face_h=face_h, face_v=face_v, gaze_h=np.mean(gh), gaze_v=np.mean(gv),
            yaw=yaw, pitch=pitch, roll=roll, cx=center[0], cy=center[1],
            size=np.linalg.norm(P[468] - P[473]),
        ).items()})
    cap.release()
    with open(a.out, "w") as f:
        json.dump({"src": a.video, "fps": fps, "frames": frames}, f)
    hit = sum(f is not None for f in frames)
    print(f"{len(frames)} frames, face in {hit} -> {a.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
