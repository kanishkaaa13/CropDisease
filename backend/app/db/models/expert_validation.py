"""
ExpertValidation model — human-in-the-loop expert validation by agricultural officers.
"""
import uuid
import enum
from datetime import datetime

from sqlalchemy import String, DateTime, Text, ForeignKey, Enum as SAEnum, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ValidationVerdict(str, enum.Enum):
    confirmed = "confirmed"
    corrected = "corrected"
    referred = "referred"


class ExpertValidation(Base):
    __tablename__ = "expert_validations"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    ai_result_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("ai_results.id", ondelete="CASCADE"), nullable=False, index=True
    )
    officer_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    verdict: Mapped[ValidationVerdict] = mapped_column(
        SAEnum(ValidationVerdict, name="validationverdict", native_enum=False),
        nullable=False,
        index=True,
    )

    corrected_label: Mapped[str | None] = mapped_column(String(150), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    ai_result: Mapped["AIResult"] = relationship("AIResult", back_populates="expert_validations")
    officer: Mapped["User"] = relationship("User", back_populates="validations")

    def __repr__(self) -> str:
        return f"<ExpertValidation verdict={self.verdict} officer={self.officer_id!r}>"
