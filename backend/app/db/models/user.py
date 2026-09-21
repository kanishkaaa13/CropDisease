"""
User model — authentication, role-based access control.
Roles:
  - farmer : uses the mobile Farmer App
  - officer : district-level field officer / agronomist
  - admin   : government / ministry level, read-only analytics
"""
import uuid
import enum
from datetime import datetime, timezone

from sqlalchemy import String, DateTime, Boolean, Enum as SAEnum, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class UserRole(str, enum.Enum):
    farmer = "farmer"
    officer = "officer"
    admin = "admin"


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    phone: Mapped[str | None] = mapped_column(String(20), unique=True, nullable=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        SAEnum(UserRole, name="userrole", native_enum=False),
        default=UserRole.farmer,
        nullable=False,
        index=True,
    )
    # Geographic scope
    state: Mapped[str | None] = mapped_column(String(100), nullable=True)
    district: Mapped[str | None] = mapped_column(String(100), nullable=True)
    taluka: Mapped[str | None] = mapped_column(String(100), nullable=True)
    village: Mapped[str | None] = mapped_column(String(100), nullable=True)
    # Preferences
    language_pref: Mapped[str] = mapped_column(String(10), default="en", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    farms: Mapped[list["Farm"]] = relationship("Farm", back_populates="owner", foreign_keys="Farm.owner_id")
    observations_reported: Mapped[list["Observation"]] = relationship(
        "Observation", back_populates="reported_by_user", foreign_keys="Observation.reported_by"
    )
    validations: Mapped[list["ExpertValidation"]] = relationship(
        "ExpertValidation", back_populates="officer"
    )
    alerts_acknowledged: Mapped[list["Alert"]] = relationship(
        "Alert", back_populates="acknowledged_by_user", foreign_keys="Alert.acknowledged_by"
    )

    def __repr__(self) -> str:
        return f"<User id={self.id!r} name={self.name!r} role={self.role}>"
