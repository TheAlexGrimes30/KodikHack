import uuid
from typing import Any

from sqlalchemy import Enum, ForeignKey, UUID, Text, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.base import TimestampMixin, Base
from backend.db.enums import AgentKind
from backend.db.sessions import Session


class SessionLog(Base, TimestampMixin):
    __tablename__ = "session_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("sessions.id", ondelete="CASCADE"),
        nullable=False
    )

    actor: Mapped[AgentKind | None] = mapped_column(
        Enum(AgentKind, name="agent_kind", values_callable=lambda e: [x.value for x in e])
    )

    event_type: Mapped[str] = mapped_column(Text, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default="{}"
    )

    session: Mapped[Session] = relationship(back_populates="logs")

    __table_args__ = (Index("idx_session_logs_session", "session_id", "created_at"),)
    