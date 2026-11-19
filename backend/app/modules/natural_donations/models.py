"""Modèles SQLAlchemy du module natural_donations."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean, DateTime, ForeignKey, Numeric, String, Uuid, func,
)
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import Mapped, mapped_column, relationship  # 👈 AJOUTEZ relationship

from app.database import Base


# ============================================================
# ENUMS PostgreSQL
# ============================================================
delivery_method_type = ENUM(
    "Deposit", "Collect",
    name="delivery_method", create_type=False,
)

natural_don_status_type = ENUM(
    "Declare", "Collection_Planned", "valid", "Refuse", "In_Stock",
    name="natural_don_status", create_type=False,
)

object_state_type = ENUM(
    "New", "Very_Good", "Good", "Fair", "Damaged", "Unusable",
    name="object_state", create_type=False,
)


# ============================================================
# MODÈLES
# ============================================================
class ObjectType(Base):
    __tablename__ = "object_types"

    id_object: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid4
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(String)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class NaturalDon(Base):
    __tablename__ = "natural_dons"

    id_don_n: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid4
    )
    recovery_mode: Mapped[str | None] = mapped_column(delivery_method_type)
    collection_address: Mapped[str | None] = mapped_column(String)
    status: Mapped[str] = mapped_column(
        natural_don_status_type, nullable=False, default="Declare", server_default="Declare"
    )
    refusal_reason: Mapped[str | None] = mapped_column(String)

    validated_by: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id_user", ondelete="SET NULL")
    )
    planned_by: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id_user", ondelete="SET NULL")
    )
    received_by: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id_user", ondelete="SET NULL")
    )

    validated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    planned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    received_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reason: Mapped[str | None] = mapped_column(String)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Clés étrangères
    id_user: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id_user", ondelete="CASCADE"), nullable=False
    )
    id_campaign: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("campaigns.id_campaign", ondelete="SET NULL")
    )
    id_collect: Mapped[str | None] = mapped_column(String)
    id_stock: Mapped[str | None] = mapped_column(String)

    # 👇 NOUVELLE RELATION : un don a plusieurs articles
    items: Mapped[list["NaturalDonItem"]] = relationship(
        "NaturalDonItem",
        back_populates="natural_don",
        cascade="all, delete-orphan",
        lazy="selectin",  # charge automatiquement (évite le N+1)
    )


class NaturalDonItem(Base):
    __tablename__ = "natural_don_items"

    id_don_n: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("natural_dons.id_don_n", ondelete="CASCADE"),
        primary_key=True,
    )
    id_nat: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid4
    )

    description: Mapped[str | None] = mapped_column(String)
    declared_quantity: Mapped[Decimal | None] = mapped_column(Numeric(15, 2))
    declared_state: Mapped[str | None] = mapped_column(object_state_type)
    image_url: Mapped[str | None] = mapped_column(String)

    received_quantity: Mapped[Decimal | None] = mapped_column(Numeric(15, 2))
    received_state: Mapped[str | None] = mapped_column(object_state_type)
    is_compliant: Mapped[bool | None] = mapped_column(Boolean)
    non_compliant_reason: Mapped[str | None] = mapped_column(String)

    id_object: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("object_types.id_object", ondelete="SET NULL")
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    natural_don: Mapped["NaturalDon"] = relationship(
        "NaturalDon",
        back_populates="items",
    )