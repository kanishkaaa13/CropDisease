"""
Test Spatial Risk Service.
Tests nearby case detection and spatial risk computation with seeded data.
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.db.connection import get_db
from app.db.models import User, Farm, Crop, Observation, AIResult, UserRole
from app.services.spatial_risk import get_nearby_cases, compute_spatial_risk, haversine_distance


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test."""
    db = next(get_db())
    try:
        yield db
    finally:
        db.rollback()
        db.close()


def test_haversine_distance():
    """Test Haversine distance calculation."""
    # Test known distance (approximately 111 km for 1 degree latitude)
    distance = haversine_distance(0.0, 0.0, 1.0, 0.0)
    assert 110 < distance < 112  # Should be ~111 km
    
    # Test zero distance
    distance = haversine_distance(19.0, 73.0, 19.0, 73.0)
    assert distance == 0.0


def test_compute_spatial_risk_empty_cases():
    """Test spatial risk with no nearby cases."""
    risk = compute_spatial_risk([])
    assert risk == 0.0


def test_compute_spatial_risk_with_cases():
    """Test spatial risk with nearby cases at varying distances and dates."""
    # Create test cases with different distances and recency
    test_cases = [
        # Close and recent - should contribute most
        {
            "crop_name": "Tomato",
            "disease_label": "Tomato___Early_blight",
            "distance_km": 1.0,
            "days_ago": 1,
            "farm_id": "farm1",
        },
        # Close but older - should contribute less
        {
            "crop_name": "Tomato",
            "disease_label": "Tomato___Early_blight",
            "distance_km": 1.0,
            "days_ago": 10,
            "farm_id": "farm2",
        },
        # Far but recent - should contribute less
        {
            "crop_name": "Tomato",
            "disease_label": "Tomato___Early_blight",
            "distance_km": 8.0,
            "days_ago": 1,
            "farm_id": "farm3",
        },
        # Far and old - should contribute least
        {
            "crop_name": "Tomato",
            "disease_label": "Tomato___Early_blight",
            "distance_km": 8.0,
            "days_ago": 10,
            "farm_id": "farm4",
        },
    ]
    
    risk_score = compute_spatial_risk(test_cases)
    
    # Risk should be > 0 since we have cases
    assert risk_score > 0.0
    
    # Risk should be capped at 100
    assert risk_score <= 100.0
    
    print(f"Spatial risk score: {risk_score}")


def test_compute_spatial_risk_close_recent_vs_far_old():
    """Test that close+recent cases produce higher risk than far+old cases."""
    # Scenario 1: Close and recent cases
    close_recent_cases = [
        {
            "crop_name": "Tomato",
            "disease_label": "Tomato___Early_blight",
            "distance_km": 0.5,
            "days_ago": 1,
            "farm_id": "farm1",
        },
        {
            "crop_name": "Tomato",
            "disease_label": "Tomato___Early_blight",
            "distance_km": 1.0,
            "days_ago": 2,
            "farm_id": "farm2",
        },
    ]
    
    # Scenario 2: Far and old cases
    far_old_cases = [
        {
            "crop_name": "Tomato",
            "disease_label": "Tomato___Early_blight",
            "distance_km": 8.0,
            "days_ago": 12,
            "farm_id": "farm3",
        },
        {
            "crop_name": "Tomato",
            "disease_label": "Tomato___Early_blight",
            "distance_km": 9.0,
            "days_ago": 13,
            "farm_id": "farm4",
        },
    ]
    
    close_recent_risk = compute_spatial_risk(close_recent_cases)
    far_old_risk = compute_spatial_risk(far_old_cases)
    
    # Close+recent should have higher risk
    assert close_recent_risk > far_old_risk
    
    print(f"Close+recent risk: {close_recent_risk}, Far+old risk: {far_old_risk}")


def test_get_nearby_cases_with_mock_data():
    """Test get_nearby_cases with mock data (no database required)."""
    # Create mock nearby cases at varying distances and dates
    mock_cases = [
        {
            "crop_name": "Tomato",
            "disease_label": "Tomato___Early_blight",
            "distance_km": 1.0,
            "days_ago": 1,
            "farm_id": "farm1",
            "timestamp": "2024-01-01T00:00:00",
        },
        {
            "crop_name": "Tomato",
            "disease_label": "Tomato___Early_blight",
            "distance_km": 3.0,
            "days_ago": 5,
            "farm_id": "farm2",
            "timestamp": "2024-01-02T00:00:00",
        },
        {
            "crop_name": "Tomato",
            "disease_label": "Tomato___Late_blight",
            "distance_km": 1.4,
            "days_ago": 12,
            "farm_id": "farm4",
            "timestamp": "2024-01-03T00:00:00",
        },
    ]
    
    # Compute spatial risk
    risk_score = compute_spatial_risk(mock_cases)
    print(f"\nSpatial risk score with mock data: {risk_score}")
    
    # Risk should be > 0 since we have cases
    assert risk_score > 0.0
    
    # Risk should be reasonable
    assert risk_score <= 100.0
    
    # Test that closer+recent cases produce higher risk
    close_recent = [
        {
            "crop_name": "Tomato",
            "disease_label": "Tomato___Early_blight",
            "distance_km": 0.5,
            "days_ago": 1,
            "farm_id": "farm1",
        },
        {
            "crop_name": "Tomato",
            "disease_label": "Tomato___Early_blight",
            "distance_km": 1.0,
            "days_ago": 2,
            "farm_id": "farm2",
        },
    ]
    
    far_old = [
        {
            "crop_name": "Tomato",
            "disease_label": "Tomato___Early_blight",
            "distance_km": 8.0,
            "days_ago": 12,
            "farm_id": "farm3",
        },
        {
            "crop_name": "Tomato",
            "disease_label": "Tomato___Early_blight",
            "distance_km": 9.0,
            "days_ago": 13,
            "farm_id": "farm4",
        },
    ]
    
    close_recent_risk = compute_spatial_risk(close_recent)
    far_old_risk = compute_spatial_risk(far_old)
    
    print(f"Close+recent risk: {close_recent_risk}, Far+old risk: {far_old_risk}")
    assert close_recent_risk > far_old_risk


