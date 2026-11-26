"""Accès aux données du module stock."""

from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.modules.natural_donations.models import NaturalDon, NaturalDonItem, ObjectType


def list_stock_items(
    session: Session,
    *,
    object_type_id: UUID | None = None,
    category: str | None = None,
    search: str | None = None,
) -> list[tuple[NaturalDonItem, str | None]]:
    statement = (
        select(NaturalDonItem, ObjectType.name)
        .join(NaturalDon, NaturalDon.id_don_n == NaturalDonItem.id_don_n)
        .outerjoin(ObjectType, ObjectType.id_object == NaturalDonItem.id_object)
        .where(
            NaturalDon.status == "In_Stock",
            NaturalDonItem.id_stock.is_not(None),
        )
        .order_by(NaturalDonItem.created_at.desc(), NaturalDonItem.id_nat)
    )

    if object_type_id is not None:
        statement = statement.where(NaturalDonItem.id_object == object_type_id)
    if category is not None:
        statement = statement.where(ObjectType.name == category)
    if search is not None:
        search_pattern = f"%{search}%"
        statement = statement.where(
            or_(
                NaturalDonItem.description.ilike(search_pattern),
                ObjectType.name.ilike(search_pattern),
            )
        )

    return list(session.execute(statement).all())
