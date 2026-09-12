"""
Training Script — KrushiRakshak AI Disease Classifier
Usage: python scripts/train.py --epochs 50 --batch-size 32
"""
import argparse
import torch
import torch.nn as nn
import torch.optim as optim
from torchvision import datasets, transforms, models
from pathlib import Path


DATA_DIR = Path(__file__).parent.parent / "data" / "raw"
WEIGHTS_DIR = Path(__file__).parent.parent.parent / "backend" / "app" / "ml" / "weights"
NUM_CLASSES = 38  # PlantVillage has 38 disease classes


def get_transforms():
    return {
        "train": transforms.Compose([
            transforms.RandomResizedCrop(224),
            transforms.RandomHorizontalFlip(),
            transforms.ColorJitter(brightness=0.2, contrast=0.2),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
        ]),
        "val": transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
        ]),
    }


def build_model(num_classes: int):
    model = models.resnet50(weights=models.ResNet50_Weights.IMAGENET1K_V1)
    model.fc = nn.Linear(model.fc.in_features, num_classes)
    return model


def train(epochs: int, batch_size: int):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Training on {device}")

    tfms = get_transforms()
    full_dataset = datasets.ImageFolder(DATA_DIR, transform=tfms["train"])
    train_size = int(0.8 * len(full_dataset))
    val_size = len(full_dataset) - train_size
    train_ds, val_ds = torch.utils.data.random_split(full_dataset, [train_size, val_size])
    val_ds.dataset.transform = tfms["val"]

    loaders = {
        "train": torch.utils.data.DataLoader(train_ds, batch_size=batch_size, shuffle=True, num_workers=4),
        "val": torch.utils.data.DataLoader(val_ds, batch_size=batch_size, shuffle=False, num_workers=4),
    }

    model = build_model(NUM_CLASSES).to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=1e-4)
    scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=10, gamma=0.5)

    best_acc = 0.0
    for epoch in range(epochs):
        for phase in ["train", "val"]:
            model.train() if phase == "train" else model.eval()
            running_loss, running_corrects = 0.0, 0
            for inputs, labels in loaders[phase]:
                inputs, labels = inputs.to(device), labels.to(device)
                optimizer.zero_grad()
                with torch.set_grad_enabled(phase == "train"):
                    outputs = model(inputs)
                    loss = criterion(outputs, labels)
                    preds = outputs.argmax(1)
                    if phase == "train":
                        loss.backward()
                        optimizer.step()
                running_loss += loss.item() * inputs.size(0)
                running_corrects += (preds == labels).sum().item()
            epoch_acc = running_corrects / len(loaders[phase].dataset)
            print(f"[{epoch+1}/{epochs}] {phase} acc={epoch_acc:.4f}")
            if phase == "val" and epoch_acc > best_acc:
                best_acc = epoch_acc
                WEIGHTS_DIR.mkdir(parents=True, exist_ok=True)
                torch.save(model.state_dict(), WEIGHTS_DIR / "disease_classifier.pth")
                print(f"  ✓ New best model saved ({best_acc:.4f})")
        scheduler.step()

    print(f"\nTraining complete. Best val accuracy: {best_acc:.4f}")
    print(f"Weights saved to: {WEIGHTS_DIR / 'disease_classifier.pth'}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--epochs", type=int, default=30)
    parser.add_argument("--batch-size", type=int, default=32)
    args = parser.parse_args()
    train(args.epochs, args.batch_size)
