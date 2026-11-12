"""Full-reference metrics (computed against the ORIGINAL image)."""
import cv2
import numpy as np
from skimage.metrics import peak_signal_noise_ratio, structural_similarity


def psnr(ref, img):
    return float(peak_signal_noise_ratio(ref, img, data_range=255))


def ssim(ref, img):
    # multichannel SSIM (mean over B, G, R), 7x7 uniform window (skimage default)
    return float(structural_similarity(ref, img, channel_axis=2, data_range=255))


def mae(ref, img):
    return float(np.mean(np.abs(ref.astype(np.float64) - img.astype(np.float64))))


def delta_e(ref, img):
    """Mean CIE76 colour difference (Euclidean distance in true CIE-Lab)."""
    def lab(x):
        return cv2.cvtColor(x.astype(np.float32) / 255.0, cv2.COLOR_BGR2Lab)
    return float(np.mean(np.linalg.norm(lab(ref) - lab(img), axis=2)))


def luminance_std(img):
    """RMS contrast: std-dev of the Lab L channel (0-100 scale). No reference."""
    L = cv2.cvtColor(img.astype(np.float32) / 255.0, cv2.COLOR_BGR2Lab)[..., 0]
    return float(L.std())
