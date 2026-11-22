"""Accès aux données du module financial_donations."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import Numeric, cast, func, select
from sqlalchemy.orm import Session

from app.modules.financial_donations.models import FinancialDon


def get_donation_by_id(session: Session, id_don_f: UUID) -> FinancialDon | None:
    return session.get(FinancialDon, id_don_f)


def list_user_donations(session: Session, id_user: UUID) -> list[FinancialDon]:
    """DON-04 : Historique des dons d'un utilisateur."""
    return list(
        session.scalars(
            select(FinancialDon)
            .where(FinancialDon.id_user == id_user)
            .order_by(FinancialDon.created_at.desc())
        ).all()
    )


def list_all_donations(
    session: Session,
    *,
    status: str | None = None,
    id_campaign: UUID | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[FinancialDon]:
    """DON-07 : Liste globale avec filtres."""
    stmt = select(FinancialDon)

    if status:
        stmt = stmt.where(FinancialDon.status == status)
    if id_campaign:
        stmt = stmt.where(FinancialDon.id_campaign == id_campaign)
    if start_date:
        stmt = stmt.where(FinancialDon.created_at >= start_date)
    if end_date:
        stmt = stmt.where(FinancialDon.created_at <= end_date)

    stmt = stmt.order_by(FinancialDon.created_at.desc()).limit(limit).offset(offset)
    return list(session.scalars(stmt).all())


def list_successful_donations(session: Session) -> list[FinancialDon]:
    """DON-08 : Tous les dons réussis."""
    return list(
        session.scalars(
            select(FinancialDon)
            .where(FinancialDon.status == "Success")
            .order_by(FinancialDon.created_at.desc())
        ).all()
    )


def list_successful_donations_by_campaign(
    session: Session, id_campaign: UUID
) -> list[FinancialDon]:
    """DON-09 : Tous les dons réussis d'une campagne."""
    return list(
        session.scalars(
            select(FinancialDon)
            .where(
                FinancialDon.id_campaign == id_campaign,
                FinancialDon.status == "Success",
            )
            .order_by(FinancialDon.created_at.desc())
        ).all()
    )


def add_donation(session: Session, donation: FinancialDon) -> None:
    session.add(donation)
    session.flush()


def update_donation(
    session: Session, donation: FinancialDon, data: dict
) -> FinancialDon:
    for field, value in data.items():
        setattr(donation, field, value)
    session.flush()
    return donation


def get_campaign_amount_collected(
    session: Session, id_campaign: UUID
) -> Decimal:
    """Calcule la somme des dons réussis pour UNE campagne."""
    total = session.scalar(
        select(
            cast(
                func.coalesce(func.sum(FinancialDon.amount), 0),
                Numeric(15, 2),
            )
        ).where(
            FinancialDon.id_campaign == id_campaign,
            FinancialDon.status == "Success",
        )
    )
    return Decimal(total or 0).quantize(Decimal("0.01"))


def get_campaigns_amounts_collected(
    session: Session, ids: list[UUID]
) -> dict[UUID, Decimal]:
    """Calcule la somme des dons réussis pour PLUSIEURS campagnes (Batch)."""
    if not ids:
        return {}
    rows = session.execute(
        select(
            FinancialDon.id_campaign,
            cast(
                func.coalesce(func.sum(FinancialDon.amount), 0),
                Numeric(15, 2),
            ),
        )
        .where(
            FinancialDon.id_campaign.in_(ids),
            FinancialDon.status == "Success",
        )
        .group_by(FinancialDon.id_campaign)
    ).all()
    return {
        row[0]: Decimal(row[1] or 0).quantize(Decimal("0.01"))
        for row in rows
    }


def list_donations_by_campaign(
    session: Session, id_campaign: UUID
) -> list[FinancialDon]:
    """Récupère la liste de TOUS les dons d'une campagne."""
    return list(
        session.scalars(
            select(FinancialDon)
            .where(FinancialDon.id_campaign == id_campaign)
            .order_by(FinancialDon.created_at.desc())
        ).all()
    )