"""
Training & Temperature Calibration Script for EfficientNet-B0 Crop Disease Classifier.
Features:
- Pretrained torchvision EfficientNet-B0 fine-tuning
- Class weight balancing for imbalanced datasets
- Early stopping on validation loss
- Temperature scaling confidence calibration (NLL optimization)
- Per-class classification report export (JSON + log)
"""
import os
import json
import argparse
from pathlib import Path
from typing import Dict, Tuple, List

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
import torchvision.models as models
from sklearn.metrics import classification_report

from dataset import prepare_dataset_splits, create_dataloaders, download_dataset


class ModelWithTemperature(nn.Module):
    """
    Temperature Scaling wrapper for confidence calibration.
    Learns a scalar T > 0 on validation set to calibrate logit probabilities: p = softmax(logits / T).
    """

    def __init__(self, model: nn.Module):
        super().__init__()
        self.model = model
        self.temperature = nn.Parameter(torch.ones(1) * 1.5)

    def forward(self, input_tensor: torch.Tensor) -> torch.Tensor:
        logits = self.model(input_tensor)
        return self.temperature_scale(logits)

    
    def temperature_scale(self, logits: torch.Tensor) -> torch.Tensor:

    # Scale logits by temperature T
        temperature = self.temperature.to(logits.device)
        temperature = temperature.unsqueeze(1).expand(logits.size(0), logits.size(1))

        return logits / temperature
    def calibrate(self, val_loader: torch.utils.data.DataLoader, device: torch.device) -> float:
        """
        Optimize scalar T on validation dataset using L-BFGS to minimize NLL Loss.
        """
        self.model.eval()
        nll_criterion = nn.CrossEntropyLoss().to(device)

        # Collect all validation logits and labels
        logits_list = []
        labels_list = []
        with torch.no_grad():
            for images, labels in val_loader:
                images = images.to(device)
                logits = self.model(images)
                logits_list.append(logits)
                labels_list.append(labels)

        logits = torch.cat(logits_list).to(device)
        labels = torch.cat(labels_list).to(device)

        # Before calibration metric
        before_calibration_nll = nll_criterion(logits, labels).item()

        # Optimize T with L-BFGS
        optimizer = optim.LBFGS([self.temperature], lr=0.01, max_iter=50)

        def eval_step():
            optimizer.zero_grad()
            loss = nll_criterion(self.temperature_scale(logits), labels)
            loss.backward()
            return loss

        optimizer.step(eval_step)

        # Clamp temperature to positive range
        with torch.no_grad():
            self.temperature.clamp_(min=0.1, max=5.0)

        after_calibration_nll = nll_criterion(self.temperature_scale(logits), labels).item()
        learned_temp = self.temperature.item()

        print(f"\n--- Temperature Calibration Complete ---")
        print(f"Optimal Temperature (T): {learned_temp:.4f}")
        print(f"Validation NLL Before: {before_calibration_nll:.4f} -> After: {after_calibration_nll:.4f}\n")

        return learned_temp


def build_efficientnet_b0(num_classes: int) -> nn.Module:
    """Build and initialize pretrained EfficientNet-B0 with custom classifier head."""
    weights = models.EfficientNet_B0_Weights.DEFAULT
    model = models.efficientnet_b0(weights=weights)
    # Replace classifier output layer
    in_features = model.classifier[1].in_features
    model.classifier[1] = nn.Linear(in_features, num_classes)
    return model


class EarlyStopping:
    """Early stopping handler based on validation loss."""

    def __init__(self, patience: int = 5, min_delta: float = 1e-4):
        self.patience = patience
        self.min_delta = min_delta
        self.counter = 0
        self.best_loss = float('inf')
        self.should_stop = False

    def check(self, val_loss: float) -> bool:
        if val_loss < self.best_loss - self.min_delta:
            self.best_loss = val_loss
            self.counter = 0
            return True  # Improvement
        else:
            self.counter += 1
            if self.counter >= self.patience:
                self.should_stop = True
            return False


