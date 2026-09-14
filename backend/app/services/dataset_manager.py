"""
Dataset Management Service
Handles downloading and managing the Kaggle crop pest and disease detection dataset.
"""
import logging
import os
from pathlib import Path
from typing import Optional, List
import shutil

logger = logging.getLogger(__name__)

# Kaggle dataset identifier
KAGGLE_DATASET = "nirmalsankalana/crop-pest-and-disease-detection"

# Default dataset storage location
DATASET_ROOT = Path(__file__).parent.parent.parent / "datasets"
DATASET_PATH = DATASET_ROOT / KAGGLE_DATASET.replace("/", "_")


class DatasetManager:
    """Manages dataset download, organization, and access."""
    
    def __init__(self, dataset_path: Optional[Path] = None):
        self.dataset_path = dataset_path or DATASET_PATH
        self.is_downloaded = self.dataset_path.exists()
        
    def download_dataset(self, force: bool = False) -> Path:
        """
        Download the Kaggle dataset using kagglehub.
        
        Args:
            force: Force re-download even if dataset exists
        
        Returns:
            Path to the downloaded dataset
        """
        if self.is_downloaded and not force:
            logger.info(f"Dataset already exists at {self.dataset_path}")
            return self.dataset_path
        
        try:
            import kagglehub
            
            logger.info(f"Downloading dataset {KAGGLE_DATASET}...")
            downloaded_path = kagglehub.dataset_download(KAGGLE_DATASET)
            
            # Move to our standard location
            if downloaded_path != str(self.dataset_path):
                self.dataset_path.parent.mkdir(parents=True, exist_ok=True)
                if self.dataset_path.exists():
                    shutil.rmtree(self.dataset_path)
                shutil.move(downloaded_path, self.dataset_path)
            
            self.is_downloaded = True
            logger.info(f"Dataset downloaded successfully to {self.dataset_path}")
            return self.dataset_path
            
        except ImportError:
            raise ImportError(
                "kagglehub is not installed. Install it with: pip install kagglehub"
            )
        except Exception as exc:
            logger.error(f"Failed to download dataset: {exc}")
            raise exc
    
    def get_dataset_path(self) -> Path:
        """Get the dataset path, downloading if necessary."""
        if not self.is_downloaded:
            return self.download_dataset()
        return self.dataset_path
    
    def get_class_directories(self) -> List[str]:
        """
        Get list of class directories from the dataset.
        
        Returns:
            List of class names (directory names)
        """
        if not self.is_downloaded:
            self.download_dataset()
        
        if not self.dataset_path.exists():
            logger.warning(f"Dataset path {self.dataset_path} does not exist")
            return []
        
        # Look for subdirectories that contain images
        class_dirs = []
        for item in self.dataset_path.iterdir():
            if item.is_dir():
                # Check if it contains image files
                image_files = list(item.glob("*.jpg")) + list(item.glob("*.jpeg")) + list(item.glob("*.png"))
                if image_files:
                    class_dirs.append(item.name)
        
        logger.info(f"Found {len(class_dirs)} class directories in dataset")
        return sorted(class_dirs)
    
    def get_training_images(self, class_name: str, limit: Optional[int] = None) -> List[Path]:
        """
        Get image paths for a specific class.
        
        Args:
            class_name: Name of the class/directory
            limit: Maximum number of images to return (None for all)
        
        Returns:
            List of image file paths
        """
        class_path = self.dataset_path / class_name
        if not class_path.exists():
            logger.warning(f"Class directory {class_path} does not exist")
            return []
        
        image_extensions = {".jpg", ".jpeg", ".png", ".webp"}
        images = [
            p for p in class_path.iterdir()
            if p.is_file() and p.suffix.lower() in image_extensions
        ]
        
        if limit:
            images = images[:limit]
        
        return images
    
    def get_dataset_stats(self) -> dict:
        """
        Get statistics about the dataset.
        
        Returns:
            Dictionary with dataset statistics
        """
        if not self.is_downloaded:
            self.download_dataset()
        
        class_dirs = self.get_class_directories()
        stats = {
            "total_classes": len(class_dirs),
            "classes": {},
            "total_images": 0,
        }
        
        for class_name in class_dirs:
            images = self.get_training_images(class_name)
            stats["classes"][class_name] = len(images)
            stats["total_images"] += len(images)
        
        return stats


# Global singleton
_dataset_manager_instance: Optional[DatasetManager] = None


def get_dataset_manager() -> DatasetManager:
    """Get or initialize the dataset manager singleton."""
    global _dataset_manager_instance
    if _dataset_manager_instance is None:
        _dataset_manager_instance = DatasetManager()
    return _dataset_manager_instance
