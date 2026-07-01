import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Index, Text, ForeignKey, UUID, Numeric, DateTime, func
from sqlalchemy.orm import Mapped, relationship, mapped_column

from backend.db.base import Base, TimestampMixin
from backend.db.projects import Project
from backend.db.sessions import Session


class Bet(Base, TimestampMixin):
    __tablename__ = "bets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("sessions.id", ondelete="CASCADE"),
        nullable=False
    )

    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False
    )
    
    description: Mapped[str] = mapped_column(Text, nullable=False)
    size_money: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    predicted_metric: Mapped[str | None] = mapped_column(Text)
    predicted_value: Mapped[Decimal | None] = mapped_column(Numeric)
    predicted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    actual_value: Mapped[Decimal | None] = mapped_column(Numeric)
    actual_spent: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    anomaly_note: Mapped[str | None] = mapped_column(Text)
    result_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    session: Mapped[Session] = relationship(back_populates="bets", foreign_keys=[session_id])
    project: Mapped[Project] = relationship(back_populates="bets")
    calibration_record: Mapped["CalibrationRecord | None"] = relationship(
        back_populates="bet",
        cascade="all, delete-orphan",
        uselist=False
    )

    __table_args__ = (
        Index("idx_bets_session", "session_id"),
        Index("idx_bets_project", "project_id"),
    )