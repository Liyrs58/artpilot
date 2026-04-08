"""Colorization via OpenCV histogram-based style transfer.

A lightweight local approach — applies the color palette of a reference
image onto a grayscale/line-art input using L*a*b* histogram matching.
For production quality, swap in MangaNinja or style2paints.
"""

from pathlib import Path
import cv2
import numpy as np
from PIL import Image


def _match_histograms(source: np.ndarray, reference: np.ndarray) -> np.ndarray:
    """Match the histogram of source to reference per channel."""
    result = np.zeros_like(source)
    for i in range(3):
        src_vals, src_counts = np.unique(source[:, :, i], return_counts=True)
        ref_vals, ref_counts = np.unique(reference[:, :, i], return_counts=True)

        src_cdf = np.cumsum(src_counts).astype(float) / source[:, :, i].size
        ref_cdf = np.cumsum(ref_counts).astype(float) / reference[:, :, i].size

        mapping = np.interp(src_cdf, ref_cdf, ref_vals)
        lut = np.zeros(256, dtype=np.uint8)
        for idx, val in enumerate(src_vals):
            lut[val] = np.clip(mapping[idx], 0, 255).astype(np.uint8)

        result[:, :, i] = lut[source[:, :, i]]
    return result


def colorize(input_path: str, reference_path: str, output_dir: str) -> str:
    """Apply color palette from reference image onto input."""
    inp = Path(input_path)
    out = Path(output_dir) / f"{inp.stem}_colorized.png"

    source = cv2.imread(str(inp))
    reference = cv2.imread(str(reference_path))

    # Convert to LAB, match, convert back
    src_lab = cv2.cvtColor(source, cv2.COLOR_BGR2LAB)
    ref_lab = cv2.cvtColor(reference, cv2.COLOR_BGR2LAB)
    matched = _match_histograms(src_lab, ref_lab)
    result = cv2.cvtColor(matched, cv2.COLOR_LAB2BGR)

    cv2.imwrite(str(out), result)
    return str(out)
