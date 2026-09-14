"""
Crop Stage Encoding Module.
Defines crop growth stages, susceptibility multipliers, and automatic stage estimation.
"""
import logging
from datetime import date, timedelta
from enum import Enum
from typing import Dict, Tuple

logger = logging.getLogger(__name__)


class CropStage(Enum):
    """Crop growth stages."""
    SOWING = "sowing"
    VEGETATIVE = "vegetative"
    FLOWERING = "flowering"
    FRUITING = "fruiting"
    MATURITY = "maturity"


# Stage susceptibility multipliers
# NOTE: Exact multipliers should be reviewed by a domain expert.
# These are based on general agronomic knowledge that flowering/fruiting stages
# are generally more disease-vulnerable than sowing/early vegetative stages.
STAGE_SUSCEPTIBILITY: Dict[Tuple[str, CropStage], float] = {
    # Cotton
    ("cotton", CropStage.SOWING): 0.8,
    ("cotton", CropStage.VEGETATIVE): 0.9,
    ("cotton", CropStage.FLOWERING): 1.3,  # High susceptibility during flowering
    ("cotton", CropStage.FRUITING): 1.2,  # Boll formation vulnerable
    ("cotton", CropStage.MATURITY): 0.9,
    
    # Tomato
    ("tomato", CropStage.SOWING): 0.8,
    ("tomato", CropStage.VEGETATIVE): 0.9,
    ("tomato", CropStage.FLOWERING): 1.3,  # High susceptibility during flowering
    ("tomato", CropStage.FRUITING): 1.2,  # Fruit set vulnerable
    ("tomato", CropStage.MATURITY): 0.9,
    
    # Chilli
    ("chilli", CropStage.SOWING): 0.8,
    ("chilli", CropStage.VEGETATIVE): 0.9,
    ("chilli", CropStage.FLOWERING): 1.3,  # High susceptibility during flowering
    ("chilli", CropStage.FRUITING): 1.2,  # Fruit development vulnerable
    ("chilli", CropStage.MATURITY): 0.9,
    
    # Soybean
    ("soybean", CropStage.SOWING): 0.8,
    ("soybean", CropStage.VEGETATIVE): 0.9,
    ("soybean", CropStage.FLOWERING): 1.3,  # High susceptibility during flowering (R1-R2)
    ("soybean", CropStage.FRUITING): 1.2,  # Pod fill vulnerable (R3-R6)
    ("soybean", CropStage.MATURITY): 0.9,
    
    # Onion
    ("onion", CropStage.SOWING): 0.8,
    ("onion", CropStage.VEGETATIVE): 1.0,  # Leaf growth moderately susceptible
    ("onion", CropStage.FLOWERING): 1.2,  # Bulb formation vulnerable
    ("onion", CropStage.FRUITING): 1.1,  # Seed set moderately vulnerable
    ("onion", CropStage.MATURITY): 0.9,
}


# Typical days to reach each growth stage
# NOTE: These are approximate and vary by variety, climate, and management practices.
# Should be reviewed by a domain expert for specific regions.
CROP_STAGE_TIMELINE: Dict[str, Dict[CropStage, int]] = {
    "cotton": {
        CropStage.SOWING: 0,
        CropStage.VEGETATIVE: 30,    # 30 days to vegetative
        CropStage.FLOWERING: 60,    # 60 days to flowering
        CropStage.FRUITING: 90,     # 90 days to boll formation
        CropStage.MATURITY: 150,    # 150 days to maturity
    },
    "tomato": {
        CropStage.SOWING: 0,
        CropStage.VEGETATIVE: 25,    # 25 days to vegetative
        CropStage.FLOWERING: 50,    # 50 days to flowering
        CropStage.FRUITING: 70,     # 70 days to fruit set
        CropStage.MATURITY: 100,    # 100 days to maturity
    },
    "chilli": {
        CropStage.SOWING: 0,
        CropStage.VEGETATIVE: 30,    # 30 days to vegetative
        CropStage.FLOWERING: 60,    # 60 days to flowering
        CropStage.FRUITING: 80,     # 80 days to fruit development
        CropStage.MATURITY: 120,    # 120 days to maturity
    },
    "soybean": {
        CropStage.SOWING: 0,
        CropStage.VEGETATIVE: 20,    # 20 days to vegetative (V stages)
        CropStage.FLOWERING: 40,    # 40 days to flowering (R1-R2)
        CropStage.FRUITING: 60,     # 60 days to pod fill (R3-R6)
        CropStage.MATURITY: 100,    # 100 days to maturity (R8)
    },
    "onion": {
        CropStage.SOWING: 0,
        CropStage.VEGETATIVE: 30,    # 30 days to vegetative
        CropStage.FLOWERING: 90,    # 90 days to bulb formation
        CropStage.FRUITING: 120,    # 120 days to seed set
        CropStage.MATURITY: 150,    # 150 days to maturity
    },
}


