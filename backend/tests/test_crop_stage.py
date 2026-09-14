"""
Unit tests for Crop Stage Encoding Module.
"""
import pytest
from datetime import date, timedelta

from app.services.crop_stage import (
    CropStage,
    get_stage_multiplier,
    auto_estimate_stage,
    get_crop_stage_timeline,
    get_supported_crops,
)


def test_get_stage_multiplier_known_crop():
    """Test stage multiplier for known crop-stage combinations."""
    # Tomato at flowering should have high susceptibility (1.3)
    multiplier = get_stage_multiplier("tomato", CropStage.FLOWERING)
    assert multiplier == 1.3
    
    # Cotton at sowing should have lower susceptibility (0.8)
    multiplier = get_stage_multiplier("cotton", CropStage.SOWING)
    assert multiplier == 0.8
    
    # Chilli at fruiting should have high susceptibility (1.2)
    multiplier = get_stage_multiplier("chilli", CropStage.FRUITING)
    assert multiplier == 1.2


def test_get_stage_multiplier_unknown_crop():
    """Test that unknown crop-stage combinations return default 1.0."""
    multiplier = get_stage_multiplier("unknown_crop", CropStage.VEGETATIVE)
    assert multiplier == 1.0
    
    multiplier = get_stage_multiplier("wheat", CropStage.FLOWERING)
    assert multiplier == 1.0


def test_get_stage_multiplier_case_insensitive():
    """Test that crop names are case-insensitive."""
    multiplier1 = get_stage_multiplier("Tomato", CropStage.FLOWERING)
    multiplier2 = get_stage_multiplier("TOMATO", CropStage.FLOWERING)
    multiplier3 = get_stage_multiplier("tomato", CropStage.FLOWERING)
    
    assert multiplier1 == multiplier2 == multiplier3 == 1.3


def test_auto_estimate_stage_tomato():
    """Test automatic stage estimation for tomato."""
    # Test sowing stage (0-25 days)
    sowing_date = date.today() - timedelta(days=10)
    stage = auto_estimate_stage(sowing_date, "tomato")
    assert stage == CropStage.SOWING
    
    # Test vegetative stage (25-50 days)
    sowing_date = date.today() - timedelta(days=35)
    stage = auto_estimate_stage(sowing_date, "tomato")
    assert stage == CropStage.VEGETATIVE
    
    # Test flowering stage (50-70 days)
    sowing_date = date.today() - timedelta(days=60)
    stage = auto_estimate_stage(sowing_date, "tomato")
    assert stage == CropStage.FLOWERING
    
    # Test fruiting stage (70-100 days)
    sowing_date = date.today() - timedelta(days=85)
    stage = auto_estimate_stage(sowing_date, "tomato")
    assert stage == CropStage.FRUITING
    
    # Test maturity stage (>100 days)
    sowing_date = date.today() - timedelta(days=110)
    stage = auto_estimate_stage(sowing_date, "tomato")
    assert stage == CropStage.MATURITY


def test_auto_estimate_stage_cotton():
    """Test automatic stage estimation for cotton."""
    # Test vegetative stage (30-60 days)
    sowing_date = date.today() - timedelta(days=45)
    stage = auto_estimate_stage(sowing_date, "cotton")
    assert stage == CropStage.VEGETATIVE
    
    # Test flowering stage (60-90 days)
    sowing_date = date.today() - timedelta(days=75)
    stage = auto_estimate_stage(sowing_date, "cotton")
    assert stage == CropStage.FLOWERING
    
    # Test fruiting stage (90-150 days)
    sowing_date = date.today() - timedelta(days=120)
    stage = auto_estimate_stage(sowing_date, "cotton")
    assert stage == CropStage.FRUITING


def test_auto_estimate_stage_soybean():
    """Test automatic stage estimation for soybean."""
    # Test sowing stage (0-20 days)
    sowing_date = date.today() - timedelta(days=15)
    stage = auto_estimate_stage(sowing_date, "soybean")
    assert stage == CropStage.SOWING
    
    # Test flowering stage (40-60 days)
    sowing_date = date.today() - timedelta(days=50)
    stage = auto_estimate_stage(sowing_date, "soybean")
    assert stage == CropStage.FLOWERING
    
    # Test maturity stage (>100 days)
    sowing_date = date.today() - timedelta(days=105)
    stage = auto_estimate_stage(sowing_date, "soybean")
    assert stage == CropStage.MATURITY


def test_auto_estimate_stage_future_date():
    """Test that future sowing dates return SOWING stage."""
    sowing_date = date.today() + timedelta(days=10)
    stage = auto_estimate_stage(sowing_date, "tomato")
    assert stage == CropStage.SOWING


def test_auto_estimate_stage_unknown_crop():
    """Test that unknown crops use default timeline (tomato)."""
    sowing_date = date.today() - timedelta(days=60)
    stage = auto_estimate_stage(sowing_date, "unknown_crop")
    # Should use tomato timeline, so 60 days = flowering
    assert stage == CropStage.FLOWERING


def test_get_crop_stage_timeline():
    """Test getting crop stage timeline."""
    timeline = get_crop_stage_timeline("tomato")
    
    assert CropStage.SOWING in timeline
    assert CropStage.VEGETATIVE in timeline
    assert CropStage.FLOWERING in timeline
    assert CropStage.FRUITING in timeline
    assert CropStage.MATURITY in timeline
    
    assert timeline[CropStage.SOWING] == 0
    assert timeline[CropStage.VEGETATIVE] == 25
    assert timeline[CropStage.FLOWERING] == 50
    assert timeline[CropStage.FRUITING] == 70
    assert timeline[CropStage.MATURITY] == 100


def test_get_crop_stage_timeline_unknown_crop():
    """Test that unknown crops return default timeline (tomato)."""
    timeline = get_crop_stage_timeline("unknown_crop")
    # Should return tomato timeline as default
    assert timeline[CropStage.VEGETATIVE] == 25


def test_get_supported_crops():
    """Test getting list of supported crops."""
    crops = get_supported_crops()
    
    assert isinstance(crops, list)
    assert "cotton" in crops
    assert "tomato" in crops
    assert "chilli" in crops
    assert "soybean" in crops
    assert "onion" in crops


def test_susceptibility_multipliers_range():
    """Test that all susceptibility multipliers are in reasonable range."""
    from app.services.crop_stage import STAGE_SUSCEPTIBILITY
    
    for (crop, stage), multiplier in STAGE_SUSCEPTIBILITY.items():
        assert 0.5 <= multiplier <= 1.5, f"Multiplier {multiplier} for {crop} at {stage} out of range"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
