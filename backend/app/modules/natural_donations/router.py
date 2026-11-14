"""Endpoints HTTP du module natural_donations."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_campaign_editor
from app.database import get_db
from app.modules.auth.models import User
from app.modules.natural_donations import service as don_service
from app.modules.natural_donations.schemas import (
    NaturalDonCreate, NaturalDonOut, NaturalDonWithItemsOut, NaturalDonItemOut,
    NaturalDonReject, NaturalDonCollectPlan, NaturalDonItemReception,
    ObjectTypeCreate, ObjectTypeUpdate, ObjectTypeOut
)
from app.modules.natural_donations.service import (
    NaturalDonNotFoundError, ObjectTypeNotFoundError, 
    InvalidStatusTransitionError, ItemNotFoundError
)

# ============================================================
# Routers
# ============================================================
router = APIRouter(prefix="", tags=["Natural Donations"])
admin_router = APIRouter(prefix="/admin", tags=["Admin - Object Types"])


# ============================================================
# NAT-01 : Liste des types d'objets actifs (Authentifié)
# ============================================================
@router.get("/object-types", response_model=list[ObjectTypeOut])
def nat01_list_active_object_types(
    session: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """NAT-01 : Liste des types d'objets actifs."""
    return don_service.list_object_types(session, only_active=True)


# ============================================================
# NAT-15 à NAT-18 : Gestion des types d'objets (Admin/Stock)
# ============================================================
@admin_router.get("/object-types", response_model=list[ObjectTypeOut])
def nat15_list_all_object_types(
    session: Session = Depends(get_db),
    user: User = Depends(require_campaign_editor) # À remplacer par require_stock_manager si existant
):
    """NAT-15 : Liste complète des types d'objets."""
    return don_service.list_object_types(session, only_active=False)

@admin_router.post("/object-types", response_model=ObjectTypeOut, status_code=status.HTTP_201_CREATED)
def nat16_create_object_type(
    payload: ObjectTypeCreate,
    session: Session = Depends(get_db),
    user: User = Depends(require_campaign_editor)
):
    """NAT-16 : Crée un type d'objet."""
    return don_service.create_object_type(session, payload)

@admin_router.put("/object-types/{id_object}", response_model=ObjectTypeOut)
def nat17_update_object_type(
    id_object: UUID,
    payload: ObjectTypeUpdate,
    session: Session = Depends(get_db),
    user: User = Depends(require_campaign_editor)
):
    """NAT-17 : Modifie un type d'objet."""
    try:
        return don_service.update_object_type(session, id_object, payload)
    except ObjectTypeNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc

@admin_router.patch("/object-types/{id_object}/activation", response_model=ObjectTypeOut)
def nat18_toggle_object_type(
    id_object: UUID,
    is_active: bool,
    session: Session = Depends(get_db),
    user: User = Depends(require_campaign_editor)
):
    """NAT-18 : Active ou désactive un type d'objet."""
    try:
        return don_service.toggle_object_type_activation(session, id_object, is_active)
    except ObjectTypeNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc


# ============================================================
# NAT-02 à NAT-11 : Dons en nature
# ============================================================
@router.post("/donations/natural", response_model=NaturalDonWithItemsOut, status_code=status.HTTP_201_CREATED)
def nat02_create_natural_don(
    payload: NaturalDonCreate,
    session: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """NAT-02 : Déclare un don en nature."""
    return don_service.create_natural_don(session, user=user, payload=payload)

@router.post("/donations/natural/{id_don_n}/items/{id_nat}/image", response_model=NaturalDonItemOut)
def nat03_upload_item_image(
    id_don_n: UUID,
    id_nat: UUID,
    image_url: str, # En vrai, ce serait un UploadFile. On prend une URL pour simplifier.
    session: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """NAT-03 : Téléverse la photo d'un article."""
    try:
        return don_service.upload_item_image(session, id_don_n, id_nat, image_url)
    except NaturalDonNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    except ItemNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc

@router.delete("/donations/natural/{id_don_n}", status_code=status.HTTP_204_NO_CONTENT)
def nat04_cancel_natural_don(
    id_don_n: UUID,
    session: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """NAT-04 : Annule la déclaration."""
    try:
        don_service.cancel_natural_don(session, id_don_n, user)
    except NaturalDonNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    except InvalidStatusTransitionError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc

@router.get("/donations/natural", response_model=list[NaturalDonOut])
def nat05_list_natural_dons(
    status: str | None = None,
    session: Session = Depends(get_db),
    user: User = Depends(require_campaign_editor)
):
    """NAT-05 : Liste filtrable par statut."""
    return don_service.list_natural_dons(session, status)

@router.get("/donations/natural/{id_don_n}", response_model=NaturalDonWithItemsOut)
def nat06_get_natural_don_detail(
    id_don_n: UUID,
    session: Session = Depends(get_db),
    user: User = Depends(require_campaign_editor)
):
    """NAT-06 : Détail du don et de ses articles."""
    try:
        return don_service.get_natural_don_detail(session, id_don_n)
    except NaturalDonNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc

@router.post("/donations/natural/{id_don_n}/validate", response_model=NaturalDonOut)
def nat07_validate_natural_don(
    id_don_n: UUID,
    session: Session = Depends(get_db),
    user: User = Depends(require_campaign_editor)
):
    """NAT-07 : Valider un don."""
    try:
        return don_service.validate_natural_don(session, id_don_n, user)
    except NaturalDonNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    except InvalidStatusTransitionError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc

@router.post("/donations/natural/{id_don_n}/reject", response_model=NaturalDonOut)
def nat08_reject_natural_don(
    id_don_n: UUID,
    payload: NaturalDonReject,
    session: Session = Depends(get_db),
    user: User = Depends(require_campaign_editor)
):
    """NAT-08 : Refuser un don."""
    try:
        return don_service.reject_natural_don(session, id_don_n, user, payload)
    except NaturalDonNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    except InvalidStatusTransitionError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc

@router.post("/donations/natural/{id_don_n}/collects", response_model=NaturalDonOut)
def nat09_plan_collect(
    id_don_n: UUID,
    payload: NaturalDonCollectPlan,
    session: Session = Depends(get_db),
    user: User = Depends(require_campaign_editor)
):
    """NAT-09 : Planifie la collecte."""
    try:
        return don_service.plan_natural_don_collect(session, id_don_n, user, payload)
    except NaturalDonNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    except InvalidStatusTransitionError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc

@router.put("/donations/natural/{id_don_n}/items/{id_nat}/reception", response_model=NaturalDonItemOut)
def nat10_update_item_reception(
    id_don_n: UUID,
    id_nat: UUID,
    payload: NaturalDonItemReception,
    session: Session = Depends(get_db),
    user: User = Depends(require_campaign_editor)
):
    """NAT-10 : Contrôle à la réception."""
    try:
        return don_service.update_item_reception(session, id_don_n, id_nat, user, payload)
    except NaturalDonNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    except ItemNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    except InvalidStatusTransitionError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc

@router.post("/donations/natural/{id_don_n}/stock-in", response_model=NaturalDonOut)
def nat11_stock_in_natural_don(
    id_don_n: UUID,
    session: Session = Depends(get_db),
    user: User = Depends(require_campaign_editor)
):
    """NAT-11 : Verse les articles conformes dans le Stock."""
    try:
        return don_service.stock_in_natural_don(session, id_don_n, user)
    except NaturalDonNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    except InvalidStatusTransitionError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc