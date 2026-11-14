"""Endpoints HTTP du module campaigns."""

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

# Corrections des imports
from app.database import get_db
from app.core.dependencies import require_campaign_editor
from app.modules.auth.models import User
from app.modules.campaigns import service as campaign_service
from app.modules.campaigns.schemas import (
    CampaignCreate, CampaignOut, CampaignProgressOut, CampaignUpdate, PublicationIn,
)
from app.modules.campaigns.service import (
    CampaignNotFoundError, CampaignTitleAlreadyExistsError, CannotPublishClosedCampaignError,
)

# ============================================================
# Deux routers : gestion (auth) + catalogue public
# ============================================================
router = APIRouter(prefix="/campaigns", tags=["campaigns"])
catalogue_router = APIRouter(prefix="/catalogue/campagnes", tags=["catalogue"])


# ============================================================
# CAT-01 — GET /catalogue/campagnes (Public)
# ============================================================
@catalogue_router.get("", response_model=list[CampaignProgressOut])
def cat01_list_active_campaigns(
    session: Session = Depends(get_db),  # <-- Correction: get_db
    limit: int = 50,
    offset: int = 0,
):
    return campaign_service.list_active_campaigns(session, limit=limit, offset=offset)


# ============================================================
# CAT-02 — GET /catalogue/campagnes/{id} (Public)
# ============================================================
@catalogue_router.get("/{id_campaign}", response_model=CampaignProgressOut)
def cat02_campaign_detail(
    id_campaign: UUID,
    session: Session = Depends(get_db),
):
    try:
        return campaign_service.get_public_campaign(session, id_campaign)
    except CampaignNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc


# ============================================================
# CAT-07 — POST /campaigns (Resp, Admin, Bénéficiaire)
# ============================================================
@router.post("", response_model=CampaignOut, status_code=status.HTTP_201_CREATED)
def cat07_create_campaign(
    payload: CampaignCreate,
    session: Session = Depends(get_db),
    user: User = Depends(require_campaign_editor),
):
    try:
        return campaign_service.create_campaign(session, user=user, payload=payload)
    except CampaignTitleAlreadyExistsError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc


# ============================================================
# CAT-08 — PUT /campaigns/{id} (Resp, Admin, Bénéficiaire)
# ============================================================
@router.put("/{id_campaign}", response_model=CampaignOut)
def cat08_update_campaign(
    id_campaign: UUID,
    payload: CampaignUpdate,
    session: Session = Depends(get_db),
    user: User = Depends(require_campaign_editor),
):
    try:
        return campaign_service.update_campaign(
            session, user=user, id_campaign=id_campaign, payload=payload
        )
    except CampaignNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    except CampaignTitleAlreadyExistsError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc


# ============================================================
# CAT-09 — PATCH /campaigns/{id}/publication
# ============================================================
@router.patch("/{id_campaign}/publication", response_model=CampaignOut)
def cat09_publish_campaign(
    id_campaign: UUID,
    payload: PublicationIn,
    session: Session = Depends(get_db),
    user: User = Depends(require_campaign_editor),
):
    try:
        return campaign_service.set_campaign_publication(
            session, user=user, id_campaign=id_campaign, payload=payload
        )
    except CampaignNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    except CannotPublishClosedCampaignError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc


# ============================================================
# CAT-10 — DELETE /campaigns/{id} (Resp, Admin, Bénéficiaire)
# ============================================================
@router.delete("/{id_campaign}", status_code=status.HTTP_204_NO_CONTENT)
def cat10_delete_campaign(
    id_campaign: UUID,
    session: Session = Depends(get_db),
    user: User = Depends(require_campaign_editor),
):
    try:
        campaign_service.delete_campaign(session, user=user, id_campaign=id_campaign)
    except CampaignNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc