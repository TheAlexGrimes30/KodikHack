import typing
import uuid
from decimal import Decimal

from sqlalchemy import UUID, Numeric, ForeignKey, Index
from sqlalchemy.orm import mapped_column, Mapped, relationship

if typing.TYPE_CHECKING:
    from backend.db.base import Base, TimestampMixin
    from backend.db.bets import Bet
    from backend.db.projects import Project


class CalibrationRecord(Base, TimestampMixin):
    __tablename__ = "calibration_records"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bet_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("bets.id", ondelete="CASCADE"),
        unique=True,
        nullable=False
    )

    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False
    )

    predicted_value: Mapped[Decimal | None] = mapped_column(Numeric)
    actual_value: Mapped[Decimal | None] = mapped_column(Numeric)
    error_abs: Mapped[Decimal | None] = mapped_column(Numeric)
    error_rel: Mapped[Decimal | None] = mapped_column(Numeric)
    optimism_bias: Mapped[Decimal | None] = mapped_column(Numeric)
    trust_delta: Mapped[Decimal | None] = mapped_column(Numeric)

    bet: Mapped[Bet] = relationship(back_populates="calibration_record")
    project: Mapped[Project] = relationship(back_populates="calibration_records")

    __table_args__ = (Index("idx_calibration_project", "project_id"),)
