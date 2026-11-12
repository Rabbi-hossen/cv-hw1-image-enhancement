"""Downscale the raw camera photos (data/raw) to data/original (long side 800 px).

Downscaling keeps the non-local-means step fast and reduces sensor noise slightly.
Run once (already done; data/original is included in the repository):
    python src/prepare_images.py
"""
import os
import cv2

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW, OUT, LONG_SIDE = os.path.join(ROOT, "data", "raw"), os.path.join(ROOT, "data", "original"), 800

os.makedirs(OUT, exist_ok=True)
for f in sorted(os.listdir(RAW)):
    img = cv2.imread(os.path.join(RAW, f), cv2.IMREAD_COLOR)
    s = LONG_SIDE / max(img.shape[:2])
    img = cv2.resize(img, None, fx=s, fy=s, interpolation=cv2.INTER_AREA)
    cv2.imwrite(os.path.join(OUT, os.path.splitext(f)[0] + ".png"), img)
    print(f, "->", img.shape)
