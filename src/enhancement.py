"""Enhancement methods. All functions take / return uint8 BGR images (OpenCV).

Luminance-based methods operate on the L channel of CIE-Lab (OpenCV 8-bit Lab:
L in [0,255]) and leave a, b untouched, which limits hue shifts.
"""
import cv2
import numpy as np

# ---- Fixed method parameters ----
STRETCH_LOW_PCT = 1.0     # percentiles clipped by the linear stretch
STRETCH_HIGH_PCT = 99.0
NLM_H = 8                 # non-local-means filter strength (luminance)
NLM_H_COLOR = 8           # non-local-means filter strength (color)
NLM_TEMPLATE = 7          # template patch size
NLM_SEARCH = 21           # search window size


def _stretch(channel: np.ndarray) -> np.ndarray:
    """Linear stretch of one channel: [p_low, p_high] -> [0, 255], clipped."""
    lo, hi = np.percentile(channel, [STRETCH_LOW_PCT, STRETCH_HIGH_PCT])
    if hi - lo < 1e-6:
        return channel.copy()
    out = (channel.astype(np.float64) - lo) * (255.0 / (hi - lo))
    return np.clip(np.rint(out), 0, 255).astype(np.uint8)


def baseline(img):
    """Method 1: degraded image, no processing."""
    return img.copy()


def stretch_luminance(img):
    """Method 2: linear contrast stretching on the Lab L channel only."""
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    lab[..., 0] = _stretch(lab[..., 0])
    return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)


def stretch_per_channel(img):
    """Method 2b (variant): independent linear stretch of each B, G, R channel."""
    return cv2.merge([_stretch(c) for c in cv2.split(img)])


def hist_equalization(img):
    """Method 3: global histogram equalization of the Lab L channel."""
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    lab[..., 0] = cv2.equalizeHist(lab[..., 0])
    return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)


def stretch_plus_nlm(img):
    """Method 4: luminance stretch followed by non-local-means denoising.

    Motivation: stretching multiplies the noise by the same gain as the signal
    (~1/alpha), so we remove it afterwards at the cost of some fine detail.
    """
    s = stretch_luminance(img)
    return cv2.fastNlMeansDenoisingColored(
        s, None, NLM_H, NLM_H_COLOR, NLM_TEMPLATE, NLM_SEARCH)


# name -> function (ordered; used for CSV columns / figures)
METHODS = {
    "degraded": baseline,
    "stretch_lum": stretch_luminance,
    "stretch_rgb": stretch_per_channel,
    "hist_eq": hist_equalization,
    "stretch_nlm": stretch_plus_nlm,
}

LABELS = {
    "original": "Original (reference)",
    "degraded": "Degraded (baseline)",
    "stretch_lum": "Stretch (Lab-L)",
    "stretch_rgb": "Stretch (per RGB ch.)",
    "hist_eq": "Hist. eq. (Lab-L)",
    "stretch_nlm": "Stretch + NLM",
}