def get_stage_multiplier(crop_name: str, stage: CropStage) -> float:
    """
    Get disease susceptibility multiplier for a crop at a specific stage.
    
    Args:
        crop_name: Name of the crop (e.g., "tomato", "cotton")
        stage: Current growth stage
    
    Returns:
        Susceptibility multiplier (default 1.0 if crop/stage not found)
    """
    crop_name_lower = crop_name.lower().strip()
    key = (crop_name_lower, stage)
    
    multiplier = STAGE_SUSCEPTIBILITY.get(key, 1.0)
    
    if multiplier == 1.0 and key not in STAGE_SUSCEPTIBILITY:
        logger.debug(f"No susceptibility data for {crop_name} at {stage}, using default 1.0")
    
    return multiplier


def auto_estimate_stage(sowing_date: date, crop_name: str) -> CropStage:
    """
    Automatically estimate current crop stage based on days since sowing.
    
    Args:
        sowing_date: Date when crop was sown
        crop_name: Name of the crop
    
    Returns:
        Estimated CropStage based on typical timeline
    """
    crop_name_lower = crop_name.lower().strip()
    
    # Get timeline for crop, or use default if not found
    timeline = CROP_STAGE_TIMELINE.get(crop_name_lower)
    if not timeline:
        logger.warning(f"No timeline data for crop '{crop_name}', using default timeline")
        timeline = CROP_STAGE_TIMELINE["tomato"]  # Use tomato as default
    
    # Calculate days since sowing
    days_since_sowing = (date.today() - sowing_date).days
    
    if days_since_sowing < 0:
        logger.warning(f"Sowing date {sowing_date} is in the future, assuming SOWING stage")
        return CropStage.SOWING
    
    # Determine stage based on days since sowing
    if days_since_sowing < timeline[CropStage.VEGETATIVE]:
        return CropStage.SOWING
    elif days_since_sowing < timeline[CropStage.FLOWERING]:
        return CropStage.VEGETATIVE
    elif days_since_sowing < timeline[CropStage.FRUITING]:
        return CropStage.FLOWERING
    elif days_since_sowing < timeline[CropStage.MATURITY]:
        return CropStage.FRUITING
    else:
        return CropStage.MATURITY


def get_crop_stage_timeline(crop_name: str) -> Dict[CropStage, int]:
    """
    Get the typical timeline for a crop's growth stages.
    
    Args:
        crop_name: Name of the crop
    
    Returns:
        Dictionary mapping CropStage to days from sowing
    """
    crop_name_lower = crop_name.lower().strip()
    return CROP_STAGE_TIMELINE.get(crop_name_lower, CROP_STAGE_TIMELINE["tomato"])


def get_supported_crops() -> list:
    """
    Get list of crops with susceptibility data.
    
    Returns:
        List of crop names
    """
    crops = set()
    for crop, _ in STAGE_SUSCEPTIBILITY.keys():
        crops.add(crop)
    return sorted(list(crops))