def train_model(
    data_dir: str,
    epochs: int = 15,
    batch_size: int = 32,
    lr: float = 1e-3,
    output_dir: str = "output",
    patience: int = 5
) -> str:
    """Train EfficientNet-B0 model, perform calibration, evaluate, and save artifacts."""
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using compute device: {device}")

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # 1. Prepare data & data loaders
    (
        train_paths, train_labels,
        val_paths, val_labels,
        test_paths, test_labels,
        idx_to_class,
        class_weights
    ) = prepare_dataset_splits(data_dir)

    num_classes = len(idx_to_class)
    classes_list = [idx_to_class[i] for i in range(num_classes)]

    train_loader, val_loader, test_loader = create_dataloaders(
        train_paths, train_labels,
        val_paths, val_labels,
        test_paths, test_labels,
        batch_size=batch_size
    )

    # 2. Build model, loss, optimizer
    model = build_efficientnet_b0(num_classes).to(device)

    # Class weighted loss
    weights_tensor = torch.tensor(class_weights, dtype=torch.float32).to(device)
    criterion = nn.CrossEntropyLoss(weight=weights_tensor)

    optimizer = optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', factor=0.5, patience=2)

    early_stopping = EarlyStopping(patience=patience)
    best_model_weights_path = output_path / "temp_best.pth"

    # 3. Training Loop
    print("\nStarting Training...")
    for epoch in range(1, epochs + 1):
        model.train()
        running_loss = 0.0
        correct_train = 0
        total_train = 0

        for images, labels in train_loader:
            images, labels = images.to(device), labels.to(device)
            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            running_loss += loss.item() * images.size(0)
            preds = outputs.argmax(dim=1)
            correct_train += (preds == labels).sum().item()
            total_train += labels.size(0)

        epoch_train_loss = running_loss / total_train
        epoch_train_acc = correct_train / total_train

        # Validation loop
        model.eval()
        val_loss = 0.0
        correct_val = 0
        total_val = 0

        with torch.no_grad():
            for images, labels in val_loader:
                images, labels = images.to(device), labels.to(device)
                outputs = model(images)
                loss = criterion(outputs, labels)

                val_loss += loss.item() * images.size(0)
                preds = outputs.argmax(dim=1)
                correct_val += (preds == labels).sum().item()
                total_val += labels.size(0)

        epoch_val_loss = val_loss / total_val
        epoch_val_acc = correct_val / total_val

        scheduler.step(epoch_val_loss)

        print(f"Epoch [{epoch:02d}/{epochs:02d}] - "
              f"Train Loss: {epoch_train_loss:.4f}, Train Acc: {epoch_train_acc:.4f} | "
              f"Val Loss: {epoch_val_loss:.4f}, Val Acc: {epoch_val_acc:.4f}")

        # Save checkpoint if improvement
        if early_stopping.check(epoch_val_loss):
            print(f"  -> Validation loss improved to {epoch_val_loss:.4f}. Saving best checkpoint.")
            torch.save(model.state_dict(), best_model_weights_path)

        if early_stopping.should_stop:
            print(f"\nEarly stopping triggered after {epoch} epochs.")
            break

    # Load best checkpoint
    print("\nLoading best model weights for calibration & testing...")
    model.load_state_dict(torch.load(best_model_weights_path, map_location=device))

    # 4. Temperature Scaling Calibration
    calibrated_model = ModelWithTemperature(model).to(device)
    learned_temperature = calibrated_model.calibrate(val_loader, device)

    # 5. Final Test Set Evaluation
    calibrated_model.eval()
    all_test_preds = []
    all_test_targets = []

    with torch.no_grad():
        for images, labels in test_loader:
            images = images.to(device)
            scaled_logits = calibrated_model(images)
            preds = scaled_logits.argmax(dim=1).cpu().numpy()

            all_test_preds.extend(preds)
            all_test_targets.extend(labels.numpy())

    # Classification Report
    report_dict = classification_report(
        all_test_targets,
        all_test_preds,
        target_names=classes_list,
        output_dict=True
    )
    report_text = classification_report(
        all_test_targets,
        all_test_preds,
        target_names=classes_list
    )

    print("\n=== Final Test Classification Report ===")
    print(report_text)

    # Save metrics JSON
    metrics_path = output_path / "metrics.json"
    with open(metrics_path, "w") as f:
        json.dump(report_dict, f, indent=2)
    print(f"Saved classification metrics to {metrics_path}")

    # 6. Save Final Model Payload
    final_checkpoint_path = output_path / "disease_classifier_efficientnet_b0.pth"
    payload = {
        "model_state_dict": model.state_dict(),
        "temperature": learned_temperature,
        "classes": classes_list,
        "idx_to_class": idx_to_class,
        "num_classes": num_classes,
        "architecture": "efficientnet_b0",
        "val_loss": early_stopping.best_loss,
        "test_accuracy": report_dict.get("accuracy", 0.0)
    }

    torch.save(payload, final_checkpoint_path)
    print(f"Saved final calibrated model checkpoint to {final_checkpoint_path}")

    # Copy to backend weights directory for direct server deployment
    backend_weights_dir = Path(__file__).parent.parent / "backend" / "app" / "ml" / "weights"
    backend_weights_dir.mkdir(parents=True, exist_ok=True)
    backend_weights_file = backend_weights_dir / "disease_classifier_efficientnet_b0.pth"
    torch.save(payload, backend_weights_file)
    print(f"Copied deployment weights to {backend_weights_file}")

    # Clean up temp file
    if best_model_weights_path.exists():
        best_model_weights_path.unlink()

    return str(final_checkpoint_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train EfficientNet-B0 Crop Disease Classifier")
    parser.add_argument("--data_dir", type=str, default=None, help="Path to raw dataset directory. If None, downloads via kagglehub.")
    parser.add_argument("--epochs", type=int, default=15, help="Maximum number of epochs to train.")
    parser.add_argument("--batch_size", type=int, default=32, help="Batch size for training and validation.")
    parser.add_argument("--lr", type=float, default=1e-3, help="Initial learning rate.")
    parser.add_argument("--output_dir", type=str, default="output", help="Directory to save model artifacts.")

    args = parser.parse_args()

    data_directory = args.data_dir
    if data_directory is None:
        data_directory = download_dataset()

    train_model(
        data_dir=data_directory,
        epochs=args.epochs,
        batch_size=args.batch_size,
        lr=args.lr,
        output_dir=args.output_dir
    )
