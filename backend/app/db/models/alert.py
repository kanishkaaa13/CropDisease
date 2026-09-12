"""
Alert model — notifications sent to farmers/officers when risk thresholds are breached.
"""
import uuid
import enum
from datetime import datetime

from sqlalchemy import String, DateTime, Text, Boolean, ForeignKey, Enum as SAEnum, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class AlertLevel(str, enum.Enum):
    info = "info"
    warning = "warning"
    danger = "danger"
    critical = "critical"


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    crop_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("crops.id", ondelete="CASCADE"), nullable=False, index=True
    )
    risk_score_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("risk_scores.id", ondelete="SET NULL"), nullable=True, index=True
    )

    level: Mapped[AlertLevel] = mapped_column(
        SAEnum(AlertLevel, name="alertlevel", native_enum=False),
        default=AlertLevel.warning,
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)

    acknowledged: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    acknowledged_by: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    # Relationships
    crop: Mapped["Crop"] = relationship("Crop", back_populates="alerts")
    risk_score: Mapped["RiskScore | None"] = relationship("RiskScore", back_populates="alerts")
    acknowledged_by_user: Mapped["User | None"] = relationship(
        "User", back_populates="alerts_acknowledged", foreign_keys=[acknowledged_by]
    )

    def __repr__(self) -> str:
        return f"<Alert id={self.id!r} level={self.level} acknowledged={self.acknowledged}>"
