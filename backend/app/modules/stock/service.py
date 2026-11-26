"""Logique métier du module stock."""

from uuid import UUID

from sqlalchemy.orm import Session

from app.modules.stock import repository as stock_repo
from app.modules.stock.schemas import StockItemOut


def list_stock_items(
    session: Session,
    *,
    object_type_id: UUID | None = None,
    category: str | None = None,
    search: str | None = None,
) -> list[StockItemOut]:
    items = stock_repo.list_stock_items(
        session,
        object_type_id=object_type_id,
        category=category,
        search=search,
    )
    return [
        StockItemOut(
            id_don_n=item.id_don_n,
            id_nat=item.id_nat,
            id_stock=item.id_stock,
            id_object=item.id_object,
            object_type=object_type,
            category=object_type,
            description=item.description,
            declared_quantity=item.declared_quantity,
            received_quantity=item.received_quantity,
            declared_state=item.declared_state,
            received_state=item.received_state,
            image_url=item.image_url,
        )
        for item, object_type in items
    ]
