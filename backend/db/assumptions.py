import uuid
from datetime import datetime

from sqlalchemy import Integer, Boolean, Text, CheckConstraint, Index, UUID, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.attacks import Attack
from backend.db.base import Base
from backend.db.intents import Intent


class Assumption(Base):
    __tablename__ = "assumptions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    intent_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("intents.id", ondelete="CASCADE"),
        nullable=False
    )
    statement: Mapped[str] = mapped_column(Text, nullable=False)
    is_explicit: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false"
    )

    criticality: Mapped[int | None] = mapped_column(Integer)

    intent: Mapped[Intent] = relationship(back_populates="assumptions")
    attacks: Mapped[list["Attack"]] = relationship(back_populates="assumption")

    __table_args__ = (
        CheckConstraint("criticality BETWEEN 1 AND 5", name="ck_assumptions_criticality"),
        Index("idx_assumptions_intent", "intent_id"),
    )
