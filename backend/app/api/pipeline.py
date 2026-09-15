"""
FastAPI Router for Full Pipeline Endpoint.
Endpoint: POST /api/pipeline/run/{crop_id}

This is the unified endpoint that runs the complete fusion + risk engine + decision engine pipeline.
It replaces the need to call /api/scan, /api/risk-score, /api/advisory separately.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.connection import get_db
from app.services.risk_engine import run_full_pipeline

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/pipeline/run/{crop_id}",
    summary="Run full risk assessment pipeline",
    description=(
        "Executes the complete fusion + risk engine + decision engine pipeline for a crop. "
        "This unified endpoint runs all risk assessment branches (disease detection, weather risk, "
        "crop stage analysis, pest trend analysis, spatial risk) and returns a comprehensive result "
        "with all intermediate scores and automated decisions."
    ),
)
async def run_pipeline(
    crop_id: str,
    db: Session = Depends(get_db),
):
    """
    Run the complete risk assessment pipeline for a crop.
    
    This endpoint orchestrates:
    1. Image quality check
    2. Disease probability detection
    3. Weather risk calculation
    4. Crop stage multiplier application
    5. Pest trend analysis (if trap data exists)
    6. Spatial risk analysis (nearby cases)
    7. Fusion of all sub-scores
    8. Overall risk calculation
    9. Decision engine (alerts, follow-ups, expert validation)
    
    Args:
        crop_id: ID of the crop to analyze
        db: Database session
    
    Returns:
        Complete PipelineResult with all intermediate scores, final risk, and decisions
    """
    try:
        logger.info(f"Pipeline request received for crop_id: {crop_id}")
        
        # Run the full pipeline
        pipeline_result = run_full_pipeline(db, crop_id)
        
        logger.info(f"Pipeline completed successfully for crop_id: {crop_id}")
        return pipeline_result
        
    except ValueError as exc:
        # Crop not found
        logger.error(f"Crop not found: {exc}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc)
        )
    except Exception as exc:
        # Unexpected error
        logger.error(f"Pipeline execution error: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Pipeline execution failed: {exc}"
        )
