"""
Farm model — represents a physical agricultural field owned by a farmer.
PostGIS `location` column stores a POINT(lng, lat) in WGS84 (SRID 4326)
for spatial queries. Raw `gps_lat` / `gps_lng` floats are kept for simple
non-spatial lookups without needing ST_ functions.

Geospatial query example (within 5 km):
    SELECT * FROM farms
    WHERE ST_DWithin(
        location::geography,
        ST_MakePoint(:lng, :lat)::geography,
        5000   -- metres
    );
"""
import uuid
from datetime import datetime

from sqlalchemy import String, Float, DateTime, ForeignKey, func, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

try:
    from geoalchemy2 import Geometry  # type: ignore[import]
    _HAS_GEOALCHEMY = True
except ImportError:
    _HAS_GEOALCHEMY = False

from app.db.base import Base


class Farm(Base):
    __tablename__ = "farms"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    owner_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Identity
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Address hierarchy
    village: Mapped[str] = mapped_column(String(150), nullable=False)
    taluka: Mapped[str] = mapped_column(String(150), nullable=False)
    district: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    state: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    # GPS — raw floats for simple queries
    gps_lat: Mapped[float] = mapped_column(Float, nullable=False)
    gps_lng: Mapped[float] = mapped_column(Float, nullable=False)

    # PostGIS geometry column (POINT, WGS84). Falls back to None if geoalchemy2 not installed.
    if _HAS_GEOALCHEMY:
        location: Mapped[object | None] = mapped_column(
            Geometry(geometry_type="POINT", srid=4326), nullable=True
        )

    # Farm metadata
    area_acres: Mapped[float] = mapped_column(Float, nullable=False)
    soil_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    irrigation_type: Mapped[str | None] = mapped_column(String(100), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    owner: Mapped["User"] = relationship("User", back_populates="farms", foreign_keys=[owner_id])
    crops: Mapped[list["Crop"]] = relationship("Crop", back_populates="farm")
    weather_snapshots: Mapped[list["WeatherSnapshot"]] = relationship(
        "WeatherSnapshot", back_populates="farm"
    )
    pest_trap_readings: Mapped[list["PestTrapReading"]] = relationship(
        "PestTrapReading", back_populates="farm"
    )

    __table_args__ = (
        # GIST index on the geometry column for fast spatial queries
        Index("ix_farms_location_gist", "location", postgresql_using="gist")
        if _HAS_GEOALCHEMY else (),
    )

    def __repr__(self) -> str:
        return f"<Farm id={self.id!r} name={self.name!r} district={self.district!r}>"
