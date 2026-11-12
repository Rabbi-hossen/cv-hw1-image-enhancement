# Homework 1 – Image Enhancement (Computer Vision, Fall 2026)

Classical pipeline (no deep learning) that degrades five real photographs
(contrast reduction + Gaussian noise), enhances them with four methods and
compares the results with PSNR, SSIM, MAE and mean ΔE (CIE76).

## Requirements
* Python 3.10+ (developed and tested with Python 3.12)
* `pip install -r requirements.txt`  (NumPy, OpenCV, scikit-image, Matplotlib)

## Run the whole experiment
From the repository root:

    python src/run_experiment.py

This reads `data/original/`, writes `data/degraded/`, `results/processed/`,
`results/figures/` and `results/metrics.csv`. Runtime: well under one minute on a laptop CPU.
The run is deterministic (fixed seed): re-running gives a byte-identical `metrics.csv`.

## Degradation parameters (`src/degradation.py`)
| Parameter | Value |
|---|---|
| Contrast reduction | `I' = mean + 0.4 * (I - mean)` (mean = global mean of all pixels) |
| Gaussian noise | σ = 4 gray levels (0–255 scale), zero mean |
| Random seed | 42 (`np.random.default_rng(42)`) |
| Output | clipped, rounded, saved as 8-bit PNG |

## Methods (`src/enhancement.py`)
1. `degraded` – baseline, no processing.
2. `stretch_lum` – linear contrast stretch of the CIE-Lab **L** channel (1st–99th percentile → 0–255); a, b untouched.
   `stretch_rgb` – variant: independent stretch of each B, G, R channel (used to discuss colour shifts).
3. `hist_eq` – global histogram equalization (`cv2.equalizeHist`) on the CIE-Lab **L** channel.
4. `stretch_nlm` – combination: `stretch_lum` followed by non-local-means denoising
   (`cv2.fastNlMeansDenoisingColored`, h = hColor = 8, template 7, search window 21).

All parameters are fixed for every image (nothing is tuned per image).

## Metrics (`src/metrics.py`)
Computed against the **original** image (which exists only because the degradation is synthetic):
PSNR (mandatory), SSIM (scikit-image, multichannel, data_range=255), MAE, mean ΔE76 in CIE-Lab,
and the std-dev of L (`L_std`, a no-reference contrast indicator).

## File structure
    src/degradation.py       degradation model + parameters
    src/enhancement.py       enhancement methods + parameters
    src/metrics.py           PSNR, SSIM, MAE, ΔE76, L_std
    src/run_experiment.py    runs everything, writes images, CSV and figures
    src/prepare_images.py    downscales data/raw -> data/original (run once, already done)
    data/raw/                5 raw photographs (own work)
    data/original/           5 downscaled originals (references)
    data/degraded/           degraded versions (generated, kept in repo)
    results/processed/<img>/ processed images, one PNG per method
    results/metrics.csv      all metrics (image x method)
    results/figures/         side-by-side figures, crops, histograms, colour-shift figure
    report/                  report PDF and the script that builds it

## Image sources and licenses
All five images are the author's own photographs (indoor scenes, smartphone camera), included in
`data/raw/` (1659x2212 px). `src/prepare_images.py` downscaled them once to 600x800 px
(`data/original/`, INTER_AREA); these are the "original" references. Own work, included for this assignment.

| File | Content / why chosen |
|---|---|
| `bottle.jpg` | transparent bottle, specular highlights, fine label text |
| `cap.jpg` | dark cap and shadow on a bright floor |
| `lamp.jpg` | black lamp against a bright curtain, green frame |
| `mug.jpg` | white mug on white wall (intrinsically low contrast), hand |
| `phone.jpg` | small keypad digits, uneven lighting |
