"""
PestTrapReading model — record of pest trap inspections and count logs.
"""
import uuid
from datetime import datetime

from sqlalchemy import String, Integer, Float, DateTime, ForeignKey, func, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class PestTrapReading(Base):
    __tablename__ = "pest_trap_readings"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    farm_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("farms.id", ondelete="CASCADE"), nullable=False, index=True
    )

    trap_type: Mapped[str] = mapped_column(
        String(100), default="Pheromone Trap", nullable=False
    )  # e.g., Pheromone Trap, Yellow Sticky Trap, Light Trap
    location_description: Mapped[str | None] = mapped_column(String(255), nullable=True)

    installed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_checked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    pest_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    dominant_pest: Mapped[str | None] = mapped_column(String(150), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    farm: Mapped["Farm"] = relationship("Farm", back_populates="pest_trap_readings")

    __table_args__ = (
        Index("ix_pest_trap_readings_farm_checked", "farm_id", "last_checked_at"),
    )

    def __repr__(self) -> str:
        return f"<PestTrapReading farm={self.farm_id!r} type={self.trap_type!r} count={self.pest_count}>"
