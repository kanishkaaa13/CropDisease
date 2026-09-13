"""
Dataset & Preprocessing Module for Crop Pest & Disease Detection.
Uses kagglehub to download 'nirmalsankalana/crop-pest-and-disease-detection',
performs stratified train/val/test splits, and applies Albumentations data augmentations.
"""
import os
import glob
from pathlib import Path
from typing import Tuple, List, Dict, Optional, Callable

import cv2
import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader
from sklearn.model_selection import train_test_split
import albumentations as A
from albumentations.pytorch import ToTensorV2

try:
    import kagglehub
    _HAS_KAGGLEHUB = True
except ImportError:
    _HAS_KAGGLEHUB = False

# ImageNet normalization statistics
IMAGENET_MEAN = (0.485, 0.456, 0.406)
IMAGENET_STD = (0.229, 0.224, 0.225)


def download_dataset() -> str:
    """Download dataset from Kaggle via kagglehub."""
    if not _HAS_KAGGLEHUB:
        raise RuntimeError("kagglehub is not installed. Run 'pip install kagglehub' first.")
    print("Downloading 'nirmalsankalana/crop-pest-and-disease-detection' via kagglehub...")
    path = kagglehub.dataset_download("nirmalsankalana/crop-pest-and-disease-detection")
    print(f"Dataset downloaded to: {path}")
    return path


def get_transforms(img_size: int = 224) -> Tuple[A.Compose, A.Compose]:
    """
    Construct Albumentations augmentation pipelines.
    - Train: RandomRotate90, Flip, ShiftScaleRotate, ColorJitter, Normalization.
    - Val/Test: Resize + Normalization.
    """
    train_transform = A.Compose([
        A.Resize(img_size, img_size),
        A.RandomRotate90(p=0.5),
        A.HorizontalFlip(p=0.5),
        A.VerticalFlip(p=0.5),
        A.ShiftScaleRotate(shift_limit=0.1, scale_limit=0.1, rotate_limit=30, p=0.5),
        A.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2, hue=0.1, p=0.5),
        A.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
        ToTensorV2(),
    ])

    val_transform = A.Compose([
        A.Resize(img_size, img_size),
        A.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
        ToTensorV2(),
    ])

    return train_transform, val_transform


class AlbumentationsDataset(Dataset):
    """PyTorch Dataset wrapper accepting Albumentations transforms."""

    def __init__(self, file_paths: List[str], labels: List[int], transform: Optional[Callable] = None):
        self.file_paths = file_paths
        self.labels = labels
        self.transform = transform

    def __len__(self) -> int:
        return len(self.file_paths)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, int]:
        img_path = self.file_paths[idx]
        image = cv2.imread(img_path)
        if image is None:
            raise ValueError(f"Could not load image at {img_path}")
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        if self.transform:
            augmented = self.transform(image=image)
            image = augmented["image"]

        label = self.labels[idx]
        return image, label


def prepare_dataset_splits(
    data_dir: str,
    test_size: float = 0.1,
    val_size: float = 0.1,
    seed: int = 42
) -> Tuple[List[str], List[int], List[str], List[int], List[str], List[int], Dict[int, str], List[float]]:
    """
    Discover image paths, build class mappings, perform stratified train/val/test splits,
    and compute class weights for imbalanced classes.
    """
    supported_exts = ("*.jpg", "*.jpeg", "*.png", "*.JPG", "*.JPEG", "*.PNG", "*.webp")
    image_paths = []
    class_names = []

    # Find class folders
    data_path = Path(data_dir)
    # Check if dataset is wrapped in a subfolder
    subdirs = [d for d in data_path.iterdir() if d.is_dir() and not d.name.startswith(".")]
    if len(subdirs) == 1 and subdirs[0].name.lower() in ("crop-pest-and-disease-detection", "dataset", "data"):
        data_path = subdirs[0]
        subdirs = [d for d in data_path.iterdir() if d.is_dir() and not d.name.startswith(".")]

    classes = sorted([d.name for d in subdirs if d.is_dir()])
    class_to_idx = {cls_name: i for i, cls_name in enumerate(classes)}
    idx_to_class = {i: cls_name for i, cls_name in enumerate(classes)}

    all_paths = []
    all_labels = []

    for cls_name in classes:
        cls_dir = data_path / cls_name
        cls_idx = class_to_idx[cls_name]
        cls_files = []
        for ext in supported_exts:
            cls_files.extend(glob.glob(str(cls_dir / "**" / ext), recursive=True))

        for fpath in cls_files:
            all_paths.append(fpath)
            all_labels.append(cls_idx)

    print(f"Found {len(all_paths)} total images across {len(classes)} classes.")
    for cls_name, cls_idx in class_to_idx.items():
        count = all_labels.count(cls_idx)
        print(f"  [{cls_idx:02d}] {cls_name}: {count} images")

    # Stratified Train / Test split
    train_val_paths, test_paths, train_val_labels, test_labels = train_test_split(
        all_paths, all_labels, test_size=test_size, random_state=seed, stratify=all_labels
    )

    # Stratified Train / Val split
    adjusted_val_size = val_size / (1.0 - test_size)
    train_paths, val_paths, train_labels, val_labels = train_test_split(
        train_val_paths, train_val_labels, test_size=adjusted_val_size, random_state=seed, stratify=train_val_labels
    )

    print(f"Splits: Train = {len(train_paths)}, Val = {len(val_paths)}, Test = {len(test_paths)}")

    # Compute Class Weights: w_c = Total / (Num_Classes * Count_c)
    num_classes = len(classes)
    total_train = len(train_labels)
    class_counts = [train_labels.count(i) for i in range(num_classes)]
    class_weights = [total_train / (num_classes * max(1, count)) for count in class_counts]

    return (
        train_paths, train_labels,
        val_paths, val_labels,
        test_paths, test_labels,
        idx_to_class,
        class_weights
    )


def create_dataloaders(
    train_paths: List[str], train_labels: List[int],
    val_paths: List[str], val_labels: List[int],
    test_paths: List[str], test_labels: List[int],
    batch_size: int = 32,
    num_workers: int = 2,
    img_size: int = 224
) -> Tuple[DataLoader, DataLoader, DataLoader]:
    """Construct PyTorch DataLoaders with Albumentations transforms."""
    train_tf, val_tf = get_transforms(img_size)

    train_ds = AlbumentationsDataset(train_paths, train_labels, transform=train_tf)
    val_ds = AlbumentationsDataset(val_paths, val_labels, transform=val_tf)
    test_ds = AlbumentationsDataset(test_paths, test_labels, transform=val_tf)

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True, num_workers=num_workers, pin_memory=True)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False, num_workers=num_workers, pin_memory=True)
    test_loader = DataLoader(test_ds, batch_size=batch_size, shuffle=False, num_workers=num_workers, pin_memory=True)

    return train_loader, val_loader, test_loader
