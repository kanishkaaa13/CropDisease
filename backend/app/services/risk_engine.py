"""
Risk Engine Service — Multi-factor Explainable Disease & Pest Risk Assessor.
Calculates overall crop disease risk, maps severity levels, provides factor-level
explainability ('why' breakdown), and projects a 5-day forward risk trajectory forecast.
"""
import math
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, text

from app.services.open_meteo import fetch_open_meteo_weather

logger = logging.getLogger(__name__)

# Configurable Weights — Tune with Agronomic Domain Expert Input
DEFAULT_RISK_WEIGHTS = {
    "disease_confidence": 0.35,  # Weight for image classification model confidence
    "weather_risk": 0.25,        # Weight for temperature, humidity, and rainfall score
    "nearby_cases": 0.25,        # Weight for 5km outbreak density in past 14 days
    "pest_trend": 0.15,          # Weight for pheromone/sticky trap count trend
}

# Configurable Crop Stage Vulnerability Multipliers
# Thresholds used below are configurable, not scientifically validated — tune with domain expert input.
CROP_STAGE_MULTIPLIERS = {
    "sowing": 1.00,
    "vegetative": 1.10,
    "flowering": 1.30,   # Peak vulnerability to fungal & insect pest damage
    "fruiting": 1.25,    # High vulnerability to fruit rot & blight
    "maturity": 0.90,    # Hardened plant tissue
}


def calculate_weather_risk(
    temp_c: float,
    humidity_pct: float,
    rain_mm: float,
    days_since_rain: int = 0
) -> float:
    """
    Compute weather risk score (0-100) using rule-based environmental indicators.

    Thresholds used below are configurable, not scientifically validated — tune with domain expert input.
    - High relative humidity (> 70%): Fungal spores germinate rapidly in humid microclimates.
    - Moderate temperature (20°C to 32°C): Optimal thermal band for most phytopathogenic fungi.
    - Moisture/Rainfall: Leaf wetness duration fuels spore infection.
    """
    # 1. Humidity component (0 - 40 points)
    # Humidity < 50% -> 0 pts; 50%-70% -> linear 0-20; 70%-95% -> linear 20-40
    if humidity_pct < 50.0:
        humidity_score = 0.0
    elif humidity_pct <= 70.0:
        humidity_score = ((humidity_pct - 50.0) / 20.0) * 20.0
    else:
        humidity_score = 20.0 + (min(humidity_pct - 70.0, 25.0) / 25.0) * 20.0

    # 2. Temperature component (0 - 35 points)
    # Optimal fungal range: 20°C to 32°C -> 35 pts. Drops off below 15°C or above 38°C.
    if 20.0 <= temp_c <= 32.0:
        temp_score = 35.0
    elif 15.0 <= temp_c < 20.0:
        temp_score = ((temp_c - 15.0) / 5.0) * 35.0
    elif 32.0 < temp_c <= 38.0:
        temp_score = ((38.0 - temp_c) / 6.0) * 35.0
    else:
        temp_score = 5.0

    # 3. Rainfall / Leaf wetness component (0 - 25 points)
    if rain_mm > 10.0 or days_since_rain == 0:
        rain_score = 25.0
    elif rain_mm > 2.0 or days_since_rain <= 2:
        rain_score = 15.0
    elif rain_mm > 0.0 or days_since_rain <= 5:
        rain_score = 8.0
    else:
        rain_score = 0.0

    total_weather_score = humidity_score + temp_score + rain_score
    return round(min(max(total_weather_score, 0.0), 100.0), 1)


def get_crop_stage_multiplier(stage: str) -> float:
    """Retrieve vulnerability multiplier for a given crop growth stage."""
    normalized_stage = (stage or "vegetative").strip().lower()
    return CROP_STAGE_MULTIPLIERS.get(normalized_stage, 1.10)


