import uuid

from sqlalchemy import UUID, ForeignKey, Enum, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.attacks import Attack
from backend.db.base import Base
from backend.db.enums import SessionStatus
from backend.db.env_scenarios import EnvScenario
from backend.db.projects import Project


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False
    )

    status: Mapped[SessionStatus] = mapped_column(
        Enum(SessionStatus, name="session_status", values_callable=lambda e: [x.value for x in e]),
        nullable=False,
        default=SessionStatus.DRAFT,
        server_default="draft"
    )

    parent_bet_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("bets.id", ondelete="SET NULL")
    )

    project: Mapped[Project] = relationship(back_populates="sessions")
    parent_bet: Mapped["Bet | None"] = relationship(foreign_keys=[parent_bet_id], post_update=True)
    intent: Mapped["Intent | None"] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
        uselist=False
    )
    env_scenarios: Mapped[list["EnvScenario"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan"
    )
    attacks: Mapped[list["Attack"]] = relationship(back_populates="session", cascade="all, delete-orphan")
    threshold_decision: Mapped["ThresholdDecision | None"] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
        uselist=False
    )
    bets: Mapped[list["Bet"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
        foreign_keys="Bet.session_id"
    )
    logs: Mapped[list["SessionLog"]] = relationship(back_populates="session", cascade="all, delete-orphan")

    __table_args__ = (Index("idx_sessions_project", "project_id"),)