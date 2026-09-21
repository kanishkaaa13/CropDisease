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

    weights_path = WEIGHTS_DIR / "disease_classifier_efficientnet_b0.pth"
    if not weights_path.exists():
        weights_path = WEIGHTS_DIR / "disease_classifier.pth"
    if not weights_path.exists():
        raise FileNotFoundError(
            f"Model weights not found at {weights_path}. Model execution disabled."
        )

    try:
        import torch
        import torchvision.models as models

        checkpoint = torch.load(weights_path, map_location="cpu")
        
        # Enforce trained validation gate
        if not isinstance(checkpoint, dict) or not checkpoint.get("trained", False):
            raise RuntimeError(
                f"Model checkpoint at {weights_path} is an untrained placeholder or missing 'trained: True' flag. "
                "Please train the model using ml-training/train_kaggle.ipynb and place the trained weights file."
            )

        num_classes = len(checkpoint.get("classes", []))
        model = models.efficientnet_b0(weights=None)
        if num_classes:
            model.classifier[1] = torch.nn.Linear(model.classifier[1].in_features, num_classes)
        
        model.load_state_dict(checkpoint["model_state_dict"])
            
        model.eval()
        _disease_model = model
        logger.info("Trained disease model loaded from %s (classes=%d)", weights_path, num_classes)
        return _disease_model
    except Exception as exc:
        logger.error("Failed to load model from %s: %s", weights_path, exc)
        raise RuntimeError(f"Failed to load model weights: {exc}")
