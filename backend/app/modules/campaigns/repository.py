"""AccÃ¨s aux donnÃ©es du module campaigns."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.campaigns.models import Campaign, Event


# ============================================================
# LECTURE
# ============================================================
def get_campaign_by_id(session: Session, id_campaign: UUID) -> Campaign | None:
    return session.get(Campaign, id_campaign)


def get_campaign_by_title(session: Session, title: str) -> Campaign | None:
    return session.scalar(select(Campaign).where(func.lower(Campaign.title) == title.lower()))


def get_published_campaign_by_id(session: Session, id_campaign: UUID) -> Campaign | None:
    return session.scalar(
        select(Campaign).where(Campaign.id_campaign == id_campaign, Campaign.status != "Draft")
    )


def list_active_campaigns(session: Session, *, limit: int = 50, offset: int = 0) -> list[Campaign]:
    """CAT-01 : Campagnes en cours."""
    stmt = (
        select(Campaign)
        .where(Campaign.status == "In_progress")
        .order_by(Campaign.start_at.asc().nulls_last(), Campaign.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(session.scalars(stmt).all())


def list_closed_campaigns(session: Session, *, limit: int = 50, offset: int = 0) -> list[Campaign]:
    """CAM-07 : Campagnes clÃ´turÃ©es."""
    stmt = (
        select(Campaign)
        .where(Campaign.status == "closed")
        .order_by(Campaign.closed_at.desc().nulls_last())
        .limit(limit)
        .offset(offset)
    )
    return list(session.scalars(stmt).all())


def list_filtered_campaigns(
    session: Session,
    *,
    status: str | None = None,
    start_at: datetime | None = None,
    finish_at: datetime | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[Campaign]:
    """CAM-09 : Toutes les campagnes (avec filtres)."""
    stmt = select(Campaign)

    if status:
        stmt = stmt.where(Campaign.status == status)
    if start_at:
        stmt = stmt.where(Campaign.start_at >= start_at)
    if finish_at:
        stmt = stmt.where(Campaign.finish_at <= finish_at)

    stmt = stmt.order_by(Campaign.created_at.desc()).limit(limit).offset(offset)
    return list(session.scalars(stmt).all())


def list_user_drafts(session: Session, id_user: UUID) -> list[Campaign]:
    """CAM-08 : Brouillons d'un utilisateur spÃ©cifique."""
    return list(
        session.scalars(
            select(Campaign)
            .where(Campaign.id_user == id_user, Campaign.status == "Draft")
            .order_by(Campaign.created_at.desc())
        ).all()
    )


def list_user_invisible_campaigns(session: Session, id_user: UUID) -> list[Campaign]:
    """CAM-10 : Campagnes dÃ©sactivÃ©es (invisibles) d'un utilisateur spÃ©cifique."""
    # Dans notre logique, une campagne dÃ©sactivÃ©e (CAT-09) repasse en "Draft"
    return list(
        session.scalars(
            select(Campaign)
            .where(Campaign.id_user == id_user, Campaign.status == "Draft")
            .order_by(Campaign.created_at.desc())
        ).all()
    )


# ============================================================
# Ã‰CRITURE
# ============================================================
def add_campaign(session: Session, campaign: Campaign) -> None:
    session.add(campaign)
    session.flush()


def update_campaign(session: Session, campaign: Campaign, data: dict) -> Campaign:
    for field, value in data.items():
        setattr(campaign, field, value)
    session.flush()
    return campaign


def publish_campaign(session: Session, campaign: Campaign) -> Campaign:
    """Passe le statut Ã  In_progress."""
    campaign.status = "In_progress"
    session.flush()
    return campaign


def deactivate_campaign(session: Session, campaign: Campaign) -> Campaign:
    """Repasse une campagne en brouillon (invisible)."""
    campaign.status = "Invisible"
    session.flush()
    return campaign


def close_campaign(session: Session, campaign: Campaign, reason: str | None = None) -> Campaign:
    """Passe le statut Ã  closed."""
    campaign.status = "closed"
    if reason:
        campaign.closure_reason = reason
    session.flush()
    return campaign


def delete_campaign(session: Session, campaign: Campaign) -> None:
    session.delete(campaign)
    session.flush()


# ============================================================
# Ã‰VÃ‰NEMENTS
# ============================================================


def add_event(session: Session, event: Event) -> None:
    session.add(event)
    session.flush()


def get_event_by_id(session: Session, id_event: UUID) -> Event | None:
    return session.get(Event, id_event)


def list_events(
    session: Session,
    *,
    event_at: datetime | None = None,
    id_campaign: UUID | None = None,
) -> list[Event]:
    stmt = select(Event)

    if event_at is not None:
        stmt = stmt.where(Event.event_at == event_at)

    if id_campaign is not None:
        stmt = stmt.where(Event.id_campaign == id_campaign)

    stmt = stmt.order_by(Event.event_at.asc().nulls_last())

    return list(session.scalars(stmt).all())


def update_event(session: Session, event: Event, data: dict) -> Event:
    for field, value in data.items():
        setattr(event, field, value)

    session.flush()
    return event


def delete_event(session: Session, event: Event) -> None:
    session.delete(event)
    session.flush()


def list_upcoming_events(session: Session) -> list[Event]:
    """CAT-03 : Ã‰vÃ©nements de collecte Ã  venir."""
    stmt = select(Event).where(Event.event_at >= func.now()).order_by(Event.event_at.asc())

    return list(session.scalars(stmt).all())
