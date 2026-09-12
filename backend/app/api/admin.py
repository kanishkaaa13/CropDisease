from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.connection import get_db
from app.models.schemas import AdminCommandStats

router = APIRouter()


@router.get("/stats", response_model=AdminCommandStats, summary="Government command center KPIs")
def admin_stats(db: Session = Depends(get_db)):
    from app.db.models import User, DiseaseReport
    farmers = db.query(User).count()
    reports = db.query(DiseaseReport).count()
    states = db.query(User.state).distinct().count()
    return AdminCommandStats(
        total_farmers=farmers,
        total_reports=reports,
        states_covered=states,
        model_accuracy=0.94,  # placeholder — replace with real model eval metric
        alerts_issued=0,
    )


@router.post("/alert", summary="Broadcast advisory alert to a region")
def broadcast_alert(state: str, message: str):
    # TODO: integrate with SMS / push notification service
    return {"status": "queued", "state": state, "message": message}
