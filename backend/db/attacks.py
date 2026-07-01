import typing
import uuid
from decimal import Decimal

from sqlalchemy import UUID, ForeignKey, Text, Numeric, Boolean, Index
from sqlalchemy.orm import mapped_column, Mapped, relationship

if typing.TYPE_CHECKING:
    from backend.db.assumptions import Assumption
    from backend.db.base import Base, TimestampMixin
    from backend.db.env_scenarios import EnvScenario
    from backend.db.sessions import Session


class Attack(Base, TimestampMixin):
    __tablename__ = "attacks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("sessions.id", ondelete="CASCADE"),
        nullable=False
    )
    assumption_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("assumptions.id", ondelete="SET NULL")
    )
    scenario_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("env_scenarios.id", ondelete="SET NULL")
    )
    narrative: Mapped[str] = mapped_column(Text, nullable=False)
    failure_point: Mapped[str | None] = mapped_column(Text)
    est_loss_money: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    survivable: Mapped[bool | None] = mapped_column(Boolean)

    session: Mapped[Session] = relationship(back_populates="attacks")
    assumption: Mapped[Assumption | None] = relationship(back_populates="attacks")
    scenario: Mapped[EnvScenario | None] = relationship(back_populates="attacks")

    __table_args__ = (Index("idx_attacks_session", "session_id"),)