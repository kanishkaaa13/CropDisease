"""
Evaluation Script for Crop Disease Classifier
---------------------------------------------
Evaluates trained DiseaseClassifier on a held-out test split of the Kaggle dataset
'nirmalsankalana/crop-pest-and-disease-detection'.

Calculates:
- Overall accuracy
- Top-3 accuracy
- Per-class precision, recall, and F1-score
- Confusion matrix (saved as PNG)
- 10 most confused class pairs
- Classes with recall < 70%

Saves report to backend/reports/evaluation_report.json and backend/reports/confusion_matrix.png.
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Tuple, Any

# Ensure backend root is in sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
from PIL import Image
from sklearn.metrics import classification_report, confusion_matrix
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

from app.ml.disease_classifier import DiseaseClassifier, get_disease_classifier
from app.services.dataset_manager import get_dataset_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Reports output directory
REPORTS_DIR = Path(__file__).parent.parent / "reports"


def get_held_out_test_split(dataset_path: Path, test_size: float = 0.1, seed: int = 42) -> Tuple[List[str], List[int], List[str]]:
    """
    Build a deterministic stratified held-out test split from the dataset directory.
    Returns (test_file_paths, test_labels, class_names).
    """
    from sklearn.model_selection import train_test_split

    class_dirs = sorted([d.name for d in dataset_path.iterdir() if d.is_dir() and not d.name.startswith(".")])
    
    all_paths = []
    all_labels = []
    image_extensions = {".jpg", ".jpeg", ".png", ".webp"}

    for idx, class_name in enumerate(class_dirs):
        class_path = dataset_path / class_name
        for p in class_path.iterdir():
            if p.is_file() and p.suffix.lower() in image_extensions:
                all_paths.append(str(p))
                all_labels.append(idx)

    logger.info("Found %d images across %d classes in dataset.", len(all_paths), len(class_dirs))

    # Perform stratified split to get held-out test set
    _, test_paths, _, test_labels = train_test_split(
        all_paths, all_labels, test_size=test_size, random_state=seed, stratify=all_labels
    )

    logger.info("Held-out test set size: %d images.", len(test_paths))
    return test_paths, test_labels, class_dirs


def evaluate():
    """Run model evaluation on test set."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Load dataset & held-out test split
    dataset_manager = get_dataset_manager()
    dataset_path = dataset_manager.get_dataset_path()
    
    test_paths, test_labels, class_names = get_held_out_test_split(dataset_path, test_size=0.1, seed=42)

    # 2. Load model
    logger.info("Loading DiseaseClassifier model...")
    classifier = get_disease_classifier()

    # Ensure model classes align
    if classifier.classes != class_names:
        logger.info("Updating classifier classes to match dataset class list.")
        classifier.classes = class_names

    # 3. Predict on held-out test set
    logger.info("Evaluating predictions on %d test samples...", len(test_paths))
    all_preds = []
    all_top3_preds = []

    for i, file_path in enumerate(test_paths):
        if (i + 1) % 100 == 0 or (i + 1) == len(test_paths):
            logger.info("Processed %d/%d samples...", i + 1, len(test_paths))

        try:
            with Image.open(file_path) as img:
                res = classifier.predict(img, top_k=3)
                pred_label = res["predicted_label"]
                
                # Convert pred_label string to class index
                if pred_label in class_names:
                    pred_idx = class_names.index(pred_label)
                else:
                    pred_idx = 0

                top3_indices = []
                for p in res["top3"]:
                    lbl = p["label"]
                    if lbl in class_names:
                        top3_indices.append(class_names.index(lbl))

                all_preds.append(pred_idx)
                all_top3_preds.append(top3_indices)

        except Exception as exc:
            logger.warning("Error processing test sample %s: %s", file_path, exc)
            all_preds.append(0)
            all_top3_preds.append([0])

    # 4. Metrics Calculation
    test_labels_arr = np.array(test_labels)
    all_preds_arr = np.array(all_preds)

    overall_acc = float(np.mean(test_labels_arr == all_preds_arr))
    
    # Top-3 Accuracy
    top3_hits = sum(1 for true_lbl, top3_list in zip(test_labels, all_top3_preds) if true_lbl in top3_list)
    top3_acc = float(top3_hits / len(test_labels)) if test_labels else 0.0

    # Per-class report
    clf_report_dict = classification_report(
        test_labels, all_preds, target_names=class_names, output_dict=True, zero_division=0
    )
    clf_report_str = classification_report(
        test_labels, all_preds, target_names=class_names, zero_division=0
    )

    # 5. Confusion Matrix Analysis
    cm = confusion_matrix(test_labels, all_preds, labels=range(len(class_names)))
    
    # Identify 10 most confused class pairs (true != pred)
    confused_pairs = []
    for r in range(len(class_names)):
        for c in range(len(class_names)):
            if r != c and cm[r, c] > 0:
                confused_pairs.append({
                    "true_class": class_names[r],
                    "predicted_class": class_names[c],
                    "count": int(cm[r, c])
                })

    confused_pairs.sort(key=lambda x: x["count"], reverse=True)
    top10_confused = confused_pairs[:10]

    # Classes with recall below 70%
    low_recall_classes = []
    for class_name in class_names:
        if class_name in clf_report_dict:
            rec = clf_report_dict[class_name]["recall"]
            if rec < 0.70:
                low_recall_classes.append({
                    "class": class_name,
                    "recall": round(float(rec), 4),
                    "precision": round(float(clf_report_dict[class_name]["precision"]), 4),
                    "f1_score": round(float(clf_report_dict[class_name]["f1-score"]), 4),
                    "support": int(clf_report_dict[class_name]["support"])
                })

    # Print summary report
    print("\n" + "=" * 70)
    print(" CROP DISEASE CLASSIFIER EVALUATION REPORT")
    print("=" * 70)
    print(f"Total Test Samples : {len(test_paths)}")
    print(f"Overall Accuracy   : {overall_acc * 100:.2f}%")
    print(f"Top-3 Accuracy     : {top3_acc * 100:.2f}%")
    print("\n--- Per-Class Metrics ---")
    print(clf_report_str)

    print("\n--- 10 Most Confused Class Pairs ---")
    if top10_confused:
        for idx, pair in enumerate(top10_confused, 1):
            print(f" {idx:2d}. True: '{pair['true_class']}' --> Predicted: '{pair['predicted_class']}' ({pair['count']} misclassifications)")
    else:
        print(" None (perfect confusion matrix)")

    print("\n--- Classes with Recall Below 70% ---")
    if low_recall_classes:
        for item in low_recall_classes:
            print(f" - {item['class']}: Recall = {item['recall'] * 100:.1f}%, Precision = {item['precision'] * 100:.1f}%, F1 = {item['f1_score'] * 100:.1f}% (Support: {item['support']})")
    else:
        print(" None (all classes have recall >= 70%)")

    print("=" * 70 + "\n")

    # 6. Save Confusion Matrix Plot
    plt.figure(figsize=(14, 12))
    sns.heatmap(
        cm,
        annot=True,
        fmt="d",
        cmap="Blues",
        xticklabels=class_names,
        yticklabels=class_names,
        cbar=True
    )
    plt.title("Crop Disease Classification Confusion Matrix", fontsize=14, fontweight="bold", pad=15)
    plt.xlabel("Predicted Class", fontsize=12)
    plt.ylabel("True Class", fontsize=12)
    plt.xticks(rotation=90, fontsize=8)
    plt.yticks(rotation=0, fontsize=8)
    plt.tight_layout()

    cm_png_path = REPORTS_DIR / "confusion_matrix.png"
    plt.savefig(cm_png_path, dpi=300)
    plt.close()
    logger.info("Saved confusion matrix plot to %s", cm_png_path)

    # 7. Save JSON Report
    json_report = {
        "dataset": "nirmalsankalana/crop-pest-and-disease-detection",
        "total_test_samples": len(test_paths),
        "overall_accuracy": round(overall_acc, 4),
        "top3_accuracy": round(top3_acc, 4),
        "top10_most_confused_pairs": top10_confused,
        "low_recall_classes_under_70": low_recall_classes,
        "per_class_report": clf_report_dict
    }

    report_json_path = REPORTS_DIR / "evaluation_report.json"
    with open(report_json_path, "w") as f:
        json.dump(json_report, f, indent=2)
    logger.info("Saved JSON evaluation report to %s", report_json_path)

    return json_report


if __name__ == "__main__":
    evaluate()
