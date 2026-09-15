"""
Database models package.
Importing this package registers all SQLAlchemy models with Base.metadata.
"""
from app.db.base import Base
from app.db.models.user import User, UserRole
from app.db.models.farm import Farm
from app.db.models.crop import Crop, CropStatus
from app.db.models.observation import Observation, ObservationSource
from app.db.models.ai_result import AIResult
from app.db.models.weather_snapshot import WeatherSnapshot
from app.db.models.risk_score import RiskScore, RiskLevel
from app.db.models.alert import Alert, AlertLevel
from app.db.models.expert_validation import ExpertValidation, ValidationVerdict
from app.db.models.follow_up import FollowUp, FollowUpStatus
from app.db.models.pest_trap import PestTrapReading
from app.db.models.historical_outbreak import HistoricalOutbreak

__all__ = [
    "Base",
    "User",
    "UserRole",
    "Farm",
    "Crop",
    "CropStatus",
    "Observation",
    "ObservationSource",
    "AIResult",
    "WeatherSnapshot",
    "RiskScore",
    "RiskLevel",
    "Alert",
    "AlertLevel",
    "ExpertValidation",
    "ValidationVerdict",
    "FollowUp",
    "FollowUpStatus",
    "PestTrapReading",
    "HistoricalOutbreak",
]
