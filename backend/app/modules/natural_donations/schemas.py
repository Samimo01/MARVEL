"""Schémas Pydantic du module natural_donations."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# ============================================================
# ObjectType
# ============================================================
class ObjectTypeBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    description: str | None = None


class ObjectTypeCreate(ObjectTypeBase):
    pass


class ObjectTypeUpdate(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=100)
    description: str | None = None


class ObjectTypeOut(ObjectTypeBase):
    id_object: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================
# NaturalDonItem
# ============================================================
class NaturalDonItemCreate(BaseModel):
    id_object: UUID
    declared_quantity: Decimal = Field(..., gt=0)
    declared_state: str
    description: str | None = None
    id_stock: str | None = None


class NaturalDonItemReception(BaseModel):
    received_quantity: Decimal = Field(..., ge=0)
    received_state: str
    is_compliant: bool
    non_compliant_reason: str | None = None


class NaturalDonItemOut(BaseModel):
    id_don_n: UUID
    id_nat: UUID
    id_object: UUID | None
    description: str | None
    declared_quantity: Decimal | None
    declared_state: str | None
    image_url: str | None
    received_quantity: Decimal | None
    received_state: str | None
    is_compliant: bool | None
    non_compliant_reason: str | None
    id_stock: str | None
    model_config = ConfigDict(from_attributes=True)


# ============================================================
# NaturalDon
# ============================================================
class NaturalDonCreate(BaseModel):
    recovery_mode: str = Field(..., description="Deposit ou Collect")
    collection_address: str | None = None
    id_campaign: UUID | None = None
    items: list[NaturalDonItemCreate] = Field(..., min_length=1)


class NaturalDonReject(BaseModel):
    refusal_reason: str = Field(..., min_length=5)


class NaturalDonCollectPlan(BaseModel):
    planned_at: datetime
    collection_address: str


class NaturalDonOut(BaseModel):
    id_don_n: UUID
    recovery_mode: str | None
    collection_address: str | None
    status: str
    refusal_reason: str | None
    validated_by: UUID | None
    planned_by: UUID | None
    received_by: UUID | None
    validated_at: datetime | None
    planned_at: datetime | None
    received_at: datetime | None
    created_at: datetime
    id_user: UUID
    id_campaign: UUID | None
    id_collect: UUID | None

    model_config = ConfigDict(from_attributes=True)


class NaturalDonWithItemsOut(NaturalDonOut):
    items: list[NaturalDonItemOut]


class CollectOut(BaseModel):
    id_collect: UUID
    place: str
    planned_at: datetime
    status: str
    id_user: UUID

    model_config = ConfigDict(from_attributes=True)


class CollectUpdate(BaseModel):
    planned_at: datetime | None = None
    place: str | None = Field(None, min_length=1)
