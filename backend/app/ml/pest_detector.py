"""
Pest Detection Module.
Detects pests from sticky trap images using blob detection (MOCK MODE).
This is a placeholder for a trained YOLOv8 model.
"""
import logging
import base64
import io
from typing import Dict, Any
import numpy as np

try:
    import cv2
    _HAS_CV2 = True
except ImportError:
    _HAS_CV2 = False
    cv2 = None

from PIL import Image

logger = logging.getLogger(__name__)

# MOCK MODE FLAG
# Set to True to use blob detection as placeholder
# Set to False to use trained YOLOv8 model (when available)
USE_MOCK_MODE = True


def detect_pests(image: Image.Image) -> Dict[str, Any]:
    """
    Detect pests from sticky trap image.
    
    MOCK MODE: Uses OpenCV blob detection to count dark spots as stand-in for insects.
    REAL MODE: Would use trained YOLOv8 model for actual pest classification.
    
    Args:
        image: PIL Image of sticky trap
    
    Returns:
        dict containing:
        - pest_counts: dict with counts by pest type
        - total_count: total number of detected pests
        - annotated_image_base64: base64-encoded image with bounding circles/boxes
    """
    if USE_MOCK_MODE:
        logger.warning("=" * 60)
        logger.warning("PEST DETECTOR MODE: MOCK (Blob Detection)")
        logger.warning("NOTE: Replace with trained YOLOv8 model for production")
        logger.warning("=" * 60)
        return _detect_pests_mock(image)
    else:
        logger.info("PEST DETECTOR MODE: REAL (YOLOv8)")
        return _detect_pests_real(image)


def _detect_pests_mock(image: Image.Image) -> Dict[str, Any]:
    """
    MOCK MODE: Use blob detection to count dark spots as pests.
    This is a placeholder for actual pest detection.
    """
    if not _HAS_CV2:
        logger.error("OpenCV not installed, cannot run mock detection")
        return {
            "pest_counts": {"whitefly": 0, "unknown": 0},
            "total_count": 0,
            "annotated_image_base64": "",
        }
    
    # Convert PIL to OpenCV format
    img_array = np.array(image.convert("RGB"))
    img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
    img_gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    
    # Set up blob detector parameters
    params = cv2.SimpleBlobDetector_Params()
    
    # Filter by area (adjust based on expected pest size)
    params.filterByArea = True
    params.minArea = 10  # Minimum blob area
    params.maxArea = 500  # Maximum blob area
    
    # Filter by circularity (pests are roughly circular)
    params.filterByCircularity = True
    params.minCircularity = 0.3
    
    # Filter by convexity
    params.filterByConvexity = True
    params.minConvexity = 0.5
    
    # Filter by inertia
    params.filterByInertia = True
    params.minInertiaRatio = 0.3
    
    # Create detector
    detector = cv2.SimpleBlobDetector_create(params)
    
    # Detect blobs
    keypoints = detector.detect(img_gray)
    
    # Draw detected blobs as circles
    annotated_img = img_bgr.copy()
    for keypoint in keypoints:
        x, y = int(keypoint.pt[0]), int(keypoint.pt[1])
        radius = int(keypoint.size / 2)
        cv2.circle(annotated_img, (x, y), radius, (0, 255, 0), 2)
        cv2.circle(annotated_img, (x, y), 2, (0, 0, 255), -1)  # Center dot
    
    # Convert back to PIL and encode as base64
    annotated_pil = Image.fromarray(cv2.cvtColor(annotated_img, cv2.COLOR_BGR2RGB))
    buffered = io.BytesIO()
    annotated_pil.save(buffered, format="JPEG")
    annotated_base64 = base64.b64encode(buffered.getvalue()).decode()
    
    # In mock mode, we can't distinguish pest types, so classify all as "unknown"
    # In real mode with YOLO, we would have actual class labels
    total_count = len(keypoints)
    
    # Mock: assume some are whiteflies based on size heuristic
    whitefly_count = sum(1 for kp in keypoints if kp.size < 20)
    unknown_count = total_count - whitefly_count
    
    return {
        "pest_counts": {
            "whitefly": whitefly_count,
            "unknown": unknown_count,
        },
        "total_count": total_count,
        "annotated_image_base64": annotated_base64,
    }


def _detect_pests_real(image: Image.Image) -> Dict[str, Any]:
    """
    REAL MODE: Use trained YOLOv8 model for pest detection.
    
    NOTE: This is a placeholder. To implement:
    1. Install ultralytics: pip install ultralytics
    2. Load trained model: from ultralytics import YOLO; model = YOLO('pest_model.pt')
    3. Run inference: results = model(image)
    4. Parse results and extract bounding boxes, class labels, confidence scores
    5. Draw bounding boxes on image
    6. Return pest counts by type
    """
    logger.error("REAL MODE not implemented yet. Set USE_MOCK_MODE=True or train YOLOv8 model.")
    return {
        "pest_counts": {"whitefly": 0, "unknown": 0},
        "total_count": 0,
        "annotated_image_base64": "",
    }
