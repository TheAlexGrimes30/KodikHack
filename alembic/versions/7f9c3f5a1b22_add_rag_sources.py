"""add rag sources

Revision ID: 7f9c3f5a1b22
Revises: ad85a401a8bc
Create Date: 2026-07-02 13:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "7f9c3f5a1b22"
down_revision: Union[str, Sequence[str], None] = "ad85a401a8bc"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "source_catalog",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("source_key", sa.Text(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("source_type", sa.Text(), nullable=False),
        sa.Column("base_url", sa.Text(), nullable=True),
        sa.Column("vertical_key", sa.Text(), nullable=True),
        sa.Column("country", sa.Text(), nullable=True),
        sa.Column("language", sa.Text(), nullable=True),
        sa.Column("trust_score", sa.Numeric(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("source_key"),
    )
    op.create_index("idx_source_catalog_vertical", "source_catalog", ["vertical_key"], unique=False)
    op.create_index("idx_source_catalog_type", "source_catalog", ["source_type"], unique=False)

    op.create_table(
        "ingestion_runs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("source_id", sa.UUID(), nullable=False),
        sa.Column("status", sa.Text(), server_default="running", nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("docs_seen", sa.Integer(), server_default="0", nullable=False),
        sa.Column("docs_new", sa.Integer(), server_default="0", nullable=False),
        sa.Column("docs_updated", sa.Integer(), server_default="0", nullable=False),
        sa.Column("error_log", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["source_id"], ["source_catalog.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "source_documents",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("source_id", sa.UUID(), nullable=False),
        sa.Column("external_id", sa.Text(), nullable=True),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("author", sa.Text(), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("doc_type", sa.Text(), server_default="article", nullable=False),
        sa.Column("raw_text", sa.Text(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("content_hash", sa.Text(), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), server_default="{}", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["source_id"], ["source_catalog.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("source_id", "url", name="uq_source_documents_source_url"),
    )
    op.create_index("idx_source_documents_published", "source_documents", ["published_at"], unique=False)
    op.create_index("idx_source_documents_hash", "source_documents", ["content_hash"], unique=False)

    op.create_table(
        "source_chunks",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("document_id", sa.UUID(), nullable=False),
        sa.Column("chunk_no", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("token_count", sa.Integer(), nullable=True),
        sa.Column("embedding_model", sa.Text(), nullable=True),
        sa.Column("embedding_dim", sa.Integer(), nullable=True),
        sa.Column("qdrant_point_id", sa.Text(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), server_default="{}", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["source_documents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_source_chunks_document", "source_chunks", ["document_id", "chunk_no"], unique=False)
    op.create_index("idx_source_chunks_qdrant", "source_chunks", ["qdrant_point_id"], unique=False)


def downgrade() -> None:
    op.drop_index("idx_source_chunks_qdrant", table_name="source_chunks")
    op.drop_index("idx_source_chunks_document", table_name="source_chunks")
    op.drop_table("source_chunks")
    op.drop_index("idx_source_documents_hash", table_name="source_documents")
    op.drop_index("idx_source_documents_published", table_name="source_documents")
    op.drop_table("source_documents")
    op.drop_table("ingestion_runs")
    op.drop_index("idx_source_catalog_type", table_name="source_catalog")
    op.drop_index("idx_source_catalog_vertical", table_name="source_catalog")
    op.drop_table("source_catalog")
