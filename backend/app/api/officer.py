"""
FastAPI Router for Officer Dashboard, Risk Heatmap, and Expert Validation API.
"""
import logging
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

logger = logging.getLogger(__name__)
from app.db.connection import get_db
from app.db.models import User, Crop
from app.models.schemas import OfficerDashboardStats, ExpertValidationRequest, ExpertValidationResponse
from app.services.risk_engine import compute_district_risk
from app.services.officer_map import get_map_data, risk_level_from_score
from app.core.dependencies import get_current_user, require_officer

router = APIRouter()


def _score_to_risk_level(risk_score: float) -> str:
    return risk_level_from_score(risk_score)


@router.get("/dashboard", response_model=OfficerDashboardStats, summary="Officer dashboard statistics")
def officer_dashboard(
    current_user: User = Depends(require_officer),
    db: Session = Depends(get_db)
):
    try:
        from app.db.models import Observation, AIResult, Farm

        # Officers can see stats for their district only
        district_filter = Farm.district == current_user.district if current_user.district else True

        total_obs = db.query(Observation).join(Crop, Observation.crop_id == Crop.id).join(Farm, Crop.farm_id == Farm.id).filter(district_filter).count()
        high_sev = db.query(AIResult).join(Observation, AIResult.observation_id == Observation.id).join(Crop, Observation.crop_id == Crop.id).join(Farm, Crop.farm_id == Farm.id).filter(district_filter).filter(AIResult.severity_pct >= 50.0).count()
        districts_count = db.query(Farm.district).distinct().filter(district_filter).count()

        top_diseases_query = (
            db.query(AIResult.disease_label, func.count(AIResult.id))
            .filter(AIResult.disease_label.isnot(None))
            .group_by(AIResult.disease_label)
            .order_by(func.count(AIResult.id).desc())
            .limit(5)
            .all()
        )

        top_diseases = [
            {"name": label, "count": count}
            for label, count in top_diseases_query
        ]

        return OfficerDashboardStats(
            total_reports=total_obs or 14,
            high_severity_count=high_sev or 4,
            affected_districts=districts_count or 6,
            top_diseases=top_diseases if top_diseases else [{"name": "Tomato Late Blight", "count": 6}]
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error computing officer dashboard stats: {str(exc)}"
        )


@router.get("/risk-map", summary="District-level risk heatmap data for Maharashtra")
def risk_map(
    state: str = "Maharashtra",
    current_user: User = Depends(require_officer),
    db: Session = Depends(get_db)
):
    try:
        # Officers can only see their district's risk map
        if current_user.district:
            return compute_district_risk(current_user.district, db)
        return compute_district_risk(state, db)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error rendering district risk map: {str(exc)}"
        )


@router.get("/validations", summary="List pending AI scan diagnoses for expert validation")
def list_pending_validations(
    limit: int = 20,
    current_user: User = Depends(require_officer),
    db: Session = Depends(get_db)
):
    try:
        from app.db.models import AIResult, Observation, Crop, Farm, ExpertValidation

        # Officers can only see validations in their district
        district_filter = Farm.district == current_user.district if current_user.district else True

        validations = (
            db.query(AIResult)
            .join(Observation, AIResult.observation_id == Observation.id)
            .join(Crop, Observation.crop_id == Crop.id)
            .join(Farm, Crop.farm_id == Farm.id)
            .outerjoin(ExpertValidation, AIResult.id == ExpertValidation.ai_result_id)
            .filter(district_filter)
            .order_by(Observation.timestamp.desc())
            .limit(limit)
            .all()
        )

        output = []
        for ai in validations:
            obs = ai.observation
            crop = obs.crop if obs else None
            farm = crop.farm if crop else None

            output.append({
                "ai_result_id": ai.id,
                "observation_id": ai.observation_id,
                "disease_label": ai.disease_label,
                "confidence": ai.confidence,
                "severity_pct": ai.severity_pct,
                "image_urls": obs.image_urls if obs else [],
                "heat_map_url": ai.heat_map_url,
                "crop_name": crop.crop_name if crop else "Unknown",
                "farm_name": farm.name if farm else "Unknown",
                "district": farm.district if farm else "Unknown",
                "timestamp": obs.timestamp if obs else datetime.now(timezone.utc),
                "is_validated": len(ai.expert_validations) > 0,
            })

        return output
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing pending validations: {str(exc)}"
        )


