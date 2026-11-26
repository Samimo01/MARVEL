"""Schémas Pydantic du module stock."""

from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel


class StockItemOut(BaseModel):
    id_don_n: UUID
    id_nat: UUID
    id_stock: UUID
    id_object: UUID | None
    object_type: str | None
    category: str | None
    description: str | None
    declared_quantity: Decimal | None
    received_quantity: Decimal | None
    declared_state: str | None
    received_state: str | None
    image_url: str | None
