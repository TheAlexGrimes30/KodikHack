import typing
import uuid
from datetime import datetime

from sqlalchemy import UUID, DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.base import Base

if typing.TYPE_CHECKING:
    from backend.db.source_catalog import SourceCatalog


class IngestionRun(Base):
    __tablename__ = "ingestion_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    source_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("source_catalog.id", ondelete="CASCADE"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(Text, nullable=False, default="running", server_default="running")
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    docs_seen: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    docs_new: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    docs_updated: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    error_log: Mapped[str | None] = mapped_column(Text)

    source: Mapped["SourceCatalog"] = relationship(back_populates="ingestion_runs")
