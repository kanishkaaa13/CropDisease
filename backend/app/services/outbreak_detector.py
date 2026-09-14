"""
Outbreak Detection Service
Detects emerging outbreaks by analyzing week-over-week growth in case counts.
"""
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

logger = logging.getLogger(__name__)


class EmergingOutbreak:
    def __init__(
        self,
        village: str,
        district: str,
        taluka: str,
        crop: str,
        disease: str,
        current_week_cases: int,
        previous_week_cases: int,
        growth_pct: float,
        risk_level: str,
    ):
        self.village = village
        self.district = district
        self.taluka = taluka
        self.crop = crop
        self.disease = disease
        self.current_week_cases = current_week_cases
        self.previous_week_cases = previous_week_cases
        self.growth_pct = growth_pct
        self.risk_level = risk_level


def detect_emerging_outbreaks(
    db: Session,
    growth_threshold: float = 30.0,
    lookback_days: int = 14,
) -> List[EmergingOutbreak]:
    """
    Detects emerging outbreaks by comparing case counts between consecutive weeks.
    
    Args:
        db: Database session
        growth_threshold: Minimum week-over-week growth percentage to flag as outbreak
        lookback_days: Number of days to look back for analysis
    
    Returns:
        List of EmergingOutbreak objects
    """
    try:
        from app.db.models import Observation, AIResult, Crop, Farm

        # Calculate date ranges for current and previous week
        now = datetime.now(timezone.utc)
        current_week_start = now - timedelta(days=7)
        previous_week_start = now - timedelta(days=14)

        # Query cases by village/crop/disease for current week
        current_week_query = (
            db.query(
                Farm.village,
                Farm.district,
                Farm.taluka,
                Crop.crop_name,
                AIResult.disease_label,
                func.count(Observation.id).label("case_count"),
            )
            .join(Observation, Observation.crop_id == Crop.id)
            .join(Farm, Crop.farm_id == Farm.id)
            .join(AIResult, AIResult.observation_id == Observation.id)
            .filter(
                and_(
                    Observation.timestamp >= current_week_start,
                    Observation.timestamp < now,
                    AIResult.disease_label.isnot(None),
                )
            )
            .group_by(Farm.village, Farm.district, Farm.taluka, Crop.crop_name, AIResult.disease_label)
        )

        current_week_data = {
            (
                row.village,
                row.district,
                row.taluka,
                row.crop_name,
                row.disease_label,
            ): row.case_count
            for row in current_week_query.all()
        }

        # Query cases by village/crop/disease for previous week
        previous_week_query = (
            db.query(
                Farm.village,
                Farm.district,
                Farm.taluka,
                Crop.crop_name,
                AIResult.disease_label,
                func.count(Observation.id).label("case_count"),
            )
            .join(Observation, Observation.crop_id == Crop.id)
            .join(Farm, Crop.farm_id == Farm.id)
            .join(AIResult, AIResult.observation_id == Observation.id)
            .filter(
                and_(
                    Observation.timestamp >= previous_week_start,
                    Observation.timestamp < current_week_start,
                    AIResult.disease_label.isnot(None),
                )
            )
            .group_by(Farm.village, Farm.district, Farm.taluka, Crop.crop_name, AIResult.disease_label)
        )

        previous_week_data = {
            (
                row.village,
                row.district,
                row.taluka,
                row.crop_name,
                row.disease_label,
            ): row.case_count
            for row in previous_week_query.all()
        }

        # Calculate growth and identify outbreaks
        outbreaks = []
        for key, current_count in current_week_data.items():
            previous_count = previous_week_data.get(key, 0)
            
            # Only consider if there were cases in previous week (avoid division by zero)
            if previous_count > 0:
                growth_pct = ((current_count - previous_count) / previous_count) * 100
                
                if growth_pct >= growth_threshold:
                    village, district, taluka, crop, disease = key
                    
                    # Determine risk level based on growth
                    if growth_pct >= 100:
                        risk_level = "CRITICAL"
                    elif growth_pct >= 50:
                        risk_level = "HIGH"
                    else:
                        risk_level = "MODERATE"
                    
                    outbreaks.append(
                        EmergingOutbreak(
                            village=village,
                            district=district,
                            taluka=taluka,
                            crop=crop,
                            disease=disease,
                            current_week_cases=current_count,
                            previous_week_cases=previous_count,
                            growth_pct=round(growth_pct, 1),
                            risk_level=risk_level,
                        )
                    )

        # Sort by growth percentage descending
        outbreaks.sort(key=lambda x: x.growth_pct, reverse=True)
        
        logger.info(f"Detected {len(outbreaks)} emerging outbreaks")
        return outbreaks

    except Exception as exc:
        logger.error(f"Error detecting outbreaks: {exc}")
        raise exc


def get_district_outbreak_summary(
    db: Session,
    district: str,
    growth_threshold: float = 30.0,
) -> Dict[str, any]:
    """
    Get outbreak summary for a specific district.
    
    Args:
        db: Database session
        district: District name
        growth_threshold: Minimum growth percentage to flag as outbreak
    
    Returns:
        Dictionary with outbreak summary statistics
    """
    try:
        outbreaks = detect_emerging_outbreaks(db, growth_threshold)
        district_outbreaks = [o for o in outbreaks if o.district == district]
        
        return {
            "district": district,
            "total_outbreaks": len(district_outbreaks),
            "high_risk_outbreaks": len([o for o in district_outbreaks if o.risk_level in ["HIGH", "CRITICAL"]]),
            "avg_growth_pct": round(sum(o.growth_pct for o in district_outbreaks) / len(district_outbreaks), 1) if district_outbreaks else 0,
            "affected_villages": len(set(o.village for o in district_outbreaks)),
        }
    except Exception as exc:
        logger.error(f"Error getting district outbreak summary: {exc}")
        raise exc
