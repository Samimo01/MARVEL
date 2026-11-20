"""Modèles SQLAlchemy du module financial_donations."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean, DateTime, ForeignKey, Numeric, String, Uuid, func,
)
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

# Enumération définie dans votre script SQL
financial_donation_status_type = ENUM(
    "Failure", "Success",
    name="financial_donation_status", create_type=False,
)

class FinancialDon(Base):
    __tablename__ = "financial_dons"

    id_don_f: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid4
    )
    is_anonymous: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    status: Mapped[str] = mapped_column(
        financial_donation_status_type, nullable=False, default="Failure"
    )
    failure_reason: Mapped[str | None] = mapped_column(String)
    reference_payment: Mapped[str | None] = mapped_column(String)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Clés étrangères
    id_user: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id_user", ondelete="SET NULL")
    )
    id_campaign: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("campaigns.id_campaign", ondelete="CASCADE"), nullable=False
    )
    id_ben_file: Mapped[str | None] = mapped_column(String) # TEXT dans le script SQL