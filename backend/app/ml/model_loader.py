"""
Model Loader
------------
Handles loading PyTorch / scikit-learn model weights from disk.
Models are loaded once at startup and cached as module-level singletons.

Usage:
    from app.ml.model_loader import get_disease_model
    model = get_disease_model()
    output = model(tensor_input)
"""
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Path where weights should be mounted / downloaded
WEIGHTS_DIR = Path(__file__).parent / "weights"

_disease_model = None  # module-level singleton


def get_disease_model():
    """
    Return the cached disease detection model.
    Falls back gracefully if weights are not yet available (scaffold mode).
    """
    global _disease_model
    if _disease_model is not None:
        return _disease_model

    weights_path = WEIGHTS_DIR / "disease_classifier.pth"
    if not weights_path.exists():
        logger.warning(
            "Model weights not found at %s — running in mock/scaffold mode.", weights_path
        )
        return None

    try:
        import torch
        import torchvision.models as models

        model = models.resnet50(pretrained=False)
        model.load_state_dict(torch.load(weights_path, map_location="cpu"))
        model.eval()
        _disease_model = model
        logger.info("Disease model loaded from %s", weights_path)
        return _disease_model
    except Exception as exc:
        logger.error("Failed to load model: %s", exc)
        return None
