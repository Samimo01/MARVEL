"""Logique métier du module campaigns."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from app.modules.auth.models import User
from app.modules.campaigns import repository as campaign_repo
from app.modules.campaigns.models import Campaign
from app.modules.campaigns.schemas import (
    CampaignCreate, 
    CampaignOut, 
    CampaignProgressOut, 
    CampaignUpdate,
    GaugeOut
)
from app.modules.financial_donations import service as don_service
from app.modules.financial_donations.schemas import FinancialDonOut


# ============================================================
# Exceptions
# ============================================================
class CampaignNotFoundError(Exception): pass
class CampaignTitleAlreadyExistsError(Exception): pass
class InvalidStatusTransitionError(Exception): pass


# ============================================================
# Helpers
# ============================================================
def _progress_percent(collected: Decimal, goal: Decimal | None) -> float:
    if not goal or goal <= 0: 
        return 0.0
    return round(min(float(collected / goal * 100), 100.0), 2)

def _to_progress_out(campaign: Campaign, collected: Decimal) -> CampaignProgressOut:
    return CampaignProgressOut(
        id_campaign=campaign.id_campaign, 
        title=campaign.title,
        description=campaign.description, 
        goal=campaign.goal,
        collected_amount=collected, 
        start_at=campaign.start_at,
        finish_at=campaign.finish_at, 
        categories=campaign.categories,
        image_url=campaign.image_url, 
        status=campaign.status,
        progress_percent=_progress_percent(collected, campaign.goal),
    )

def _get_or_raise(session: Session, id_campaign: UUID) -> Campaign:
    campaign = campaign_repo.get_campaign_by_id(session, id_campaign)
    if campaign is None:
        raise CampaignNotFoundError(f"Campagne {id_campaign} introuvable")
    return campaign


# ============================================================
# LECTURE PUBLIQUE (CAT-01, CAT-02, CAM-05, CAM-07)
# ============================================================
def list_active_campaigns(session: Session, *, limit: int = 50, offset: int = 0) -> list[CampaignProgressOut]:
    campaigns = campaign_repo.list_active_campaigns(session, limit=limit, offset=offset)
    if not campaigns: 
        return []
    
    ids = [c.id_campaign for c in campaigns]
    amounts = don_service.get_campaigns_amounts_collected(session, ids)
    
    return [_to_progress_out(c, amounts.get(c.id_campaign, Decimal("0.00"))) for c in campaigns]

def get_public_campaign(session: Session, id_campaign: UUID) -> CampaignProgressOut:
    campaign = campaign_repo.get_published_campaign_by_id(session, id_campaign)
    if campaign is None:
        raise CampaignNotFoundError(f"Campagne {id_campaign} introuvable")
    
    collected = don_service.get_campaign_amount_collected(session, id_campaign)
    return _to_progress_out(campaign, collected)

def list_closed_campaigns(session: Session, *, limit: int = 50, offset: int = 0) -> list[CampaignProgressOut]:
    """CAM-07 : Liste des campagnes fermées."""
    campaigns = campaign_repo.list_closed_campaigns(session, limit=limit, offset=offset)
    if not campaigns: 
        return []
    
    ids = [c.id_campaign for c in campaigns]
    amounts = don_service.get_campaigns_amounts_collected(session, ids)
    
    return [_to_progress_out(c, amounts.get(c.id_campaign, Decimal("0.00"))) for c in campaigns]

def get_gauge(session: Session, id_campaign: UUID) -> GaugeOut:
    """CAM-05 : Jauge de progression."""
    campaign = _get_or_raise(session, id_campaign)
    collected = don_service.get_campaign_amount_collected(session, id_campaign)
    
    return GaugeOut(
        id_campaign=campaign.id_campaign,
        goal=campaign.goal,
        collected=collected,
        percentage=_progress_percent(collected, campaign.goal)
    )


# ============================================================
# GESTION (CAT-07, CAT-08, CAT-09, CAT-10)
# ============================================================
def create_campaign(session: Session, *, user: User, payload: CampaignCreate) -> CampaignOut:
    if campaign_repo.get_campaign_by_title(session, payload.title) is not None:
        raise CampaignTitleAlreadyExistsError(f"Campagne '{payload.title}' déjà existante")
    
    campaign = Campaign(**payload.model_dump(), id_user=user.id_user, status="Draft")
    campaign_repo.add_campaign(session, campaign)
    session.commit()
    session.refresh(campaign)
    return CampaignOut.model_validate(campaign)

def create_draft_campaign(session: Session, *, user: User, payload: CampaignCreate) -> CampaignOut:
    """CAM-11 : Créer une campagne en mode brouillon."""
    return create_campaign(session, user=user, payload=payload)

def update_campaign(session: Session, *, user: User, id_campaign: UUID, payload: CampaignUpdate) -> CampaignOut:
    campaign = _get_or_raise(session, id_campaign)
    data = payload.model_dump(exclude_unset=True)
    
    new_title = data.get("title")
    if new_title is not None and new_title != campaign.title:
        existing = campaign_repo.get_campaign_by_title(session, new_title)
        if existing is not None and existing.id_campaign != campaign.id_campaign:
            raise CampaignTitleAlreadyExistsError(f"Campagne '{new_title}' déjà existante")
    
    campaign_repo.update_campaign(session, campaign, data)
    session.commit()
    session.refresh(campaign)
    return CampaignOut.model_validate(campaign)

def deactivate_campaign(session: Session, *, user: User, id_campaign: UUID) -> CampaignOut:
    """CAT-09 : Repasser en brouillon (invisible)."""
    campaign = _get_or_raise(session, id_campaign)
    campaign_repo.deactivate_campaign(session, campaign)
    session.commit()
    session.refresh(campaign)
    return CampaignOut.model_validate(campaign)

def delete_campaign(session: Session, *, user: User, id_campaign: UUID) -> None:
    campaign = _get_or_raise(session, id_campaign)
    campaign_repo.delete_campaign(session, campaign)
    session.commit()


# ============================================================
# WORKFLOW (CAM-03, CAM-04, CAM-06, CAM-08, CAM-09, CAM-10)
# ============================================================
def publish_campaign_action(session: Session, *, user: User, id_campaign: UUID) -> CampaignOut:
    """CAM-03 : Brouillon vers En_Cours."""
    campaign = _get_or_raise(session, id_campaign)
    if campaign.status != "Draft":
        raise InvalidStatusTransitionError("Seule une campagne en brouillon peut être publiée.")
    
    campaign_repo.publish_campaign(session, campaign)
    session.commit()
    session.refresh(campaign)
    return CampaignOut.model_validate(campaign)

def close_campaign_action(session: Session, *, user: User, id_campaign: UUID, reason: str | None = None) -> CampaignOut:
    """CAM-04 : Clôturer la campagne."""
    campaign = _get_or_raise(session, id_campaign)
    if campaign.status == "closed":
        raise InvalidStatusTransitionError("La campagne est déjà clôturée.")
    
    campaign_repo.close_campaign(session, campaign, reason)
    session.commit()
    session.refresh(campaign)
    return CampaignOut.model_validate(campaign)

def get_campaign_donations(session: Session, id_campaign: UUID) -> list[FinancialDonOut]:
    """CAM-06 : Dons rattachés à la campagne."""
    _get_or_raise(session, id_campaign)
    return don_service.list_campaign_donations(session, id_campaign)

def list_user_drafts(session: Session, id_user: UUID) -> list[CampaignOut]:
    """CAM-08 : Brouillons d'un utilisateur spécifique."""
    drafts = campaign_repo.list_user_drafts(session, id_user)
    return [CampaignOut.model_validate(c) for c in drafts]

def list_user_invisible_campaigns(session: Session, id_user: UUID) -> list[CampaignOut]:
    """CAM-10 : Toutes les campagnes désactivées d'un utilisateur."""
    campaigns = campaign_repo.list_user_invisible_campaigns(session, id_user)
    return [CampaignOut.model_validate(c) for c in campaigns]

def list_all_campaigns(
    session: Session, 
    *, 
    status: str | None = None, 
    start_at: datetime | None = None, 
    finish_at: datetime | None = None, 
    limit: int = 50, 
    offset: int = 0
) -> list[CampaignOut]:
    """CAM-09 : Toutes les campagnes (Admin)."""
    campaigns = campaign_repo.list_filtered_campaigns(
        session, status=status, start_at=start_at, finish_at=finish_at, limit=limit, offset=offset
    )
    return [CampaignOut.model_validate(c) for c in campaigns]