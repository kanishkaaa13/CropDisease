"""
Risk Engine Service
-------------------
Aggregates disease reports by district and computes a risk score for
officer dashboards and the government command center map.
"""
from sqlalchemy.orm import Session
from sqlalchemy import func


def compute_district_risk(state: str, db: Session) -> list[dict]:
    """
    Return a list of district-level risk records for a given state.
    Each record contains: district, report_count, high_severity_count, risk_score.
    """
    from app.db.models import DiseaseReport, User

    rows = (
        db.query(
            User.district,
            func.count(DiseaseReport.id).label("total"),
            func.sum(
                func.cast(DiseaseReport.severity == "high", db.bind.dialect.name == "postgresql" and "integer" or "integer")
            ).label("high_count"),
        )
        .join(DiseaseReport, DiseaseReport.farmer_id == User.id)
        .filter(User.state == state)
        .group_by(User.district)
        .all()
    )

    results = []
    for row in rows:
        total = row.total or 0
        high = int(row.high_count or 0)
        risk_score = round(min((high / max(total, 1)) * 100, 100), 1)
        risk_level = "high" if risk_score > 60 else "medium" if risk_score > 25 else "low"
        results.append({
            "district": row.district or "Unknown",
            "report_count": total,
            "high_severity_count": high,
            "risk_score": risk_score,
            "risk_level": risk_level,
        })

    return results
