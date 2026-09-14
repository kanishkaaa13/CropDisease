"""
FastAPI Router for Image Scan & Disease Diagnostic Endpoints.
Endpoint: POST /api/scan
"""
import io
from fastapi import APIRouter, UploadFile, File, HTTPException, status
from PIL import Image

from app.models.schemas import ScanResponse
from app.ml.disease_classifier import get_disease_classifier
from app.services.dataset_manager import get_dataset_manager

router = APIRouter()


@router.post(
    "/scan",
    response_model=ScanResponse,
    summary="Scan crop leaf image for disease diagnosis & Grad-CAM heatmap",
    description=(
        "Accepts an uploaded crop leaf image file. Returns model predicted disease label, "
        "calibrated confidence score, top-3 predictions, HSV severity estimation, "
        "Grad-CAM visual heatmap overlay (Base64 URI), and low-confidence flag."
    ),
)
async def scan_crop_disease(
    file: UploadFile = File(..., description="Crop leaf or plant image (JPEG, PNG, WEBP)")
):
    # Validate content type
    if file.content_type and not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type '{file.content_type}'. Please upload an image file (JPEG, PNG, WEBP)."
        )

    try:
        # Read image bytes
        contents = await file.read()
        if not contents:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty."
            )

        # Open PIL Image
        try:
            pil_image = Image.open(io.BytesIO(contents)).convert("RGB")
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unable to decode image file. Please upload a valid image."
            )

        # Run DiseaseClassifier diagnostic pipeline
        classifier = get_disease_classifier()
        scan_result = classifier.scan_crop_image(pil_image)

        return ScanResponse(**scan_result)

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during crop scanning: {str(exc)}"
        )


@router.post("/dataset/download", summary="Download Kaggle crop disease dataset")
def download_dataset(force: bool = False):
    """
    Download the Kaggle crop pest and disease detection dataset.
    Returns dataset statistics after download.
    """
    try:
        dataset_manager = get_dataset_manager()
        dataset_path = dataset_manager.download_dataset(force=force)
        stats = dataset_manager.get_dataset_stats()
        
        return {
            "status": "success",
            "dataset_path": str(dataset_path),
            "stats": stats,
        }
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download dataset: {str(exc)}"
        )


@router.get("/dataset/stats", summary="Get dataset statistics")
def get_dataset_stats():
    """
    Get statistics about the downloaded dataset including
    number of classes and images per class.
    """
    try:
        dataset_manager = get_dataset_manager()
        stats = dataset_manager.get_dataset_stats()
        
        return {
            "status": "success",
            "stats": stats,
        }
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get dataset stats: {str(exc)}"
        )


@router.get("/dataset/classes", summary="Get dataset class names")
def get_dataset_classes():
    """
    Get list of class names from the dataset.
    """
    try:
        dataset_manager = get_dataset_manager()
        classes = dataset_manager.get_class_directories()
        
        return {
            "status": "success",
            "classes": classes,
            "total_classes": len(classes),
        }
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get dataset classes: {str(exc)}"
        )
