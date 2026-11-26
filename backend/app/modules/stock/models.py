"""Modèle SQLAlchemy des articles de stock."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Numeric, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Stock(Base):
    __tablename__ = "stocks"

    id_stock: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    title: Mapped[str] = mapped_column(String, nullable=False)
    available_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), nullable=False, default=Decimal(0), server_default="0"
    )
    limit_alert: Mapped[Decimal | None] = mapped_column(Numeric(15, 2))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
