"""
Image Quality Assessment Module.
Performs quality checks on uploaded crop images before disease classification.
"""
import logging
from typing import Dict, List
import numpy as np

try:
    import cv2
    _HAS_CV2 = True
except ImportError:
    _HAS_CV2 = False
    cv2 = None

from PIL import Image

logger = logging.getLogger(__name__)

# Quality thresholds (configurable)
BLUR_THRESHOLD = 100.0  # Laplacian variance threshold
BRIGHTNESS_MIN = 40.0   # Minimum mean brightness (0-255)
BRIGHTNESS_MAX = 220.0  # Maximum mean brightness (0-255)
MIN_RESOLUTION = (224, 224)  # Minimum width x height
PLANT_PIXEL_RATIO = 0.15  # Minimum ratio of plant-colored pixels (green/brown)


def check_image_quality(image: Image.Image) -> Dict[str, any]:
    """
    Perform quality checks on an uploaded crop image.
    
    Args:
        image: PIL Image object
    
    Returns:
        dict containing:
        - passed (bool): True if all checks pass
        - blur_score (float): Laplacian variance score
        - brightness_score (float): Mean pixel brightness
        - issues (list[str]): List of quality issues found
    """
    issues = []
    blur_score = 0.0
    brightness_score = 0.0
    
    # Convert to RGB if necessary
    if image.mode != "RGB":
        image = image.convert("RGB")
    
    # 1. Resolution check
    width, height = image.size
    if width < MIN_RESOLUTION[0] or height < MIN_RESOLUTION[1]:
        issues.append(f"too_low_res: Image resolution {width}x{height} below minimum {MIN_RESOLUTION[0]}x{MIN_RESOLUTION[1]}")
    
    # Convert to numpy array for OpenCV operations
    img_array = np.array(image)
    
    # 2. Blur detection
    if _HAS_CV2:
        try:
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()
            if blur_score < BLUR_THRESHOLD:
                issues.append(f"too_blurry: Image too blurry (score: {blur_score:.2f}, threshold: {BLUR_THRESHOLD})")
        except Exception as exc:
            logger.warning(f"Blur detection failed: {exc}")
    else:
        logger.warning("OpenCV not installed, skipping blur detection")
    
    # 3. Brightness check
    try:
        brightness_score = np.mean(img_array)
        if brightness_score < BRIGHTNESS_MIN:
            issues.append(f"too_dark: Image too dark (brightness: {brightness_score:.1f}, minimum: {BRIGHTNESS_MIN})")
        elif brightness_score > BRIGHTNESS_MAX:
            issues.append(f"too_bright: Image too bright (brightness: {brightness_score:.1f}, maximum: {BRIGHTNESS_MAX})")
    except Exception as exc:
        logger.warning(f"Brightness check failed: {exc}")
    
    # 4. Leaf presence heuristic (HSV color range)
    # Note: This is a heuristic based on color, not a real object detector
    if _HAS_CV2:
        try:
            hsv = cv2.cvtColor(img_array, cv2.COLOR_RGB2HSV)
            
            # Define green and brown ranges in HSV
            # Green: H 35-85, S 40-255, V 40-255
            green_lower = np.array([35, 40, 40])
            green_upper = np.array([85, 255, 255])
            
            # Brown: H 10-25, S 50-255, V 50-255
            brown_lower = np.array([10, 50, 50])
            brown_upper = np.array([25, 255, 255])
            
            # Create masks for green and brown pixels
            green_mask = cv2.inRange(hsv, green_lower, green_upper)
            brown_mask = cv2.inRange(hsv, brown_lower, brown_upper)
            
            # Count plant-colored pixels
            plant_pixels = np.count_nonzero(green_mask) + np.count_nonzero(brown_mask)
            total_pixels = hsv.shape[0] * hsv.shape[1]
            plant_ratio = plant_pixels / total_pixels
            
            if plant_ratio < PLANT_PIXEL_RATIO:
                issues.append(f"no_plant_detected: Not enough plant-colored pixels detected (ratio: {plant_ratio:.2%}, minimum: {PLANT_PIXEL_RATIO:.0%})")
        except Exception as exc:
            logger.warning(f"Leaf presence check failed: {exc}")
    else:
        logger.warning("OpenCV not installed, skipping leaf presence check")
    
    passed = len(issues) == 0
    
    return {
        "passed": passed,
        "blur_score": blur_score,
        "brightness_score": brightness_score,
        "issues": issues,
    }


def get_farmer_friendly_message(issues: List[str]) -> str:
    """
    Convert technical issues into farmer-friendly messages.
    
    Args:
        issues: List of technical issue strings
    
    Returns:
        Farmer-friendly message
    """
    messages = []
    
    for issue in issues:
        if "too_blurry" in issue:
            messages.append("Image too blurry — please retake in good lighting")
        elif "too_dark" in issue:
            messages.append("Image too dark — please take in better lighting")
        elif "too_bright" in issue:
            messages.append("Image too bright — please reduce lighting or avoid direct sunlight")
        elif "too_low_res" in issue:
            messages.append("Image resolution too low — please use a higher resolution camera")
        elif "no_plant_detected" in issue:
            messages.append("No plant detected — please ensure the crop leaf is clearly visible in the image")
        else:
            messages.append(f"Image quality issue: {issue.split(':')[0]}")
    
    return ". ".join(messages)
