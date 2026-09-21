"""
FastAPI Router for Risk Assessment & Score Endpoints.
Endpoint: POST /api/risk-score
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, Header
from sqlalchemy.orm import Session

from app.db.connection import get_db
from app.models.schemas import RiskScoreRequest, RiskScoreResponse
from app.services.risk_engine import evaluate_crop_risk_from_db
from app.i18n.catalog import get_locale_from_request, translate_risk_level

router = APIRouter()


@router.post(
    "/risk-score",
    response_model=RiskScoreResponse,
    summary="Compute crop risk score, explainability breakdown, and 5-day forecast",
    description=(
        "Pulls crop, farm, and observation history from the database, fetches live weather "
        "and 5-day forecast from Open-Meteo API, queries 5km PostGIS outbreak density and pest trap trends, "
        "computes weighted overall risk (LOW, MODERATE, HIGH, CRITICAL), produces factor explainability ('why' list), "
        "and returns a 5-day risk projection forecast."
    ),
)
def compute_risk_score(
    payload: RiskScoreRequest,
    db: Session = Depends(get_db),
    lang: str | None = Query(None, description="Response language: en, hi, or mr"),
    accept_language: str | None = Header(None, alias="Accept-Language"),
):
    try:
        risk_result = evaluate_crop_risk_from_db(db=db, crop_id=payload.crop_id)
        locale = get_locale_from_request(lang, accept_language)
        risk_result["risk_level_key"] = str(risk_result.get("risk_level", "MODERATE")).lower()
        risk_result["risk_level"] = translate_risk_level(risk_result["risk_level_key"], locale)
        risk_result["language"] = locale
        for forecast_day in risk_result.get("forecast", []):
            key = str(forecast_day.get("risk_level", "MODERATE")).lower()
            forecast_day["risk_level_key"] = key
            forecast_day["risk_level"] = translate_risk_level(key, locale)
        return RiskScoreResponse(**risk_result)

    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(val_err)
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during risk score calculation: {str(exc)}"
        )
