"""
Database seed script for KrushiRakshak AI.
Populates realistic sample data across all 11 tables:
- 14 Users (10 farmers, 3 field officers, 1 admin)
- 15 Farms in Maharashtra districts with GPS coordinates
- 25 Crops (Cotton, Rice, Wheat, Sugarcane, Tomato, Chilli, Soybean)
- 40 Observations with sample images & notes
- 40 AI Results with realistic plant pathology labels & severity %
- 60 Weather Snapshots across farms
- 40 Risk Scores & Alerts (Info, Warning, Danger, Critical)
- 15 Expert Validations by field officers
- 8 FollowUps tracking treatment progress
- 20 Pest Trap readings
"""
import random
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.db.base import Base
from app.db.models import (
    User, UserRole,
    Farm,
    Crop, CropStatus,
    Observation, ObservationSource,
    AIResult,
    WeatherSnapshot,
    RiskScore, RiskLevel,
    Alert, AlertLevel,
    ExpertValidation, ValidationVerdict,
    FollowUp, FollowUpStatus,
    PestTrapReading,
)

# Sample geographic locations in Maharashtra
MAHARASHTRA_LOCATIONS = [
    {"district": "Pune", "taluka": "Haveli", "village": "Khed", "lat": 18.5204, "lng": 73.8567},
    {"district": "Pune", "taluka": "Baramati", "village": "Malegaon", "lat": 18.1519, "lng": 74.5771},
    {"district": "Nashik", "taluka": "Niphad", "village": "Pimpalgaon", "lat": 20.0984, "lng": 74.1039},
    {"district": "Nashik", "taluka": "Dindori", "village": "Vani", "lat": 20.2016, "lng": 73.8291},
    {"district": "Solapur", "taluka": "Pandharpur", "village": "Bhalwani", "lat": 17.6775, "lng": 75.3239},
    {"district": "Kolhapur", "taluka": "Kagal", "village": "Vathar", "lat": 16.5786, "lng": 74.3168},
    {"district": "Nagpur", "taluka": "Katol", "village": "Sawargaon", "lat": 21.2800, "lng": 78.5800},
    {"district": "Ahmednagar", "taluka": "Rahata", "village": "Shirdi", "lat": 19.7667, "lng": 74.4767},
    {"district": "Satara", "taluka": "Phaltan", "village": "Taradgaon", "lat": 17.9833, "lng": 74.4333},
    {"district": "Aurangabad", "taluka": "Paithan", "village": "Apegaon", "lat": 19.4797, "lng": 75.3850},
]

CROP_TYPES = [
    {"name": "Tomato", "varieties": ["Abhinav", "Heemsohna", "Lakshmi"], "diseases": ["Tomato Early Blight", "Tomato Late Blight", "Tomato Yellow Leaf Curl Virus", "Healthy Tomato"]},
    {"name": "Cotton", "varieties": ["RCH-659", "Bollgard II", "Bunny BG-II"], "diseases": ["Cotton Bacterial Blight", "Cotton Pink Bollworm Damage", "Cotton Leaf Curl Virus", "Healthy Cotton"]},
    {"name": "Rice", "varieties": ["Indrayani", "Basmati 370", "IR-64"], "diseases": ["Rice Blast", "Rice Brown Spot", "Rice Bacterial Blight", "Healthy Rice"]},
    {"name": "Chilli", "varieties": ["Byadgi", "Guntur Sannam", "Jwala"], "diseases": ["Chilli Leaf Curl Virus", "Chilli Anthracnose", "Healthy Chilli"]},
    {"name": "Sugarcane", "varieties": ["Co 86032", "Co 0238"], "diseases": ["Sugarcane Red Rot", "Sugarcane Rust", "Healthy Sugarcane"]},
    {"name": "Soybean", "varieties": ["JS 335", "KDS 726"], "diseases": ["Soybean Rust", "Soybean Yellow Mosaic Virus", "Healthy Soybean"]},
    {"name": "Wheat", "varieties": ["GW 322", "MACS 6222"], "diseases": ["Wheat Stripe Rust", "Wheat Loose Smut", "Healthy Wheat"]},
]

