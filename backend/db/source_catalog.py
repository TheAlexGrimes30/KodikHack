import typing
import uuid
from decimal import Decimal

from sqlalchemy import UUID, Boolean, Index, Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.base import Base, TimestampMixin

if typing.TYPE_CHECKING:
    from backend.db.ingestion_runs import IngestionRun
    from backend.db.source_documents import SourceDocument


class SourceCatalog(Base, TimestampMixin):
    __tablename__ = "source_catalog"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    source_key: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    source_type: Mapped[str] = mapped_column(Text, nullable=False)
    base_url: Mapped[str | None] = mapped_column(Text)
    vertical_key: Mapped[str | None] = mapped_column(Text)
    country: Mapped[str | None] = mapped_column(Text)
    language: Mapped[str | None] = mapped_column(Text)
    trust_score: Mapped[Decimal | None] = mapped_column(Numeric)
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )

    documents: Mapped[list["SourceDocument"]] = relationship(
        back_populates="source",
        cascade="all, delete-orphan",
    )
    ingestion_runs: Mapped[list["IngestionRun"]] = relationship(
        back_populates="source",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("idx_source_catalog_vertical", "vertical_key"),
        Index("idx_source_catalog_type", "source_type"),
    )