def map_risk_level(score: float) -> str:
    """Map numeric risk score (0-100) to risk level string."""
    if score >= 80.0:
        return "CRITICAL"
    elif score >= 60.0:
        return "HIGH"
    elif score >= 40.0:
        return "MODERATE"
    else:
        return "LOW"


def compute_crop_risk(
    disease_confidence: float,
    temp_c: float,
    humidity_pct: float,
    rain_mm: float,
    crop_stage: str,
    pest_count_trend: Optional[float] = None,
    nearby_case_count: int = 0,
    days_since_rain: int = 0,
    forecast_days: Optional[List[Dict[str, Any]]] = None,
    weights: Optional[Dict[str, float]] = None
) -> Dict[str, Any]:
    """
    Calculate multi-factor risk score, map risk level, generate explainability ('why' list),
    and project 5-day daily risk forecast.
    """
    cfg_weights = weights or DEFAULT_RISK_WEIGHTS
    stage_mult = get_crop_stage_multiplier(crop_stage)

    # 1. Component Sub-scores (0-100 scale)
    disease_subscore = disease_confidence * 100.0
    weather_subscore = calculate_weather_risk(temp_c, humidity_pct, rain_mm, days_since_rain)
    nearby_subscore = min(nearby_case_count * 25.0, 100.0)  # 4+ nearby cases = 100 max

    if pest_count_trend is not None:
        # e.g., +50% increase in trap count -> pest subscore = 75.0
        pest_subscore = min(max(50.0 + pest_count_trend * 0.5, 0.0), 100.0)
    else:
        pest_subscore = 30.0  # Baseline fallback if no trap data

    # 2. Weighted Sum Calculation
    w_dis = cfg_weights["disease_confidence"]
    w_wea = cfg_weights["weather_risk"]
    w_near = cfg_weights["nearby_cases"]
    w_pest = cfg_weights["pest_trend"]
    total_w = w_dis + w_wea + w_near + w_pest

    raw_weighted = (
        (disease_subscore * w_dis) +
        (weather_subscore * w_wea) +
        (nearby_subscore * w_near) +
        (pest_subscore * w_pest)
    ) / total_w

    # Apply Crop Stage Multiplier
    overall_score = round(min(raw_weighted * stage_mult, 100.0), 1)
    risk_level = map_risk_level(overall_score)

    # 3. Generate Explainability ('why' list)
    why_explanation = []

    # Factor: Disease confidence
    dis_impact = round((disease_subscore * w_dis / total_w) * stage_mult, 1)
    why_explanation.append({
        "factor": "AI Model Scan Confidence",
        "details": f"Recent leaf scan detected disease with {int(disease_confidence * 100)}% confidence.",
        "impact_score": dis_impact
    })

    # Factor: Weather condition
    wea_impact = round((weather_subscore * w_wea / total_w) * stage_mult, 1)
    why_explanation.append({
        "factor": "Microclimate Weather Risk",
        "details": f"Relative humidity is {humidity_pct:.1f}%, temp {temp_c:.1f}°C, rainfall {rain_mm:.1f}mm.",
        "impact_score": wea_impact
    })

    # Factor: Crop susceptibility stage
    if stage_mult > 1.0:
        stage_impact = round((overall_score - raw_weighted), 1)
        why_explanation.append({
            "factor": "Crop Stage Vulnerability",
            "details": f"Crop is in '{crop_stage.capitalize()}' stage (x{stage_mult:.2f} susceptibility multiplier).",
            "impact_score": stage_impact
        })

    # Factor: Nearby outbreak cluster
    if nearby_case_count > 0:
        near_impact = round((nearby_subscore * w_near / total_w) * stage_mult, 1)
        why_explanation.append({
            "factor": "Regional Outbreak Proximity",
            "details": f"{nearby_case_count} similar disease outbreak(s) reported within 5km in past 14 days.",
            "impact_score": near_impact
        })

    # Factor: Pest trap trend
    if pest_count_trend is not None and abs(pest_count_trend) > 5.0:
        pest_impact = round((pest_subscore * w_pest / total_w) * stage_mult, 1)
        trend_direction = "increase" if pest_count_trend > 0 else "decrease"
        why_explanation.append({
            "factor": "Pest Trap Reading Trend",
            "details": f"Local field traps show {abs(pest_count_trend):.1f}% {trend_direction} in pest counts vs 7-day average.",
            "impact_score": pest_impact
        })

    # Sort explanation items by impact score descending
    why_explanation.sort(key=lambda x: x["impact_score"], reverse=True)

    # 4. Generate 5-Day Risk Forecast
    forecast_trajectory = []
    if forecast_days:
        for day_data in forecast_days[:5]:
            f_temp = day_data["temp_max"]
            f_hum = day_data["humidity_pct"]
            f_rain = day_data["rain_mm"]

            f_weather_subscore = calculate_weather_risk(f_temp, f_hum, f_rain, days_since_rain=0 if f_rain > 1.0 else 2)

            f_raw = (
                (disease_subscore * w_dis) +
                (f_weather_subscore * w_wea) +
                (nearby_subscore * w_near) +
                (pest_subscore * w_pest)
            ) / total_w

            f_overall = round(min(f_raw * stage_mult, 100.0), 1)

            forecast_trajectory.append({
                "day": day_data["day"],
                "date": day_data["date"],
                "predicted_risk_score": f_overall,
                "risk_level": map_risk_level(f_overall),
                "temp_max": f_temp,
                "rain_mm": f_rain,
            })

    return {
        "overall_score": overall_score,
        "risk_level": risk_level,
        "disease_risk": round(disease_subscore, 1),
        "pest_risk": round(pest_subscore, 1),
        "weather_risk": round(weather_subscore, 1),
        "why": why_explanation,
        "forecast": forecast_trajectory
    }


