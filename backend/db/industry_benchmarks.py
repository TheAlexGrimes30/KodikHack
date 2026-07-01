import typing
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import UUID, ForeignKey, Text, Numeric, DateTime, func, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.db.base import Base

if typing.TYPE_CHECKING:
    from backend.db.configurators import Configurator


class IndustryBenchmark(Base):
    __tablename__ = "industry_benchmarks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vertical_key: Mapped[str] = mapped_column(
        ForeignKey("configurators.vertical_key", ondelete="CASCADE"),
        nullable=False
    )

    metric_key: Mapped[str] = mapped_column(Text, nullable=False)
    segment: Mapped[str | None] = mapped_column(Text)
    value: Mapped[Decimal | None] = mapped_column(Numeric)
    unit: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str | None] = mapped_column(Text)
    captured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    configurator: Mapped[Configurator] = relationship(back_populates="benchmarks")

    __table_args__ = (Index("idx_benchmarks_vertical", "vertical_key"),)
