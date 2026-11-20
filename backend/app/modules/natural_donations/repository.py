"""Accès aux données du module natural_donations."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.orm import Session, selectinload

from app.modules.natural_donations.models import NaturalDon, NaturalDonItem, ObjectType


# ============================================================
# OBJECT TYPES
# ============================================================
def get_object_type_by_id(session: Session, id_object: UUID) -> ObjectType | None:
    return session.get(ObjectType, id_object)

def list_object_types(session: Session, only_active: bool = False) -> list[ObjectType]:
    stmt = select(ObjectType).order_by(ObjectType.name)
    if only_active:
        stmt = stmt.where(ObjectType.is_active == True)
    return list(session.scalars(stmt).all())

def add_object_type(session: Session, obj_type: ObjectType) -> None:
    session.add(obj_type)
    session.flush()

def update_object_type(session: Session, obj_type: ObjectType, data: dict) -> ObjectType:
    for field, value in data.items():
        setattr(obj_type, field, value)
    session.flush()
    return obj_type


# ============================================================
# NATURAL DONS
# ============================================================
def get_natural_don_by_id(session: Session, id_don_n: UUID, with_items: bool = True) -> NaturalDon | None:
    stmt = select(NaturalDon).where(NaturalDon.id_don_n == id_don_n)
    if with_items:
        stmt = stmt.options(selectinload(NaturalDon.items))
    return session.scalar(stmt)

def list_natural_dons(session: Session, status: str | None = None) -> list[NaturalDon]:
    stmt = select(NaturalDon).order_by(NaturalDon.created_at.desc())
    if status:
        stmt = stmt.where(NaturalDon.status == status)
    return list(session.scalars(stmt).all())

def add_natural_don(session: Session, don: NaturalDon) -> None:
    session.add(don)
    session.flush()

def delete_natural_don(session: Session, don: NaturalDon) -> None:
    session.delete(don)
    session.flush()


# ============================================================
# NATURAL DON ITEMS
# ============================================================
def get_natural_don_item(session: Session, id_don_n: UUID, id_nat: UUID) -> NaturalDonItem | None:
    return session.scalar(
        select(NaturalDonItem).where(
            NaturalDonItem.id_don_n == id_don_n,
            NaturalDonItem.id_nat == id_nat
        )
    )