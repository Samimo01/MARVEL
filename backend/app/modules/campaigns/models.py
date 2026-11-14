"""Modèles SQLAlchemy du module campaigns."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean, Computed, DateTime, ForeignKey, Numeric, String, Uuid, func,
)
from sqlalchemy.dialects.postgresql import ARRAY, ENUM
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


campaign_status_type = ENUM(
    "Draft", "In_progress", "closed",
    name="campaign_status", create_type=False,
)

campaign_category_type = ENUM(
    "Food_aid", "Clothing_cover", "Hygienne", "Health",
    "Education", "Urgence", "Other",
    name="campaign_category", create_type=False,
)


class Campaign(Base):
    __tablename__ = "campaigns"

    id_campaign: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid4
    )
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(String)
    goal: Mapped[Decimal | None] = mapped_column(Numeric(15, 2))
    start_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finish_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(
        campaign_status_type, nullable=False, default="Draft", server_default="Draft"
    )
    categories: Mapped[list[str] | None] = mapped_column(ARRAY(campaign_category_type))
    image_url: Mapped[str | None] = mapped_column(String)
    closure_reason: Mapped[str | None] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    id_user: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id_user", ondelete="CASCADE"),
        nullable=False,
    )