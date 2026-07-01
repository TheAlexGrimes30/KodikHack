import typing
import uuid
from decimal import Decimal
from typing import Any

from sqlalchemy import UUID, ForeignKey, Text, Integer, Numeric, CheckConstraint, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.db.base import Base, TimestampMixin

if typing.TYPE_CHECKING:
    from backend.db.attacks import Attack
    from backend.db.sessions import Session


class EnvScenario(Base, TimestampMixin):
    __tablename__ = "env_scenarios"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("sessions.id", ondelete="CASCADE"),
        nullable=False
    )
    shock_class: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[int | None] = mapped_column(Integer)
    likelihood: Mapped[Decimal | None] = mapped_column(Numeric)
    source_refs: Mapped[list[Any]] = mapped_column(JSONB, default=list, server_default="[]")

    session: Mapped["Session"] = relationship(back_populates="env_scenarios")
    attacks: Mapped[list["Attack"]] = relationship(back_populates="scenario")

    __table_args__ = (
        CheckConstraint("severity BETWEEN 1 AND 5", name="ck_env_scenarios_severity"),
        CheckConstraint("likelihood BETWEEN 0 AND 1", name="ck_env_scenarios_likelihood"),
        Index("idx_env_session", "session_id"),
    )
