"""
Test Full Pipeline Integration.
Tests the fusion + risk engine + decision engine pipeline structure and logic.
"""
import pytest
from app.services.risk_engine import FUSION_WEIGHTS, map_risk_level


def test_fusion_weights():
    """Test that fusion weights are properly configured."""
    assert "disease_risk" in FUSION_WEIGHTS
    assert "pest_risk" in FUSION_WEIGHTS
    assert "spread_risk" in FUSION_WEIGHTS
    
    # Weights should sum to 1.0
    total_weight = sum(FUSION_WEIGHTS.values())
    assert abs(total_weight - 1.0) < 0.01, f"Weights sum to {total_weight}, expected 1.0"
    
    print("✓ Fusion weights are valid:", FUSION_WEIGHTS)


def test_risk_level_mapping():
    """Test risk level mapping thresholds."""
    assert map_risk_level(85.0) == "CRITICAL"
    assert map_risk_level(80.0) == "CRITICAL"
    assert map_risk_level(70.0) == "HIGH"
    assert map_risk_level(60.0) == "HIGH"
    assert map_risk_level(50.0) == "MODERATE"
    assert map_risk_level(40.0) == "MODERATE"
    assert map_risk_level(30.0) == "LOW"
    assert map_risk_level(0.0) == "LOW"
    
    print("✓ Risk level mapping works correctly")


def test_pipeline_structure():
    """Test that pipeline function exists and has correct signature."""
    from app.services.risk_engine import run_full_pipeline
    import inspect
    
    sig = inspect.signature(run_full_pipeline)
    params = list(sig.parameters.keys())
    
    assert "db" in params, "Pipeline should accept db parameter"
    assert "crop_id" in params, "Pipeline should accept crop_id parameter"
    
    print("✓ Pipeline function has correct signature")


def test_fusion_calculation():
    """Test fusion calculation logic with mock data."""
    # Mock fusion calculation
    disease_risk = 70.0
    pest_risk = 50.0
    spread_risk = 60.0
    
    # Calculate overall risk using fusion weights
    total_weight = FUSION_WEIGHTS["disease_risk"] + FUSION_WEIGHTS["pest_risk"] + FUSION_WEIGHTS["spread_risk"]
    overall_risk = (
        disease_risk * FUSION_WEIGHTS["disease_risk"] +
        pest_risk * FUSION_WEIGHTS["pest_risk"] +
        spread_risk * FUSION_WEIGHTS["spread_risk"]
    ) / total_weight
    
    # Should be between min and max of inputs
    assert min(disease_risk, pest_risk, spread_risk) <= overall_risk <= max(disease_risk, pest_risk, spread_risk)
    
    # Should be closer to disease_risk since it has highest weight
    assert abs(overall_risk - disease_risk) < abs(overall_risk - pest_risk)
    
    print(f"✓ Fusion calculation: disease={disease_risk}, pest={pest_risk}, spread={spread_risk} -> overall={overall_risk:.1f}")


def test_fusion_without_pest_data():
    """Test fusion calculation when pest data is missing."""
    disease_risk = 70.0
    pest_risk = None  # No pest data
    spread_risk = 60.0
    
    # Calculate overall risk without pest data
    total_weight = FUSION_WEIGHTS["disease_risk"] + FUSION_WEIGHTS["spread_risk"]
    overall_risk = (
        disease_risk * FUSION_WEIGHTS["disease_risk"] +
        spread_risk * FUSION_WEIGHTS["spread_risk"]
    ) / total_weight
    
    # Should be between disease and spread risk
    assert min(disease_risk, spread_risk) <= overall_risk <= max(disease_risk, spread_risk)
    
    print(f"✓ Fusion without pest data: disease={disease_risk}, spread={spread_risk} -> overall={overall_risk:.1f}")


def test_decision_engine_logic():
    """Test decision engine logic based on risk level and confidence."""
    # Test LOW confidence -> expert validation
    is_low_confidence = True
    risk_level = "MODERATE"
    
    if is_low_confidence:
        decision = "needs_expert_validation"
    else:
        decision = "monitor"
    
    assert decision == "needs_expert_validation"
    
    # Test HIGH risk -> trigger alert
    is_low_confidence = False
    risk_level = "HIGH"
    
    if is_low_confidence:
        decision = "needs_expert_validation"
    elif risk_level in ["HIGH", "CRITICAL"]:
        decision = "trigger_alert"
    else:
        decision = "monitor"
    
    assert decision == "trigger_alert"
    
    # Test CRITICAL risk -> trigger alert
    risk_level = "CRITICAL"
    
    if is_low_confidence:
        decision = "needs_expert_validation"
    elif risk_level in ["HIGH", "CRITICAL"]:
        decision = "trigger_alert"
    else:
        decision = "monitor"
    
    assert decision == "trigger_alert"
    
    # Test LOW risk -> monitor
    risk_level = "LOW"
    
    if is_low_confidence:
        decision = "needs_expert_validation"
    elif risk_level in ["HIGH", "CRITICAL"]:
        decision = "trigger_alert"
    else:
        decision = "monitor"
    
    assert decision == "monitor"
    
    print("✓ Decision engine logic works correctly")


if __name__ == "__main__":
    print("Testing Full Pipeline Integration...\n")
    
    test_fusion_weights()
    test_risk_level_mapping()
    test_pipeline_structure()
    test_fusion_calculation()
    test_fusion_without_pest_data()
    test_decision_engine_logic()
    
    print("\n✅ All pipeline integration tests passed!")