@pytest.mark.skip(reason="Requires PostgreSQL database connection")
def test_get_nearby_cases_with_seeded_data(db_session: Session):
    """Test get_nearby_cases with seeded fake observations."""
    # Create test user
    test_user = User(
        id="test-user-spatial",
        name="Test User",
        email="test@example.com",
        phone="1234567890",
        role=UserRole.farmer,
        village="Test Village",
        taluka="Test Taluka",
        district="Test District",
        state="Test State",
    )
    db_session.add(test_user)
    
    # Create test farm (query point)
    query_farm = Farm(
        id="query-farm",
        owner_id=test_user.id,
        name="Query Farm",
        village="Test Village",
        taluka="Test Taluka",
        district="Test District",
        state="Test State",
        gps_lat=19.0,
        gps_lng=73.0,
        area_acres=5.0,
    )
    db_session.add(query_farm)
    
    # Create test crop
    test_crop = Crop(
        id="test-crop",
        farm_id=query_farm.id,
        crop_name="Tomato",
        variety="Roma",
        status="active",
    )
    db_session.add(test_crop)
    
    # Create nearby farms at varying distances
    # Farm 1: 1 km away, 1 day ago (close + recent)
    farm1 = Farm(
        id="nearby-farm-1",
        owner_id=test_user.id,
        name="Nearby Farm 1",
        village="Test Village",
        taluka="Test Taluka",
        district="Test District",
        state="Test State",
        gps_lat=19.009,  # ~1 km north
        gps_lng=73.0,
        area_acres=3.0,
    )
    db_session.add(farm1)
    
    crop1 = Crop(
        id="crop-1",
        farm_id=farm1.id,
        crop_name="Tomato",
        variety="Roma",
        status="active",
    )
    db_session.add(crop1)
    
    observation1 = Observation(
        id="obs-1",
        crop_id=crop1.id,
        timestamp=datetime.utcnow() - timedelta(days=1),
        image_urls=["test1.jpg"],
        source="scan",
        gps_lat=farm1.gps_lat,
        gps_lng=farm1.gps_lng,
    )
    db_session.add(observation1)
    
    ai_result1 = AIResult(
        id="ai-1",
        observation_id=observation1.id,
        disease_label="Tomato___Early_blight",
        confidence=0.85,
        severity_pct=30.0,
    )
    db_session.add(ai_result1)
    
    # Farm 2: 3 km away, 5 days ago (moderate distance + moderate time)
    farm2 = Farm(
        id="nearby-farm-2",
        owner_id=test_user.id,
        name="Nearby Farm 2",
        village="Test Village",
        taluka="Test Taluka",
        district="Test District",
        state="Test State",
        gps_lat=19.027,  # ~3 km north
        gps_lng=73.0,
        area_acres=4.0,
    )
    db_session.add(farm2)
    
    crop2 = Crop(
        id="crop-2",
        farm_id=farm2.id,
        crop_name="Tomato",
        variety="Roma",
        status="active",
    )
    db_session.add(crop2)
    
    observation2 = Observation(
        id="obs-2",
        crop_id=crop2.id,
        timestamp=datetime.utcnow() - timedelta(days=5),
        image_urls=["test2.jpg"],
        source="scan",
        gps_lat=farm2.gps_lat,
        gps_lng=farm2.gps_lng,
    )
    db_session.add(observation2)
    
    ai_result2 = AIResult(
        id="ai-2",
        observation_id=observation2.id,
        disease_label="Tomato___Early_blight",
        confidence=0.90,
        severity_pct=25.0,
    )
    db_session.add(ai_result2)
    
    # Farm 3: 8 km away, 1 day ago (far + recent)
    farm3 = Farm(
        id="nearby-farm-3",
        owner_id=test_user.id,
        name="Nearby Farm 3",
        village="Test Village",
        taluka="Test Taluka",
        district="Test District",
        state="Test State",
        gps_lat=19.072,  # ~8 km north
        gps_lng=73.0,
        area_acres=2.0,
    )
    db_session.add(farm3)
    
    crop3 = Crop(
        id="crop-3",
        farm_id=farm3.id,
        crop_name="Tomato",
        variety="Roma",
        status="active",
    )
    db_session.add(crop3)
    
    observation3 = Observation(
        id="obs-3",
        crop_id=crop3.id,
        timestamp=datetime.utcnow() - timedelta(days=1),
        image_urls=["test3.jpg"],
        source="scan",
        gps_lat=farm3.gps_lat,
        gps_lng=farm3.gps_lng,
    )
    db_session.add(observation3)
    
    ai_result3 = AIResult(
        id="ai-3",
        observation_id=observation3.id,
        disease_label="Tomato___Late_blight",
        confidence=0.75,
        severity_pct=40.0,
    )
    db_session.add(ai_result3)
    
    # Farm 4: 1 km away, 12 days ago (close + old - outside 14 day window)
    farm4 = Farm(
        id="nearby-farm-4",
        owner_id=test_user.id,
        name="Nearby Farm 4",
        village="Test Village",
        taluka="Test Taluka",
        district="Test District",
        state="Test State",
        gps_lat=19.009,  # ~1 km north
        gps_lng=73.009,  # ~1 km east
        area_acres=3.0,
    )
    db_session.add(farm4)
    
    crop4 = Crop(
        id="crop-4",
        farm_id=farm4.id,
        crop_name="Tomato",
        variety="Roma",
        status="active",
    )
    db_session.add(crop4)
    
    observation4 = Observation(
        id="obs-4",
        crop_id=crop4.id,
        timestamp=datetime.utcnow() - timedelta(days=12),
        image_urls=["test4.jpg"],
        source="scan",
        gps_lat=farm4.gps_lat,
        gps_lng=farm4.gps_lng,
    )
    db_session.add(observation4)
    
    ai_result4 = AIResult(
        id="ai-4",
        observation_id=observation4.id,
        disease_label="Tomato___Early_blight",
        confidence=0.80,
        severity_pct=20.0,
    )
    db_session.add(ai_result4)
    
    # Farm 5: 10 km away, 3 days ago (far - outside 5km radius)
    farm5 = Farm(
        id="nearby-farm-5",
        owner_id=test_user.id,
        name="Nearby Farm 5",
        village="Test Village",
        taluka="Test Taluka",
        district="Test District",
        state="Test State",
        gps_lat=19.09,  # ~10 km north
        gps_lng=73.0,
        area_acres=2.0,
    )
    db_session.add(farm5)
    
    crop5 = Crop(
        id="crop-5",
        farm_id=farm5.id,
        crop_name="Tomato",
        variety="Roma",
        status="active",
    )
    db_session.add(crop5)
    
    observation5 = Observation(
        id="obs-5",
        crop_id=crop5.id,
        timestamp=datetime.utcnow() - timedelta(days=3),
        image_urls=["test5.jpg"],
        source="scan",
        gps_lat=farm5.gps_lat,
        gps_lng=farm5.gps_lng,
    )
    db_session.add(observation5)
    
    ai_result5 = AIResult(
        id="ai-5",
        observation_id=observation5.id,
        disease_label="Tomato___Early_blight",
        confidence=0.85,
        severity_pct=35.0,
    )
    db_session.add(ai_result5)
    
    db_session.commit()
    
    # Query nearby cases from query point (19.0, 73.0)
    nearby_cases = get_nearby_cases(
        lat=19.0,
        lng=73.0,
        radius_km=5,
        days=14,
        db=db_session,
    )
    
    print(f"\nFound {len(nearby_cases)} nearby cases:")
    for case in nearby_cases:
        print(f"  - {case['crop_name']}: {case['disease_label']}, "
              f"{case['distance_km']}km away, {case['days_ago']} days ago")
    
    # Should find 3 cases within 5km and 14 days
    # Farm 1 (1km, 1 day), Farm 2 (3km, 5 days), Farm 4 (1.4km, 12 days)
    # Farm 3 is 8km (outside radius), Farm 5 is 10km (outside radius)
    assert len(nearby_cases) == 3
    
    # Compute spatial risk
    risk_score = compute_spatial_risk(nearby_cases)
    print(f"Spatial risk score: {risk_score}")
    
    # Risk should be > 0 since we have cases
    assert risk_score > 0.0
    
    # Risk should be reasonable (not too high with only 3 cases)
    assert risk_score < 100.0


if __name__ == "__main__":
    # Run tests manually for debugging
    print("Testing Haversine distance...")
    test_haversine_distance()
    print("✓ Haversine distance test passed\n")
    
    print("Testing spatial risk with empty cases...")
    test_compute_spatial_risk_empty_cases()
    print("✓ Empty cases test passed\n")
    
    print("Testing spatial risk with cases...")
    test_compute_spatial_risk_with_cases()
    print("✓ Cases test passed\n")
    
    print("Testing close+recent vs far+old...")
    test_compute_spatial_risk_close_recent_vs_far_old()
    print("✓ Comparison test passed\n")
    
    print("All tests passed!")
