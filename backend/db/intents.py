import uuid
from decimal import Decimal
from typing import Any

from sqlalchemy import Text, Numeric, ForeignKey, UUID
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.base import Base
from backend.db.sessions import Session


class Intent(Base):
    __tablename__ = "intents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("sessions.id", ondelete="CASCADE"),
        unique=True,
        nullable=False
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    invest_money: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    invest_effort: Mapped[Decimal | None] = mapped_column(Numeric(8, 1))
    horizon_months: Mapped[Decimal | None] = mapped_column(Numeric(5, 1))
    expected_result: Mapped[str | None] = mapped_column(Text)
    metrics: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default="{}"
    )

    session: Mapped[Session] = relationship(back_populates="intent")
    assumptions: Mapped[list["Assumption"]] = relationship(back_populates="intent", cascade="all, delete-orphan")