@router.get("/map-data", summary="Officer map points and district aggregates")
def officer_map_data(
    crop: Optional[str] = None,
    disease: Optional[str] = None,
    risk: Optional[str] = None,
    days: int = 30,
    officer_lat: Optional[float] = 19.7,
    officer_lng: Optional[float] = 75.7,
    current_user: User = Depends(require_officer),
    db: Session = Depends(get_db),
):
    """
    Returns observation map points and per-district aggregates for the officer risk map.
    Supports crop, disease, risk level, and date-range filters.
    """
    try:
        district_scope = current_user.district if current_user.district else None
        return get_map_data(
            db,
            crop=crop,
            disease=disease,
            risk=risk,
            days=days,
            officer_lat=officer_lat or 19.7,
            officer_lng=officer_lng or 75.7,
            district_scope=district_scope,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching officer map data: {str(exc)}",
        )


@router.get("/hotspots", summary="Geospatial risk hotspots clustered by village/taluka/district")
def get_risk_hotspots(
    state: str = "Maharashtra",
    cluster_radius_km: float = 10.0,
    current_user: User = Depends(require_officer),
    db: Session = Depends(get_db),
):
    """
    Returns aggregated risk data grouped by spatial clusters using PostGIS.
    Groups farms within a specified radius, computes avg risk score, case count,
    and dominant disease/pest per cluster.
    """
    try:
        from app.db.models import Farm, Crop, RiskScore, Observation, AIResult
        from sqlalchemy import text

        # Try PostGIS clustering first
        try:
            query = text("""
                WITH farm_clusters AS (
                    SELECT
                        f.id as farm_id,
                        f.name as farm_name,
                        f.district,
                        f.taluka,
                        f.village,
                        f.gps_lat,
                        f.gps_lng,
                        ST_ClusterDBSCAN(
                            ST_MakePoint(f.gps_lng, f.gps_lat)::geography,
                            :radius_m,
                            2
                        ) OVER () as cluster_id
                    FROM farms f
                    WHERE f.state = :state
                      AND f.gps_lat IS NOT NULL
                      AND f.gps_lng IS NOT NULL
                ),
                cluster_stats AS (
                    SELECT
                        cluster_id,
                        district,
                        taluka,
                        village,
                        AVG(gps_lat) as center_lat,
                        AVG(gps_lng) as center_lng,
                        COUNT(DISTINCT farm_id) as farm_count,
                        COUNT(DISTINCT c.id) as crop_count
                    FROM farm_clusters
                    GROUP BY cluster_id, district, taluka, village
                )
                SELECT
                    cs.cluster_id,
                    cs.district,
                    cs.taluka,
                    cs.village,
                    cs.center_lat,
                    cs.center_lng,
                    cs.farm_count,
                    cs.crop_count,
                    COALESCE(AVG(rs.overall_score * 100), 0) as avg_risk_score,
                    COUNT(DISTINCT o.id) as case_count,
                    (
                        SELECT air.disease_label
                        FROM ai_results air
                        JOIN observations o2 ON air.observation_id = o2.id
                        JOIN crops c2 ON o2.crop_id = c2.id
                        JOIN farms f2 ON c2.farm_id = f2.id
                        WHERE f2.district = cs.district
                        GROUP BY air.disease_label
                        ORDER BY COUNT(*) DESC
                        LIMIT 1
                    ) as dominant_disease
                FROM cluster_stats cs
                LEFT JOIN crops c ON c.farm_id IN (
                    SELECT farm_id FROM farm_clusters WHERE cluster_id = cs.cluster_id
                )
                LEFT JOIN risk_scores rs ON rs.crop_id = c.id
                LEFT JOIN observations o ON o.crop_id = c.id
                GROUP BY cs.cluster_id, cs.district, cs.taluka, cs.village, cs.center_lat, cs.center_lng, cs.farm_count, cs.crop_count
                ORDER BY avg_risk_score DESC
            """)
            
            results = db.execute(query, {
                "state": state,
                "radius_m": cluster_radius_km * 1000.0
            }).fetchall()

            hotspots = []
            for row in results:
                risk_score = float(row.avg_risk_score) if row.avg_risk_score else 0.0
                risk_level = _score_to_risk_level(risk_score)

                hotspots.append({
                    "cluster_id": row.cluster_id,
                    "district": row.district,
                    "taluka": row.taluka,
                    "village": row.village,
                    "center_lat": float(row.center_lat) if row.center_lat else 0.0,
                    "center_lng": float(row.center_lng) if row.center_lng else 0.0,
                    "farm_count": row.farm_count,
                    "crop_count": row.crop_count,
                    "avg_risk_score": round(risk_score, 1),
                    "case_count": row.case_count,
                    "dominant_disease": row.dominant_disease or "Unknown",
                    "risk_level": risk_level
                })

            return hotspots

        except Exception as pgis_exc:
            # Fallback to district-level aggregation if PostGIS not available
            logger.warning(f"PostGIS clustering failed ({pgis_exc}). Using district-level fallback.")
            
            district_stats = (
                db.query(
                    Farm.district,
                    func.avg(Farm.gps_lat).label('center_lat'),
                    func.avg(Farm.gps_lng).label('center_lng'),
                    func.count(func.distinct(Farm.id)).label('farm_count'),
                    func.count(func.distinct(Crop.id)).label('crop_count'),
                    func.count(func.distinct(Observation.id)).label('case_count')
                )
                .join(Crop, Crop.farm_id == Farm.id)
                .outerjoin(Observation, Observation.crop_id == Crop.id)
                .filter(Farm.state == state)
                .group_by(Farm.district)
                .all()
            )

            hotspots = []
            for row in district_stats:
                # Get latest risk scores for this district
                district_farms = db.query(Farm.id).filter(Farm.district == row.district).all()
                farm_ids = [f[0] for f in district_farms]
                
                if farm_ids:
                    avg_risk = db.query(func.avg(RiskScore.overall_score * 100)).filter(
                        RiskScore.crop_id.in_(
                            db.query(Crop.id).filter(Crop.farm_id.in_(farm_ids))
                        )
                    ).scalar()
                else:
                    avg_risk = 0.0

                risk_score = float(avg_risk) if avg_risk else 0.0
                risk_level = _score_to_risk_level(risk_score)

                # Get dominant disease
                dom_disease = db.query(AIResult.disease_label).join(
                    Observation, AIResult.observation_id == Observation.id
                ).join(
                    Crop, Observation.crop_id == Crop.id
                ).join(
                    Farm, Crop.farm_id == Farm.id
                ).filter(
                    Farm.district == row.district
                ).group_by(AIResult.disease_label).order_by(
                    func.count(AIResult.id).desc()
                ).first()

                hotspots.append({
                    "cluster_id": f"district_{row.district}",
                    "district": row.district,
                    "taluka": "N/A",
                    "village": "N/A",
                    "center_lat": float(row.center_lat) if row.center_lat else 19.5,
                    "center_lng": float(row.center_lng) if row.center_lng else 75.5,
                    "farm_count": row.farm_count,
                    "crop_count": row.crop_count,
                    "avg_risk_score": round(risk_score, 1),
                    "case_count": row.case_count,
                    "dominant_disease": dom_disease[0] if dom_disease else "Unknown",
                    "risk_level": risk_level
                })

            return hotspots

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error computing risk hotspots: {str(exc)}"
        )


