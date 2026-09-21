import io
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional, List
from PIL import Image

from app.db.connection import get_db
from app.db.models import User, UserRole, Farm, Crop, CropStatus, Observation, AIResult
from app.models.schemas import (
    DiseaseDetectionResponse,
    FarmerReportSummary,
    WeatherResponse,
    FarmerRegisterRequest,
    UserResponse,
    FarmCreateRequest,
    FarmResponse,
    CropCreateRequest,
    CropResponse,
)
from app.ml.disease_classifier import get_disease_classifier
from app.services.weather import get_weather_risk
from app.services.advisory import generate_advisory
from app.core.dependencies import get_current_user, require_farmer

router = APIRouter()


# ---------------------------------------------------------------------------
# Farmer Onboarding & CRUD
# ---------------------------------------------------------------------------

@router.post("/register", response_model=UserResponse, summary="Register a new farmer")
def register_farmer(payload: FarmerRegisterRequest, db: Session = Depends(get_db)):
    """Create a new farmer user or return existing farmer if phone matches."""
    existing_user = db.query(User).filter(User.phone == payload.phone).first()
    if existing_user:
        return existing_user

    new_user = User(
        name=payload.name,
        phone=payload.phone,
        role=UserRole.farmer,
        state=payload.state,
        district=payload.district,
        taluka=payload.taluka,
        village=payload.village,
        language_pref=payload.language_pref or "en",
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.post("/farms", response_model=FarmResponse, summary="Register a new farm plot")
def create_farm(
    payload: FarmCreateRequest,
    current_user: User = Depends(require_farmer),
    db: Session = Depends(get_db)
):
    """Create a farm plot for the authenticated farmer."""
    # Override owner_id with the authenticated user's ID
    new_farm = Farm(
        owner_id=current_user.id,
        name=payload.name,
        village=payload.village,
        taluka=payload.taluka,
        district=payload.district,
        state=payload.state,
        gps_lat=payload.gps_lat,
        gps_lng=payload.gps_lng,
        area_acres=payload.area_acres,
        soil_type=payload.soil_type,
        irrigation_type=payload.irrigation_type,
    )
    db.add(new_farm)
    db.commit()
    db.refresh(new_farm)
    return new_farm


@router.get("/farms", response_model=List[FarmResponse], summary="Get all farms for authenticated farmer")
def get_farmer_farms(
    current_user: User = Depends(require_farmer),
    db: Session = Depends(get_db)
):
    """List all farms owned by the authenticated farmer."""
    farms = db.query(Farm).filter(Farm.owner_id == current_user.id).order_by(Farm.created_at.desc()).all()
    return farms


@router.post("/crops", response_model=CropResponse, summary="Register a planted crop in a farm")
def create_crop(
    payload: CropCreateRequest,
    current_user: User = Depends(require_farmer),
    db: Session = Depends(get_db)
):
    """Record a planted crop with sowing date."""
    farm = db.query(Farm).filter(Farm.id == payload.farm_id, Farm.owner_id == current_user.id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found or access denied")

    new_crop = Crop(
        farm_id=payload.farm_id,
        crop_type=payload.crop_type,
        variety=payload.variety,
        sowing_date=payload.sowing_date,
        stage=payload.stage or "vegetative",
        status=CropStatus.active,
        acreage=payload.acreage or farm.area_acres,
    )
    db.add(new_crop)
    db.commit()
    db.refresh(new_crop)
    return new_crop


@router.get("/crops/{farm_id}", response_model=List[CropResponse], summary="List crops for a farm")
def get_farm_crops(
    farm_id: str,
    current_user: User = Depends(require_farmer),
    db: Session = Depends(get_db)
):
    """List all crops registered under a given farm (must own the farm)."""
    farm = db.query(Farm).filter(Farm.id == farm_id, Farm.owner_id == current_user.id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found or access denied")
    crops = db.query(Crop).filter(Crop.farm_id == farm_id).order_by(Crop.created_at.desc()).all()
    return crops


# ---------------------------------------------------------------------------
# Diagnostics & Reports
# ---------------------------------------------------------------------------

@router.post("/detect", response_model=DiseaseDetectionResponse, summary="Upload crop image for disease detection")
async def detect_crop_disease(
    image: UploadFile = File(..., description="Crop leaf/plant image"),
    crop_type: str = Form(..., description="e.g. wheat, rice, tomato"),
    farm_id: Optional[str] = Form(None),
    latitude: Optional[float] = Form(None),
    longitude: Optional[float] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Diagnose disease from image using the classifier engine."""
    # If farm_id is provided, verify ownership
    if farm_id:
        farm = db.query(Farm).filter(Farm.id == farm_id, Farm.owner_id == current_user.id).first()
        if not farm:
            raise HTTPException(status_code=403, detail="Access denied to this farm")
    
    image_bytes = await image.read()
    try:
        pil_image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid image file: {exc}")

    classifier = get_disease_classifier()
    scan_result = classifier.scan_crop_image(pil_image)

    disease_name = scan_result.get("label", "Unknown")
    confidence = float(scan_result.get("confidence", 0.0))
    severity_pct = float(scan_result.get("severity_pct", 0.0))
    severity_level = "high" if severity_pct > 50 else ("medium" if severity_pct > 20 else "low")

    advisory = generate_advisory(disease_name, severity_level, crop_type)

    return DiseaseDetectionResponse(
        disease_name=disease_name,
        confidence=confidence,
        severity=severity_level,
        advisory=advisory,
    )


@router.get("/weather", response_model=WeatherResponse, summary="Get weather risk for a location")
def weather_risk(lat: float, lon: float):
    return get_weather_risk(lat, lon)


@router.get("/reports", response_model=List[FarmerReportSummary], summary="Get authenticated farmer's report history")
def get_farmer_reports(
    current_user: User = Depends(require_farmer),
    db: Session = Depends(get_db)
):
    """Fetch past diagnostic observations and results for the authenticated farmer."""
    observations = (
        db.query(Observation)
        .filter(Observation.reported_by == current_user.id)
        .order_by(Observation.created_at.desc())
        .all()
    )

    reports: List[FarmerReportSummary] = []
    for obs in observations:
        crop_type = obs.crop.crop_type if obs.crop else "Unknown"
        disease_name = obs.ai_result.disease_label if obs.ai_result else "Undetected"
        severity = f"{obs.ai_result.severity_pct:.1f}%" if (obs.ai_result and obs.ai_result.severity_pct is not None) else "low"

        reports.append(FarmerReportSummary(
            report_id=obs.id,
            crop_type=crop_type,
            disease_name=disease_name,
            severity=severity,
            created_at=obs.created_at,
        ))

    return reports
