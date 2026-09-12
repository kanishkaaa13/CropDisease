from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional


class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: datetime
    db_connected: bool


class DiseaseDetectionRequest(BaseModel):
    crop_type: str = Field(..., example="wheat")
    farmer_id: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class DiseaseDetectionResponse(BaseModel):
    disease_name: str
    confidence: float
    severity: str
    advisory: str
    report_id: Optional[str] = None


class WeatherResponse(BaseModel):
    temperature: float
    humidity: float
    wind_speed: float
    description: str
    risk_level: str  # low / medium / high


class FarmerReportSummary(BaseModel):
    report_id: str
    crop_type: str
    disease_name: Optional[str]
    severity: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class OfficerDashboardStats(BaseModel):
    total_reports: int
    high_severity_count: int
    affected_districts: int
    top_diseases: list[dict]


class AdminCommandStats(BaseModel):
    total_farmers: int
    total_reports: int
    states_covered: int
    model_accuracy: float
    alerts_issued: int
