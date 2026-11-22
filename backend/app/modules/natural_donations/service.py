"""Logique mÃ©tier du module natural_donations."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.image_utils import convert_image_to_webp
from app.core.supabase_client import NATURAL_DONATIONS_BUCKET, supabase_admin
from app.modules.auth import repository as auth_repo
from app.modules.auth.models import User
from app.modules.natural_donations import repository as don_repo
from app.modules.natural_donations.models import (
    Collect,
    NaturalDon,
    NaturalDonItem,
    ObjectType,
)
from app.modules.natural_donations.schemas import (
    CollectUpdate,
    NaturalDonCollectPlan,
    NaturalDonCreate,
    NaturalDonItemOut,
    NaturalDonItemReception,
    NaturalDonOut,
    NaturalDonReject,
    NaturalDonWithItemsOut,
    ObjectTypeCreate,
    ObjectTypeOut,
    ObjectTypeUpdate,
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

def _upload_natural_item_image(
    id_don_n: UUID,
    id_nat: UUID,
    image_bytes: bytes,
    *,
    replace: bool = False,
) -> str:
    """Convertit en WebP, upload vers Supabase, retourne l'URL publique."""
    webp_bytes = convert_image_to_webp(image_bytes)
    path = f"{id_don_n}/{id_nat}.webp"

    supabase_admin.storage.from_(NATURAL_DONATIONS_BUCKET).upload(
        path=path,
        file=webp_bytes,
        file_options={
            "content-type": "image/webp",
            "upsert": "true" if replace else "false",
        },
    )

    return supabase_admin.storage.from_(NATURAL_DONATIONS_BUCKET).get_public_url(path)
# app/modules/natural_donations/service.py


def _is_staff(session: Session, user: User) -> bool:
    """VÃ©rifie si l'utilisateur a un rÃ´le de staff via le repository d'auth."""
    for role_name in ("Stock_Manager", "Collection_Manager", "Administrator"):
        assignment = auth_repo.get_latest_role_assignment(
            session, user.id_user, role_name
        )
        if assignment is not None and assignment.assignment_type == "assigned":
            return True
    return False
# ============================================================
# NAT-01, NAT-15 Ã  NAT-18 : OBJECT TYPES
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
# NAT-02 : CrÃ©ation d'un don
# ============================================================
def create_natural_don(session: Session, *, user: User, payload: NaturalDonCreate) -> NaturalDonWithItemsOut:
    # 1. CrÃ©er le don
    don = NaturalDon(
        id_user=user.id_user,
        recovery_mode=payload.recovery_mode,
        collection_address=payload.collection_address,
        id_campaign=payload.id_campaign,
        status="Declare"
    )
    don_repo.add_natural_don(session, don)

    # 2. CrÃ©er les items
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
# NAT-03 : Upload (crÃ©ation) de l'image d'un article
# ============================================================
def upload_item_image(
    session: Session,
    *,
    user: User,
    id_don_n: UUID,
    id_nat: UUID,
    image_bytes: bytes,
) -> NaturalDonItemOut:
    don = _get_don_or_raise(session, id_don_n)

    is_owner = don.id_user == user.id_user
    is_staff = _is_staff(session, user)
    # 1. ContrÃ´le d'accÃ¨s : propriÃ©taire OU staff
    if not is_owner and not is_staff:
        raise InvalidStatusTransitionError(
            "Vous n'Ãªtes ni le propriÃ©taire du don ni un membre du staff autorisÃ©."
        )

    # 2. VÃ©rification du statut (uniquement pour le propriÃ©taire)
    if not is_staff and don.status != "Declare":
        raise InvalidStatusTransitionError(
            "L'image ne peut Ãªtre ajoutÃ©e qu'au statut 'Declare'."
        )

    item = don_repo.get_natural_don_item(session, id_don_n, id_nat)
    if not item:
        raise ItemNotFoundError("Article introuvable")

    if item.image_url:
        raise InvalidStatusTransitionError(
            "Une image existe dÃ©jÃ  pour cet article. Utilisez PATCH pour la remplacer."
        )

    url = _upload_natural_item_image(id_don_n, id_nat, image_bytes, replace=False)
    item.image_url = url
    session.commit()
    session.refresh(item)
    return NaturalDonItemOut.model_validate(item)


def replace_item_image(
    session: Session,
    *,
    user: User,
    id_don_n: UUID,
    id_nat: UUID,
    image_bytes: bytes,
) -> NaturalDonItemOut:
    don = _get_don_or_raise(session, id_don_n)
    item = don_repo.get_natural_don_item(session, id_don_n, id_nat)

    if not item:
        raise ItemNotFoundError("Article introuvable")

    # ðŸ‘‡ ContrÃ´le d'accÃ¨s pour le remplacement
    if don.id_user != user.id_user and not _is_staff(session, user):
        raise InvalidStatusTransitionError(
            "Vous n'Ãªtes ni le propriÃ©taire du don ni un membre du staff autorisÃ©."
        )

    url = _upload_natural_item_image(id_don_n, id_nat, image_bytes, replace=True)
    item.image_url = url
    session.commit()
    session.refresh(item)
    return NaturalDonItemOut.model_validate(item)
