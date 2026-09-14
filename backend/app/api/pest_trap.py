"""
FastAPI Router for Pest Trap Endpoints.
Endpoint: POST /api/pest-trap/reading
"""
import io
import logging
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from PIL import Image
from sqlalchemy.orm import Session

from app.db.connection import get_db
from app.db.models.pest_trap import PestTrapReading
from app.ml.pest_detector import detect_pests
from app.services.pest_trend import compute_pest_trend

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/pest-trap/reading",
    summary="Submit pest trap image for detection and trend analysis",
    description=(
        "Uploads a sticky trap image, runs pest detection (currently in MOCK mode using blob detection), "
        "stores the reading in the database, and returns pest counts with 7-day trend analysis."
    ),
)
async def submit_pest_trap_reading(
    device_id: str,
    farm_id: str,
    trap_type: str = "Pheromone Trap",
    location_description: str = None,
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Process pest trap image and store reading.
    
    Args:
        device_id: Device identifier
        farm_id: Farm ID
        trap_type: Type of trap (default: Pheromone Trap)
        location_description: Optional location description
        image: Uploaded trap image
        db: Database session
    
    Returns:
        Detection results with pest counts and trend analysis
    """
    try:
        # Read image
        contents = await image.read()
        
        # Open PIL Image
        try:
            pil_image = Image.open(io.BytesIO(contents)).convert("RGB")
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unable to decode image file: {exc}"
            )
        
        # Run pest detection
        detection_result = detect_pests(pil_image)
        
        # Create database record
        reading = PestTrapReading(
            farm_id=farm_id,
            trap_type=trap_type,
            location_description=location_description,
            pest_count=detection_result["total_count"],
            dominant_pest=None,  # Could be determined from pest_counts
            last_checked_at=None,  # Will be set by server_default
        )
        
        db.add(reading)
        db.commit()
        db.refresh(reading)
        
        # Compute pest trend
        trend_result = compute_pest_trend(db, farm_id, detection_result["total_count"])
        
        logger.info(f"Stored pest trap reading for farm {farm_id}: {detection_result['total_count']} pests")
        
        return {
            "reading_id": reading.id,
            "farm_id": farm_id,
            "device_id": device_id,
            "pest_counts": detection_result["pest_counts"],
            "total_count": detection_result["total_count"],
            "annotated_image_base64": detection_result["annotated_image_base64"],
            "trend": trend_result,
            "checked_at": reading.last_checked_at.isoformat() if reading.last_checked_at else None,
        }
        
    except HTTPException:
        raise
    except Exception as exc:
        db.rollback()
        logger.error(f"Error processing pest trap reading: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing pest trap reading: {exc}"
        )


@router.get(
    "/pest-trap/readings/{farm_id}",
    summary="Get pest trap readings for a farm",
    description="Retrieves recent pest trap readings for a specific farm.",
)
def get_pest_trap_readings(
    farm_id: str,
    limit: int = 10,
    db: Session = Depends(get_db),
):
    """
    Get recent pest trap readings for a farm.
    
    Args:
        farm_id: Farm ID
        limit: Maximum number of readings to return (default: 10)
        db: Database session
    
    Returns:
        List of pest trap readings
    """
    readings = db.query(PestTrapReading).filter(
        PestTrapReading.farm_id == farm_id
    ).order_by(PestTrapReading.last_checked_at.desc()).limit(limit).all()
    
    return {
        "farm_id": farm_id,
        "count": len(readings),
        "readings": [
            {
                "id": r.id,
                "trap_type": r.trap_type,
                "location_description": r.location_description,
                "pest_count": r.pest_count,
                "dominant_pest": r.dominant_pest,
                "last_checked_at": r.last_checked_at.isoformat() if r.last_checked_at else None,
            }
            for r in readings
        ],
    }
