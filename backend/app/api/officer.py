from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.connection import get_db
from app.models.schemas import OfficerDashboardStats
from app.services.risk_engine import compute_district_risk

router = APIRouter()


@router.get("/dashboard", response_model=OfficerDashboardStats, summary="Officer dashboard statistics")
def officer_dashboard(db: Session = Depends(get_db)):
    from app.db.models import DiseaseReport, User
    total = db.query(DiseaseReport).count()
    high_sev = db.query(DiseaseReport).filter(DiseaseReport.severity == "high").count()
    # Distinct districts via users
    districts = (
        db.query(User.district)
        .join(DiseaseReport, DiseaseReport.farmer_id == User.id)
        .distinct()
        .count()
    )
    return OfficerDashboardStats(
        total_reports=total,
        high_severity_count=high_sev,
        affected_districts=districts,
        top_diseases=[{"name": "Mock Disease", "count": total}],
    )


@router.get("/risk-map", summary="District-level risk heatmap data")
def risk_map(state: str = "Maharashtra", db: Session = Depends(get_db)):
    return compute_district_risk(state, db)
