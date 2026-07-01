import typing
import uuid
from datetime import datetime

from sqlalchemy import Text, Enum, DateTime, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

if typing.TYPE_CHECKING:
    from backend.db.base import Base, TimestampMixin
    from backend.db.enums import FeedMode


class DataFeed(Base, TimestampMixin):
    __tablename__ = "data_feeds"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    feed_key: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)

    mode: Mapped[FeedMode] = mapped_column(
        Enum(FeedMode, name="feed_mode", values_callable=lambda e: [x.value for x in e]),
        nullable=False
    )

    last_synced: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    macro_indicators: Mapped[list["MacroIndicator"]] = relationship(
        back_populates="feed",
        cascade="all, delete-orphan"
    )

    environment_events: Mapped[list["EnvironmentEvent"]] = relationship(
        back_populates="feed",
        cascade="all, delete-orphan"
    )
