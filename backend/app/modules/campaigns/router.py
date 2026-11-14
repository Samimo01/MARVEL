"""Endpoints HTTP du module campaigns."""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import require_campaign_editor

# Corrections des imports
from app.database import get_db
from app.modules.auth.models import User
from app.modules.campaigns import repository as campaign_repo
from app.modules.campaigns import service as campaign_service
from app.modules.campaigns.schemas import (
    CampaignCreate,
    CampaignOut,
    CampaignProgressOut,
    CampaignUpdate,
    GaugeOut,
    PublicationIn,
    # FinancialDonOut,
)
from app.modules.campaigns.service import (
    CampaignNotFoundError,
    CampaignTitleAlreadyExistsError,
    CannotPublishClosedCampaignError,
)

# ============================================================
# Deux routers : gestion (auth) + catalogue public
# ============================================================
router = APIRouter(prefix="/campaigns", tags=["campaigns"])
campaign_catalog_router = APIRouter(prefix="/catalogue/campaigns", tags=["campaign catalog"])


# ============================================================
# CAT-01 — GET /catalogue/campaigns (Public)
# ============================================================
@campaign_catalog_router.get("", response_model=list[CampaignProgressOut])
def cat01_list_active_campaigns(
    session: Session = Depends(get_db), 
    limit: int = 50,
    offset: int = 0,
):
    return campaign_service.list_active_campaigns(session, limit=limit, offset=offset)


# ============================================================
# CAT-02 — GET /catalogue/campaigns/{id} (Public)
# ============================================================
@campaign_catalog_router.get("/{id_campaign}", response_model=CampaignProgressOut)
def cat02_campaign_detail(
    id_campaign: UUID,
    session: Session = Depends(get_db),
):
    try:
        return campaign_service.get_public_campaign(session, id_campaign)
    except CampaignNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc


# ============================================================
# CAT-07 — POST /campaigns (Gestionnaire de collecte, Administrateur)
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
# CAT-08 — PUT /campaigns/{id} (Gestionnaire de collecte, Administrateur)
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
# CAT-10 — DELETE /campaigns/{id} (Gestionnaire de collecte, Administrateur)
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

# ... (vos imports existants)

# ============================================================
# CAM-01 à CAM-06
# ============================================================

# CAM-01 : Liste paginée
@router.get("", response_model=list[CampaignOut])
def cam01_list_campaigns(
    status: str | None = None,
    start_at: datetime | None = None,
    finish_at: datetime | None = None,
    limit: int = 50,
    offset: int = 0,
    session: Session = Depends(get_db),
    user: User = Depends(require_campaign_editor)
):
    return campaign_service.list_campaigns_filtered(
        session, status=status, start_at=start_at, finish_at=finish_at, limit=limit, offset=offset
    )

# CAM-02 : Détail d'une campagne
@router.get("/{id_campaign}", response_model=CampaignOut)
def cam02_get_campaign(
    id_campaign: UUID, 
    session: Session = Depends(get_db),
    user: User = Depends(require_campaign_editor)
):
    try:
        campaign = campaign_repo.get_campaign_by_id(session, id_campaign)
        if not campaign:
            raise CampaignNotFoundError()
        return CampaignOut.model_validate(campaign)
    except CampaignNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc

# CAM-03 : Publish a draft campaign
@router.post("/{id_campaign}/publish", response_model=CampaignOut)
def cam03_publish(
    id_campaign: UUID, 
    session: Session = Depends(get_db),
    user: User = Depends(require_campaign_editor)
):
    try:
        return campaign_service.publish_campaign_action(session, user=user, id_campaign=id_campaign)
    except Exception as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc

# CAM-04 : Close a campaign
@router.post("/{id_campaign}/close", response_model=CampaignOut)
def cam04_close(
    id_campaign: UUID,
    reason: str | None = None,
    session: Session = Depends(get_db),
    user: User = Depends(require_campaign_editor)
):
    try:
        return campaign_service.close_campaign_action(
            session, user=user, id_campaign=id_campaign, reason=reason
        )
    except Exception as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc

# CAM-05 : Public campaign gauge
@router.get("/{id_campaign}/gauge", response_model=GaugeOut)
def cam05_gauge(
    id_campaign: UUID, 
    session: Session = Depends(get_db)
):
    try:
        return campaign_service.get_gauge(session, id_campaign)
    except CampaignNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc

#@router.get("/{id_campaign}/donations", response_model=list[FinancialDonOut])
#def cam06_donations(
 #   id_campaign: UUID,
  #  session: Session = Depends(get_db),
   # user: User = Depends(get_current_user)
#):
 #   try:
  #      return campaign_service.get_campaign_donations(session, id_campaign)
   # except CampaignNotFoundError as exc:
    #    raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc