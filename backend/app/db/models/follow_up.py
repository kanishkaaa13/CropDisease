"""
FollowUp model — tracks progression between an initial observation and subsequent checkups.
"""
import uuid
import enum
from datetime import datetime

from sqlalchemy import String, Float, DateTime, Text, ForeignKey, Enum as SAEnum, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class FollowUpStatus(str, enum.Enum):
    improving = "improving"
    stable = "stable"
    worsening = "worsening"
    resolved = "resolved"


class FollowUp(Base):
    __tablename__ = "follow_ups"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    crop_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("crops.id", ondelete="CASCADE"), nullable=False, index=True
    )
    previous_observation_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("observations.id", ondelete="CASCADE"), nullable=False
    )
    new_observation_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("observations.id", ondelete="CASCADE"), nullable=False
    )

    severity_before: Mapped[float] = mapped_column(Float, nullable=False)  # 0 to 100%
    severity_after: Mapped[float] = mapped_column(Float, nullable=False)   # 0 to 100%

    status: Mapped[FollowUpStatus] = mapped_column(
        SAEnum(FollowUpStatus, name="followupstatus", native_enum=False),
        nullable=False,
        index=True,
    )

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    crop: Mapped["Crop"] = relationship("Crop", back_populates="followups")
    previous_observation: Mapped["Observation"] = relationship(
        "Observation", foreign_keys=[previous_observation_id]
    )
    new_observation: Mapped["Observation"] = relationship(
        "Observation", foreign_keys=[new_observation_id]
    )

    def __repr__(self) -> str:
        return f"<FollowUp crop={self.crop_id!r} status={self.status} before={self.severity_before}% after={self.severity_after}%>"
