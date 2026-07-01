import typing
import uuid
from decimal import Decimal

from sqlalchemy import ForeignKey, UUID, Text, Enum, Integer, Numeric, Index
from sqlalchemy.orm import mapped_column, Mapped, relationship

from backend.db.base import Base, TimestampMixin

if typing.TYPE_CHECKING:
    from backend.db.bets import Bet
    from backend.db.callibration_records import CalibrationRecord
    from backend.db.enums import ProjectStage, RiskAppetite
    from backend.db.sessions import Session
    from backend.db.users import User


class Project(Base, TimestampMixin):
    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    vertical_key: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="it_startup",
        server_default="it_startup"
    )
    stage: Mapped[ProjectStage] = mapped_column(
        Enum(ProjectStage, name="project_stage", values_callable=lambda e: [x.value for x in e]),
        nullable=False,
        default=ProjectStage.IDEA, server_default="idea"
    )
    risk_appetite: Mapped[RiskAppetite] = mapped_column(
        Enum(RiskAppetite, name="risk_appetite", values_callable=lambda e: [x.value for x in e]),
        nullable=False,
        default=RiskAppetite.BALANCED, server_default="balanced"
    )
    team_size: Mapped[int | None] = mapped_column(Integer)
    runway_months: Mapped[Decimal | None] = mapped_column(Numeric(5, 1))
    geography: Mapped[str | None] = mapped_column(Text)

    user: Mapped[User] = relationship(back_populates="projects")
    sessions: Mapped[list["Session"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    bets: Mapped[list["Bet"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    calibration_records: Mapped[list["CalibrationRecord"]] = relationship(back_populates="project",
                                                                          cascade="all, delete-orphan")
    __table_args__ = (Index("idx_projects_user", "user_id"),)