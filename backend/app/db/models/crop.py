"""
Crop model — tracks individual crops cultivated on a Farm.
"""
import uuid
import enum
from datetime import date, datetime

from sqlalchemy import String, Date, DateTime, ForeignKey, Enum as SAEnum, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class CropStatus(str, enum.Enum):
    active = "active"
    harvested = "harvested"
    abandoned = "abandoned"
    destroyed = "destroyed"


class Crop(Base):
    __tablename__ = "crops"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    farm_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("farms.id", ondelete="CASCADE"), nullable=False, index=True
    )

    crop_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    variety: Mapped[str | None] = mapped_column(String(100), nullable=True)
    sowing_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    growth_stage: Mapped[str | None] = mapped_column(String(50), nullable=True)  # e.g., Vegetative, Flowering, Harvesting
    status: Mapped[CropStatus] = mapped_column(
        SAEnum(CropStatus, name="cropstatus", native_enum=False),
        default=CropStatus.active,
        nullable=False,
        index=True,
    )
    expected_harvest_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    farm: Mapped["Farm"] = relationship("Farm", back_populates="crops")
    observations: Mapped[list["Observation"]] = relationship(
        "Observation", back_populates="crop", cascade="all, delete-orphan"
    )
    risk_scores: Mapped[list["RiskScore"]] = relationship(
        "RiskScore", back_populates="crop", cascade="all, delete-orphan"
    )
    alerts: Mapped[list["Alert"]] = relationship(
        "Alert", back_populates="crop", cascade="all, delete-orphan"
    )
    followups: Mapped[list["FollowUp"]] = relationship(
        "FollowUp", back_populates="crop", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Crop id={self.id!r} crop_name={self.crop_name!r} status={self.status}>"
