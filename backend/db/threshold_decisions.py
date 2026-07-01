import typing
import uuid
from decimal import Decimal

from sqlalchemy import UUID, ForeignKey, Enum, Numeric, Text, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.base import Base, TimestampMixin
from backend.db.enums import Reversibility, ThresholdVerdict

if typing.TYPE_CHECKING:
    from backend.db.sessions import Session


class ThresholdDecision(Base, TimestampMixin):
    __tablename__ = "threshold_decisions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("sessions.id", ondelete="CASCADE"),
        unique=True,
        nullable=False
    )

    reversibility: Mapped[Reversibility] = mapped_column(
        Enum(Reversibility, name="reversibility", values_callable=lambda e: [x.value for x in e]),
        nullable=False
    )

    verdict: Mapped[ThresholdVerdict] = mapped_column(
        Enum(ThresholdVerdict, name="threshold_verdict", values_callable=lambda e: [x.value for x in e]),
        nullable=False
    )

    recommended_step: Mapped[str | None] = mapped_column(Text)
    step_budget: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    trust_level: Mapped[Decimal | None] = mapped_column(Numeric)
    rationale: Mapped[str | None] = mapped_column(Text)

    session: Mapped["Session"] = relationship(back_populates="threshold_decision")

    __table_args__ = (CheckConstraint("trust_level BETWEEN 0 AND 1", name="ck_threshold_trust_level"),)
