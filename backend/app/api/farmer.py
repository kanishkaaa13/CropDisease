from fastapi import APIRouter, UploadFile, File, Form, Depends
from sqlalchemy.orm import Session
from typing import Optional

from app.db.connection import get_db
from app.models.schemas import DiseaseDetectionResponse, FarmerReportSummary, WeatherResponse
from app.services.disease_detection import detect_disease
from app.services.weather import get_weather_risk
from app.services.advisory import generate_advisory

router = APIRouter()


@router.post("/detect", response_model=DiseaseDetectionResponse, summary="Upload crop image for disease detection")
async def detect_crop_disease(
    image: UploadFile = File(..., description="Crop leaf/plant image"),
    crop_type: str = Form(..., description="e.g. wheat, rice, tomato"),
    farmer_id: Optional[str] = Form(None),
    latitude: Optional[float] = Form(None),
    longitude: Optional[float] = Form(None),
    db: Session = Depends(get_db),
):
    image_bytes = await image.read()
    result = detect_disease(image_bytes, crop_type)
    advisory = generate_advisory(result["disease_name"], result["severity"], crop_type)
    return DiseaseDetectionResponse(**result, advisory=advisory)


@router.get("/weather", response_model=WeatherResponse, summary="Get weather risk for a location")
def weather_risk(lat: float, lon: float):
    return get_weather_risk(lat, lon)


@router.get("/reports/{farmer_id}", response_model=list[FarmerReportSummary], summary="Get farmer's report history")
def get_farmer_reports(farmer_id: str, db: Session = Depends(get_db)):
    from app.db.models import DiseaseReport
    reports = db.query(DiseaseReport).filter(DiseaseReport.farmer_id == farmer_id).order_by(DiseaseReport.created_at.desc()).all()
    return reports
