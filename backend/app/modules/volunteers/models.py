"""Modèles SQLAlchemy du module volunteers (les schémas de l'API sont dans schemas.py)."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Uuid,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import ENUM, ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


mission_status_type = ENUM(
    "Draft",
    "Publish",
    "Complete",
    "Finished",
    "Canceled",
    name="mission_status",
    create_type=False,
)


class Mission(Base):
    __tablename__ = "missions"

    id_mission: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    title: Mapped[str] = mapped_column(String, nullable=False)

    start_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )

    finish_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )

    seat_number: Mapped[int | None] = mapped_column(Integer)

    skills: Mapped[list[str]] = mapped_column(
        ARRAY(String),
        nullable=False,
        server_default=text("'{}'"),
    )

    status: Mapped[str] = mapped_column(
        mission_status_type,
        nullable=False,
        server_default=text("'Publish'::mission_status"),
    )

    id_collect: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("collects.id_collect", ondelete="SET NULL"),
    )

    id_event: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("events.id_event", ondelete="SET NULL"),
    )


class SignIn(Base):
    __tablename__ = "sign_ins"

    id_user: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id_user", ondelete="CASCADE"),
        primary_key=True,
    )

    id_mission: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("missions.id_mission", ondelete="CASCADE"),
        primary_key=True,
    )

    application_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    is_validated: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("false"),
    )

    is_canceled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("false"),
    )

    canceled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )

    validated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )
