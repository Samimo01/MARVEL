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
    CampaignCreate, CampaignOut, CampaignProgressOut, CampaignUpdate,
    GaugeOut#, FinancialDonOut
)
from app.modules.campaigns.service import (
    CampaignNotFoundError, CampaignTitleAlreadyExistsError, InvalidStatusTransitionError
)

# ============================================================
# Déclaration des routers
# ============================================================
# Routes publiques (catalog en français)
catalog_router = APIRouter(prefix="/catalog/campagnes", tags=["catalog"])

# Routes privées (Gestion en anglais)
router = APIRouter(prefix="/campaigns", tags=["Campaigns"])


# ============================================================
# ROUTES PUBLIQUES (CAT-01, CAT-02, CAM-07)
# ============================================================

@catalog_router.get("", response_model=list[CampaignProgressOut])
def cat01_list_active_campaigns(
    session: Session = Depends(get_db),
    limit: int = 50,
    offset: int = 0,
):
    """CAT-01 : Campagnes en cours avec jauge."""
    return campaign_service.list_active_campaigns(session, limit=limit, offset=offset)

@catalog_router.get("/closed", response_model=list[CampaignProgressOut])
def cam07_list_closed_campaigns(
    session: Session = Depends(get_db),
    limit: int = 50,
    offset: int = 0,
):
    """CAM-07 : Campagnes fermées avec jauge."""
    return campaign_service.list_closed_campaigns(session, limit=limit, offset=offset)

@catalog_router.get("/{id_campaign}", response_model=CampaignProgressOut)
def cat02_campaign_detail(
    id_campaign: UUID,
    session: Session = Depends(get_db),
):
    """CAT-02 : Détail d'une campagne publique."""
    try:
        return campaign_service.get_public_campaign(session, id_campaign)
    except CampaignNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc


# ============================================================
# ROUTES PRIVÉES DE CRÉATION ET LISTES SPÉCIFIQUES
# (Déclarées AVANT /{id_campaign} pour éviter les conflits)
# ============================================================

@router.post("/draft", response_model=CampaignOut, status_code=status.HTTP_201_CREATED)
def cam11_create_draft_campaign(
    payload: CampaignCreate,
    session: Session = Depends(get_db),
    user: User = Depends(require_campaign_editor), # Resp. collecte, Admin
):
    """CAM-11 : Créer une campagne en mode brouillon."""
    try:
        return campaign_service.create_draft_campaign(session, user=user, payload=payload)
    except CampaignTitleAlreadyExistsError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc

@router.get("/{id_user}/draft", response_model=list[CampaignOut])
def cam08_list_user_drafts(
    id_user: UUID,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user) # Authentifié
):
    """CAM-08 : Les brouillons d'une personne."""
    return campaign_service.list_user_drafts(session, id_user)

@router.get("/{id_user}/invisible", response_model=list[CampaignOut])
def cam10_list_user_invisible_campaigns(
    id_user: UUID,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user) # Admin, bénéficiaire, resp.
):
    """CAM-10 : Toutes les campagnes désactivées d'un utilisateur."""
    return campaign_service.list_user_invisible_campaigns(session, id_user)


# ============================================================
# ROUTES PRIVÉES DE GESTION GLOBALE
# ============================================================

@router.post("", response_model=CampaignOut, status_code=status.HTTP_201_CREATED)
def cat07_create_campaign(
    payload: CampaignCreate,
    session: Session = Depends(get_db),
    user: User = Depends(require_campaign_editor),
):
    """CAT-07 : Créer une campagne (directement publiée ou en brouillon selon la logique métier)."""
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
    user: User = Depends(get_current_user) # Admin
):
    """CAM-09 : Toutes les campagnes."""
    return campaign_service.list_all_campaigns(
        session, status=status, start_at=start_at, finish_at=finish_at, limit=limit, offset=offset
    )

@router.get("/{id_campaign}", response_model=CampaignOut)
def cam02_get_campaign_private(
    id_campaign: UUID, 
    session: Session = Depends(get_db),
    user: User = Depends(require_campaign_editor)
):
    """Détail privé d'une campagne."""
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
    """CAM-04 : Clôturer une campagne."""
    try:
        return campaign_service.close_campaign_action(
            session, user=user, id_campaign=id_campaign, reason=reason
        )
    except CampaignNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    except InvalidStatusTransitionError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc

#@router.get("/{id_campaign}/gauge", response_model=GaugeOut)
#def cam05_get_gauge(
 #   id_campaign: UUID,
  #  session: Session = Depends(get_db),
#):
 #   """CAM-05 : Jauge de progression (Public)."""
  #  try:
   #     return campaign_service.get_gauge(session, id_campaign)
    #except CampaignNotFoundError as exc:
     #   raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc

#@router.get("/{id_campaign}/donations", response_model=list[FinancialDonOut])
#def cam06_get_donations(
 #   id_campaign: UUID,
  #  session: Session = Depends(get_db),
   # user: User = Depends(get_current_user),
#):
 #   """CAM-06 : Dons rattachés à la campagne."""
  #  try:
   #     return campaign_service.get_campaign_donations(session, id_campaign)
    #except CampaignNotFoundError as exc:
     #   raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc