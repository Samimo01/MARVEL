"""ModÃ¨les SQLAlchemy du module campaigns."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Uuid,
    func,
    types,
)
from sqlalchemy.dialects.postgresql import ARRAY, ENUM
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

campaign_status_type = ENUM(
    "Draft",
    "In_progress",
    "closed",
    "Invisible",
    name="campaign_status",
    create_type=False,
)

campaign_category_type = ENUM(
    "Food_aid",
    "Clothing_cover",
    "Hygienne",
    "Health",
    "Education",
    "Urgence",
    "Other",
    name="campaign_category",
    create_type=False,
)

donation_type_enum = ENUM(
    "Mature",
    "Mixed",
    "Finnancial",
    name="donation_type",
    create_type=False,
)


class ArrayOfEnum(types.TypeDecorator):
    """Utilise ARRAY sur PostgreSQL, et JSON sur SQLite (pour les tests)."""

    impl = types.JSON
    cache_ok = True

    def __init__(self, enum_type, *args, **kwargs):
        self.enum_type = enum_type
        super().__init__(*args, **kwargs)

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(ARRAY(self.enum_type))
        else:
            return dialect.type_descriptor(types.JSON)


class Campaign(Base):
    __tablename__ = "campaigns"

    id_campaign: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(String)
    goal: Mapped[Decimal | None] = mapped_column(Numeric(15, 2))
    start_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finish_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(
        campaign_status_type, nullable=False, default="Draft", server_default="Draft"
    )

    categories: Mapped[list[str] | None] = mapped_column(ArrayOfEnum(campaign_category_type))

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


class Event(Base):
    __tablename__ = "events"

    id_event: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)

    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(String)
    expected_donation_types: Mapped[str | None] = mapped_column(donation_type_enum)
    event_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    place: Mapped[str | None] = mapped_column(String)

    goal: Mapped[Decimal | None] = mapped_column(Numeric(15, 2))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    id_campaign: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("campaigns.id_campaign", ondelete="CASCADE"), nullable=False
    )
