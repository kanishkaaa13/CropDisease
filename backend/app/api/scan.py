import uuid
import logging
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, status
from sqlalchemy.orm import Session
from PIL import Image

from app.db.connection import get_db
from app.db.models import Observation, AIResult, ObservationSource, Crop, Farm
from app.models.schemas import ScanResponse
from app.ml.disease_classifier import get_disease_classifier
from app.ml.image_quality import check_image_quality, get_farmer_friendly_message
from app.services.dataset_manager import get_dataset_manager

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/scan",
    response_model=ScanResponse,
    summary="Scan crop leaf image for disease diagnosis & Grad-CAM heatmap",
    description=(
        "Accepts an uploaded crop leaf image file. Returns model predicted disease label, "
        "calibrated confidence score, top-3 predictions, HSV severity estimation, "
        "Grad-CAM visual heatmap overlay (Base64 URI), low-confidence flag, and persists "
        "the observation and uploaded image."
    ),
)
async def scan_crop_disease(
    file: UploadFile = File(..., description="Crop leaf or plant image (JPEG, PNG, WEBP)"),
    crop_id: Optional[str] = Form(None, description="Optional Crop ID to link the observation to"),
    farmer_id: Optional[str] = Form(None, description="Optional Farmer ID who performed the scan"),
    gps_lat: Optional[float] = Form(None, description="Latitude of scan location"),
    gps_lng: Optional[float] = Form(None, description="Longitude of scan location"),
    notes: Optional[str] = Form(None, description="Optional notes"),
    db: Session = Depends(get_db),
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

        # 1. Save uploaded image to disk
        uploads_dir = Path(__file__).parent.parent.parent / "uploads" / "scans"
        uploads_dir.mkdir(parents=True, exist_ok=True)
        ext = Path(file.filename or "image.jpg").suffix or ".jpg"
        saved_filename = f"{uuid.uuid4()}{ext}"
        save_path = uploads_dir / saved_filename
        with open(save_path, "wb") as f:
            f.write(contents)
        stored_image_url = f"/uploads/scans/{saved_filename}"

        # 2. Run image quality check BEFORE disease classification
        quality_result = check_image_quality(pil_image)
        
        if not quality_result["passed"]:
            farmer_message = get_farmer_friendly_message(quality_result["issues"])
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error": "Image quality check failed",
                    "issues": quality_result["issues"],
                    "farmer_message": farmer_message,
                    "blur_score": quality_result["blur_score"],
                    "brightness_score": quality_result["brightness_score"],
                }
            )

        # 3. Run DiseaseClassifier diagnostic pipeline
        classifier = get_disease_classifier()
        scan_result = classifier.scan_crop_image(pil_image)

        # 4. Persist Observation + AIResult to database
        observation_id = None
        target_crop_id = crop_id
        if not target_crop_id:
            if farmer_id:
                farmer_crop = db.query(Crop).join(Farm).filter(Farm.owner_id == farmer_id).first()
                if farmer_crop:
                    target_crop_id = farmer_crop.id
            if not target_crop_id:
                any_crop = db.query(Crop).first()
                if any_crop:
                    target_crop_id = any_crop.id

        if target_crop_id:
            try:
                obs = Observation(
                    crop_id=target_crop_id,
                    reported_by=farmer_id,
                    image_urls=[stored_image_url],
                    source=ObservationSource.scan,
                    notes=notes,
                    gps_lat=gps_lat,
                    gps_lng=gps_lng,
                )
                db.add(obs)
                db.flush()

                ai_res = AIResult(
                    observation_id=obs.id,
                    disease_label=scan_result.get("label"),
                    confidence=float(scan_result.get("confidence", 0.0)),
                    severity_pct=float(scan_result.get("severity_pct", 0.0)),
                    model_version="v1.0.0",
                    heat_map_url=scan_result.get("gradcam_image_base64"),
                    treatment_recommendations={"top3": scan_result.get("top3", [])},
                )
                db.add(ai_res)
                db.commit()
                observation_id = obs.id
            except Exception as db_err:
                logger.warning("Failed to persist scan observation: %s", db_err)
                db.rollback()

        return ScanResponse(
            **scan_result,
            observation_id=observation_id,
            image_url=stored_image_url,
        )

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