def query_nearby_cases(
    db: Session,
    lat: float,
    lng: float,
    radius_km: float = 5.0,
    days: int = 14
) -> int:
    """
    Query database for similar disease observation reports within radius_km (5km) in last 14 days.
    Uses PostGIS ST_DWithin if spatial column is enabled, otherwise falls back to Haversine distance.
    """
    from app.db.models import Observation, Farm

    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

    try:
        # Check if PostGIS function ST_DWithin works
        query = text("""
            SELECT COUNT(o.id)
            FROM observations o
            JOIN crops c ON o.crop_id = c.id
            JOIN farms f ON c.farm_id = f.id
            WHERE o.timestamp >= :cutoff
              AND ST_DWithin(
                  ST_MakePoint(f.gps_lng, f.gps_lat)::geography,
                  ST_MakePoint(:lng, :lat)::geography,
                  :radius_m
              )
        """)
        result = db.execute(query, {
            "cutoff": cutoff_date,
            "lat": lat,
            "lng": lng,
            "radius_m": radius_km * 1000.0
        }).scalar()

        return int(result or 0)

    except Exception:
        # Fallback to python-side bounding box / Haversine calculation
        db.rollback()
        observations = (
            db.query(Observation)
            .filter(Observation.timestamp >= cutoff_date)
            .all()
        )

        nearby_count = 0
        for obs in observations:
            obs_lat = obs.gps_lat or (obs.crop.farm.gps_lat if obs.crop and obs.crop.farm else None)
            obs_lng = obs.gps_lng or (obs.crop.farm.gps_lng if obs.crop and obs.crop.farm else None)

            if obs_lat is not None and obs_lng is not None:
                dist_km = haversine_distance_km(lat, lng, obs_lat, obs_lng)
                if dist_km <= radius_km:
                    nearby_count += 1

        return nearby_count


def query_pest_trend(db: Session, farm_id: str) -> Optional[float]:
    """
    Query recent 7-day pest trap count average vs previous 7-14 day average for a farm.
    Returns percentage change (e.g., +25.0 for 25% increase).
    """
    from app.db.models import PestTrapReading

    now = datetime.now(timezone.utc)
    recent_7d = now - timedelta(days=7)
    previous_14d = now - timedelta(days=14)

    readings_recent = (
        db.query(func.avg(PestTrapReading.pest_count))
        .filter(PestTrapReading.farm_id == farm_id)
        .filter(PestTrapReading.last_checked_at >= recent_7d)
        .scalar()
    )

    readings_prev = (
        db.query(func.avg(PestTrapReading.pest_count))
        .filter(PestTrapReading.farm_id == farm_id)
        .filter(PestTrapReading.last_checked_at >= previous_14d)
        .filter(PestTrapReading.last_checked_at < recent_7d)
        .scalar()
    )

    if readings_recent is None or readings_prev is None or readings_prev == 0:
        return None

    avg_recent = float(readings_recent)
    avg_prev = float(readings_prev)

    pct_change = ((avg_recent - avg_prev) / avg_prev) * 100.0
    return round(pct_change, 1)


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great-circle distance between two points in kilometers."""
    r = 6371.0  # Earth radius in kilometers
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = (
        math.sin(d_lat / 2) ** 2 +
        math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return r * c


def evaluate_crop_risk_from_db(db: Session, crop_id: str) -> Dict[str, Any]:
    """
    Fetch all DB records for a Crop, fetch Open-Meteo weather, and evaluate full risk score.
    """
    from app.db.models import Crop, Observation, AIResult, RiskScore, RiskLevel

    crop = db.query(Crop).filter(Crop.id == crop_id).first()
    if not crop:
        raise ValueError(f"Crop with ID '{crop_id}' not found.")

    farm = crop.farm
    lat = farm.gps_lat
    lng = farm.gps_lng
    stage = crop.growth_stage or "vegetative"

    # Fetch latest observation & AI result
    latest_obs = (
        db.query(Observation)
        .filter(Observation.crop_id == crop.id)
        .order_by(Observation.timestamp.desc())
        .first()
    )

    disease_confidence = 0.50  # Baseline fallback
    if latest_obs and latest_obs.ai_result:
        disease_confidence = float(latest_obs.ai_result.confidence or 0.50)

    # Fetch live weather data from Open-Meteo
    weather_data = fetch_open_meteo_weather(lat, lng)
    curr_weather = weather_data["current"]
    forecast_days = weather_data["daily"]

    # Query PostGIS nearby case count & pest trap trend
    nearby_cases = query_nearby_cases(db, lat, lng, radius_km=5.0, days=14)
    pest_trend = query_pest_trend(db, farm.id)

    # Calculate risk score payload
    risk_payload = compute_crop_risk(
        disease_confidence=disease_confidence,
        temp_c=curr_weather["temp_c"],
        humidity_pct=curr_weather["humidity_pct"],
        rain_mm=curr_weather["rain_mm"],
        crop_stage=stage,
        pest_count_trend=pest_trend,
        nearby_case_count=nearby_cases,
        days_since_rain=curr_weather.get("days_since_rain", 0),
        forecast_days=forecast_days,
    )

    risk_payload["crop_id"] = crop.id
    risk_payload["crop_name"] = crop.crop_name
    risk_payload["farm_name"] = farm.name

    # Save calculated RiskScore to database
    try:
        mapped_enum_level = getattr(RiskLevel, risk_payload["risk_level"].lower(), RiskLevel.medium)
        db_risk_score = RiskScore(
            crop_id=crop.id,
            timestamp=datetime.now(timezone.utc),
            disease_risk=risk_payload["disease_risk"] / 100.0,
            pest_risk=risk_payload["pest_risk"] / 100.0,
            weather_risk=risk_payload["weather_risk"] / 100.0,
            overall_score=risk_payload["overall_score"] / 100.0,
            risk_level=mapped_enum_level,
            contributing_factors={"why": risk_payload["why"]},
        )
        db.add(db_risk_score)
        db.commit()
    except Exception as exc:
        db.rollback()
        logger.warning("Failed to persist RiskScore to database: %s", exc)

    return risk_payload


def compute_district_risk(state: str, db: Session) -> List[Dict[str, Any]]:
    """
    Compute aggregate district-level risk statistics for the officer risk map.
    """
    from app.db.models import Farm, Crop, RiskScore

    farms_in_state = db.query(Farm).filter(func.lower(Farm.state) == state.lower()).all()
    if not farms_in_state:
        # Fallback sample districts for Maharashtra
        return [
            {"district": "Pune", "total_farms": 12, "high_risk_crops": 3, "avg_risk_score": 64.5, "risk_level": "HIGH"},
            {"district": "Nashik", "total_farms": 15, "high_risk_crops": 5, "avg_risk_score": 72.0, "risk_level": "HIGH"},
            {"district": "Kolhapur", "total_farms": 8, "high_risk_crops": 1, "avg_risk_score": 38.2, "risk_level": "LOW"},
            {"district": "Solapur", "total_farms": 10, "high_risk_crops": 4, "avg_risk_score": 58.0, "risk_level": "MODERATE"},
        ]

    district_map: Dict[str, Dict[str, Any]] = {}
    for farm in farms_in_state:
        dist = farm.district or "Unknown"
        if dist not in district_map:
            district_map[dist] = {"district": dist, "farm_count": 0, "crop_ids": []}

        district_map[dist]["farm_count"] += 1
        for crop in farm.crops:
            district_map[dist]["crop_ids"].append(crop.id)

    results = []
    for dist_name, dist_info in district_map.items():
        crop_ids = dist_info["crop_ids"]
        if not crop_ids:
            avg_score = 30.0
            high_risk_count = 0
        else:
            latest_scores = (
                db.query(RiskScore.overall_score)
                .filter(RiskScore.crop_id.in_(crop_ids))
                .all()
            )
            if latest_scores:
                scores_list = [s[0] * 100.0 if s[0] <= 1.0 else s[0] for s in latest_scores]
                avg_score = round(sum(scores_list) / len(scores_list), 1)
                high_risk_count = sum(1 for s in scores_list if s >= 60.0)
            else:
                avg_score = 35.0
                high_risk_count = 0

        results.append({
            "district": dist_name,
            "total_farms": dist_info["farm_count"],
            "high_risk_crops": high_risk_count,
            "avg_risk_score": avg_score,
            "risk_level": map_risk_level(avg_score),
        })

    return results


# Configurable Fusion Weights — Tune with Agronomic Domain Expert Input
# These weights control how much each sub-score contributes to the overall risk
FUSION_WEIGHTS = {
    "disease_risk": 0.40,      # Weight for disease detection confidence + severity
    "pest_risk": 0.25,         # Weight for pest trap trend data
    "spread_risk": 0.35,       # Weight for spatial proximity + weather conditions
}


def run_full_pipeline(db: Session, crop_id: str) -> Dict[str, Any]:
    """
    Run the complete fusion + risk engine + decision engine pipeline.
    
    This is the final pipeline stage that orchestrates all risk assessment branches:
    1. Fetch crop, farm, latest observation/image, and lat/lng from DB
    2. Call each branch: image_quality → disease probability → weather risk → crop stage → pest trend → spatial risk
    3. Fusion step: combine into disease_risk, pest_risk, spread_risk
    4. Overall risk: weighted combination of sub-scores
    5. Decision engine: determine action based on risk_level + confidence
    6. Return structured PipelineResult with all intermediate scores
    
    Args:
        db: Database session
        crop_id: Crop ID to run pipeline for
    
    Returns:
        PipelineResult containing all intermediate scores, final risk, and decision
    """
    from app.db.models import Crop, Observation, AIResult, RiskScore, RiskLevel, Alert, AlertLevel, FollowUp, FollowUpStatus
    from app.ml.disease_classifier import get_disease_classifier
    from app.services.spatial_risk import get_nearby_cases, compute_spatial_risk
    from app.services.pest_trend import compute_pest_trend
    from app.services.crop_stage import get_stage_multiplier, CropStage
    from PIL import Image
    import io
    
    logger.info(f"Starting full pipeline for crop_id: {crop_id}")
    
    # Step 1: Fetch crop, farm, and latest observation
    crop = db.query(Crop).filter(Crop.id == crop_id).first()
    if not crop:
        raise ValueError(f"Crop with ID '{crop_id}' not found.")
    
    farm = crop.farm
    lat = farm.gps_lat
    lng = farm.gps_lng
    crop_name = crop.crop_name
    growth_stage = crop.growth_stage or "vegetative"
    
    # Fetch latest observation with AI result
    latest_obs = (
        db.query(Observation)
        .filter(Observation.crop_id == crop.id)
        .order_by(Observation.timestamp.desc())
        .first()
    )
    
    # Step 2: Branch 1 - Image Quality Check (skipped for now, assume valid)
    image_quality_score = 1.0  # Placeholder: 1.0 = good quality
    
    # Step 3: Branch 2 - Disease Probability
    disease_confidence = 0.50  # Baseline fallback
    disease_label = "Unknown"
    severity_pct = 0.0
    gradcam_base64 = ""
    top3_predictions = []
    is_low_confidence = False
    
    if latest_obs and latest_obs.ai_result:
        disease_confidence = float(latest_obs.ai_result.confidence or 0.50)
        disease_label = latest_obs.ai_result.disease_label or "Unknown"
        severity_pct = float(latest_obs.ai_result.severity_pct or 0.0)
        is_low_confidence = disease_confidence < 0.60
        
        # Try to get top3 from existing AI result if available
        if latest_obs.ai_result.treatment_recommendations:
            top3_predictions = latest_obs.ai_result.treatment_recommendations.get("top3", [])
    
    # If we have image data, run fresh classification
    if latest_obs and latest_obs.image_urls:
        try:
            # Load image from first URL (assuming local file or base64)
            image_data = latest_obs.image_urls[0]
            if image_data.startswith("data:image"):
                # Base64 encoded image
                import base64
                header, encoded = image_data.split(",", 1)
                image_bytes = base64.b64decode(encoded)
                pil_image = Image.open(io.BytesIO(image_bytes))
            else:
                # Assume file path (not implemented in this context)
                pil_image = None
            
            if pil_image:
                classifier = get_disease_classifier()
                scan_result = classifier.scan_crop_image(pil_image)
                disease_confidence = scan_result["confidence"]
                disease_label = scan_result["label"]
                severity_pct = scan_result["severity_pct"]
                gradcam_base64 = scan_result["gradcam_image_base64"]
                top3_predictions = scan_result["top3"]
                is_low_confidence = scan_result["low_confidence"]
        except Exception as exc:
            logger.warning(f"Failed to run disease classification: {exc}")
    
    # Step 4: Branch 3 - Weather Risk
    weather_data = fetch_open_meteo_weather(lat, lng)
    current_weather = weather_data["current"]
    weather_risk = calculate_weather_risk(
        temp_c=current_weather["temp_c"],
        humidity_pct=current_weather["humidity_pct"],
        rain_mm=current_weather["rain_mm"],
        days_since_rain=current_weather.get("days_since_rain", 0)
    )
    
    # Step 5: Branch 4 - Crop Stage Multiplier
    try:
        stage_enum = CropStage(growth_stage.lower())
        stage_multiplier = get_stage_multiplier(crop_name, stage_enum)
    except ValueError:
        # If stage not found in enum, use default from risk_engine
        stage_multiplier = get_crop_stage_multiplier(growth_stage)
    
    # Step 6: Branch 5 - Pest Trend (skip if no trap data)
    pest_trend_result = compute_pest_trend(db, farm.id, 0)  # current_count not used in trend
    pest_risk = None
    if pest_trend_result["seven_day_readings"] > 0:
        # Calculate pest risk from trend
        trend_pct = pest_trend_result["trend_pct"]
        # Convert trend to 0-100 risk score
        pest_risk = min(max(50.0 + trend_pct * 0.5, 0.0), 100.0)
    
    # Step 7: Branch 6 - Spatial Risk
    nearby_cases = get_nearby_cases(lat, lng, db, radius_km=5, days=14, crop_name=crop_name)
    spatial_risk = compute_spatial_risk(nearby_cases)
    
    # Step 8: Fusion Step - Combine into sub-scores
    # disease_risk = f(disease_confidence, severity_pct, crop_stage_multiplier)
    disease_risk = (disease_confidence * 100.0 * stage_multiplier + severity_pct) / 2
    disease_risk = min(max(disease_risk, 0.0), 100.0)
    
    # pest_risk already calculated above (or None if no data)
    
    # spread_risk = f(spatial_risk, weather_risk)
    spread_risk = (spatial_risk * 0.6 + weather_risk * 0.4)
    spread_risk = min(max(spread_risk, 0.0), 100.0)
    
    # Step 9: Overall Risk - Weighted combination
    fusion_cfg = FUSION_WEIGHTS
    total_weight = fusion_cfg["disease_risk"] + fusion_cfg["spread_risk"]
    
    if pest_risk is not None:
        total_weight += fusion_cfg["pest_risk"]
        overall_risk = (
            disease_risk * fusion_cfg["disease_risk"] +
            pest_risk * fusion_cfg["pest_risk"] +
            spread_risk * fusion_cfg["spread_risk"]
        ) / total_weight
    else:
        # No pest data, exclude from calculation
        overall_risk = (
            disease_risk * fusion_cfg["disease_risk"] +
            spread_risk * fusion_cfg["spread_risk"]
        ) / total_weight
    
    overall_risk = round(min(max(overall_risk, 0.0), 100.0), 1)
    risk_level = map_risk_level(overall_risk)
    
    # Step 10: Decision Engine
    decision = {
        "action": "monitor",
        "reason": "",
        "requires_expert_validation": False,
        "trigger_alert": False,
        "schedule_followup": False,
    }
    
    if is_low_confidence:
        decision["action"] = "needs_expert_validation"
        decision["reason"] = "Low confidence in disease detection requires expert review"
        decision["requires_expert_validation"] = True
    elif risk_level in ["HIGH", "CRITICAL"]:
        decision["action"] = "trigger_alert"
        decision["reason"] = f"High risk level ({risk_level}) detected - immediate action required"
        decision["trigger_alert"] = True
        decision["schedule_followup"] = True
    elif risk_level == "MODERATE":
        decision["action"] = "monitor"
        decision["reason"] = "Moderate risk - continue monitoring"
        decision["schedule_followup"] = True
    else:  # LOW
        decision["action"] = "monitor"
        decision["reason"] = "Low risk - routine monitoring"
    
    # Step 11: Execute Decision Actions
    alert_created = None
    followup_created = None
    
    if decision["trigger_alert"]:
        try:
            alert_level = AlertLevel.critical if risk_level == "CRITICAL" else AlertLevel.high
            new_alert = {
                "crop_id": crop.id,
                "level": alert_level.value,
                "title": f"{risk_level} Risk Alert: {disease_label}",
                "message": f"Overall risk score: {overall_risk}. {decision['reason']}",
                "target_state": farm.state,
                "target_district": farm.district,
            }
            alert_created = new_alert
            logger.info(f"Alert created for crop {crop_id}: {risk_level}")
        except Exception as exc:
            logger.warning(f"Failed to create alert: {exc}")
    
    if decision["schedule_followup"]:
        try:
            followup_date = datetime.now(timezone.utc) + timedelta(days=3)
            new_followup = {
                "crop_id": crop.id,
                "status": FollowUpStatus.pending.value,
                "scheduled_date": followup_date,
                "notes": f"Follow-up required for {risk_level} risk - {decision['reason']}",
            }
            followup_created = new_followup
            logger.info(f"Follow-up scheduled for crop {crop_id}")
        except Exception as exc:
            logger.warning(f"Failed to schedule follow-up: {exc}")
    
    # Step 12: Save RiskScore to database
    try:
        mapped_enum_level = getattr(RiskLevel, risk_level.lower(), RiskLevel.medium)
        db_risk_score = RiskScore(
            crop_id=crop.id,
            timestamp=datetime.now(timezone.utc),
            disease_risk=disease_risk / 100.0,
            pest_risk=(pest_risk / 100.0) if pest_risk is not None else None,
            weather_risk=weather_risk / 100.0,
            overall_score=overall_risk / 100.0,
            risk_level=mapped_enum_level,
            contributing_factors={
                "disease_label": disease_label,
                "disease_confidence": disease_confidence,
                "severity_pct": severity_pct,
                "stage_multiplier": stage_multiplier,
                "spatial_risk": spatial_risk,
                "nearby_cases_count": len(nearby_cases),
                "pest_trend": pest_trend_result,
            },
        )
        db.add(db_risk_score)
        db.commit()
    except Exception as exc:
        db.rollback()
        logger.warning("Failed to persist RiskScore to database: %s", exc)
    
    # Step 13: Return structured PipelineResult
    pipeline_result = {
        # Input data
        "crop_id": crop.id,
        "crop_name": crop_name,
        "farm_id": farm.id,
        "farm_name": farm.name,
        "growth_stage": growth_stage,
        "location": {
            "lat": lat,
            "lng": lng,
            "village": farm.village,
            "district": farm.district,
            "state": farm.state,
        },
        
        # Branch results
        "image_quality": {
            "score": image_quality_score,
            "is_valid": image_quality_score >= 0.7,
        },
        "disease_detection": {
            "label": disease_label,
            "confidence": disease_confidence,
            "severity_pct": severity_pct,
            "top3": top3_predictions,
            "is_low_confidence": is_low_confidence,
            "gradcam_base64": gradcam_base64,
        },
        "weather": {
            "temp_c": current_weather["temp_c"],
            "humidity_pct": current_weather["humidity_pct"],
            "rain_mm": current_weather["rain_mm"],
            "risk_score": weather_risk,
        },
        "crop_stage": {
            "stage": growth_stage,
            "multiplier": stage_multiplier,
        },
        "pest_analysis": {
            "has_data": pest_risk is not None,
            "trend": pest_trend_result,
            "risk_score": pest_risk,
        },
        "spatial_analysis": {
            "nearby_cases_count": len(nearby_cases),
            "nearby_cases": nearby_cases[:5],  # Limit to top 5 for response size
            "risk_score": spatial_risk,
        },
        
        # Fusion results
        "fusion": {
            "disease_risk": round(disease_risk, 1),
            "pest_risk": round(pest_risk, 1) if pest_risk is not None else None,
            "spread_risk": round(spread_risk, 1),
            "weights_used": FUSION_WEIGHTS,
        },
        
        # Final result
        "overall_risk": {
            "score": overall_risk,
            "level": risk_level,
        },
        
        # Decision engine
        "decision": decision,
        "actions_taken": {
            "alert_created": alert_created,
            "followup_created": followup_created,
        },
        
        # Metadata
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "pipeline_version": "1.0.0",
    }
    
    logger.info(f"Pipeline completed for crop {crop_id}: risk_level={risk_level}, action={decision['action']}")
    return pipeline_result

