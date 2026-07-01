import uuid

from sqlalchemy import UUID, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.base import Base, TimestampMixin


class Configurator(Base, TimestampMixin):
    __tablename__ = "configurators"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    vertical_key: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true"
    )

    benchmarks: Mapped[list["IndustryBenchmark"]] = relationship(
        back_populates="configurator",
        cascade="all, delete-orphan"
    )

    failure_cases: Mapped[list["FailureCase"]] = relationship(
        back_populates="configurator",
        cascade="all, delete-orphan"
    )
