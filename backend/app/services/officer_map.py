"""
Officer map data service — observation points and district aggregates for the risk map.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.models import AIResult, Crop, ExpertValidation, Farm, Observation, RiskScore
from app.services.risk_engine import haversine_distance_km

RISK_ORDER = {"LOW": 1, "MODERATE": 2, "HIGH": 3, "CRITICAL": 4}


def risk_level_from_score(score: float) -> str:
    """Map a 0–100 risk score to a display risk level."""
    if score >= 80:
        return "CRITICAL"
    if score >= 60:
        return "HIGH"
    if score >= 40:
        return "MODERATE"
    return "LOW"


def normalize_risk_level(raw: str | None) -> str:
    if not raw:
        return "MODERATE"
    upper = str(raw).upper()
    if upper in ("MEDIUM", "MODERATE"):
        return "MODERATE"
    if upper in RISK_ORDER:
        return upper
    return "MODERATE"


def max_risk_level(levels: list[str]) -> str:
    if not levels:
        return "LOW"
    return max(levels, key=lambda level: RISK_ORDER.get(level, 0))


def get_map_data(
    db: Session,
    *,
    crop: Optional[str] = None,
    disease: Optional[str] = None,
    risk: Optional[str] = None,
    days: int = 30,
    officer_lat: float = 19.7,
    officer_lng: float = 75.7,
    district_scope: Optional[str] = None,
) -> dict[str, Any]:
    """Build map payload: observation points, district aggregates, and filter options."""
    since = datetime.now(timezone.utc) - timedelta(days=max(1, min(days, 365)))

    query = (
        db.query(AIResult, Observation, Crop, Farm, RiskScore)
        .join(Observation, AIResult.observation_id == Observation.id)
        .join(Crop, Observation.crop_id == Crop.id)
        .join(Farm, Crop.farm_id == Farm.id)
        .outerjoin(RiskScore, RiskScore.crop_id == Crop.id)
        .outerjoin(ExpertValidation, ExpertValidation.ai_result_id == AIResult.id)
        .filter(Observation.timestamp >= since)
        .filter(Farm.state == "Maharashtra")
        .filter(Farm.gps_lat.isnot(None))
        .filter(Farm.gps_lng.isnot(None))
        .filter(ExpertValidation.id.is_(None))
    )

    if district_scope:
        query = query.filter(Farm.district == district_scope)
    if crop:
        query = query.filter(func.lower(Crop.crop_name) == crop.lower())
    if disease:
        query = query.filter(func.lower(AIResult.disease_label).contains(disease.lower()))

    rows = query.order_by(Observation.timestamp.desc()).limit(500).all()

    points: list[dict[str, Any]] = []
    district_cases: dict[str, list[dict[str, Any]]] = defaultdict(list)
    crop_set: set[str] = set()
    disease_set: set[str] = set()
    daily_counts: dict[str, int] = defaultdict(int)

    for ai, obs, crop_row, farm, risk_row in rows:
        crop_name = crop_row.crop_name or "Unknown"
        disease_label = ai.disease_label or "Unknown"
        crop_set.add(crop_name)
        disease_set.add(disease_label)

        if risk_row and risk_row.overall_score is not None:
            risk_score = (
                risk_row.overall_score * 100
                if risk_row.overall_score <= 1.0
                else float(risk_row.overall_score)
            )
            risk_level = normalize_risk_level(
                str(risk_row.risk_level.value if hasattr(risk_row.risk_level, "value") else risk_row.risk_level)
            )
        else:
            risk_score = float(ai.severity_pct or 50.0)
            risk_level = risk_level_from_score(risk_score)

        if risk and normalize_risk_level(risk) != risk_level:
            continue

        lat = farm.gps_lat
        lng = farm.gps_lng
        distance_km = haversine_distance_km(officer_lat, officer_lng, lat, lng)
        obs_date = obs.timestamp or datetime.now(timezone.utc)
        day_key = obs_date.date().isoformat()
        daily_counts[day_key] += 1

        point = {
            "id": ai.id,
            "ai_result_id": ai.id,
            "observation_id": obs.id,
            "lat": lat,
            "lng": lng,
            "risk": risk_level,
            "risk_score": round(risk_score, 1),
            "disease": disease_label,
            "crop": crop_name,
            "confidence": round((ai.confidence or 0.5) * 100, 1),
            "farm_name": farm.name,
            "farm_id": farm.id,
            "district": farm.district,
            "taluka": farm.taluka,
            "date": obs_date.isoformat(),
            "distance_km": round(distance_km, 1),
        }
        points.append(point)
        district_cases[farm.district].append(point)

    districts: list[dict[str, Any]] = []
    for district_name, cases in district_cases.items():
        disease_counter = Counter(c["disease"] for c in cases)
        crop_counter = Counter(c["crop"] for c in cases)
        risk_levels = [c["risk"] for c in cases]
        districts.append(
            {
                "district": district_name,
                "total": len(cases),
                "dominant_disease": disease_counter.most_common(1)[0][0] if disease_counter else "Unknown",
                "dominant_crop": crop_counter.most_common(1)[0][0] if crop_counter else "Unknown",
                "max_risk": max_risk_level(risk_levels),
                "avg_risk_score": round(sum(c["risk_score"] for c in cases) / len(cases), 1),
                "top_diseases": [
                    {"name": name, "count": count}
                    for name, count in disease_counter.most_common(3)
                ],
                "crops": [{"name": name, "count": count} for name, count in crop_counter.most_common(5)],
            }
        )

    districts.sort(key=lambda d: d["total"], reverse=True)

    trend: list[dict[str, Any]] = []
    for i in range(29, -1, -1):
        day = (datetime.now(timezone.utc) - timedelta(days=i)).date().isoformat()
        trend.append({"date": day, "count": daily_counts.get(day, 0)})

    priority_cases = sorted(points, key=lambda p: (RISK_ORDER.get(p["risk"], 0), p["confidence"]), reverse=True)[:5]

    return {
        "points": points,
        "districts": districts,
        "trend": trend,
        "priority_cases": priority_cases,
        "filter_options": {
            "crops": sorted(crop_set),
            "diseases": sorted(disease_set),
        },
    }