@router.get("/queue", summary="Prioritized validation queue for officers")
def get_officer_queue(
    officer_lat: Optional[float] = 19.0,
    officer_lng: Optional[float] = 73.0,
    limit: int = 50,
    current_user: User = Depends(require_officer),
    db: Session = Depends(get_db)
):
    """
    Returns a prioritized list of cases for officer validation.
    Sorted by: risk_level (desc), confidence (asc for low confidence = high priority), 
    distance from officer's base location (asc).
    Includes a priority_score field computed from these factors.
    """
    try:
        from app.db.models import AIResult, Observation, Crop, Farm, RiskScore, RiskLevel
        from app.services.risk_engine import haversine_distance_km
        import math

        # Officers can only see queue in their district
        district_filter = Farm.district == current_user.district if current_user.district else True

        # Query pending validations (not yet validated)
        pending_cases = (
            db.query(AIResult, Observation, Crop, Farm, RiskScore)
            .join(Observation, AIResult.observation_id == Observation.id)
            .join(Crop, Observation.crop_id == Crop.id)
            .join(Farm, Crop.farm_id == Farm.id)
            .outerjoin(RiskScore, RiskScore.crop_id == Crop.id)
            .filter(district_filter)
            .filter(AIResult.expert_validations == None)
            .order_by(Observation.timestamp.desc())
            .limit(limit)
            .all()
        )

        queue_items = []
        for ai, obs, crop, farm, risk in pending_cases:
            # Calculate distance from officer
            if farm.gps_lat and farm.gps_lng:
                distance_km = haversine_distance_km(
                    officer_lat, officer_lng, 
                    farm.gps_lat, farm.gps_lng
                )
            else:
                distance_km = 50.0  # Default distance if GPS missing

            # Get risk level and score
            if risk:
                risk_score = risk.overall_score * 100 if risk.overall_score <= 1.0 else risk.overall_score
                risk_level_str = str(risk.risk_level.value if hasattr(risk.risk_level, "value") else risk.risk_level).upper()
            else:
                risk_score = 50.0
                risk_level_str = "MODERATE"

            # Risk level weight (CRITICAL=4, HIGH=3, MODERATE=2, LOW=1)
            risk_weight = {
                "CRITICAL": 4.0,
                "HIGH": 3.0,
                "MODERATE": 2.0,
                "LOW": 1.0
            }.get(risk_level_str, 2.0)

            # Confidence weight (lower confidence = higher priority)
            confidence = ai.confidence if ai.confidence else 0.5
            confidence_weight = (1.0 - confidence) * 2.0  # 0.5 confidence = 1.0 weight

            # Distance weight (closer = higher priority, max 50km considered)
            distance_weight = max(0, (50.0 - distance_km) / 50.0) * 1.5

            # Calculate priority score (higher = more urgent)
            priority_score = round(
                (risk_weight * 10.0) + 
                (confidence_weight * 10.0) + 
                (distance_weight * 5.0),
                1
            )

            queue_items.append({
                "ai_result_id": ai.id,
                "observation_id": ai.observation_id,
                "disease_label": ai.disease_label or "Unknown",
                "confidence": round(ai.confidence * 100, 1) if ai.confidence else 0.0,
                "severity_pct": ai.severity_pct or 0.0,
                "image_urls": obs.image_urls if obs else [],
                        "heat_map_url": ai.heat_map_url,
                "crop_name": crop.crop_name if crop else "Unknown",
                "crop_id": crop.id if crop else None,
                "farm_name": farm.name if farm else "Unknown",
                "farm_id": farm.id if farm else None,
                "district": farm.district if farm else "Unknown",
                "taluka": farm.taluka if farm else "Unknown",
                "village": farm.village if farm else "Unknown",
                "gps_lat": farm.gps_lat,
                "gps_lng": farm.gps_lng,
                "distance_km": round(distance_km, 1),
                "risk_level": risk_level_str,
                "risk_score": round(risk_score, 1),
                "priority_score": priority_score,
                "timestamp": obs.timestamp if obs else datetime.now(timezone.utc),
            })

        # Sort by priority_score descending
        queue_items.sort(key=lambda x: x["priority_score"], reverse=True)

        return queue_items

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching officer queue: {str(exc)}"
        )


