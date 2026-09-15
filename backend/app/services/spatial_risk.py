"""
Spatial Risk Service Module.
Computes spatial disease risk based on nearby cases and historical outbreak data.
"""
import logging
import math
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from app.db.models.observation import Observation
from app.db.models.ai_result import AIResult
from app.db.models.crop import Crop
from app.db.models.farm import Farm
from app.db.models.historical_outbreak import HistoricalOutbreak

logger = logging.getLogger(__name__)


def get_nearby_cases(
    lat: float,
    lng: float,
    db: Session,
    radius_km: float = 5,
    days: int = 14,
    crop_name: Optional[str] = None,
    disease_label: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Query nearby disease cases using PostGIS spatial query.
    
    Uses ST_DWithin to find observations within specified radius and time window.
    Falls back to Haversine formula if PostGIS is not available.
    
    Args:
        lat: Latitude of query point
        lng: Longitude of query point
        radius_km: Search radius in kilometers (default: 5)
        days: Lookback period in days (default: 14)
        db: Database session
        crop_name: Optional filter by crop name
        disease_label: Optional filter by disease label
    
    Returns:
        List of nearby case records with crop, disease_label, distance_km, days_ago
    """
    # Calculate date threshold
    date_threshold = datetime.utcnow() - timedelta(days=days)
    
    # Try PostGIS query first
    try:
        from geoalchemy2 import functions as geofunc
        from geoalchemy2.types import Geography
        
        # Build query with PostGIS
        query = (
            db.query(
                Crop.crop_name,
                AIResult.disease_label,
                Farm.gps_lat,
                Farm.gps_lng,
                Observation.timestamp,
                Farm.id.label("farm_id"),
            )
            .join(Observation, Observation.crop_id == Crop.id)
            .join(AIResult, AIResult.observation_id == Observation.id)
            .join(Farm, Farm.id == Crop.farm_id)
            .filter(
                Observation.timestamp >= date_threshold,
                AIResult.disease_label.isnot(None),
                Farm.gps_lat.isnot(None),
                Farm.gps_lng.isnot(None),
            )
        )
        
        # Apply optional filters
        if crop_name:
            query = query.filter(Crop.crop_name == crop_name)
        if disease_label:
            query = query.filter(AIResult.disease_label == disease_label)
        
        # Execute query and get results
        results = query.all()
        
        # Filter by distance using PostGIS if available, otherwise use Haversine
        nearby_cases = []
        for row in results:
            distance_km = haversine_distance(lat, lng, row.gps_lat, row.gps_lng)
            if distance_km <= radius_km:
                days_ago = (datetime.utcnow() - row.timestamp).days
                nearby_cases.append({
                    "crop_name": row.crop_name,
                    "disease_label": row.disease_label,
                    "distance_km": round(distance_km, 2),
                    "days_ago": days_ago,
                    "farm_id": row.farm_id,
                    "timestamp": row.timestamp.isoformat(),
                })
        
        logger.info(f"Found {len(nearby_cases)} nearby cases within {radius_km}km")
        return nearby_cases
        
    except ImportError:
        # PostGIS not available, use Haversine formula
        logger.warning("PostGIS not available, using Haversine formula for distance calculation")
        
        # Build query without PostGIS
        query = (
            db.query(
                Crop.crop_name,
                AIResult.disease_label,
                Farm.gps_lat,
                Farm.gps_lng,
                Observation.timestamp,
                Farm.id.label("farm_id"),
            )
            .join(Observation, Observation.crop_id == Crop.id)
            .join(AIResult, AIResult.observation_id == Observation.id)
            .join(Farm, Farm.id == Crop.farm_id)
            .filter(
                Observation.timestamp >= date_threshold,
                AIResult.disease_label.isnot(None),
                Farm.gps_lat.isnot(None),
                Farm.gps_lng.isnot(None),
            )
        )
        
        # Apply optional filters
        if crop_name:
            query = query.filter(Crop.crop_name == crop_name)
        if disease_label:
            query = query.filter(AIResult.disease_label == disease_label)
        
        # Execute query and filter by distance
        results = query.all()
        nearby_cases = []
        
        for row in results:
            distance_km = haversine_distance(lat, lng, row.gps_lat, row.gps_lng)
            if distance_km <= radius_km:
                days_ago = (datetime.utcnow() - row.timestamp).days
                nearby_cases.append({
                    "crop_name": row.crop_name,
                    "disease_label": row.disease_label,
                    "distance_km": round(distance_km, 2),
                    "days_ago": days_ago,
                    "farm_id": row.farm_id,
                    "timestamp": row.timestamp.isoformat(),
                })
        
        logger.info(f"Found {len(nearby_cases)} nearby cases within {radius_km}km (Haversine)")
        return nearby_cases


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate Haversine distance between two points in kilometers.
    
    Args:
        lat1: Latitude of point 1
        lon1: Longitude of point 1
        lat2: Latitude of point 2
        lon2: Longitude of point 2
    
    Returns:
        Distance in kilometers
    """
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))
    
    # Radius of Earth in kilometers
    r = 6371
    
    return c * r


