"""
Seed demo data for Government Command Center presentation.
Populates realistic demo farms, scans, and alerts across Maharashtra districts.
Only seeds data for districts with zero real scans to avoid mixing with live data.
"""
import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from app.db.connection import get_db
from app.db.models import (
    User, UserRole, Farm, Crop, Observation, AIResult, 
    Alert, AlertLevel, RiskScore, RiskLevel, ExpertValidation
)
from app.data.maharashtra_locations import (
    MAHARASHTRA_LOCATIONS,
    get_location_by_name,
    get_common_diseases_for_location,
    get_common_pests_for_location,
    get_disease_skew_for_location
)
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def seed_demo_data():
    """Seed demo data for admin dashboard presentation.
    Only seeds data for districts with zero real scans to avoid mixing with live data."""
    db: Session = next(get_db())
    
    try:
        # Check for existing real data (observations in last 7 days)
        from app.db.models import Observation, Crop
        seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
        
        real_observations = (
            db.query(Observation)
            .join(Crop, Crop.id == Observation.crop_id)
            .filter(Observation.timestamp >= seven_days_ago)
            .count()
        )
        
        if real_observations > 0:
            print(f"⚠️  Found {real_observations} real observations in the last 7 days.")
            print("Skipping seed data to avoid mixing with live data.")
            print("To force seed data, clear the database first.")
            return
        
        # Clear existing demo data if needed (optional)
        # Uncomment to clean slate
        db.query(ExpertValidation).delete()
        db.query(Observation).delete()
        db.query(AIResult).delete()
        db.query(RiskScore).delete()
        db.query(Alert).delete()
        db.query(Crop).delete()
        db.query(Farm).delete()
        db.query(User).filter(User.role == UserRole.farmer).delete()
        db.query(User).filter(User.role == UserRole.officer).delete()
        db.commit()
        print("✓ Cleared existing demo data")
        
        # Create demo users with known credentials
        # Demo farmer: farmer@krushirakshak.in / farmer123
        demo_farmer = User(
            name="Demo Farmer",
            email="farmer@krushirakshak.in",
            password_hash=pwd_context.hash("farmer123"),
            phone="+919876543210",
            role=UserRole.farmer,
            district="Nashik",
            state="Maharashtra",
            language_pref="en",
            created_at=datetime.now(timezone.utc) - timedelta(days=30)
        )
        db.add(demo_farmer)
        db.flush()
        print("✓ Created demo farmer (farmer@krushirakshak.in / farmer123)")
        
        # Demo officer: officer@krushirakshak.in / officer123
        demo_officer = User(
            name="Demo Officer",
            email="officer@krushirakshak.in",
            password_hash=pwd_context.hash("officer123"),
            phone="+919876543211",
            role=UserRole.officer,
            district="Nashik",
            state="Maharashtra",
            language_pref="en",
            created_at=datetime.now(timezone.utc) - timedelta(days=30)
        )
        db.add(demo_officer)
        db.flush()
        print("✓ Created demo officer (officer@krushirakshak.in / officer123)")
        
        # Use Maharashtra locations from data file
        locations = MAHARASHTRA_LOCATIONS
        
        villages = ["Shirpur", "Wadgaon", "Nandgaon", "Malegaon", "Rahuri", 
                   "Sangamner", "Junnar", "Ambegaon", "Maval", "Mulshi"]
        
        crops_data = [
            "Cotton", "Soybean", "Sugarcane", "Wheat", "Jowar", 
            "Gram", "Tur", "Groundnut", "Sunflower", "Maize"
        ]
        
        # Create demo farmers and farms based on Maharashtra locations
        # Use the demo farmer for all farms
        farmers = [demo_farmer]
        farms = []
        
        for i, location in enumerate(locations):
            village = villages[i % len(villages)]
            
            # Create farm at location coordinates
            farm = Farm(
                owner_id=demo_farmer.id,
                name=f"{location['name']} Farm",
                village=village,
                taluka=location["district"],  # Use district as taluka for demo
                district=location["district"],
                state="Maharashtra",
                gps_lat=location["lat"],
                gps_lng=location["lng"],
                area_acres=2.5,
                soil_type="Black Cotton Soil",
                created_at=datetime.now(timezone.utc) - timedelta(days=30+i)
            )
            db.add(farm)
            db.flush()
            farms.append(farm)
        
        print(f"✓ Created {len(farmers)} farmers and {len(farms)} farms")
        
        # Create crops and observations with climate-zone-specific data
        crops = []
        observations = []
        
        for farm_idx, farm in enumerate(farms):
            # Get location data for this farm
            location = locations[farm_idx % len(locations)]
            disease_skew = location["disease_skew"]
            common_diseases = location["common_diseases"]
            common_pests = location["common_pests"]
            base_scan_volume = location["base_scan_volume"]
            
            # Create 1-2 crops per farm
            for j in range(1 + (farm_idx % 2)):
                crop_name = crops_data[(farm_idx + j) % len(crops_data)]
                
                crop = Crop(
                    farm_id=farm.id,
                    crop_name=crop_name,
                    variety="Desi",
                    sowing_date=datetime.now(timezone.utc) - timedelta(days=60),
                    growth_stage="Vegetative",
                    created_at=datetime.now(timezone.utc) - timedelta(days=60)
                )
                db.add(crop)
                db.flush()
                crops.append(crop)
                
                # Create observations (scans) for each crop - volume based on location
                num_observations = max(3, base_scan_volume // 10) + (farm_idx % 5)
                for k in range(num_observations):
                    days_ago = k * 3
                    obs = Observation(
                        crop_id=crop.id,
                        image_urls=[f"https://demo-images.cropdisease.ai/scan_{farm_idx}_{j}_{k}.jpg"],
                        timestamp=datetime.now(timezone.utc) - timedelta(days=days_ago),
                        notes=f"Routine scan #{k+1}"
                    )
                    db.add(obs)
                    db.flush()
                    observations.append(obs)
                    
                    # Create AI results based on climate zone disease/pest skew
                    if disease_skew == "fungal":
                        # Higher chance of fungal diseases
                        disease = common_diseases[(farm_idx + j + k) % len(common_diseases)]
                        pest_label = None
                        disease_risk = 0.5 + (k * 0.06)
                        pest_risk = 0.15 + (k * 0.02)
                    elif disease_skew == "pest":
                        # Higher chance of pests
                        pest_label = common_pests[(farm_idx + j + k) % len(common_pests)]
                        disease = common_diseases[(farm_idx + j + k) % len(common_diseases)] if common_diseases else "Unknown"
                        disease_risk = 0.2 + (k * 0.03)
                        pest_risk = 0.5 + (k * 0.06)
                    else:  # mixed
                        # Balanced disease and pest risk
                        if k % 2 == 0:
                            disease = common_diseases[(farm_idx + j + k) % len(common_diseases)]
                            pest_label = None
                            disease_risk = 0.4 + (k * 0.05)
                            pest_risk = 0.25 + (k * 0.03)
                        else:
                            pest_label = common_pests[(farm_idx + j + k) % len(common_pests)]
                            disease = common_diseases[(farm_idx + j + k) % len(common_diseases)] if common_diseases else "Unknown"
                            disease_risk = 0.3 + (k * 0.04)
                            pest_risk = 0.4 + (k * 0.05)
                    
                    confidence = 0.75 + (k * 0.02)
                    severity_pct = 30 + (k * 10)
                    
                    ai_result = AIResult(
                        observation_id=obs.id,
                        disease_label=disease,
                        pest_label=pest_label,
                        confidence=confidence,
                        severity_pct=severity_pct,
                        heat_map_url=f"https://demo-images.cropdisease.ai/gradcam_{farm_idx}_{j}_{k}.jpg"
                    )
                    db.add(ai_result)
                    db.flush()
                    
                    # Create risk scores based on climate zone
                    overall_score = 0.4 + (k * 0.05)
                    if disease_skew == "fungal":
                        overall_score += 0.1  # Higher overall risk for fungal zones
                    elif disease_skew == "pest":
                        overall_score += 0.05
                    
                    if overall_score >= 0.7:
                        risk_level = RiskLevel.critical
                    elif overall_score >= 0.5:
                        risk_level = RiskLevel.high
                    elif overall_score >= 0.3:
                        risk_level = RiskLevel.medium
                    else:
                        risk_level = RiskLevel.low
                    
                    risk_score = RiskScore(
                        crop_id=crop.id,
                        overall_score=min(overall_score, 0.95),
                        disease_risk=disease_risk,
                        pest_risk=pest_risk,
                        weather_risk=0.25 + (k * 0.04),
                        risk_level=risk_level
                    )
                    db.add(risk_score)
                    
                    # Create alerts for high severity cases
                    if severity_pct > 50:
                        alert_level = AlertLevel.critical if severity_pct > 70 else AlertLevel.warning
                        alert_title = f"{pest_label if pest_label else disease} Detected in {location['name']}"
                        alert = Alert(
                            crop_id=crop.id,
                            risk_score_id=risk_score.id,
                            level=alert_level,
                            title=alert_title,
                            message=f"High severity { (pest_label if pest_label else disease).lower() } detected. Immediate action recommended.",
                            acknowledged=False,
                            created_at=datetime.now(timezone.utc) - timedelta(days=days_ago)
                        )
                        db.add(alert)
        
        db.commit()
        
        print(f"✓ Created {len(crops)} crops")
        print(f"✓ Created {len(observations)} observations/scans")
        print(f"✓ Created alerts for high-severity cases")
        
        # Count pending expert validations (AI results without validations)
        from sqlalchemy import and_
        pending_validations = (
            db.query(AIResult)
            .outerjoin(ExpertValidation, ExpertValidation.ai_result_id == AIResult.id)
            .filter(ExpertValidation.id == None)
            .count()
        )
        
        print("\n✅ Demo data seeded successfully!")
        print(f"Summary:")
        print(f"  - Farmers: {len(farmers)}")
        print(f"  - Farms: {len(farms)}")
        print(f"  - Crops: {len(crops)}")
        print(f"  - Observations: {len(observations)}")
        print(f"  - Alerts: {db.query(Alert).count()}")
        print(f"  - Pending validations: {pending_validations}")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error seeding demo data: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_demo_data()
