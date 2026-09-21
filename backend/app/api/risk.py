"""
FastAPI Router for Risk Assessment & Score Endpoints.
Endpoint: POST /api/risk-score
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, Header
from sqlalchemy.orm import Session

from app.db.connection import get_db
from app.models.schemas import RiskScoreRequest, RiskScoreResponse, CropRiskPredictionRequest, CropRiskPredictionResponse
from app.services.risk_engine import evaluate_crop_risk_from_db
from app.services.risk_engine import compute_crop_risk
from app.services.weather import fetch_weather, engineer_weather_features, compute_weather_risk
from datetime import datetime, timezone
from app.i18n.catalog import get_locale_from_request, translate_risk_level

router = APIRouter()


def _prediction_actions(crop: str, soil_type: str, soil_ph: float, weather_risk: float) -> list[str]:
    actions = [f"Inspect {crop} leaves twice this week and remove visibly infected material."]
    if weather_risk >= 60:
        actions.append("Improve field ventilation and avoid overhead irrigation while humidity is high.")
    if soil_ph < 5.5 or soil_ph > 7.5:
        actions.append(f"Test and correct the {soil_type} soil pH with local agronomy guidance.")
    if weather_risk >= 40:
        actions.append("Monitor after rainfall and follow only locally approved crop protection guidance.")
    return actions[:4]


@router.post("/predict/risk", response_model=CropRiskPredictionResponse, summary="Predict seven-day crop risk from weather and soil data")
async def predict_crop_risk(payload: CropRiskPredictionRequest):
    try:
        latitude = payload.latitude if payload.latitude is not None else 19.9975
        longitude = payload.longitude if payload.longitude is not None else 73.7898
        snapshot = await fetch_weather(latitude, longitude, forecast_days=7)
        features = engineer_weather_features(snapshot)
        live_weather_risk = compute_weather_risk(features)
        # The fusion engine combines disease, weather, local-case, and pest signals.
        # Without a confirmed image or field history, neutral priors are used explicitly.
        stage = "vegetative"
        if payload.sowing_date:
            age_days = max(0, (datetime.now(timezone.utc).date() - payload.sowing_date.date()).days)
            stage = "sowing" if age_days < 21 else "flowering" if age_days < 75 else "fruiting" if age_days < 120 else "maturity"
        result = compute_crop_risk(
            disease_confidence=0.35,
            temp_c=payload.temperature,
            humidity_pct=payload.humidity,
            rain_mm=payload.rainfall,
            crop_stage=stage,
            nearby_case_count=0,
            days_since_rain=features["days_since_rain"],
            forecast_days=[
                {"day": f"Day {index + 1}", "date": item["date"], "temp_max": item["temp_max"], "humidity_pct": item["humidity_mean"], "rain_mm": item["precipitation_sum"]}
                for index, item in enumerate(snapshot.forecast[:7])
            ],
        )
        factors = [
            {"name": "Weather pressure", "value": round(live_weather_risk, 1), "detail": f"{payload.temperature:.1f}°C, {payload.humidity:.0f}% humidity, {payload.rainfall:.1f} mm rainfall."},
            {"name": "Soil condition", "value": round(max(0.0, 100.0 - abs(payload.soil_ph - 6.5) * 18), 1), "detail": f"{payload.soil_type.title()} soil at pH {payload.soil_ph:.1f}."},
            {"name": "Crop stage", "value": round(result["overall_score"], 1), "detail": f"{stage.title()} stage vulnerability included in the fusion score."},
        ]
        return CropRiskPredictionResponse(
            risk_level=result["risk_level"],
            score=result["overall_score"],
            factors=factors,
            actions=_prediction_actions(payload.crop, payload.soil_type, payload.soil_ph, live_weather_risk),
            forecast=result["forecast"],
            weather={"temperature": snapshot.temperature, "humidity": snapshot.humidity, "precipitation": snapshot.precipitation, "wind_speed": snapshot.wind_speed, "risk": round(live_weather_risk, 1)},
        )
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Risk prediction unavailable: {exc}") from exc


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
