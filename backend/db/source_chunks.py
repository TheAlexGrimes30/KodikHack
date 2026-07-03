import typing
import uuid
from typing import Any

from sqlalchemy import UUID, ForeignKey, Index, Integer, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.base import Base, TimestampMixin

if typing.TYPE_CHECKING:
    from backend.db.source_documents import SourceDocument


class SourceChunk(Base, TimestampMixin):
    __tablename__ = "source_chunks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("source_documents.id", ondelete="CASCADE"),
        nullable=False,
    )
    chunk_no: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    token_count: Mapped[int | None] = mapped_column(Integer)
    embedding_model: Mapped[str | None] = mapped_column(Text)
    embedding_dim: Mapped[int | None] = mapped_column(Integer)
    qdrant_point_id: Mapped[str | None] = mapped_column(Text)
    chunk_meta: Mapped[dict[str, Any]] = mapped_column(
        "metadata",
        JSONB,
        nullable=False,
        default=dict,
        server_default="{}",
    )

    document: Mapped["SourceDocument"] = relationship(back_populates="chunks")

    __table_args__ = (
        Index("idx_source_chunks_document", "document_id", "chunk_no"),
        Index("idx_source_chunks_qdrant", "qdrant_point_id"),
    )
