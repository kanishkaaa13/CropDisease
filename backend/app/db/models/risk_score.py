"""
RiskScore model — calculated disease, pest, and weather risk scores for a Crop.
"""
import uuid
import enum
from datetime import datetime

from sqlalchemy import String, Float, DateTime, ForeignKey, JSON, Enum as SAEnum, func, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class RiskLevel(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class RiskScore(Base):
    __tablename__ = "risk_scores"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    crop_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("crops.id", ondelete="CASCADE"), nullable=False, index=True
    )

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    disease_risk: Mapped[float] = mapped_column(Float, nullable=False)   # 0.0 to 1.0
    pest_risk: Mapped[float] = mapped_column(Float, nullable=False)      # 0.0 to 1.0
    weather_risk: Mapped[float] = mapped_column(Float, nullable=False)   # 0.0 to 1.0
    overall_score: Mapped[float] = mapped_column(Float, nullable=False)  # 0.0 to 1.0

    risk_level: Mapped[RiskLevel] = mapped_column(
        SAEnum(RiskLevel, name="risklevel", native_enum=False),
        nullable=False,
        index=True,
    )

    contributing_factors: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    crop: Mapped["Crop"] = relationship("Crop", back_populates="risk_scores")
    alerts: Mapped[list["Alert"]] = relationship("Alert", back_populates="risk_score")

    __table_args__ = (
        Index("ix_risk_scores_crop_timestamp", "crop_id", "timestamp"),
    )

    def __repr__(self) -> str:
        return f"<RiskScore crop={self.crop_id!r} overall={self.overall_score:.2f} level={self.risk_level}>"
