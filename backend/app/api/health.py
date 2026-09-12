from datetime import datetime, timezone
from fastapi import APIRouter
from sqlalchemy import text

from app.db.connection import SessionLocal
from app.models.schemas import HealthResponse

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
def health_check():
    """Health-check endpoint — confirms API is up and DB is reachable."""
    db_ok = False
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        db_ok = True
    except Exception:
        db_ok = False

    return HealthResponse(
        status="ok",
        version="1.0.0",
        timestamp=datetime.now(timezone.utc),
        db_connected=db_ok,
    )
