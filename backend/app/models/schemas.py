from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: datetime
    db_connected: bool


class ChatConversationCreate(BaseModel):
    farm_id: str
    officer_id: str
    scan_id: Optional[str] = None


class ChatMessageCreate(BaseModel):
    body: str = ""
    attachment_url: Optional[str] = None
    lang: Optional[str] = "en"


class ChatMessageResponse(BaseModel):
    id: str
    conversation_id: str
    sender_id: str
    sender_role: str
    body: str
    attachment_url: Optional[str] = None
    lang: str
    created_at: datetime
    read_at: Optional[datetime] = None


class ChatConversationResponse(BaseModel):
    id: str
    farm_id: str
    farmer_id: str
    officer_id: str
    scan_id: Optional[str] = None
    status: str
    created_at: datetime
    unread_count: int = 0
    last_message: Optional[ChatMessageResponse] = None
    scan_label: Optional[str] = None
    scan_image_url: Optional[str] = None
    heat_map_url: Optional[str] = None


class ChatPageResponse(BaseModel):
    items: List[ChatMessageResponse]
    total: int
    offset: int
    limit: int


class TopPrediction(BaseModel):
    label: str
    confidence: float
    disease_key: Optional[str] = None
    localized_label: Optional[str] = None


class ScanResponse(BaseModel):
    label: str
    scan_id: Optional[str] = None
    disease_key: Optional[str] = None
    localized_label: Optional[str] = None
    confidence: float
    top3: List[TopPrediction]
    severity_estimate: float = Field(..., description="Estimated percentage of leaf area affected (0.0 to 100.0)")
    severity_pct: float = Field(..., description="Estimated percentage of leaf area affected (0.0 to 100.0)")
    gradcam_image_base64: str = Field(..., description="Base64 encoded PNG data URI of Grad-CAM heatmap overlay")
    low_confidence: bool = Field(..., description="True if top prediction confidence is below 0.60 threshold")
    status: str = Field(default="confident", description="Status of prediction: 'confident' or 'uncertain'")
    status_key: Optional[str] = None
    severity_key: Optional[str] = None
    language: str = "en"
    observation_id: Optional[str] = Field(None, description="Persisted observation record ID")
    image_url: Optional[str] = Field(None, description="Relative URL of the stored scan image")



class RiskScoreRequest(BaseModel):
    crop_id: str = Field(..., example="550e8400-e29b-41d4-a716-446655440000")


class RiskWhyFactor(BaseModel):
    factor: str
    details: str
    impact_score: float
    factor_key: Optional[str] = None


class RiskForecastDay(BaseModel):
    day: str
    date: str
    predicted_risk_score: float
    risk_level: str
    risk_level_key: Optional[str] = None
    temp_max: float
    rain_mm: float


class RiskScoreResponse(BaseModel):
    crop_id: str
    overall_score: float
    risk_level: str  # LOW / MODERATE / HIGH / CRITICAL
    risk_level_key: Optional[str] = None
    language: str = "en"
    disease_risk: float
    pest_risk: float
    weather_risk: float
    why: List[RiskWhyFactor]
    forecast: List[RiskForecastDay]


class AdvisoryRequest(BaseModel):
    crop_id: Optional[str] = None
    ai_result_id: Optional[str] = None
    disease_label: Optional[str] = Field(default="Tomato___Early_blight", example="Tomato___Early_blight")
    severity_pct: float = Field(default=25.0, example=32.5)
    crop_name: Optional[str] = Field(default="Tomato", example="Tomato")
    growth_stage: Optional[str] = Field(default="flowering", example="flowering")
    language_pref: Optional[str] = Field(default="en", example="mr")


class AdvisoryTreatments(BaseModel):
    chemical: List[str]
    organic: List[str]
    cultural: List[str]


class AdvisoryResponse(BaseModel):
    disease_label: str
    disease_name_formatted: str
    severity_pct: float
    severity_category: str
    crop_name: str
    growth_stage: str
    language: str
    treatments: AdvisoryTreatments
    urgency_level: str


class LanguageAdvisoryContent(BaseModel):
    summary: str
    action_steps: List[str]


class RAGAdvisoryResponse(BaseModel):
    crop_id: Optional[str] = None
    ai_result_id: Optional[str] = None
    match_confidence: str = Field(..., description="exact_match, fuzzy_match, or generic_fallback")
    kb_entry_found: bool = Field(..., description="True if IPM knowledge base entry was found")
    advisory: Dict[str, LanguageAdvisoryContent] = Field(..., description="Multilingual advisories in en, hi, mr")
    advisory_key: Optional[str] = None
    disease_key: Optional[str] = None
    crop_key: Optional[str] = None
    language: str = "en"
    retrieved_kb: Dict[str, Any] = Field(..., description="Retrieved IPM Knowledge Base entry (ground truth)")


class ExpertValidationRequest(BaseModel):
    ai_result_id: str
    officer_id: str
    verdict: str = Field(..., example="confirmed")  # confirmed / corrected / referred
    corrected_label: Optional[str] = None
    notes: Optional[str] = None


class ExpertValidationResponse(BaseModel):
    id: str
    ai_result_id: str
    officer_id: str
    verdict: str
    corrected_label: Optional[str]
    notes: Optional[str]
    timestamp: datetime


class AdminAlertRequest(BaseModel):
    crop_id: Optional[str] = None
    level: str = Field(default="warning", example="danger")  # info / warning / danger / critical
    title: str = Field(..., example="High Late Blight Outbreak Risk")
    message: str = Field(..., example="Preventative fungicidal spray recommended across Nashik district.")
    target_state: Optional[str] = "Maharashtra"
    target_district: Optional[str] = None


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
    model_accuracy: Optional[float] = None
    alerts_issued: int


class FarmerRegisterRequest(BaseModel):
    name: str
    phone: str
    state: Optional[str] = None
    district: Optional[str] = None
    taluka: Optional[str] = None
    village: Optional[str] = None
    language_pref: Optional[str] = "en"


class UserResponse(BaseModel):
    id: str
    name: str
    phone: str
    role: str
    state: Optional[str] = None
    district: Optional[str] = None
    village: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class FarmCreateRequest(BaseModel):
    owner_id: str
    name: str
    village: str
    taluka: str
    district: str
    state: str
    gps_lat: float
    gps_lng: float
    area_acres: float
    soil_type: Optional[str] = None
    irrigation_type: Optional[str] = None


class FarmResponse(BaseModel):
    id: str
    owner_id: str
    name: str
    village: str
    taluka: str
    district: str
    state: str
    gps_lat: float
    gps_lng: float
    area_acres: float
    created_at: datetime

    class Config:
        from_attributes = True


class CropCreateRequest(BaseModel):
    farm_id: str
    crop_type: str
    variety: Optional[str] = None
    sowing_date: datetime
    stage: Optional[str] = "vegetative"
    acreage: Optional[float] = None


class CropResponse(BaseModel):
    id: str
    farm_id: str
    crop_type: str
    variety: Optional[str] = None
    sowing_date: datetime
    stage: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

