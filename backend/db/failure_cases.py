import typing
import uuid

from sqlalchemy import UUID, ForeignKey, Text, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

if typing.TYPE_CHECKING:
    from backend.db.base import Base, TimestampMixin
    from backend.db.configurators import Configurator


class FailureCase(Base, TimestampMixin):
    __tablename__ = "failure_cases"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vertical_key: Mapped[str] = mapped_column(
        ForeignKey("configurators.vertical_key", ondelete="CASCADE"),
        nullable=False
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    risk_type: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str | None] = mapped_column(Text)
    outcome: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str | None] = mapped_column(Text)
    qdrant_point_id: Mapped[str | None] = mapped_column(Text)

    configurator: Mapped[Configurator] = relationship(back_populates="failure_cases")

    __table_args__ = (
        Index("idx_failure_cases_vertical", "vertical_key"),
        Index("idx_failure_cases_risk", "risk_type"),
    )
