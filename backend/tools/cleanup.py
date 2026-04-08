"""Line cleanup using OpenCV — thresholds and smooths sketchy line art."""

from pathlib import Path
import cv2
import numpy as np


def cleanup_lines(input_path: str, output_dir: str, thickness: int = 1) -> str:
    """Clean up line art: denoise, threshold, and thin lines."""
    inp = Path(input_path)
    out = Path(output_dir) / f"{inp.stem}_clean.png"

    img = cv2.imread(str(inp), cv2.IMREAD_GRAYSCALE)

    # Denoise
    img = cv2.fastNlMeansDenoising(img, h=10)

    # Adaptive threshold for clean black lines on white
    binary = cv2.adaptiveThreshold(
        img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
    )

    # Optional morphological thinning
    if thickness <= 1:
        kernel = np.ones((2, 2), np.uint8)
        binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)

    cv2.imwrite(str(out), binary)
    return str(out)
