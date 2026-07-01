import typing
import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import UUID, ForeignKey, Date, Numeric, Text, UniqueConstraint, Index
from sqlalchemy.orm import mapped_column, Mapped, relationship

from backend.db.base import Base, TimestampMixin

if typing.TYPE_CHECKING:
    from backend.db.data_feeds import DataFeed


class MacroIndicator(Base, TimestampMixin):
    __tablename__ = "macro_indicators"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    feed_key: Mapped[str] = mapped_column(
        ForeignKey("data_feeds.feed_key", ondelete="CASCADE"),
        nullable=False,
    )

    indicator: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    value: Mapped[Decimal] = mapped_column(
        Numeric,
        nullable=False,
    )

    observed_at: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    feed: Mapped["DataFeed"] = relationship(
        back_populates="macro_indicators",
    )

    __table_args__ = (
        UniqueConstraint(
            "indicator",
            "observed_at",
            name="uq_macro_indicator_observed_at",
        ),
        Index(
            "idx_macro_indicator_date",
            "indicator",
            "observed_at",
        ),
    )
