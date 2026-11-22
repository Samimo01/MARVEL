"""Endpoints HTTP du module campaigns."""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_campaign_editor
from app.database import get_db
from app.modules.auth.models import User
from app.modules.campaigns import service as campaign_service
from app.modules.campaigns.schemas import (
    CampaignCreate,
    CampaignOut,
    CampaignProgressOut,
    CampaignUpdate,
    EventCreate,
    EventOut,
    EventUpdate,
    FinancialDonOut,
    GaugeOut,
)
from app.modules.campaigns.service import (
    CampaignNotFoundError,
    CampaignTitleAlreadyExistsError,
    EventNotFoundError,
    InvalidStatusTransitionError,
)

# ============================================================
# DÃ©claration des routers
# ============================================================
campaign_catalog_router = APIRouter(prefix="/catalog/campaigns", tags=["catalog"])
router = APIRouter(prefix="/campaigns", tags=["Campaigns"])

events_router = APIRouter(prefix="/events", tags=["Events"])
event_catalog_router = APIRouter(prefix="/catalogue/events", tags=["catalog"])

# ============================================================
# ROUTES PUBLIQUES (CAT-01, CAT-02, CAM-07)
# ============================================================
@campaign_catalog_router.get("", response_model=list[CampaignProgressOut])
def cat01_list_active_campaigns(
    session: Session = Depends(get_db),
    limit: int = 50,
    offset: int = 0,
):
    """CAT-01 : Campagnes en cours avec jauge."""
    return campaign_service.list_active_campaigns(session, limit=limit, offset=offset)

@campaign_catalog_router.get("/closed", response_model=list[CampaignProgressOut])
def cam07_list_closed_campaigns(
    session: Session = Depends(get_db),
    limit: int = 50,
    offset: int = 0,
):
    """CAM-07 : Campagnes fermÃ©es avec jauge."""
    return campaign_service.list_closed_campaigns(session, limit=limit, offset=offset)

@campaign_catalog_router.get("/{id_campaign}", response_model=CampaignProgressOut)
def cat02_campaign_detail(
    id_campaign: UUID,
    session: Session = Depends(get_db),
):
    """CAT-02 : DÃ©tail d'une campagne publique."""
    try:
        return campaign_service.get_public_campaign(session, id_campaign)
    except CampaignNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc


# ============================================================
# ROUTES PRIVÃ‰ES DE CRÃ‰ATION ET LISTES SPÃ‰CIFIQUES
# ============================================================
@router.post("/draft", response_model=CampaignOut, status_code=status.HTTP_201_CREATED)
def cam11_create_draft_campaign(
    payload: CampaignCreate,
    session: Session = Depends(get_db),
    user: User = Depends(require_campaign_editor),
):
    """CAM-11 : CrÃ©er une campagne en mode brouillon."""
    try:
        return campaign_service.create_draft_campaign(session, user=user, payload=payload)
    except CampaignTitleAlreadyExistsError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc

