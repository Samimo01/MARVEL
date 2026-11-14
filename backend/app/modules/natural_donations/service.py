"""Logique métier du module natural_donations."""

from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from app.modules.auth.models import User
from app.modules.natural_donations import repository as don_repo
from app.modules.natural_donations.models import NaturalDon, NaturalDonItem, ObjectType
from app.modules.natural_donations.schemas import (
    NaturalDonCreate, NaturalDonOut, NaturalDonWithItemsOut, NaturalDonItemOut,
    NaturalDonReject, NaturalDonCollectPlan, NaturalDonItemReception,
    ObjectTypeCreate, ObjectTypeUpdate, ObjectTypeOut
)


# ============================================================
# Exceptions
# ============================================================
class NaturalDonNotFoundError(Exception): pass
class ObjectTypeNotFoundError(Exception): pass
class InvalidStatusTransitionError(Exception): pass
class ItemNotFoundError(Exception): pass


# ============================================================
# Helpers
# ============================================================
def _get_don_or_raise(session: Session, id_don_n: UUID) -> NaturalDon:
    don = don_repo.get_natural_don_by_id(session, id_don_n)
    if not don:
        raise NaturalDonNotFoundError(f"Don en nature {id_don_n} introuvable")
    return don


# ============================================================
# NAT-01, NAT-15 à NAT-18 : OBJECT TYPES
# ============================================================
def list_object_types(session: Session, only_active: bool = False) -> list[ObjectTypeOut]:
    objs = don_repo.list_object_types(session, only_active)
    return [ObjectTypeOut.model_validate(o) for o in objs]

def create_object_type(session: Session, payload: ObjectTypeCreate) -> ObjectTypeOut:
    obj = ObjectType(**payload.model_dump())
    don_repo.add_object_type(session, obj)
    session.commit()
    session.refresh(obj)
    return ObjectTypeOut.model_validate(obj)

def update_object_type(session: Session, id_object: UUID, payload: ObjectTypeUpdate) -> ObjectTypeOut:
    obj = don_repo.get_object_type_by_id(session, id_object)
    if not obj:
        raise ObjectTypeNotFoundError("Type d'objet introuvable")
    data = payload.model_dump(exclude_unset=True)
    don_repo.update_object_type(session, obj, data)
    session.commit()
    session.refresh(obj)
    return ObjectTypeOut.model_validate(obj)

def toggle_object_type_activation(session: Session, id_object: UUID, is_active: bool) -> ObjectTypeOut:
    obj = don_repo.get_object_type_by_id(session, id_object)
    if not obj:
        raise ObjectTypeNotFoundError("Type d'objet introuvable")
    don_repo.update_object_type(session, obj, {"is_active": is_active})
    session.commit()
    session.refresh(obj)
    return ObjectTypeOut.model_validate(obj)


# ============================================================
# NAT-02 : Création d'un don
# ============================================================
def create_natural_don(session: Session, *, user: User, payload: NaturalDonCreate) -> NaturalDonWithItemsOut:
    # 1. Créer le don
    don = NaturalDon(
        id_user=user.id_user,
        recovery_mode=payload.recovery_mode,
        collection_address=payload.collection_address,
        id_campaign=payload.id_campaign,
        status="Declare"
    )
    don_repo.add_natural_don(session, don)
    
    # 2. Créer les items
    for item_data in payload.items:
        item = NaturalDonItem(
            id_don_n=don.id_don_n,
            **item_data.model_dump()
        )
        session.add(item)
    
    session.commit()
    session.refresh(don)
    
    # On recharge avec les items
    don = don_repo.get_natural_don_by_id(session, don.id_don_n)
    return NaturalDonWithItemsOut.model_validate(don)


# ============================================================
# NAT-03 : Uploader une image d'article (Simulation)
# ============================================================
def upload_item_image(session: Session, id_don_n: UUID, id_nat: UUID, image_url: str) -> NaturalDonItemOut:
    don = _get_don_or_raise(session, id_don_n)
    item = don_repo.get_natural_don_item(session, id_don_n, id_nat)
    if not item:
        raise ItemNotFoundError("Article introuvable")
    
    item.image_url = image_url
    session.commit()
    session.refresh(item)
    return NaturalDonItemOut.model_validate(item)


# ============================================================
# NAT-04 : Annuler un don
# ============================================================
def cancel_natural_don(session: Session, id_don_n: UUID, user: User) -> None:
    don = _get_don_or_raise(session, id_don_n)
    if don.status != "Declare":
        raise InvalidStatusTransitionError("Seul un don à l'état 'Declare' peut être annulé.")
    if don.id_user != user.id_user:
        raise InvalidStatusTransitionError("Vous n'êtes pas le propriétaire de ce don.")
    
    don_repo.delete_natural_don(session, don)
    session.commit()


# ============================================================
# NAT-05, NAT-06 : Lecture
# ============================================================
def list_natural_dons(session: Session, status: str | None = None) -> list[NaturalDonOut]:
    dons = don_repo.list_natural_dons(session, status)
    return [NaturalDonOut.model_validate(d) for d in dons]

def get_natural_don_detail(session: Session, id_don_n: UUID) -> NaturalDonWithItemsOut:
    don = _get_don_or_raise(session, id_don_n)
    return NaturalDonWithItemsOut.model_validate(don)


# ============================================================
# NAT-07 : Valider un don
# ============================================================
def validate_natural_don(session: Session, id_don_n: UUID, user: User) -> NaturalDonOut:
    don = _get_don_or_raise(session, id_don_n)
    if don.status != "Declare":
        raise InvalidStatusTransitionError("Seul un don à l'état 'Declare' peut être validé.")
    
    don.status = "valid"
    don.validated_by = user.id_user
    don.validated_at = datetime.now(timezone.utc)
    session.commit()
    session.refresh(don)
    return NaturalDonOut.model_validate(don)


# ============================================================
# NAT-08 : Refuser un don
# ============================================================
def reject_natural_don(session: Session, id_don_n: UUID, user: User, payload: NaturalDonReject) -> NaturalDonOut:
    don = _get_don_or_raise(session, id_don_n)
    if don.status in ["In_Stock", "Refuse"]:
        raise InvalidStatusTransitionError("Ce don ne peut plus être refusé.")
    
    don.status = "Refuse"
    don.refusal_reason = payload.refusal_reason
    don.validated_by = user.id_user
    don.validated_at = datetime.now(timezone.utc)
    session.commit()
    session.refresh(don)
    return NaturalDonOut.model_validate(don)


# ============================================================
# NAT-09 : Planifier une collecte
# ============================================================
def plan_natural_don_collect(session: Session, id_don_n: UUID, user: User, payload: NaturalDonCollectPlan) -> NaturalDonOut:
    don = _get_don_or_raise(session, id_don_n)
    if don.recovery_mode != "Collect":
        raise InvalidStatusTransitionError("Ce don n'est pas en mode 'Collect'.")
    if don.status != "valid":
        raise InvalidStatusTransitionError("Le don doit d'abord être validé.")
    
    don.status = "Collection_Planned"
    don.planned_by = user.id_user
    don.planned_at = datetime.now(timezone.utc)
    don.collection_address = payload.collection_address
    session.commit()
    session.refresh(don)
    return NaturalDonOut.model_validate(don)


# ============================================================
# NAT-10 : Contrôle à la réception
# ============================================================
def update_item_reception(session: Session, id_don_n: UUID, id_nat: UUID, user: User, payload: NaturalDonItemReception) -> NaturalDonItemOut:
    don = _get_don_or_raise(session, id_don_n)
    if don.status not in ["valid", "Collection_Planned"]:
        raise InvalidStatusTransitionError("Le don doit être validé ou planifié.")
    
    item = don_repo.get_natural_don_item(session, id_don_n, id_nat)
    if not item:
        raise ItemNotFoundError("Article introuvable")
    
    item.received_quantity = payload.received_quantity
    item.received_state = payload.received_state
    item.is_compliant = payload.is_compliant
    item.non_compliant_reason = payload.non_compliant_reason
    
    session.commit()
    session.refresh(item)
    return NaturalDonItemOut.model_validate(item)


# ============================================================
# NAT-11 : Versement en stock
# ============================================================
def stock_in_natural_don(session: Session, id_don_n: UUID, user: User) -> NaturalDonOut:
    don = _get_don_or_raise(session, id_don_n)
    if don.status not in ["valid", "Collection_Planned"]:
        raise InvalidStatusTransitionError("Le don doit être validé ou planifié.")
    
    # Normalement, on ajoute les items conformes au module de stock ici.
    # Pour l'instant, on simule l'affectation à un ID de stock.
    don.status = "In_Stock"
    don.received_by = user.id_user
    don.received_at = datetime.now(timezone.utc)
    don.id_stock = f"STOCK-{don.id_don_n.hex[:6].upper()}"
    
    session.commit()
    session.refresh(don)
    return NaturalDonOut.model_validate(don)