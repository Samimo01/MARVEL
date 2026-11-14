"""Logique métier du module campaigns."""

from decimal import Decimal
from uuid import UUID
from sqlalchemy.orm import Session

from app.modules.auth.models import User
# Correction des imports ci-dessous
from app.modules.campaigns import repository as campaign_repo
from app.modules.campaigns.models import Campaign
from app.modules.campaigns.schemas import (
    CampaignCreate, CampaignOut, CampaignProgressOut, CampaignUpdate, PublicationIn,
)

class CampaignNotFoundError(Exception): pass
class CampaignTitleAlreadyExistsError(Exception): pass
class CannotPublishClosedCampaignError(Exception): pass

def _progress_percent(collected: Decimal, goal: Decimal | None) -> float:
    if not goal or goal <= 0: return 0.0
    return round(min(float(collected / goal * 100), 100.0), 2)

def _to_progress_out(campaign: Campaign, collected: Decimal) -> CampaignProgressOut:
    return CampaignProgressOut(
        id_campaign=campaign.id_campaign, title=campaign.title,
        description=campaign.description, goal=campaign.goal,
        collected_amount=collected, start_at=campaign.start_at,
        finish_at=campaign.finish_at, categories=campaign.categories,
        image_url=campaign.image_url, status=campaign.status,
        progress_percent=_progress_percent(collected, campaign.goal),
    )

def _get_or_raise(session: Session, id_campaign: UUID) -> Campaign:
    campaign = campaign_repo.get_campaign_by_id(session, id_campaign)
    if campaign is None:
        raise CampaignNotFoundError(f"Campagne {id_campaign} introuvable")
    return campaign

#def list_active_campaigns(session: Session, *, limit: int = 50, offset: int = 0) -> list[CampaignProgressOut]:
 #   campaigns = campaign_repo.list_active_campaigns(session, limit=limit, offset=offset)
#    if not campaigns: return []
 #   ids = [c.id_campaign for c in campaigns]
  #  amounts = campaign_repo.get_campaigns_amounts_collected(session, ids)
   # return [_to_progress_out(c, amounts.get(c.id_campaign, Decimal(0))) for c in campaigns]
def list_active_campaigns(session: Session, *, limit: int = 50, offset: int = 0) -> list[CampaignProgressOut]:

    campaigns = campaign_repo.list_active_campaigns(session, limit=limit, offset=offset)
    if not campaigns:
        return []
    
    return [_to_progress_out(c, Decimal(0)) for c in campaigns]
#def get_public_campaign(session: Session, id_campaign: UUID) -> CampaignProgressOut:
 #   campaign = campaign_repo.get_published_campaign_by_id(session, id_campaign)
  #  if campaign is None:
   #     raise CampaignNotFoundError(f"Campagne {id_campaign} introuvable")
    #collected = campaign_repo.get_campaign_amount_collected(session, id_campaign)
    #return _to_progress_out(campaign, collected)
def get_public_campaign(session: Session, id_campaign: UUID) -> CampaignProgressOut:
    campaign = campaign_repo.get_published_campaign_by_id(session, id_campaign)
    if campaign is None:
        raise CampaignNotFoundError(f"Campagne {id_campaign} introuvable")
    
    # On ne calcule plus le montant, on force à 0
    return _to_progress_out(campaign, Decimal(0))


def create_campaign(session: Session, *, user: User, payload: CampaignCreate) -> CampaignOut:
    if campaign_repo.get_campaign_by_title(session, payload.title) is not None:
        raise CampaignTitleAlreadyExistsError(f"Campagne '{payload.title}' déjà existante")
    campaign = Campaign(**payload.model_dump(), id_user=user.id_user)
    campaign_repo.add_campaign(session, campaign)
    session.commit()
    session.refresh(campaign)
    return CampaignOut.model_validate(campaign)

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

def set_campaign_publication(session: Session, *, user: User, id_campaign: UUID, payload: PublicationIn) -> CampaignOut:
    campaign = _get_or_raise(session, id_campaign)
    if payload.est_publier:
        if campaign.status == "closed":
            raise CannotPublishClosedCampaignError(f"Impossible de publier une campagne clôturée ({id_campaign})")
        campaign_repo.publish_campaign(session, campaign)
    else:
        campaign_repo.unpublish_campaign(session, campaign)
    session.commit()
    session.refresh(campaign)
    return CampaignOut.model_validate(campaign)

def delete_campaign(session: Session, *, user: User, id_campaign: UUID) -> None:
    campaign = _get_or_raise(session, id_campaign)
    campaign_repo.delete_campaign(session, campaign)
    session.commit()