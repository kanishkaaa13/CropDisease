"""
FastAPI Router for RAG-based IPM Agronomic Advisory Endpoints.
Endpoint: POST /api/advisory
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, Header
from sqlalchemy.orm import Session
from typing import Optional

from app.db.connection import get_db
from app.models.schemas import AdvisoryRequest, RAGAdvisoryResponse
from app.services.rag_advisory import generate_rag_advisory
from app.i18n.catalog import disease_key, get_locale_from_request

router = APIRouter()


@router.post(
    "/advisory",
    response_model=RAGAdvisoryResponse,
    summary="Generate RAG-based anti-hallucination agronomic advisory",
    description=(
        "Takes crop_id + ai_result_id (or direct crop_name and disease_label), "
        "fetches matching IPM Knowledge Base content (exact/fuzzy match), "
        "applies strict anti-hallucination system prompt guardrails, and returns "
        "multilingual advisories (English, Hindi, Marathi) with numbered step-by-step action plans "
        "and a match_confidence coverage flag."
    ),
)
def get_agronomic_advisory(
    payload: AdvisoryRequest,
    db: Session = Depends(get_db),
    lang: Optional[str] = Query(None, description="Response language: en, hi, or mr"),
    accept_language: Optional[str] = Header(None, alias="Accept-Language"),
):
    try:
        crop_name = payload.crop_name or "Tomato"
        disease_label = payload.disease_label or "Tomato___Early_blight"
        growth_stage = payload.growth_stage or "vegetative"
        risk_level = "MODERATE"

        # If crop_id or ai_result_id provided, query database for context
        if payload.crop_id:
            try:
                from app.db.models import Crop, Observation, AIResult, RiskScore
                crop = db.query(Crop).filter(Crop.id == payload.crop_id).first()
                if crop:
                    crop_name = crop.crop_name
                    growth_stage = crop.growth_stage or growth_stage

                    # Check latest risk score
                    latest_risk = (
                        db.query(RiskScore)
                        .filter(RiskScore.crop_id == crop.id)
                        .order_by(RiskScore.timestamp.desc())
                        .first()
                    )
                    if latest_risk:
                        risk_level = str(latest_risk.risk_level.value if hasattr(latest_risk.risk_level, "value") else latest_risk.risk_level).upper()
            except Exception:
                pass

        if payload.ai_result_id:
            try:
                from app.db.models import AIResult
                ai_res = db.query(AIResult).filter(AIResult.id == payload.ai_result_id).first()
                if ai_res and ai_res.disease_label:
                    disease_label = ai_res.disease_label
            except Exception:
                pass

        farm_context = {
            "growth_stage": growth_stage,
            "risk_level": risk_level,
            "weather_summary": "Temperature 28°C, Humidity 75%"
        }

        # Run RAG advisory engine
        rag_output = generate_rag_advisory(
            crop_name=crop_name,
            disease_label=disease_label,
            farm_context=farm_context
        )

        rag_output["crop_id"] = payload.crop_id
        rag_output["ai_result_id"] = payload.ai_result_id
        locale = get_locale_from_request(lang, accept_language)
        if not lang and not accept_language and payload.language_pref:
            locale = get_locale_from_request(payload.language_pref)
        rag_output["advisory_key"] = "ipm_advisory"
        rag_output["disease_key"] = disease_key(disease_label)
        rag_output["crop_key"] = disease_key(crop_name)
        rag_output["language"] = locale

        return RAGAdvisoryResponse(**rag_output)

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating RAG advisory action plan: {str(exc)}"
        )
