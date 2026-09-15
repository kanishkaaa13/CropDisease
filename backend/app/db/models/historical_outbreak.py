"""
HistoricalOutbreak model — records historical disease outbreaks by village and crop.
Used for spatial risk analysis and local disease history.
"""
import uuid
from datetime import datetime

from sqlalchemy import String, Integer, Float, DateTime, ForeignKey, func, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class HistoricalOutbreak(Base):
    __tablename__ = "historical_outbreaks"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    
    # Location identifiers
    village: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    district: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    state: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    
    # Crop and disease information
    crop_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    disease_label: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    
    # Outbreak severity and extent
    severity_level: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # low, moderate, high, severe
    
    affected_farms_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_area_affected_hectares: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    
    # Seasonal information
    season: Mapped[str] = mapped_column(String(50), nullable=True)  # e.g., Kharif, Rabi
    year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    
    # Timestamps
    outbreak_start_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    outbreak_end_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        Index("ix_historical_outbreaks_village_crop", "village", "crop_name"),
        Index("ix_historical_outbreaks_year_season", "year", "season"),
    )

    def __repr__(self) -> str:
        return (
            f"<HistoricalOutbreak village={self.village!r} "
            f"crop={self.crop_name!r} disease={self.disease_label!r} "
            f"year={self.year!r}>"
        )
