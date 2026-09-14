"""
Pest Trap Service Module.
Computes pest trends from historical trap readings.
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, Any
from sqlalchemy.orm import Session

from app.db.models.pest_trap import PestTrapReading

logger = logging.getLogger(__name__)


def compute_pest_trend(db: Session, farm_id: str, current_count: int) -> Dict[str, Any]:
    """
    Compute pest trend based on last 7 days of trap readings.
    
    Args:
        db: Database session
        farm_id: Farm ID
        current_count: Current pest count
    
    Returns:
        dict containing:
        - trend_pct: percentage change vs 7-day average
        - direction: "increasing", "decreasing", or "stable"
        - seven_day_avg: average count over last 7 days
        - seven_day_readings: number of readings in last 7 days
    """
    # Calculate date range (last 7 days)
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    
    # Query last 7 days of readings for this farm
    readings = db.query(PestTrapReading).filter(
        PestTrapReading.farm_id == farm_id,
        PestTrapReading.last_checked_at >= seven_days_ago
    ).order_by(PestTrapReading.last_checked_at).all()
    
    if not readings:
        # No historical data, return neutral trend
        logger.info(f"No historical readings for farm {farm_id}, returning stable trend")
        return {
            "trend_pct": 0.0,
            "direction": "stable",
            "seven_day_avg": 0.0,
            "seven_day_readings": 0,
        }
    
    # Calculate 7-day average
    total_count = sum(reading.pest_count for reading in readings)
    seven_day_avg = total_count / len(readings)
    
    # Calculate percentage change
    if seven_day_avg == 0:
        # Avoid division by zero
        if current_count > 0:
            trend_pct = 100.0  # From 0 to something is 100% increase
        else:
            trend_pct = 0.0
    else:
        trend_pct = ((current_count - seven_day_avg) / seven_day_avg) * 100
    
    # Determine direction
    if trend_pct > 10:
        direction = "increasing"
    elif trend_pct < -10:
        direction = "decreasing"
    else:
        direction = "stable"
    
    logger.info(f"Pest trend for farm {farm_id}: {direction} ({trend_pct:.1f}% vs 7-day avg {seven_day_avg:.1f})")
    
    return {
        "trend_pct": round(trend_pct, 2),
        "direction": direction,
        "seven_day_avg": round(seven_day_avg, 2),
        "seven_day_readings": len(readings),
    }
