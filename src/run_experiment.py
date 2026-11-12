"""Run the complete pipeline: degrade -> enhance -> metrics -> figures.

Usage (from the repository root):   python src/run_experiment.py
"""
import csv
import os
import sys

import cv2
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from degradation import degrade, CONTRAST_ALPHA, NOISE_SIGMA, SEED
from enhancement import METHODS, LABELS
import metrics as M

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORIG = os.path.join(ROOT, "data", "original")
DEGR = os.path.join(ROOT, "data", "degraded")
PROC = os.path.join(ROOT, "results", "processed")
FIGS = os.path.join(ROOT, "results", "figures")
CSV_PATH = os.path.join(ROOT, "results", "metrics.csv")

# (image, crop used for the zoomed figure: y0, y1, x0, x1)
CROPS = {
    "bottle": (290, 410, 200, 340),
    "cap": (340, 460, 330, 470),
    "lamp": (400, 520, 250, 390),
    "mug": (340, 460, 390, 530),
    "phone": (380, 500, 220, 360),
}
COLS = ["original", "degraded", "stretch_lum", "hist_eq", "stretch_nlm"]


def to_rgb(x):
    return cv2.cvtColor(x, cv2.COLOR_BGR2RGB)


def grid_figure(rows, path, crop=False):
    """rows: list of (name, {key: bgr image}). Same size/scale for every panel."""
    first = rows[0][1]["original"]
    if crop:
        y0, y1, x0, x1 = CROPS[rows[0][0]]; ratio = (y1 - y0) / (x1 - x0)
    else:
        ratio = first.shape[0] / first.shape[1]
    fig, axes = plt.subplots(len(rows), len(COLS), figsize=(1.7 * len(COLS), 1.7 * ratio * len(rows) + 0.3), squeeze=False)
    for r, (name, ims) in enumerate(rows):
        for c, key in enumerate(COLS):
            ax = axes[r, c]
            img = ims[key]
            if crop:
                y0, y1, x0, x1 = CROPS[name]
                img = img[y0:y1, x0:x1]
            ax.imshow(to_rgb(img), vmin=0, vmax=255, interpolation="nearest" if crop else "bilinear")
            ax.set_xticks([]); ax.set_yticks([])
            for s in ax.spines.values():
                s.set_visible(False)
            if r == 0:
                ax.set_title(LABELS[key], fontsize=7.5)
            if c == 0:
                ax.set_ylabel(name, fontsize=8)
    plt.tight_layout(pad=0.3)
    fig.savefig(path, dpi=200)
    plt.close(fig)


def hist_figure(name, ims, path):
    """Luminance histograms (Lab L) of original / degraded / methods."""
    keys = ["original", "degraded", "stretch_lum", "hist_eq", "stretch_nlm"]
    fig, axes = plt.subplots(1, len(keys), figsize=(2.3 * len(keys), 1.6), sharey=True)
    for ax, k in zip(axes, keys):
        L = cv2.cvtColor(ims[k], cv2.COLOR_BGR2LAB)[..., 0]
        ax.hist(L.ravel(), bins=64, range=(0, 255), color="0.35")
        ax.set_title(LABELS[k], fontsize=7.5)
        ax.tick_params(labelsize=6)
        ax.set_yticks([])
    plt.tight_layout(pad=0.3)
    fig.savefig(path, dpi=200)
    plt.close(fig)


def color_shift_figure(rows, path, names=("lamp", "phone")):
    """Original vs luminance-only stretch vs per-channel stretch (colour shifts)."""
    keys = ["original", "stretch_lum", "stretch_rgb"]
    sel = [r for r in rows if r[0] in names]
    fig, axes = plt.subplots(len(sel), 3, figsize=(1.7 * 3, 2.3 * len(sel)), squeeze=False)
    for r, (name, ims) in enumerate(sel):
        for c, k in enumerate(keys):
            ax = axes[r, c]
            ax.imshow(to_rgb(ims[k]), vmin=0, vmax=255)
            ax.set_xticks([]); ax.set_yticks([])
            for sp in ax.spines.values():
                sp.set_visible(False)
            if r == 0:
                ax.set_title(LABELS[k], fontsize=7.5)
            if c == 0:
                ax.set_ylabel(name, fontsize=8)
    plt.tight_layout(pad=0.3)
    fig.savefig(path, dpi=200)
    plt.close(fig)


def main():
    for d in (DEGR, PROC, FIGS):
        os.makedirs(d, exist_ok=True)
    files = sorted(f for f in os.listdir(ORIG) if f.lower().endswith((".png", ".jpg", ".jpeg")))
    rows, records = [], []
    for f in files:
        name = os.path.splitext(f)[0]
        ref = cv2.imread(os.path.join(ORIG, f), cv2.IMREAD_COLOR)
        deg = degrade(ref)
        cv2.imwrite(os.path.join(DEGR, name + ".png"), deg)
        ims = {"original": ref}
        os.makedirs(os.path.join(PROC, name), exist_ok=True)
        for key, fn in METHODS.items():
            out = fn(deg)
            ims[key] = out
            cv2.imwrite(os.path.join(PROC, name, key + ".png"), out)
            records.append({
                "image": name, "method": key,
                "PSNR_dB": round(M.psnr(ref, out), 3),
                "SSIM": round(M.ssim(ref, out), 4),
                "MAE": round(M.mae(ref, out), 3),
                "DeltaE76": round(M.delta_e(ref, out), 3),
                "L_std": round(M.luminance_std(out), 3),
            })
            print(f"{name:10s} {key:12s}", records[-1])
        rows.append((name, ims))
        hist_figure(name, ims, os.path.join(FIGS, f"hist_{name}.png"))
        # per-image side-by-side figure (original, degraded, result for each method)
        grid_figure([(name, ims)], os.path.join(FIGS, f"compare_{name}.png"))

    grid_figure(rows, os.path.join(FIGS, "comparison_all.png"))
    grid_figure(rows, os.path.join(FIGS, "crops_all.png"), crop=True)
    color_shift_figure(rows, os.path.join(FIGS, "color_shift.png"))

    with open(CSV_PATH, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(records[0].keys()))
        w.writeheader(); w.writerows(records)
    print(f"\nDegradation: alpha={CONTRAST_ALPHA}, sigma={NOISE_SIGMA}, seed={SEED}")
    print("Wrote", CSV_PATH)


if __name__ == "__main__":
    main()