@router.get("/{id_user}/draft", response_model=list[CampaignOut])
def cam08_list_user_drafts(
    id_user: UUID,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """CAM-08 : Les brouillons d'une personne."""
    return campaign_service.list_user_drafts(session, id_user)

@router.get("/{id_user}/invisible", response_model=list[CampaignOut])
def cam10_list_user_invisible_campaigns(
    id_user: UUID,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """CAM-10 : Toutes les campagnes dÃ©sactivÃ©es d'un utilisateur."""
    return campaign_service.list_user_invisible_campaigns(session, id_user)


# ============================================================
# ROUTES PRIVÃ‰ES DE GESTION GLOBALE
# ============================================================
@router.post("", response_model=CampaignOut, status_code=status.HTTP_201_CREATED)
def cat07_create_campaign(
    payload: CampaignCreate,
    session: Session = Depends(get_db),
    user: User = Depends(require_campaign_editor),
):
    """CAT-07 : CrÃ©er une campagne."""
    try:
        return campaign_service.create_campaign(session, user=user, payload=payload)
    except CampaignTitleAlreadyExistsError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc

@router.get("", response_model=list[CampaignOut])
def cam09_list_all_campaigns(
    status: str | None = None,
    start_at: datetime | None = None,
    finish_at: datetime | None = None,
    limit: int = 50,
    offset: int = 0,
    session: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """CAM-09 : Toutes les campagnes."""
    return campaign_service.list_all_campaigns(
        session, status=status, start_at=start_at, finish_at=finish_at, limit=limit, offset=offset
    )

@router.get("/{id_campaign}", response_model=CampaignOut)
def cam02_get_campaign_private(
    id_campaign: UUID,
    session: Session = Depends(get_db),
    user: User = Depends(require_campaign_editor),
):
    """DÃ©tail privÃ© d'une campagne."""
    try:
        campaign = campaign_service._get_or_raise(session, id_campaign)
        return CampaignOut.model_validate(campaign)
    except CampaignNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc

@router.put("/{id_campaign}", response_model=CampaignOut)
def cat08_update_campaign(
    id_campaign: UUID,
    payload: CampaignUpdate,
    session: Session = Depends(get_db),
    user: User = Depends(require_campaign_editor),
):
    """CAT-08 : Modifier une campagne."""
    try:
        return campaign_service.update_campaign(
            session, user=user, id_campaign=id_campaign, payload=payload
        )
    except CampaignNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    except CampaignTitleAlreadyExistsError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc

@router.post("/{id_campaign}/deactivate", response_model=CampaignOut)
def cat09_deactivate_campaign(
    id_campaign: UUID,
    session: Session = Depends(get_db),
    user: User = Depends(require_campaign_editor),
):
    """CAT-09 : Rendre invisible (repasser en brouillon)."""
    try:
        return campaign_service.deactivate_campaign(session, user=user, id_campaign=id_campaign)
    except CampaignNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc

@router.delete("/{id_campaign}", status_code=status.HTTP_204_NO_CONTENT)
def cat10_delete_campaign(
    id_campaign: UUID,
    session: Session = Depends(get_db),
    user: User = Depends(require_campaign_editor),
):
    """CAT-10 : Supprimer une campagne."""
    try:
        campaign_service.delete_campaign(session, user=user, id_campaign=id_campaign)
    except CampaignNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc


# ============================================================
# ROUTES WORKFLOW (CAM-03, CAM-04, CAM-05, CAM-06)
# ============================================================
@router.post("/{id_campaign}/publish", response_model=CampaignOut)
def cam03_publish_campaign(
    id_campaign: UUID,
    session: Session = Depends(get_db),
    user: User = Depends(require_campaign_editor),
):
    """CAM-03 : Publier une campagne (Brouillon -> En_Cours)."""
    try:
        return campaign_service.publish_campaign_action(session, user=user, id_campaign=id_campaign)
    except CampaignNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    except InvalidStatusTransitionError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc

@router.post("/{id_campaign}/close", response_model=CampaignOut)
def cam04_close_campaign(
    id_campaign: UUID,
    reason: str | None = None,
    session: Session = Depends(get_db),
    user: User = Depends(require_campaign_editor),
):
    """CAM-04 : ClÃ´turer une campagne."""
    try:
        return campaign_service.close_campaign_action(
            session, user=user, id_campaign=id_campaign, reason=reason
        )
    except CampaignNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    except InvalidStatusTransitionError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc

@router.get("/{id_campaign}/gauge", response_model=GaugeOut)
def cam05_get_gauge(
    id_campaign: UUID,
    session: Session = Depends(get_db),
):
    """CAM-05 : Jauge de progression (Public)."""
    try:
        return campaign_service.get_gauge(session, id_campaign)
    except CampaignNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc

@router.get("/{id_campaign}/donations", response_model=list[FinancialDonOut])
def cam06_get_donations(
    id_campaign: UUID,
    session: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """CAM-06 : Dons rattachÃ©s Ã  la campagne."""
    try:
        return campaign_service.get_campaign_donations(session, id_campaign)
    except CampaignNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
from fastapi import File, UploadFile


# ============================================================
# CAM-12 : POST /campaigns/{id}/image
# ============================================================
@router.post("/{id_campaign}/image", response_model=CampaignOut)
async def cam12_upload_campaign_image(
    id_campaign: UUID,
    image: UploadFile = File(..., description="Image de la campagne (JPEG, PNG, etc.)"),
    session: Session = Depends(get_db),
    user: User = Depends(require_campaign_editor),
):
    """CAM-12 : TÃ©lÃ©verse la photo d'une campagne (convertie en WebP)."""
    if not image.content_type.startswith("image/"):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Le fichier fourni n'est pas une image.",
        )

    image_bytes = await image.read()
    try:
        return campaign_service.upload_campaign_image(
            session, user=user, id_campaign=id_campaign, image_bytes=image_bytes
        )
    except CampaignNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    except InvalidStatusTransitionError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc


# ============================================================
# CAM-13 : PATCH /campaigns/{id}/image
# ============================================================
@router.patch("/{id_campaign}/image", response_model=CampaignOut)
async def cam13_replace_campaign_image(
    id_campaign: UUID,
    image: UploadFile = File(..., description="Nouvelle image de la campagne"),
    session: Session = Depends(get_db),
    user: User = Depends(require_campaign_editor),
):
    """CAM-13 : TÃ©lÃ©verse et remplace l'image existante (convertie en WebP)."""
    if not image.content_type.startswith("image/"):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Le fichier fourni n'est pas une image.",
        )

    image_bytes = await image.read()
    try:
        return campaign_service.replace_campaign_image(
            session, user=user, id_campaign=id_campaign, image_bytes=image_bytes
        )
    except CampaignNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc

# ============================================================
# GESTION DES Ã‰VÃ‰NEMENTS
# ============================================================

@router.post(
    "/{id_campaign}/events",
    response_model=EventOut,
    status_code=status.HTTP_201_CREATED,
)
def cam10_create_event(
    id_campaign: UUID,
    payload: EventCreate,
    session: Session = Depends(get_db),
    user: User = Depends(require_campaign_editor),
):
    try:
        return campaign_service.create_event(
            session, id_campaign=id_campaign, payload=payload
        )
    except CampaignNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc


@events_router.get("", response_model=list[EventOut])
def cam11_list_events(
    event_at: datetime | None = None,
    id_campaign: UUID | None = None,
    session: Session = Depends(get_db),
    user: User = Depends(require_campaign_editor),
):
    return campaign_service.list_events(
        session, event_at=event_at, id_campaign=id_campaign
    )


@events_router.get("/{id_event}", response_model=EventOut)
def cam12_get_event(
    id_event: UUID,
    session: Session = Depends(get_db),
    user: User = Depends(require_campaign_editor),
):
    try:
        return campaign_service.get_event(session, id_event)
    except EventNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc


@events_router.patch("/{id_event}", response_model=EventOut)
def cam13_update_event(
    id_event: UUID,
    payload: EventUpdate,
    session: Session = Depends(get_db),
    user: User = Depends(require_campaign_editor),
):
    try:
        return campaign_service.update_event(
            session, id_event=id_event, payload=payload
        )
    except EventNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc


@events_router.delete(
    "/{id_event}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def cam14_delete_event(
    id_event: UUID,
    session: Session = Depends(get_db),
    user: User = Depends(require_campaign_editor),
):
    try:
        campaign_service.delete_event(session, id_event)
    except EventNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc

# ============================================================
# ROUTES PUBLIQUES DES Ã‰VÃ‰NEMENTS (CAT-03, CAT-04)
# ============================================================

@event_catalog_router.get("", response_model=list[EventOut])
def cat03_list_upcoming_events(
    session: Session = Depends(get_db),
):
    """CAT-03 : Liste publique des Ã©vÃ©nements Ã  venir."""
    return campaign_service.list_upcoming_events(session)


@event_catalog_router.get("/{id_event}", response_model=EventOut)
def cat04_get_public_event(
    id_event: UUID,
    session: Session = Depends(get_db),
):
    """CAT-04 : DÃ©tail public d'un Ã©vÃ©nement."""
    try:
        return campaign_service.get_event(session, id_event)
    except EventNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc