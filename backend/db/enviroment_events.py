import typing
import uuid
from datetime import date

from sqlalchemy import CheckConstraint, Index, Integer, Date, Text, ForeignKey, UUID
from sqlalchemy.orm import mapped_column, relationship, Mapped

from backend.db.base import Base, TimestampMixin

if typing.TYPE_CHECKING:
    from backend.db.data_feeds import DataFeed


class EnvironmentEvent(Base, TimestampMixin):
    __tablename__ = "environment_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    feed_key: Mapped[str] = mapped_column(
        ForeignKey("data_feeds.feed_key", ondelete="CASCADE"),
        nullable=False,
    )

    category: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    body: Mapped[str | None] = mapped_column(Text)
    impact_hint: Mapped[int | None] = mapped_column(Integer)
    happened_at: Mapped[date | None] = mapped_column(Date)

    feed: Mapped["DataFeed"] = relationship(back_populates="environment_events")

    __table_args__ = (
        CheckConstraint(
            "impact_hint BETWEEN 1 AND 5",
            name="ck_environment_events_impact_hint",
        ),
        Index("idx_env_events_cat_date", "category", "happened_at"),
    )