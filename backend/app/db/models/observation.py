"""
Observation model — record of field inspection, camera upload, or trap scan.
"""
import uuid
import enum
from datetime import datetime

from sqlalchemy import String, DateTime, Text, Float, ForeignKey, JSON, Enum as SAEnum, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ObservationSource(str, enum.Enum):
    manual = "manual"
    scan = "scan"
    trap = "trap"
    satellite = "satellite"


class Observation(Base):
    __tablename__ = "observations"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    crop_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("crops.id", ondelete="CASCADE"), nullable=False, index=True
    )
    reported_by: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    image_urls: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[ObservationSource] = mapped_column(
        SAEnum(ObservationSource, name="observationsource", native_enum=False),
        default=ObservationSource.scan,
        nullable=False,
    )

    gps_lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    gps_lng: Mapped[float | None] = mapped_column(Float, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    crop: Mapped["Crop"] = relationship("Crop", back_populates="observations")
    reported_by_user: Mapped["User | None"] = relationship(
        "User", back_populates="observations_reported", foreign_keys=[reported_by]
    )
    ai_result: Mapped["AIResult | None"] = relationship(
        "AIResult", back_populates="observation", uselist=False, cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Observation id={self.id!r} crop_id={self.crop_id!r} source={self.source}>"