# ============================================================
# NAT-04 : Annuler un don
# ============================================================
def cancel_natural_don(session: Session, id_don_n: UUID, user: User) -> None:
    don = _get_don_or_raise(session, id_don_n)
    if don.status != "Declare":
        raise InvalidStatusTransitionError("Seul un don Ã  l'Ã©tat 'Declare' peut Ãªtre annulÃ©.")
    if don.id_user != user.id_user:
        raise InvalidStatusTransitionError("Vous n'Ãªtes pas le propriÃ©taire de ce don.")

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
        raise InvalidStatusTransitionError("Seul un don Ã  l'Ã©tat 'Declare' peut Ãªtre validÃ©.")

    don.status = "valid"
    don.validated_by = user.id_user
    don.validated_at = datetime.now(UTC)
    session.commit()
    session.refresh(don)
    return NaturalDonOut.model_validate(don)


# ============================================================
# NAT-08 : Refuser un don
# ============================================================
def reject_natural_don(session: Session, id_don_n: UUID, user: User, payload: NaturalDonReject) -> NaturalDonOut:
    don = _get_don_or_raise(session, id_don_n)
    if don.status in ["In_Stock", "Refuse"]:
        raise InvalidStatusTransitionError("Ce don ne peut plus Ãªtre refusÃ©.")

    don.status = "Refuse"
    don.refusal_reason = payload.refusal_reason
    don.validated_by = user.id_user
    don.validated_at = datetime.now(UTC)
    session.commit()
    session.refresh(don)
    return NaturalDonOut.model_validate(don)


# ============================================================
# NAT-09 : Planifier une collecte
# ============================================================
def plan_natural_don_collect(
    session: Session,
    id_don_n: UUID,
    user: User,
    payload: NaturalDonCollectPlan
) -> NaturalDonOut:
    don = _get_don_or_raise(session, id_don_n)

    if don.recovery_mode != "Collect":
        raise InvalidStatusTransitionError("Ce don n'est pas en mode 'Collect'.")

    if don.status != "valid":
        raise InvalidStatusTransitionError("Le don doit d'abord Ãªtre validÃ©.")

    collect = Collect(
        place=payload.collection_address,
        planned_at=payload.planned_at,
        id_user=user.id_user
    )

    don_repo.add_collect(session, collect)

    don.status = "Collection_Planned"
    don.planned_by = user.id_user
    don.planned_at = payload.planned_at
    don.collection_address = payload.collection_address

    session.flush()
    don.id_collect = collect.id_collect

    session.commit()
    session.refresh(don)

    return NaturalDonOut.model_validate(don)

def list_collects(
    session: Session,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    status: str | None = None,
):
    return don_repo.list_collects(
        session,
        start_date=start_date,
        end_date=end_date,
        status=status,
    )

def update_collect(
    session: Session,
    id_collect: UUID,
    payload: CollectUpdate,
) -> Collect:
    collect = don_repo.get_collect_by_id(session, id_collect)

    if collect is None:
        raise NaturalDonNotFoundError("Collecte introuvable.")

    data = payload.model_dump(exclude_unset=True)

    if not data:
        raise InvalidStatusTransitionError("Aucune modification fournie.")

    don_repo.update_collect(session, collect, data)

    session.commit()
    session.refresh(collect)

    return collect

def confirm_collect(
    session: Session,
    id_collect: UUID,
    user: User,
) -> NaturalDonOut:
    collect = don_repo.get_collect_by_id(session, id_collect)

    if collect is None:
        raise NaturalDonNotFoundError("Collecte introuvable.")

    don = don_repo.get_natural_don_by_collect_id(session, id_collect)

    if don is None:
        raise NaturalDonNotFoundError("Don associÃ© Ã  cette collecte introuvable.")

    if don.status != "Collection_Planned":
        raise InvalidStatusTransitionError(
            "Le don doit avoir le statut Collection_Planned."
        )

    don.status = "In_Stock"
    don.received_by = user.id_user
    don.received_at = datetime.now(UTC)
    collect.status = "Done"

    session.commit()
    session.refresh(don)

    return NaturalDonWithItemsOut.model_validate(don)
# ============================================================
# NAT-10 : ContrÃ´le Ã  la rÃ©ception
# ============================================================
def update_item_reception(session: Session, id_don_n: UUID, id_nat: UUID, user: User, payload: NaturalDonItemReception) -> NaturalDonItemOut:
    don = _get_don_or_raise(session, id_don_n)
    if don.status not in ["valid", "Collection_Planned"]:
        raise InvalidStatusTransitionError("Le don doit Ãªtre validÃ© ou planifiÃ©.")

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
        raise InvalidStatusTransitionError("Le don doit Ãªtre validÃ© ou planifiÃ©.")

    # Normalement, on ajoute les items conformes au module de stock ici.
    # Pour l'instant, on simule l'affectation Ã  un ID de stock.
    don.status = "In_Stock"
    don.received_by = user.id_user
    don.received_at = datetime.now(UTC)
    for item in don.items:
        if item.is_compliant:
            item.id_stock = f"STOCK-{item.id_nat.hex[:6].upper()}"

    session.commit()
    session.refresh(don)
    return NaturalDonWithItemsOut.model_validate(don)
