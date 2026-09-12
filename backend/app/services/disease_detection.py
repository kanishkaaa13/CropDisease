"""
Disease Detection Service
-------------------------
Wraps the ML inference pipeline. In this scaffold, returns mock results.
Replace the _run_model() call with the real torchvision/OpenCV pipeline
once the model weights are available.
"""
import io
import random
from PIL import Image

# Mock disease catalogue per crop
DISEASE_CATALOGUE = {
    "wheat": ["Wheat Rust", "Powdery Mildew", "Septoria Leaf Blotch", "Healthy"],
    "rice": ["Rice Blast", "Brown Spot", "Sheath Blight", "Healthy"],
    "tomato": ["Early Blight", "Late Blight", "Leaf Mold", "Healthy"],
    "default": ["Leaf Spot", "Root Rot", "Healthy"],
}

SEVERITY_MAP = {
    "Healthy": "none",
    "Leaf Spot": "low",
    "Root Rot": "medium",
    "Wheat Rust": "high",
    "Rice Blast": "high",
    "Early Blight": "medium",
    "Late Blight": "high",
}


def detect_disease(image_bytes: bytes, crop_type: str) -> dict:
    """
    Run disease detection on a raw image.

    Args:
        image_bytes: Raw bytes of the uploaded image file.
        crop_type: Crop category string (e.g. 'wheat').

    Returns:
        dict with keys: disease_name, confidence, severity
    """
    # Validate image can be opened
    try:
        img = Image.open(io.BytesIO(image_bytes))
        img.verify()
    except Exception as exc:
        raise ValueError(f"Invalid image file: {exc}") from exc

    catalogue = DISEASE_CATALOGUE.get(crop_type.lower(), DISEASE_CATALOGUE["default"])
    disease_name = random.choice(catalogue)
    confidence = round(random.uniform(0.72, 0.98), 4)
    severity = SEVERITY_MAP.get(disease_name, "low")

    return {
        "disease_name": disease_name,
        "confidence": confidence,
        "severity": severity,
    }
