"""
AIResult model — AI diagnostic prediction for a given Observation.
"""
import uuid
from datetime import datetime

from sqlalchemy import String, Float, DateTime, ForeignKey, JSON, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class AIResult(Base):
    __tablename__ = "ai_results"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    observation_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("observations.id", ondelete="CASCADE"), unique=True, nullable=False, index=True
    )

    disease_label: Mapped[str | None] = mapped_column(String(150), nullable=True, index=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    severity_pct: Mapped[float | None] = mapped_column(Float, nullable=True)

    pest_label: Mapped[str | None] = mapped_column(String(150), nullable=True)
    pest_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)

    model_version: Mapped[str] = mapped_column(String(50), default="v1.0.0", nullable=False)
    heat_map_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    treatment_recommendations: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    observation: Mapped["Observation"] = relationship("Observation", back_populates="ai_result")
    expert_validations: Mapped[list["ExpertValidation"]] = relationship(
        "ExpertValidation", back_populates="ai_result", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<AIResult id={self.id!r} disease={self.disease_label!r} conf={self.confidence}>"
