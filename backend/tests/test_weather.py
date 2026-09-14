"""
Unit tests for Weather Service Module.
"""
import pytest
from datetime import datetime
from app.services.weather import (
    WeatherSnapshot,
    engineer_weather_features,
    compute_weather_risk,
)


def create_mock_weather_snapshot(
    temperature=25.0,
    humidity=85.0,
    precipitation=5.0,
    wind_speed=10.0,
    lat=19.0,
    lng=75.0,
):
    """Create a mock WeatherSnapshot for testing."""
    return WeatherSnapshot(
        latitude=lat,
        longitude=lng,
        temperature=temperature,
        humidity=humidity,
        precipitation=precipitation,
        wind_speed=wind_speed,
        timestamp=datetime.now(),
        forecast=[
            {
                "date": "2026-09-14",
                "precipitation_sum": 10.0,
                "temp_max": 28.0,
                "temp_min": 22.0,
                "humidity_mean": 80.0,
            },
            {
                "date": "2026-09-15",
                "precipitation_sum": 5.0,
                "temp_max": 27.0,
                "temp_min": 21.0,
                "humidity_mean": 75.0,
            },
            {
                "date": "2026-09-16",
                "precipitation_sum": 2.0,
                "temp_max": 26.0,
                "temp_min": 20.0,
                "humidity_mean": 70.0,
            },
            {
                "date": "2026-09-17",
                "precipitation_sum": 0.0,
                "temp_max": 25.0,
                "temp_min": 19.0,
                "humidity_mean": 65.0,
            },
            {
                "date": "2026-09-18",
                "precipitation_sum": 0.0,
                "temp_max": 24.0,
                "temp_min": 18.0,
                "humidity_mean": 60.0,
            },
        ],
    )


def test_high_humidity_high_rain_scenario():
    """Test that high humidity + recent rain + moderate temp returns HIGH weather risk."""
    # Create scenario: high humidity (85%), recent rain (17mm total), moderate temp (25°C)
    snapshot = create_mock_weather_snapshot(
        temperature=25.0,
        humidity=85.0,
        precipitation=5.0,
    )
    
    # Engineer features
    features = engineer_weather_features(snapshot)
    
    # Verify features
    assert features["humidity_bucket"] == "high"
    assert features["recent_precipitation_total"] == 17.0  # 10 + 5 + 2
    assert features["temp_suitability_for_disease"] == 100.0  # 25°C is in optimal range
    
    # Compute risk
    risk_score = compute_weather_risk(features)
    
    # Should return HIGH risk score (> 70)
    assert risk_score > 70.0, f"Expected HIGH risk score, got {risk_score}"
    print(f"High humidity scenario risk score: {risk_score:.2f}")


def test_low_humidity_no_rain_scenario():
    """Test that low humidity + no rain returns LOW weather risk."""
    # Create scenario: low humidity (30%), no rain, moderate temp (25°C)
    snapshot = create_mock_weather_snapshot(
        temperature=25.0,
        humidity=30.0,
        precipitation=0.0,
    )
    
    # Modify forecast to have no precipitation
    snapshot.forecast = [
        {
            "date": "2026-09-14",
            "precipitation_sum": 0.0,
            "temp_max": 28.0,
            "temp_min": 22.0,
            "humidity_mean": 35.0,
        },
        {
            "date": "2026-09-15",
            "precipitation_sum": 0.0,
            "temp_max": 27.0,
            "temp_min": 21.0,
            "humidity_mean": 30.0,
        },
        {
            "date": "2026-09-16",
            "precipitation_sum": 0.0,
            "temp_max": 26.0,
            "temp_min": 20.0,
            "humidity_mean": 25.0,
        },
        {
            "date": "2026-09-17",
            "precipitation_sum": 0.0,
            "temp_max": 25.0,
            "temp_min": 19.0,
            "humidity_mean": 30.0,
        },
        {
            "date": "2026-09-18",
            "precipitation_sum": 0.0,
            "temp_max": 24.0,
            "temp_min": 18.0,
            "humidity_mean": 35.0,
        },
    ]
    
    # Engineer features
    features = engineer_weather_features(snapshot)
    
    # Verify features
    assert features["humidity_bucket"] == "low"
    assert features["recent_precipitation_total"] == 0.0
    
    # Compute risk
    risk_score = compute_weather_risk(features)
    
    # Should return LOW risk score (< 40)
    assert risk_score < 40.0, f"Expected LOW risk score, got {risk_score}"
    print(f"Low humidity scenario risk score: {risk_score:.2f}")


def test_temperature_suitability_bell_curve():
    """Test temperature suitability follows bell curve peaking at 20-28°C."""
    # Test optimal range (20-28°C)
    for temp in [20, 24, 28]:
        snapshot = create_mock_weather_snapshot(temperature=temp, humidity=70.0)
        features = engineer_weather_features(snapshot)
        assert features["temp_suitability_for_disease"] == 100.0
    
    # Test below optimal (10-20°C)
    snapshot = create_mock_weather_snapshot(temperature=15.0, humidity=70.0)
    features = engineer_weather_features(snapshot)
    assert 0.0 < features["temp_suitability_for_disease"] < 100.0
    
    # Test above optimal (28-35°C)
    snapshot = create_mock_weather_snapshot(temperature=32.0, humidity=70.0)
    features = engineer_weather_features(snapshot)
    assert 0.0 < features["temp_suitability_for_disease"] < 100.0
    
    # Test outside range (<10°C or >35°C)
    for temp in [5.0, 40.0]:
        snapshot = create_mock_weather_snapshot(temperature=temp, humidity=70.0)
        features = engineer_weather_features(snapshot)
        assert features["temp_suitability_for_disease"] == 0.0


def test_leaf_wetness_proxy():
    """Test leaf wetness proxy combines humidity and precipitation."""
    # High humidity, no rain
    snapshot = create_mock_weather_snapshot(temperature=25.0, humidity=90.0, precipitation=0.0)
    snapshot.forecast = [{"date": "2026-09-14", "precipitation_sum": 0.0, "temp_max": 28.0, "temp_min": 22.0, "humidity_mean": 90.0}]
    features = engineer_weather_features(snapshot)
    assert features["leaf_wetness_proxy"] > 50.0  # High humidity contributes significantly
    
    # Moderate humidity, recent rain
    snapshot = create_mock_weather_snapshot(temperature=25.0, humidity=60.0, precipitation=0.0)
    snapshot.forecast = [{"date": "2026-09-14", "precipitation_sum": 10.0, "temp_max": 28.0, "temp_min": 22.0, "humidity_mean": 60.0}]
    features = engineer_weather_features(snapshot)
    assert features["leaf_wetness_proxy"] > 50.0  # Recent rain contributes significantly


def test_risk_score_range():
    """Test that risk score is always between 0 and 100."""
    # Test various scenarios
    test_cases = [
        (25.0, 90.0, 10.0),  # High risk
        (25.0, 30.0, 0.0),   # Low risk
        (15.0, 70.0, 5.0),   # Moderate risk (suboptimal temp)
        (35.0, 70.0, 5.0),   # Moderate risk (suboptimal temp)
    ]
    
    for temp, humidity, precip in test_cases:
        snapshot = create_mock_weather_snapshot(temperature=temp, humidity=humidity, precipitation=precip)
        features = engineer_weather_features(snapshot)
        risk_score = compute_weather_risk(features)
        assert 0.0 <= risk_score <= 100.0, f"Risk score {risk_score} out of range for temp={temp}, humidity={humidity}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