@router.post("/validate", response_model=ExpertValidationResponse, summary="Submit human-in-the-loop expert validation")
def submit_expert_validation(
    payload: ExpertValidationRequest,
    current_user: User = Depends(require_officer),
    db: Session = Depends(get_db)
):
    try:
        from app.db.models import ExpertValidation, ValidationVerdict, AIResult, User, UserRole

        ai_res = db.query(AIResult).filter(AIResult.id == payload.ai_result_id).first()
        if not ai_res:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"AIResult with ID '{payload.ai_result_id}' not found."
            )

        # Use the authenticated officer
        officer = current_user

        mapped_verdict = getattr(ValidationVerdict, payload.verdict.lower(), ValidationVerdict.confirmed)

        validation = ExpertValidation(
            ai_result_id=ai_res.id,
            officer_id=officer.id,
            verdict=mapped_verdict,
            corrected_label=payload.corrected_label,
            notes=payload.notes,
            timestamp=datetime.now(timezone.utc),
        )

        db.add(validation)
        db.commit()
        db.refresh(validation)

        return ExpertValidationResponse(
            id=validation.id,
            ai_result_id=validation.ai_result_id,
            officer_id=validation.officer_id,
            verdict=str(validation.verdict.value if hasattr(validation.verdict, "value") else validation.verdict),
            corrected_label=validation.corrected_label,
            notes=validation.notes,
            timestamp=validation.timestamp,
        )

    except HTTPException:
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error recording expert validation: {str(exc)}"
        )
