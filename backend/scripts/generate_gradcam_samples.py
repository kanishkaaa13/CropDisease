"""
Grad-CAM Sample Overlay Generator
--------------------------------
Selects 5 sample leaf images from different classes in the Kaggle dataset,
generates Grad-CAM activation heatmap overlays, and saves them to
backend/reports/gradcam_samples/.
"""
import sys
import logging
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.ml.disease_classifier import get_disease_classifier
from app.services.dataset_manager import get_dataset_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

OUTPUT_DIR = Path(__file__).parent.parent / "reports" / "gradcam_samples"


def generate_samples():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    dataset_manager = get_dataset_manager()
    class_dirs = dataset_manager.get_class_directories()
    
    classifier = get_disease_classifier()

    # Pick 5 distinct classes
    sample_classes = class_dirs[:5]
    logger.info("Generating Grad-CAM sample overlays for classes: %s", sample_classes)

    saved_samples = []

    for i, cls_name in enumerate(sample_classes, 1):
        images = dataset_manager.get_training_images(cls_name, limit=10)
        valid_img_path = None
        for img_path in images:
            try:
                with Image.open(img_path) as test_img:
                    test_img.convert("RGB")
                    valid_img_path = img_path
                    break
            except Exception:
                continue

        if not valid_img_path:
            logger.warning("No valid image found for class %s", cls_name)
            continue

        logger.info("Processing sample %d: %s (%s)", i, valid_img_path.name, cls_name)
        with Image.open(valid_img_path) as pil_img:
            pil_img = pil_img.convert("RGB")
            
            # Run scan pipeline
            res = classifier.scan_crop_image(pil_img)
            gradcam_base64 = res.get("gradcam_image_base64")

            if gradcam_base64:
                import base64
                base64_data = gradcam_base64.split(",", 1)[-1]
                img_bytes = base64.b64decode(base64_data)
                
                safe_cls = cls_name.replace(" ", "_").lower()
                out_path = OUTPUT_DIR / f"sample_{i}_{safe_cls}.png"
                with open(out_path, "wb") as f:
                    f.write(img_bytes)

                logger.info("Saved Grad-CAM sample to %s", out_path)
                saved_samples.append(str(out_path))

    print("\n" + "=" * 60)
    print(" GRAD-CAM SAMPLES GENERATED SUCCESSFULLY")
    print("=" * 60)
    for s in saved_samples:
        print(f" - {s}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    generate_samples()
