"""Endpoints HTTP du module natural_donations."""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.dependencies import (
    get_current_user,
    require_campaign_editor,
    require_natural_donation_staff,
    require_stock_manager_or_admin,
)
from app.database import get_db
from app.modules.auth.models import User
from app.modules.natural_donations import service as don_service
from app.modules.natural_donations.schemas import (
    CollectOut,
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
from app.modules.natural_donations.service import (
    InvalidStatusTransitionError,
    ItemNotFoundError,
    NaturalDonNotFoundError,
    ObjectTypeNotFoundError,
)

# ============================================================
# Routers
# ============================================================
router = APIRouter(prefix="", tags=["Natural Donations"])
admin_router = APIRouter(prefix="/admin", tags=["Admin - Object Types"])


# ============================================================
# NAT-01 : Liste des types d'objets actifs (AuthentifiÃ©)
# ============================================================
@router.get("/object-types", response_model=list[ObjectTypeOut])
def nat01_list_active_object_types(
    session: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """NAT-01 : Liste des types d'objets actifs."""
    return don_service.list_object_types(session, only_active=True)


# ============================================================
# NAT-15 Ã  NAT-18 : Gestion des types d'objets (Admin/Stock)
# ============================================================
@admin_router.get("/object-types", response_model=list[ObjectTypeOut])
def nat15_list_all_object_types(
    session: Session = Depends(get_db),
    user: User = Depends(require_campaign_editor) # Ã€ remplacer par require_stock_manager si existant
):
    """NAT-15 : Liste complÃ¨te des types d'objets."""
    return don_service.list_object_types(session, only_active=False)

@admin_router.post("/object-types", response_model=ObjectTypeOut, status_code=status.HTTP_201_CREATED)
def nat16_create_object_type(
    payload: ObjectTypeCreate,
    session: Session = Depends(get_db),
    user: User = Depends(require_campaign_editor)
):
    """NAT-16 : CrÃ©e un type d'objet."""
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
    """NAT-18 : Active ou dÃ©sactive un type d'objet."""
    try:
        return don_service.toggle_object_type_activation(session, id_object, is_active)
    except ObjectTypeNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc


# ============================================================
# NAT-02 Ã  NAT-11 : Dons en nature
# ============================================================
@router.post("/donations/natural", response_model=NaturalDonWithItemsOut, status_code=status.HTTP_201_CREATED)
def nat02_create_natural_don(
    payload: NaturalDonCreate,
    session: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """NAT-02 : DÃ©clare un don en nature."""
    return don_service.create_natural_don(session, user=user, payload=payload)

# ============================================================
# NAT-03 : Upload de l'image d'un article (Donateur)
# ============================================================
@router.post(
    "/donations/natural/{id_don_n}/items/{id_nat}/image",
    response_model=NaturalDonItemOut,
)
async def nat03_upload_item_image(
    id_don_n: UUID,
    id_nat: UUID,
    image: UploadFile = File(..., description="Photo de l'article"),
    session: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """NAT-03 : TÃ©lÃ©verse la photo d'un article (conversion WebP)."""
    if not image.content_type.startswith("image/"):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Le fichier fourni n'est pas une image.",
        )

    image_bytes = await image.read()
    try:
        return don_service.upload_item_image(
            session,
            user=user,
            id_don_n=id_don_n,
            id_nat=id_nat,
            image_bytes=image_bytes,
        )
    except NaturalDonNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    except ItemNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    except InvalidStatusTransitionError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc


# ============================================================
# NAT-19 : Remplacement de l'image d'un article
# ============================================================
@router.patch(
    "/donations/natural/{id_don_n}/items/{id_nat}/image",
    response_model=NaturalDonItemOut,
)
async def nat19_replace_item_image(
    id_don_n: UUID,
    id_nat: UUID,
    image: UploadFile = File(..., description="Nouvelle photo de l'article"),
    session: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """NAT-19 : Remplace l'image existante d'un article (conversion WebP)."""
    if not image.content_type.startswith("image/"):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Le fichier fourni n'est pas une image.",
        )

    image_bytes = await image.read()
    try:
        return don_service.replace_item_image(
            session,
            user=user,
            id_don_n=id_don_n,
            id_nat=id_nat,
            image_bytes=image_bytes,
        )
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
    """NAT-04 : Annule la dÃ©claration."""
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
    """NAT-06 : DÃ©tail du don et de ses articles."""
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
    user: User = Depends(require_natural_donation_staff)
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
    """NAT-10 : ContrÃ´le Ã  la rÃ©ception."""
    try:
        return don_service.update_item_reception(session, id_don_n, id_nat, user, payload)
    except NaturalDonNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    except ItemNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    except InvalidStatusTransitionError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc

@router.post("/donations/natural/{id_don_n}/stock-in", response_model=NaturalDonWithItemsOut)
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

# ============================================================
# NAT-12 : Liste des collectes planifiÃ©es
# ============================================================
@router.get("/collects", response_model=list[CollectOut])
def nat12_list_collects(
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    status: str | None = None,
    session: Session = Depends(get_db),
    user: User = Depends(require_natural_donation_staff),
):
    """NAT-12 : Liste les collectes planifiÃ©es."""
    return don_service.list_collects(
        session,
        start_date=start_date,
        end_date=end_date,
        status=status,
    )

# ============================================================
# NAT-13 : Modification d'une collecte
# ============================================================
@router.patch("/collects/{id_collect}", response_model=CollectOut)
def nat13_update_collect(
    id_collect: UUID,
    payload: CollectUpdate,
    session: Session = Depends(get_db),
    user: User = Depends(require_natural_donation_staff),
):
    """NAT-13 : Modifie la date ou le lieu d'une collecte."""
    try:
        return don_service.update_collect(session, id_collect, payload)
    except NaturalDonNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    except InvalidStatusTransitionError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc

# ============================================================
# NAT-14 : Confirmation d'une collecte
# ============================================================
@router.post("/collects/{id_collect}/confirm", response_model=NaturalDonWithItemsOut)
def nat14_confirm_collect(
    id_collect: UUID,
    session: Session = Depends(get_db),
    user: User = Depends(require_stock_manager_or_admin),
):
    """NAT-14 : Confirme qu'une collecte a eu lieu."""
    try:
        return don_service.confirm_collect(session, id_collect, user)
    except NaturalDonNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    except InvalidStatusTransitionError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
