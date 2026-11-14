"""Accès aux données du module campaigns. Pas de commit ici."""

from decimal import Decimal
from uuid import UUID
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from datetime import datetime
# Correction des imports
from app.modules.campaigns.models import Campaign
#from app.modules.donations.models import FinancialDon 

def get_campaign_by_id(session: Session, id_campaign: UUID) -> Campaign | None:
    return session.get(Campaign, id_campaign)

def get_campaign_by_title(session: Session, title: str) -> Campaign | None:
    return session.scalar(select(Campaign).where(func.lower(Campaign.title) == title.lower()))

def get_published_campaign_by_id(session: Session, id_campaign: UUID) -> Campaign | None:
    return session.scalar(select(Campaign).where(Campaign.id_campaign == id_campaign, Campaign.status != "Draft"))

def list_active_campaigns(session: Session, *, limit: int = 50, offset: int = 0) -> list[Campaign]:
    stmt = (
        select(Campaign).where(Campaign.status == "In_progress")
        .order_by(Campaign.start_at.asc().nulls_last(), Campaign.created_at.desc())
        .limit(limit).offset(offset)
    )
    return list(session.scalars(stmt).all())

def add_campaign(session: Session, campaign: Campaign) -> None:
    session.add(campaign)
    session.flush()

def update_campaign(session: Session, campaign: Campaign, data: dict) -> Campaign:
    for field, value in data.items():
        setattr(campaign, field, value)
    session.flush()
    return campaign

def publish_campaign(session: Session, campaign: Campaign) -> Campaign:
    if campaign.status != "closed":
        campaign.status = "In_progress"
        session.flush()
    return campaign

def unpublish_campaign(session: Session, campaign: Campaign) -> Campaign:
    if campaign.status == "In_progress":
        campaign.status = "Draft"
        session.flush()
    return campaign

def delete_campaign(session: Session, campaign: Campaign) -> None:
    session.delete(campaign)
    session.flush()

#def get_campaign_amount_collected(session: Session, id_campaign: UUID) -> Decimal:
 #   total = session.scalar(
  #      select(func.coalesce(func.sum(FinancialDon.amount), 0)).where(
   #         FinancialDon.id_campaign == id_campaign, FinancialDon.status == "Success"
    #    )
    #)
    #return Decimal(total or 0)

#def get_campaigns_amounts_collected(session: Session, ids: list[UUID]) -> dict[UUID, Decimal]:
 #   if not ids: return {}
  #  rows = session.execute(
   #     select(FinancialDon.id_campaign, func.coalesce(func.sum(FinancialDon.amount), 0))
    #    .where(FinancialDon.id_campaign.in_(ids), FinancialDon.status == "Success")
     #   .group_by(FinancialDon.id_campaign)
    #).all()
    #return {row[0]: Decimal(row[1]) for row in rows}

# ... (vos fonctions existantes)

def list_filtered_campaigns(
    session: Session, 
    *, 
    status: str | None = None, 
    start_at: datetime | None = None, 
    finish_at: datetime | None = None, 
    limit: int = 50, 
    offset: int = 0
) -> list[Campaign]:
    stmt = select(Campaign)
    
    if status:
        stmt = stmt.where(Campaign.status == status)
    if start_at:
        stmt = stmt.where(Campaign.start_at >= start_at)
    if finish_at:
        stmt = stmt.where(Campaign.finish_at <= finish_at)

    stmt = stmt.order_by(Campaign.created_at.desc()).limit(limit).offset(offset)
    return list(session.scalars(stmt).all())

def close_campaign(session: Session, campaign: Campaign, reason: str | None = None) -> Campaign:
    campaign.status = "closed"
    if reason:
        campaign.closure_reason = reason
    session.flush()
    return campaign

#def get_donations_by_campaign(session: Session, id_campaign: UUID) -> list[FinancialDon]:
    # Assurez-vous que l'import from app.modules.donations.models import FinancialDon est actif
 #   return list(session.scalars(
  #      select(FinancialDon).where(FinancialDon.id_campaign == id_campaign)
   # ).all())

#def get_campaign_amount_collected(session: Session, id_campaign: UUID) -> Decimal:
 #   total = session.scalar(
  #      select(func.coalesce(func.sum(FinancialDon.amount), 0)).where(
   #         FinancialDon.id_campaign == id_campaign, 
    #        FinancialDon.status == "Success"
     #   )
    #)
    #return Decimal(total orz 0)