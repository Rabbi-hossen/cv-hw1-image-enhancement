"""Synthetic degradation: contrast reduction + additive Gaussian noise.

The ORIGINAL image is used only as the reference for the metrics. In real-world
cases a clean reference is usually not available.
"""
import numpy as np

# ---- Degradation parameters (fixed for all images; documented in README) ----
CONTRAST_ALPHA = 0.4   # I' = mean + alpha * (I - mean), alpha < 1 lowers contrast
NOISE_SIGMA = 4.0      # std-dev of Gaussian noise, in 8-bit gray levels
SEED = 42              # fixed seed -> identical noise on every run


def degrade(img_bgr: np.ndarray) -> np.ndarray:
    """Return a uint8 BGR image with reduced contrast and Gaussian noise."""
    x = img_bgr.astype(np.float64)
    mean = x.mean()                                   # global mean of all pixels
    x = mean + CONTRAST_ALPHA * (x - mean)            # linear contrast reduction
    rng = np.random.default_rng(SEED)                 # same seed for every image
    x = x + rng.normal(0.0, NOISE_SIGMA, size=x.shape)
    return np.clip(np.rint(x), 0, 255).astype(np.uint8)