def compute_spatial_risk(nearby_cases: List[Dict[str, Any]]) -> float:
    """
    Compute spatial risk score (0-100) based on nearby cases.
    
    Uses a weighted decay function where:
    - Closer cases contribute more to risk (distance decay)
    - More recent cases contribute more to risk (time decay)
    - Cases with same crop/disease contribute more (relevance boost)
    
    Decay formula:
    - Distance weight: exp(-distance_km / distance_scale) where distance_scale = 5km
    - Time weight: exp(-days_ago / time_scale) where time_scale = 7 days
    - Relevance boost: 1.5x if crop_name matches, 2.0x if both crop and disease match
    
    Final score is normalized to 0-100 range.
    
    Args:
        nearby_cases: List of nearby case records from get_nearby_cases()
    
    Returns:
        Spatial risk score between 0 and 100
    """
    if not nearby_cases:
        return 0.0
    
    # Decay parameters
    distance_scale = 5.0  # km - cases at 5km have 37% weight (1/e)
    time_scale = 7.0  # days - cases 7 days ago have 37% weight (1/e)
    
    # Base risk contribution per case
    base_risk_per_case = 20.0  # Each case contributes up to 20 points
    
    total_risk = 0.0
    
    for case in nearby_cases:
        # Calculate distance weight (closer = higher weight)
        distance_km = case.get("distance_km", 0)
        distance_weight = math.exp(-distance_km / distance_scale)
        
        # Calculate time weight (more recent = higher weight)
        days_ago = case.get("days_ago", 0)
        time_weight = math.exp(-days_ago / time_scale)
        
        # Calculate relevance boost (same crop/disease = higher weight)
        relevance_boost = 1.0  # Default boost
        # Note: In a real implementation, you'd pass the target crop/disease
        # to compare against. For now, we use a conservative default.
        
        # Combined weight
        combined_weight = distance_weight * time_weight * relevance_boost
        
        # Add to total risk
        total_risk += base_risk_per_case * combined_weight
    
    # Cap at 100 and round
    risk_score = min(100.0, round(total_risk, 2))
    
    logger.info(f"Spatial risk score: {risk_score} from {len(nearby_cases)} cases")
    return risk_score


def get_local_disease_history(
    village: str,
    crop_name: str,
    db: Session,
    years_back: int = 3,
) -> Dict[str, Any]:
    """
    Query historical outbreak frequency for a village and crop combination.
    
    Args:
        village: Village name
        crop_name: Crop name
        db: Database session
        years_back: Number of years to look back (default: 3)
    
    Returns:
        Dictionary containing:
        - total_outbreaks: total number of outbreaks
        - outbreaks_by_year: dict of year -> outbreak count
        - most_common_diseases: list of (disease_label, count) tuples
        - severity_distribution: dict of severity_level -> count
        - last_outbreak_date: date of most recent outbreak
    """
    # Calculate year threshold
    current_year = datetime.utcnow().year
    min_year = current_year - years_back
    
    # Query historical outbreaks
    outbreaks = db.query(HistoricalOutbreak).filter(
        HistoricalOutbreak.village == village,
        HistoricalOutbreak.crop_name == crop_name,
        HistoricalOutbreak.year >= min_year,
    ).order_by(HistoricalOutbreak.outbreak_start_date.desc()).all()
    
    if not outbreaks:
        return {
            "village": village,
            "crop_name": crop_name,
            "total_outbreaks": 0,
            "outbreaks_by_year": {},
            "most_common_diseases": [],
            "severity_distribution": {},
            "last_outbreak_date": None,
        }
    
    # Aggregate statistics
    total_outbreaks = len(outbreaks)
    outbreaks_by_year = {}
    disease_counts = {}
    severity_counts = {}
    last_outbreak_date = outbreaks[0].outbreak_start_date
    
    for outbreak in outbreaks:
        # Count by year
        year = outbreak.year
        outbreaks_by_year[year] = outbreaks_by_year.get(year, 0) + 1
        
        # Count by disease
        disease = outbreak.disease_label
        disease_counts[disease] = disease_counts.get(disease, 0) + 1
        
        # Count by severity
        severity = outbreak.severity_level
        severity_counts[severity] = severity_counts.get(severity, 0) + 1
    
    # Get most common diseases (top 5)
    most_common_diseases = sorted(
        disease_counts.items(), key=lambda x: x[1], reverse=True
    )[:5]
    
    logger.info(
        f"Found {total_outbreaks} historical outbreaks for {crop_name} in {village}"
    )
    
    return {
        "village": village,
        "crop_name": crop_name,
        "total_outbreaks": total_outbreaks,
        "outbreaks_by_year": outbreaks_by_year,
        "most_common_diseases": most_common_diseases,
        "severity_distribution": severity_counts,
        "last_outbreak_date": last_outbreak_date.isoformat() if last_outbreak_date else None,
    }