PEST_NAMES = ["Pink Bollworm", "Whitefly", "Fall Armyworm", "Yellow Stem Borer", "Aphids", "Thrips", "Spider Mites"]
SAMPLE_IMAGES = [
    "https://images.unsplash.com/photo-1592417817098-8f3d6eb147bc?q=80&w=600",
    "https://images.unsplash.com/photo-1530836369250-ef72a3f5cda8?q=80&w=600",
    "https://images.unsplash.com/photo-1625246333195-78d9c38ad449?q=80&w=600",
    "https://images.unsplash.com/photo-1595855759920-86582396756a?q=80&w=600",
]


def seed_database(db_url: str | None = None):
    """Execute the full database seed process."""
    target_url = db_url or settings.db_url
    print(f"Connecting to database: {target_url}...")
    engine = create_engine(target_url)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # 1. Seed Users
        print("Seeding Users...")
        farmers = []
        for i in range(1, 11):
            loc = MAHARASHTRA_LOCATIONS[(i - 1) % len(MAHARASHTRA_LOCATIONS)]
            farmer = User(
                name=f"Farmer {i} (Ramesh {['Patil', 'Deshmukh', 'Pawar', 'Kulkarni', 'Jadhav', 'Shinde', 'Chavan', 'Gaikwad', 'More', 'Kadam'][i-1]})",
                phone=f"+9198220{i:05d}",
                email=f"farmer{i}@krushirakshak.in",
                role=UserRole.farmer,
                state="Maharashtra",
                district=loc["district"],
                taluka=loc["taluka"],
                village=loc["village"],
                language_pref=random.choice(["mr", "hi", "en"]),
            )
            session.add(farmer)
            farmers.append(farmer)

        officers = []
        for i in range(1, 4):
            officer = User(
                name=f"Officer {i} (Dr. Anita {['Joshi', 'Bhosale', 'Sutar'][i-1]})",
                phone=f"+9198900{i:05d}",
                email=f"officer{i}@agri.maharashtra.gov.in",
                role=UserRole.officer,
                state="Maharashtra",
                district=["Pune", "Nashik", "Kolhapur"][i-1],
                language_pref="en",
            )
            session.add(officer)
            officers.append(officer)

        admin = User(
            name="Admin Director General",
            phone="+919000000001",
            email="admin@krushirakshak.gov.in",
            role=UserRole.admin,
            state="Maharashtra",
            language_pref="en",
        )
        session.add(admin)
        session.flush()

        # 2. Seed Farms
        print("Seeding Farms...")
        farms = []
        for i in range(1, 16):
            owner = random.choice(farmers)
            loc = MAHARASHTRA_LOCATIONS[i % len(MAHARASHTRA_LOCATIONS)]
            farm = Farm(
                owner_id=owner.id,
                name=f"{owner.name.split()[2]}'s {random.choice(['North', 'South', 'Riverside', 'Hilltop'])} Field",
                village=loc["village"],
                taluka=loc["taluka"],
                district=loc["district"],
                state="Maharashtra",
                gps_lat=loc["lat"] + random.uniform(-0.01, 0.01),
                gps_lng=loc["lng"] + random.uniform(-0.01, 0.01),
                area_acres=round(random.uniform(1.5, 12.0), 2),
                soil_type=random.choice(["Black Cotton Soil", "Red Alluvial", "Loamy Soil", "Laterite Soil"]),
                irrigation_type=random.choice(["Drip Irrigation", "Canal Irrigation", "Borewell Drip", "Rainfed"]),
            )
            session.add(farm)
            farms.append(farm)
        session.flush()

        # 3. Seed Crops
        print("Seeding Crops...")
        crops = []
        now = datetime.now(timezone.utc)
        for i in range(1, 26):
            farm = random.choice(farms)
            crop_spec = random.choice(CROP_TYPES)
            sow_days_ago = random.randint(30, 120)
            crop = Crop(
                farm_id=farm.id,
                crop_name=crop_spec["name"],
                variety=random.choice(crop_spec["varieties"]),
                sowing_date=(now - timedelta(days=sow_days_ago)).date(),
                growth_stage=random.choice(["Vegetative", "Flowering", "Fruiting", "Grain Filling", "Maturity"]),
                status=CropStatus.active if random.random() > 0.1 else CropStatus.harvested,
                expected_harvest_date=(now + timedelta(days=random.randint(20, 60))).date(),
            )
            session.add(crop)
            crops.append(crop)
        session.flush()

        # 4. Seed Observations & AI Results
        print("Seeding Observations & AI Results...")
        observations = []
        ai_results = []
        for i in range(1, 41):
            crop = random.choice(crops)
            crop_spec = next((c for c in CROP_TYPES if c["name"] == crop.crop_name), CROP_TYPES[0])
            disease = random.choice(crop_spec["diseases"])
            is_healthy = "Healthy" in disease
            days_ago = random.randint(1, 30)
            obs_time = now - timedelta(days=days_ago)

            obs = Observation(
                crop_id=crop.id,
                reported_by=crop.farm.owner_id,
                timestamp=obs_time,
                image_urls=[random.choice(SAMPLE_IMAGES)],
                notes=f"Leaf spot observed on upper canopy during morning round." if not is_healthy else "Crop appears healthy.",
                source=random.choice([ObservationSource.scan, ObservationSource.manual]),
                gps_lat=crop.farm.gps_lat,
                gps_lng=crop.farm.gps_lng,
            )
            session.add(obs)
            session.flush()
            observations.append(obs)

            ai_res = AIResult(
                observation_id=obs.id,
                disease_label=disease,
                confidence=round(random.uniform(0.78, 0.98), 2),
                severity_pct=0.0 if is_healthy else round(random.uniform(15.0, 75.0), 1),
                pest_label=random.choice(PEST_NAMES) if random.random() > 0.6 else None,
                pest_confidence=round(random.uniform(0.70, 0.92), 2) if random.random() > 0.6 else None,
                model_version="v1.2.0-resnet50",
                heat_map_url="https://krushirakshak.in/assets/heatmap_sample.png",
                treatment_recommendations={
                    "chemical": ["Spray Copper Oxychloride @ 2.5g/L", "Mancozeb 75 WP @ 2g/L"],
                    "organic": ["Neem Oil extract 10000 ppm @ 3ml/L", "Trichoderma viride bio-fungicide"],
                    "cultural": ["Ensure proper spacing and prune lower infected leaves to reduce humidity."],
                } if not is_healthy else {"message": "No treatment required. Maintain regular irrigation."},
            )
            session.add(ai_res)
            ai_results.append(ai_res)
        session.flush()

        # 5. Seed Weather Snapshots
        print("Seeding Weather Snapshots...")
        for farm in farms:
            for d in range(5):
                snapshot = WeatherSnapshot(
                    farm_id=farm.id,
                    timestamp=now - timedelta(days=d, hours=random.randint(0, 12)),
                    temp_c=round(random.uniform(24.0, 36.5), 1),
                    humidity_pct=round(random.uniform(55.0, 92.0), 1),
                    rainfall_mm=round(random.choice([0.0, 0.0, 2.5, 12.0, 45.0]), 1),
                    wind_speed_kmh=round(random.uniform(5.0, 22.0), 1),
                    condition_text=random.choice(["Partly Cloudy", "High Humidity", "Scattered Showers", "Sunny", "Overcast"]),
                )
                session.add(snapshot)
        session.flush()

        # 6. Seed Risk Scores & Alerts
        print("Seeding Risk Scores & Alerts...")
        for crop in crops[:15]:
            disease_risk = round(random.uniform(0.2, 0.9), 2)
            pest_risk = round(random.uniform(0.1, 0.8), 2)
            weather_risk = round(random.uniform(0.3, 0.85), 2)
            overall = round(0.4 * disease_risk + 0.3 * pest_risk + 0.3 * weather_risk, 2)

            if overall > 0.75:
                level = RiskLevel.critical
                alert_level = AlertLevel.critical
            elif overall > 0.55:
                level = RiskLevel.high
                alert_level = AlertLevel.danger
            elif overall > 0.35:
                level = RiskLevel.medium
                alert_level = AlertLevel.warning
            else:
                level = RiskLevel.low
                alert_level = AlertLevel.info

            risk_score = RiskScore(
                crop_id=crop.id,
                timestamp=now - timedelta(hours=random.randint(1, 48)),
                disease_risk=disease_risk,
                pest_risk=pest_risk,
                weather_risk=weather_risk,
                overall_score=overall,
                risk_level=level,
                contributing_factors={
                    "high_humidity": True if weather_risk > 0.6 else False,
                    "neighboring_outbreak": True if disease_risk > 0.6 else False,
                },
            )
            session.add(risk_score)
            session.flush()

            if alert_level in [AlertLevel.warning, AlertLevel.danger, AlertLevel.critical]:
                alert = Alert(
                    crop_id=crop.id,
                    risk_score_id=risk_score.id,
                    level=alert_level,
                    title=f"High Risk Alert: {crop.crop_name} Disease Hazard",
                    message=f"Environmental and AI diagnostic indicators show heightened threat of fungal outbreak on field '{crop.farm.name}'. Immediate preventative spray advised.",
                    acknowledged=random.choice([True, False]),
                    acknowledged_at=now - timedelta(hours=2) if random.choice([True, False]) else None,
                    acknowledged_by=officers[0].id if random.choice([True, False]) else None,
                )
                session.add(alert)
        session.flush()

        # 7. Seed Expert Validations
        print("Seeding Expert Validations...")
        for ai_res in ai_results[:15]:
            officer = random.choice(officers)
            verdict = random.choice([ValidationVerdict.confirmed, ValidationVerdict.confirmed, ValidationVerdict.corrected])
            val = ExpertValidation(
                ai_result_id=ai_res.id,
                officer_id=officer.id,
                verdict=verdict,
                corrected_label=None if verdict == ValidationVerdict.confirmed else f"Severe {ai_res.disease_label}",
                notes="Confirmed after field visit and microscopic sample verification." if verdict == ValidationVerdict.confirmed else "Slightly misclassified severity; updated to severe.",
                timestamp=now - timedelta(days=random.randint(1, 10)),
            )
            session.add(val)
        session.flush()

        # 8. Seed FollowUps
        print("Seeding FollowUps...")
        for i in range(min(8, len(observations) - 1)):
            prev_obs = observations[i]
            new_obs = observations[i + 1]
            followup = FollowUp(
                crop_id=prev_obs.crop_id,
                previous_observation_id=prev_obs.id,
                new_observation_id=new_obs.id,
                severity_before=45.0,
                severity_after=15.0,
                status=FollowUpStatus.improving,
                notes="Copper Oxychloride spray applied 5 days ago. Symptoms significantly reduced on new leaves.",
            )
            session.add(followup)

        # 9. Seed Pest Trap Readings
        print("Seeding Pest Trap Readings...")
        for farm in farms[:10]:
            reading = PestTrapReading(
                farm_id=farm.id,
                trap_type=random.choice(["Pheromone Trap (Pink Bollworm)", "Yellow Sticky Trap", "Light Trap"]),
                location_description="Center of southern quadrant plot",
                installed_at=now - timedelta(days=20),
                last_checked_at=now - timedelta(days=random.randint(1, 5)),
                image_url=random.choice(SAMPLE_IMAGES),
                pest_count=random.randint(5, 45),
                dominant_pest=random.choice(PEST_NAMES),
            )
            session.add(reading)

        session.commit()
        print("Database successfully seeded with realistic sample data!")

    except Exception as e:
        session.rollback()
        print(f"Error seeding database: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    seed_database()
