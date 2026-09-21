"""
FastAPI Router for Government Command Center & National Alert Broadcast API.
"""
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.connection import get_db
from app.db.models import User
from app.models.schemas import AdminCommandStats, AdminAlertRequest
from app.services.outbreak_detector import detect_emerging_outbreaks
from app.data.maharashtra_locations import MAHARASHTRA_LOCATIONS
from app.core.dependencies import require_admin

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/stats", response_model=AdminCommandStats, summary="National & State Command Center KPIs")
def admin_command_stats(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    try:
        import json
        from pathlib import Path
        from app.db.models import User, UserRole, Observation, Farm, Alert

        total_farmers = db.query(User).filter(User.role == UserRole.farmer).count()
        total_reports = db.query(Observation).count()
        states_count = db.query(Farm.state).distinct().count()
        alerts_count = db.query(Alert).count()

        # Dynamic model accuracy from metrics artifact if available
        accuracy = None
        weights_metrics = Path(__file__).parent.parent / "ml" / "weights" / "metrics.json"
        ml_metrics = Path(__file__).parent.parent.parent.parent / "ml-training" / "output" / "metrics.json"
        for p in (weights_metrics, ml_metrics):
            if p.exists():
                try:
                    with open(p, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        accuracy = round(float(data.get("accuracy", 0.0)) * 100, 1)
                        break
                except Exception:
                    pass

        return AdminCommandStats(
            total_farmers=total_farmers,
            total_reports=total_reports,
            states_covered=states_count,
            model_accuracy=accuracy,
            alerts_issued=alerts_count,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching admin command stats: {str(exc)}"
        )



@router.post("/alert", summary="Broadcast emergency advisory alert to targeted district/state")
def broadcast_admin_alert(
    payload: AdminAlertRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    try:
        from app.db.models import Alert, AlertLevel, Crop

        target_crop = None
        if payload.crop_id:
            target_crop = db.query(Crop).filter(Crop.id == payload.crop_id).first()

        if not target_crop:
            # Pick first active crop if none specified
            target_crop = db.query(Crop).first()

        mapped_level = getattr(AlertLevel, payload.level.lower(), AlertLevel.warning)

        new_alert = Alert(
            crop_id=target_crop.id if target_crop else "system-wide",
            risk_score_id=None,
            level=mapped_level,
            title=payload.title,
            message=payload.message,
            acknowledged=False,
            created_at=datetime.now(timezone.utc),
        )

        db.add(new_alert)
        db.commit()
        db.refresh(new_alert)

        return {
            "status": "success",
            "alert_id": new_alert.id,
            "title": new_alert.title,
            "level": str(new_alert.level.value if hasattr(new_alert.level, "value") else new_alert.level),
            "message": new_alert.message,
            "broadcast_timestamp": new_alert.created_at,
        }

    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error broadcasting emergency alert: {str(exc)}"
        )


@router.get("/summary", summary="Admin dashboard summary statistics")
def get_admin_summary(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Returns summary statistics for the admin dashboard:
    - Total monitored farms
    - Active alerts
    - High-risk villages
    - Disease outbreaks detected
    - Pending expert validations
    """
    try:
        from app.db.models import Farm, Crop, Observation, AIResult, Alert, ExpertValidation

        # Total monitored farms
        total_farms = db.query(Farm).count()

        # Active alerts (last 7 days)
        seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
        active_alerts = db.query(Alert).filter(Alert.created_at >= seven_days_ago).count()

        # High-risk villages (risk score >= 60)
        from app.db.models import RiskScore
        high_risk_villages = (
            db.query(Farm.village)
            .join(Crop, Crop.farm_id == Farm.id)
            .join(RiskScore, RiskScore.crop_id == Crop.id)
            .filter(RiskScore.overall_score >= 0.6)
            .distinct()
            .count()
        )

        # Disease outbreaks detected (unique disease labels in last 30 days)
        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
        disease_outbreaks = (
            db.query(AIResult.disease_label)
            .join(Observation, AIResult.observation_id == Observation.id)
            .filter(Observation.timestamp >= thirty_days_ago)
            .filter(AIResult.disease_label.isnot(None))
            .distinct()
            .count()
        )

        # Pending expert validations
        pending_validations = (
            db.query(AIResult)
            .filter(AIResult.expert_validations == None)
            .count()
        )

        return {
            "total_monitored_farms": total_farms or 0,
            "active_alerts": active_alerts or 0,
            "high_risk_villages": high_risk_villages or 0,
            "disease_outbreaks_detected": disease_outbreaks or 0,
            "pending_expert_validations": pending_validations or 0,
            "source": "real"
        }

    except Exception as exc:
        logger.error(f"Error fetching admin summary: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching admin summary: {str(exc)}"
        )


@router.get("/district-analytics", summary="District-level analytics data")
def get_district_analytics(
    state: str = "Maharashtra",
    sort_by: str = "risk_score",
    sort_order: str = "desc",
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Returns district-level analytics including:
    - District name
    - Dominant crop
    - Dominant threat/disease
    - Average risk score
    - Case count
    """
    try:
        from app.db.models import Farm, Crop, Observation, AIResult, RiskScore

        # Query district-level data
        district_data = (
            db.query(
                Farm.district,
                func.count(func.distinct(Farm.id)).label("farm_count"),
                func.count(func.distinct(Observation.id)).label("case_count"),
            )
            .join(Crop, Crop.farm_id == Farm.id)
            .outerjoin(Observation, Observation.crop_id == Crop.id)
            .filter(Farm.state == state)
            .group_by(Farm.district)
            .all()
        )

        results = []
        for row in district_data:
            district = row.district
            
            # Get dominant crop for this district
            dominant_crop_query = (
                db.query(Crop.crop_name, func.count(Crop.id).label("count"))
                .join(Farm, Farm.id == Crop.farm_id)
                .filter(Farm.district == district)
                .group_by(Crop.crop_name)
                .order_by(func.count(Crop.id).desc())
                .first()
            )
            dominant_crop = dominant_crop_query.crop_name if dominant_crop_query else "Unknown"

            # Get dominant disease for this district
            dominant_disease_query = (
                db.query(AIResult.disease_label, func.count(AIResult.id).label("count"))
                .join(Observation, AIResult.observation_id == Observation.id)
                .join(Crop, Observation.crop_id == Crop.id)
                .join(Farm, Crop.farm_id == Farm.id)
                .filter(Farm.district == district)
                .filter(AIResult.disease_label.isnot(None))
                .group_by(AIResult.disease_label)
                .order_by(func.count(AIResult.id).desc())
                .first()
            )
            dominant_disease = dominant_disease_query.disease_label if dominant_disease_query else "Unknown"

            # Get average risk score for this district
            avg_risk_query = (
                db.query(func.avg(RiskScore.overall_score))
                .join(Crop, RiskScore.crop_id == Crop.id)
                .join(Farm, Crop.farm_id == Farm.id)
                .filter(Farm.district == district)
                .scalar()
            )
            avg_risk_score = (avg_risk_query * 100) if avg_risk_query else 50.0

            results.append({
                "district": district,
                "dominant_crop": dominant_crop,
                "dominant_threat": dominant_disease,
                "risk_score": round(avg_risk_score, 1),
                "case_count": row.case_count,
                "farm_count": row.farm_count,
            })

        # Sort results
        reverse_order = sort_order.lower() == "desc"
        results.sort(key=lambda x: x.get(sort_by, 0), reverse=reverse_order)

        return results

    except Exception as exc:
        logger.error(f"Error fetching district analytics: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching district analytics: {str(exc)}"
        )


@router.get("/outbreaks", summary="Emerging outbreaks detection")
def get_emerging_outbreaks(
    growth_threshold: float = 30.0,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Returns emerging outbreaks detected by week-over-week growth analysis.
    Flags any village/cluster where case count grew >30% week-over-week.
    """
    try:
        outbreaks = detect_emerging_outbreaks(db, growth_threshold)
        
        return [
            {
                "village": o.village,
                "district": o.district,
                "taluka": o.taluka,
                "crop": o.crop,
                "disease": o.disease,
                "current_week_cases": o.current_week_cases,
                "previous_week_cases": o.previous_week_cases,
                "growth_pct": o.growth_pct,
                "risk_level": o.risk_level,
            }
            for o in outbreaks
        ]

    except Exception as exc:
        logger.error(f"Error fetching emerging outbreaks: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching emerging outbreaks: {str(exc)}"
        )


@router.get("/risk-trend", summary="Statewide risk trend over time")
def get_risk_trend(
    state: str = "Maharashtra",
    days: int = 30,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Returns time-series data for statewide risk trend over the specified number of days.
    """
    try:
        from app.db.models import RiskScore, Crop, Farm
        from sqlalchemy import and_

        start_date = datetime.now(timezone.utc) - timedelta(days=days)

        # Query daily average risk scores
        from sqlalchemy import cast, Date

        results = (
            db.query(
                cast(RiskScore.created_at, Date).label("entry_date"),
                func.avg(RiskScore.overall_score).label("avg_risk"),
                func.count(RiskScore.id).label("case_count"),
            )
            .filter(RiskScore.created_at >= start_date)
            .group_by(cast(RiskScore.created_at, Date))
            .order_by(cast(RiskScore.created_at, Date).asc())
            .all()
        )

        trend = []
        if results:
            for r in results:
                date_str = r.entry_date.strftime("%Y-%m-%d") if hasattr(r.entry_date, "strftime") else str(r.entry_date)
                trend.append({
                    "date": date_str,
                    "avg_risk_score": round(float(r.avg_risk) * 100, 1),
                    "case_count": int(r.case_count),
                })
        else:
            for i in range(days):
                date_str = (start_date + timedelta(days=i)).strftime("%Y-%m-%d")
                trend.append({
                    "date": date_str,
                    "avg_risk_score": 0.0,
                    "case_count": 0,
                })

        return trend


    except Exception as exc:
        logger.error(f"Error fetching risk trend: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching risk trend: {str(exc)}"
        )


@router.get("/hotspots", summary="Risk hotspot data for map visualization")
def get_hotspots(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Returns hotspot data for each Maharashtra location including:
    - Location name, lat/lng, district, climate zone
    - Current risk level (LOW/MODERATE/HIGH/CRITICAL)
    - Dominant disease or pest
    - Scan count
    - 7-day trend data (simplified for demo)
    """
    try:
        from app.db.models import Farm, Crop, Observation, AIResult, RiskScore
        from sqlalchemy import and_

        hotspots = []

        for location in MAHARASHTRA_LOCATIONS:
            # Find farms near this location (within 0.5 degrees for demo)
            lat_range = (location["lat"] - 0.5, location["lat"] + 0.5)
            lng_range = (location["lng"] - 0.5, location["lng"] + 0.5)

            nearby_farms = (
                db.query(Farm.id)
                .filter(
                    and_(
                        Farm.gps_lat >= lat_range[0],
                        Farm.gps_lat <= lat_range[1],
                        Farm.gps_lng >= lng_range[0],
                        Farm.gps_lng <= lng_range[1]
                    )
                )
                .all()
            )

            if not nearby_farms:
                # No farms near this location, use default low risk
                hotspots.append({
                    "name": location["name"],
                    "lat": location["lat"],
                    "lng": location["lng"],
                    "district": location["district"],
                    "climate_zone": location["climate_zone"],
                    "risk_level": "LOW",
                    "dominant_disease_or_pest": "No data",
                    "scan_count": 0,
                    "trend_data": [0, 0, 0, 0, 0, 0, 0],
                    "source": "none"
                })
                continue

            farm_ids = [f[0] for f in nearby_farms]

            # Get observations for these farms in the last 7 days
            seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
            observations = (
                db.query(Observation)
                .join(Crop, Crop.id == Observation.crop_id)
                .filter(Crop.farm_id.in_(farm_ids))
                .filter(Observation.timestamp >= seven_days_ago)
                .all()
            )

            scan_count = len(observations)

            if scan_count == 0:
                hotspots.append({
                    "name": location["name"],
                    "lat": location["lat"],
                    "lng": location["lng"],
                    "district": location["district"],
                    "climate_zone": location["climate_zone"],
                    "risk_level": "LOW",
                    "dominant_disease_or_pest": "No recent scans",
                    "scan_count": 0,
                    "trend_data": [0, 0, 0, 0, 0, 0, 0],
                    "source": "none"
                })
                continue

            # Get AI results for these observations
            obs_ids = [obs.id for obs in observations]
            ai_results = (
                db.query(AIResult)
                .filter(AIResult.observation_id.in_(obs_ids))
                .all()
            )

            # Calculate average risk score
            risk_scores = (
                db.query(RiskScore.overall_score)
                .join(Crop, Crop.id == RiskScore.crop_id)
                .filter(Crop.farm_id.in_(farm_ids))
                .filter(RiskScore.created_at >= seven_days_ago)
                .all()
            )

            avg_risk = sum([r[0] for r in risk_scores]) / len(risk_scores) if risk_scores else 0.3

            # Determine risk level
            if avg_risk >= 0.7:
                risk_level = "CRITICAL"
            elif avg_risk >= 0.5:
                risk_level = "HIGH"
            elif avg_risk >= 0.3:
                risk_level = "MODERATE"
            else:
                risk_level = "LOW"

            # Find dominant disease or pest
            disease_counts = {}
            pest_counts = {}

            for ai_result in ai_results:
                if ai_result.disease_label:
                    disease_counts[ai_result.disease_label] = disease_counts.get(ai_result.disease_label, 0) + 1
                if ai_result.pest_label:
                    pest_counts[ai_result.pest_label] = pest_counts.get(ai_result.pest_label, 0) + 1

            dominant_disease = max(disease_counts.items(), key=lambda x: x[1])[0] if disease_counts else None
            dominant_pest = max(pest_counts.items(), key=lambda x: x[1])[0] if pest_counts else None

            # Use disease skew from location data to decide which to show
            if location["disease_skew"] == "fungal":
                dominant = dominant_disease or dominant_pest or "Unknown"
            elif location["disease_skew"] == "pest":
                dominant = dominant_pest or dominant_disease or "Unknown"
            else:
                # Mixed - show whichever has higher count
                disease_max = max(disease_counts.values()) if disease_counts else 0
                pest_max = max(pest_counts.values()) if pest_counts else 0
                dominant = dominant_disease if disease_max >= pest_max else dominant_pest or "Unknown"

            # Generate simplified 7-day trend data
            trend_data = []
            for day_offset in range(6, -1, -1):
                day_start = datetime.now(timezone.utc) - timedelta(days=day_offset + 1)
                day_end = datetime.now(timezone.utc) - timedelta(days=day_offset)
                
                day_scans = (
                    db.query(Observation)
                    .join(Crop, Crop.id == Observation.crop_id)
                    .filter(Crop.farm_id.in_(farm_ids))
                    .filter(Observation.timestamp >= day_start)
                    .filter(Observation.timestamp < day_end)
                    .count()
                )
                trend_data.append(day_scans)

            hotspots.append({
                "name": location["name"],
                "lat": location["lat"],
                "lng": location["lng"],
                "district": location["district"],
                "climate_zone": location["climate_zone"],
                "risk_level": risk_level,
                "dominant_disease_or_pest": dominant,
                "scan_count": scan_count,
                "trend_data": trend_data,
                "source": "real"
            })

        return hotspots

    except Exception as exc:
        logger.error(f"Error fetching hotspots: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching hotspots: {str(exc)}"
        )
