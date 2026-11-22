"""Modèle SQLAlchemy de la trésorerie."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Fund(Base):
    __tablename__ = "funds"

    id_fund: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )

    category: Mapped[str | None] = mapped_column(String)

    transaction_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    justificative: Mapped[str | None] = mapped_column(String)

    id_event: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("events.id_event"),
        nullable=True,
    )

    id_user: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id_user"),
        nullable=True,
    )
