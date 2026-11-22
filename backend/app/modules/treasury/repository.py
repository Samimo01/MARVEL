
"""Accès aux données du module treasury."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import Numeric, cast, func, or_, select
from sqlalchemy.orm import Session

from app.modules.auth.models import Role, RoleAssignment
from app.modules.campaigns.models import Campaign, Event
from app.modules.financial_donations.models import FinancialDon
from app.modules.treasury.models import Fund


# ============================================================
# HELPERS
# ============================================================

def _decimal(value) -> Decimal:
    """Garantit un montant Decimal avec deux décimales."""
    return Decimal(value or 0).quantize(Decimal("0.01"))


def _sum_amount(session: Session, statement) -> Decimal:
    """Exécute une somme SQL et retourne un Decimal."""
    total = session.scalar(statement)
    return _decimal(total)


# ============================================================
# LECTURE DES OPÉRATIONS
# ============================================================

def get_fund_by_id(session: Session, id_fund: UUID) -> Fund | None:
    """TRE-02 : Récupère une opération financière par son identifiant."""
    return session.get(Fund, id_fund)


def list_all_funds(session: Session) -> list[Fund]:
    """TRE-01 : Récupère toutes les opérations financières."""
    
    statement = (
        select(Fund)
        .order_by(Fund.transaction_at.desc())
    )

    return list(session.scalars(statement).all())


def list_expenses_by_event(
    session: Session,
    id_event: UUID,
    *,
    category: str | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[Fund]:
    """TRE-04 : Liste les dépenses d'un événement."""

    stmt = select(Fund).where(
        Fund.id_event == id_event,
        Fund.amount < 0,
    )

    if category:
        stmt = stmt.where(Fund.category == category)

    if start_date:
        stmt = stmt.where(Fund.transaction_at >= start_date)

    if end_date:
        stmt = stmt.where(Fund.transaction_at <= end_date)

    stmt = (
        stmt.order_by(Fund.transaction_at.desc())
        .limit(limit)
        .offset(offset)
    )

    return list(session.scalars(stmt).all())


# ============================================================
# ÉCRITURE DES OPÉRATIONS
# ============================================================

def add_fund(session: Session, fund: Fund) -> None:
    """Ajoute une opération financière."""
    session.add(fund)
    session.flush()


def update_fund(session: Session, fund: Fund, data: dict) -> Fund:
    """Modifie une opération financière."""
    for field, value in data.items():
        setattr(fund, field, value)

    session.flush()
    return fund


# ============================================================
# AGRÉGATS GLOBAUX
# ============================================================

def get_global_donations_total(session: Session) -> Decimal:
    """Calcule le montant total des dons financiers réussis."""

    return _sum_amount(
        session,
        select(
            cast(
                func.coalesce(func.sum(FinancialDon.amount), 0),
                Numeric(15, 2),
            )
        ).where(FinancialDon.status == "Success"),
    )


def get_global_fund_totals(session: Session) -> dict[str, Decimal]:
    """Calcule les revenus et les dépenses enregistrés dans la caisse."""

    income = _sum_amount(
        session,
        select(
            cast(
                func.coalesce(func.sum(Fund.amount), 0),
                Numeric(15, 2),
            )
        ).where(Fund.amount > 0),
    )

    expenses = _sum_amount(
        session,
        select(
            cast(
                func.coalesce(func.sum(-Fund.amount), 0),
                Numeric(15, 2),
            )
        ).where(Fund.amount < 0),
    )

    return {
        "total_income": income,
        "total_expenses": expenses,
    }


# ============================================================
# AGRÉGATS PAR CAMPAGNE
# ============================================================

def get_campaign_donations_total(
    session: Session,
    id_campaign: UUID,
) -> Decimal:
    """TRE-11 : Calcule le total des dons financiers réussis d'une campagne."""

    return _sum_amount(
        session,
        select(
            cast(
                func.coalesce(func.sum(FinancialDon.amount), 0),
                Numeric(15, 2),
            )
        ).where(
            FinancialDon.id_campaign == id_campaign,
            FinancialDon.status == "Success",
        ),
    )


def get_campaign_fund_totals(
    session: Session,
    id_campaign: UUID,
) -> dict[str, Decimal]:
    """Calcule les revenus et les dépenses des événements d'une campagne."""

    income = _sum_amount(
        session,
        select(
            cast(func.coalesce(func.sum(Fund.amount), 0), Numeric(15, 2))
        )
        .join(Event, Event.id_event == Fund.id_event)
        .where(
            Event.id_campaign == id_campaign,
            Fund.amount > 0,
        ),
    )

    expenses = _sum_amount(
        session,
        select(
            cast(func.coalesce(func.sum(-Fund.amount), 0), Numeric(15, 2))
        )
        .join(Event, Event.id_event == Fund.id_event)
        .where(
            Event.id_campaign == id_campaign,
            Fund.amount < 0,
        ),
    )

    return {
        "total_fund_income": income,
        "total_expenses": expenses,
    }


# ============================================================
# AGRÉGATS PAR ÉVÉNEMENT
# ============================================================

def get_event_fund_totals(
    session: Session,
    id_event: UUID,
) -> dict[str, Decimal]:
    """Calcule les revenus et les dépenses d'un événement."""

    income = _sum_amount(
        session,
        select(
            cast(func.coalesce(func.sum(Fund.amount), 0), Numeric(15, 2))
        ).where(
            Fund.id_event == id_event,
            Fund.amount > 0,
        ),
    )

    expenses = _sum_amount(
        session,
        select(
            cast(func.coalesce(func.sum(-Fund.amount), 0), Numeric(15, 2))
        ).where(
            Fund.id_event == id_event,
            Fund.amount < 0,
        ),
    )

    return {
        "total_income": income,
        "total_expenses": expenses,
    }


# ============================================================
# VÉRIFICATION DES ENTITÉS
# ============================================================

def get_event_by_id(session: Session, id_event: UUID) -> Event | None:
    return session.get(Event, id_event)


def get_campaign_by_id(
    session: Session,
    id_campaign: UUID,
) -> Campaign | None:
    return session.get(Campaign, id_campaign)


def get_campaign_events_fund_totals(
    session: Session,
    id_campaign: UUID,
) -> dict[str, Decimal]:
    """Calcule les revenus et les dépenses cumulés des événements d'une campagne."""

    income = _sum_amount(
        session,
        select(
            cast(func.coalesce(func.sum(Fund.amount), 0), Numeric(15, 2))
        )
        .join(Event, Event.id_event == Fund.id_event)
        .where(
            Event.id_campaign == id_campaign,
            Fund.amount > 0,
        ),
    )

    expenses = _sum_amount(
        session,
        select(
            cast(func.coalesce(func.sum(-Fund.amount), 0), Numeric(15, 2))
        )
        .join(Event, Event.id_event == Fund.id_event)
        .where(
            Event.id_campaign == id_campaign,
            Fund.amount < 0,
        ),
    )

    return {
        "total_income": income,
        "total_expenses": expenses,
    }


def list_system_campaigns(session: Session) -> list[Campaign]:
    """TRE-09 : Liste les campagnes dont le créateur n'est pas bénéficiaire."""

    latest_beneficiary_assignment = (
        select(RoleAssignment.assignment_type)
        .join(Role, Role.id_role == RoleAssignment.id_role)
        .where(
            RoleAssignment.id_user == Campaign.id_user,
            Role.role_name == "Beneficiary",
        )
        .order_by(
            RoleAssignment.created_at.desc(),
            RoleAssignment.id_role_assignment.desc(),
        )
        .limit(1)
        .correlate(Campaign)
        .scalar_subquery()
    )

    statement = select(Campaign).where(
        latest_beneficiary_assignment.is_distinct_from("assigned")
    )

    return list(session.scalars(statement).all())

def list_all_expenses(session: Session) -> list[Fund]:
    """Récupère toutes les dépenses pour l'export de la trésorerie."""
    statement = (
        select(Fund)
        .where(Fund.amount < 0)
        .order_by(Fund.transaction_at.desc())
    )
    return list(session.scalars(statement).all())


def list_successful_donations(session: Session) -> list[FinancialDon]:
    """Récupère les dons financiers réussis pour l'export de la trésorerie."""
    statement = (
        select(FinancialDon)
        .where(FinancialDon.status == "Success")
        .order_by(FinancialDon.created_at.desc())
    )
    return list(session.scalars(statement).all())