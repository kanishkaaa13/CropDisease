"""
WeatherSnapshot model — historical & real-time weather readings for a Farm.
"""
import uuid
from datetime import datetime

from sqlalchemy import String, Float, DateTime, ForeignKey, func, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class WeatherSnapshot(Base):
    __tablename__ = "weather_snapshots"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    farm_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("farms.id", ondelete="CASCADE"), nullable=False, index=True
    )

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    temp_c: Mapped[float] = mapped_column(Float, nullable=False)
    humidity_pct: Mapped[float] = mapped_column(Float, nullable=False)
    rainfall_mm: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    wind_speed_kmh: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    condition_text: Mapped[str | None] = mapped_column(String(100), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    farm: Mapped["Farm"] = relationship("Farm", back_populates="weather_snapshots")

    __table_args__ = (
        Index("ix_weather_snapshots_farm_timestamp", "farm_id", "timestamp"),
    )

    def __repr__(self) -> str:
        return f"<WeatherSnapshot farm={self.farm_id!r} temp={self.temp_c}°C humidity={self.humidity_pct}%>"
