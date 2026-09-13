"""
Severity Estimator Module using HSV Color-Thresholding.
Estimates the percentage of affected (chlorotic, brown, necrotic, rust) leaf area
versus healthy green leaf area.
"""
from typing import Tuple
import cv2
import numpy as np
from PIL import Image


def estimate_disease_severity(image: Image.Image) -> Tuple[float, dict]:
    """
    Estimate disease severity percentage of a crop leaf image using HSV color segmentation.

    Returns:
        - severity_pct (float): Estimated percentage of diseased/affected leaf area (0.0 to 100.0).
        - details (dict): Pixel count breakdown for healthy vs affected regions.
    """
    # Convert PIL Image to RGB NumPy array
    img_rgb = np.array(image.convert("RGB"))
    img_bgr = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)

    # Convert to HSV color space
    hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)

    # Define HSV color thresholds for Healthy Green
    # Green range: H [35, 85], S [30, 255], V [30, 255]
    lower_green = np.array([35, 30, 30], dtype=np.uint8)
    upper_green = np.array([85, 255, 255], dtype=np.uint8)
    green_mask = cv2.inRange(hsv, lower_green, upper_green)

    # Define HSV color thresholds for Affected Regions (Yellow, Brown, Necrotic, Rust)
    # 1. Chlorotic / Yellowing spots: H [15, 35], S [30, 255], V [40, 255]
    lower_yellow = np.array([15, 30, 40], dtype=np.uint8)
    upper_yellow = np.array([35, 255, 255], dtype=np.uint8)
    yellow_mask = cv2.inRange(hsv, lower_yellow, upper_yellow)

    # 2. Brown / Necrotic spots: H [0, 20], S [25, 255], V [20, 200]
    lower_brown = np.array([0, 25, 20], dtype=np.uint8)
    upper_brown = np.array([20, 255, 200], dtype=np.uint8)
    brown_mask = cv2.inRange(hsv, lower_brown, upper_brown)

    # 3. Fungal Rust / Reddish Brown spots: H [165, 180], S [30, 255], V [20, 200]
    lower_rust = np.array([165, 30, 20], dtype=np.uint8)
    upper_rust = np.array([180, 255, 200], dtype=np.uint8)
    rust_mask = cv2.inRange(hsv, lower_rust, upper_rust)

    # Combine all affected disease masks
    affected_mask = cv2.bitwise_or(yellow_mask, brown_mask)
    affected_mask = cv2.bitwise_or(affected_mask, rust_mask)

    # Combine total leaf area mask (Healthy Green + Affected Diseased)
    total_leaf_mask = cv2.bitwise_or(green_mask, affected_mask)

    # Count non-zero pixels
    total_leaf_pixels = int(cv2.countNonZero(total_leaf_mask))
    affected_pixels = int(cv2.countNonZero(affected_mask))
    healthy_pixels = int(cv2.countNonZero(green_mask))

    # Calculate severity percentage
    if total_leaf_pixels < 100:
        # Fallback if background segmentation isolated very few leaf pixels
        severity_pct = 0.0
    else:
        severity_pct = (affected_pixels / total_leaf_pixels) * 100.0

    severity_pct = round(min(max(severity_pct, 0.0), 100.0), 1)

    details = {
        "severity_pct": severity_pct,
        "total_leaf_pixels": total_leaf_pixels,
        "affected_pixels": affected_pixels,
        "healthy_pixels": healthy_pixels,
    }

    return severity_pct, details
