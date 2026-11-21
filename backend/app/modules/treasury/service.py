"""Logique métier du module treasury."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from app.modules.auth.models import User
from app.modules.campaigns import repository as campaign_repo
from app.modules.treasury import repository as treasury_repo
from app.modules.treasury.models import Fund
from app.modules.treasury.schemas import (
    BudgetSummaryOut,
    CampaignDonationsTotalOut,
    CampaignEventsGainsOut,
    CampaignGainsOut,
    EventGainsOut,
    ExpenseCreate,
    ExpenseOut,
    ExpenseUpdate,
    FundOut,
    SystemCampaignGainsOut,
)
from app.core.image_utils import convert_image_to_webp
from app.core.supabase_client import supabase_admin, TREASURY_BUCKET


# ============================================================
# Exceptions
# ============================================================

class FundNotFoundError(Exception):
    pass


class EventNotFoundError(Exception):
    pass


class CampaignNotFoundError(Exception):
    pass


class InvalidExpenseError(Exception):
    pass


# ============================================================
# Helpers
# ============================================================

def _get_fund_or_raise(session: Session, id_fund: UUID) -> Fund:
    """Récupère une opération financière ou déclenche une exception."""
    fund = treasury_repo.get_fund_by_id(session, id_fund)

    if fund is None:
        raise FundNotFoundError(f"Opération financière {id_fund} introuvable.")

    return fund


def _get_event_or_raise(session: Session, id_event: UUID):
    """Récupère un événement ou déclenche une exception."""
    event = treasury_repo.get_event_by_id(session, id_event)

    if event is None:
        raise EventNotFoundError(f"Événement {id_event} introuvable.")

    return event


def _get_campaign_or_raise(session: Session, id_campaign: UUID):
    """Récupère une campagne ou déclenche une exception."""
    campaign = treasury_repo.get_campaign_by_id(session, id_campaign)

    if campaign is None:
        raise CampaignNotFoundError(f"Campagne {id_campaign} introuvable.")

    return campaign


def _upload_expense_image(id_fund: UUID, image_bytes: bytes) -> str:
    """Convertit et téléverse le justificatif photographique."""

    try:
        webp_bytes = convert_image_to_webp(image_bytes)
        path = f"expenses/{id_fund}.webp"

        supabase_admin.storage.from_(TREASURY_BUCKET).upload(
            path=path,
            file=webp_bytes,
            file_options={
                "content-type": "image/webp",
                "upsert": "true",
            },
        )

        return supabase_admin.storage.from_(TREASURY_BUCKET).get_public_url(path)

    except Exception as exc:
        raise InvalidExpenseError(
            f"Échec du téléversement du justificatif : {exc}"
        ) from exc


def _commit_and_refresh(session: Session, fund: Fund) -> None:
    """Valide la transaction et actualise l'opération financière."""
    try:
        session.commit()
        session.refresh(fund)
    except Exception:
        session.rollback()
        raise


# ============================================================
# 	TRE-01 : Liste toutes les opérations financières.
# ============================================================

def list_funds(session: Session) -> list[FundOut]:
    """TRE-01 : Liste toutes les opérations financières."""

    funds = treasury_repo.list_all_funds(session)

    return [
        FundOut.model_validate(fund)
        for fund in funds
    ]

# ============================================================
# TRE-02 : Détail d'une opération financière
# ============================================================

def get_fund_detail(session: Session, id_fund: UUID) -> FundOut:
    """TRE-02 : Récupère le détail d'une opération financière."""
    
    fund = _get_fund_or_raise(session, id_fund)
    
    return FundOut.model_validate(fund)


# ============================================================
# TRE-03 : Enregistrer une dépense
# ============================================================

def create_expense(
    session: Session,
    *,
    user: User,
    id_event: UUID,
    payload: ExpenseCreate,
    image_bytes: bytes | None = None,
) -> ExpenseOut:
    """TRE-03 : Enregistre une dépense associée à un événement."""
    
    _get_event_or_raise(session, id_event)

    if payload.justificative and image_bytes:
        raise InvalidExpenseError(
            "Choisissez une justification textuelle ou photographique, pas les deux."
        )

    id_fund = uuid4()
    justificative = payload.justificative

    if image_bytes:
        justificative = _upload_expense_image(id_fund, image_bytes)

    fund = Fund(
        id_fund=id_fund,
        amount=-abs(payload.amount),
        category=payload.category.strip(),
        transaction_at=payload.transaction_at,
        justificative=justificative,
        id_event=id_event,
        id_user=user.id_user,
    )

    try:
        treasury_repo.add_fund(session, fund)
        _commit_and_refresh(session, fund)
    except Exception:
        session.rollback()
        raise

    return ExpenseOut.model_validate(fund)


# ============================================================
# TRE-04 : Liste des dépenses d'un événement
# ============================================================

def list_expenses(
    session: Session,
    id_event: UUID,
    *,
    category: str | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[ExpenseOut]:
    """TRE-04 : Liste les dépenses d'un événement avec filtres et pagination."""
    
    _get_event_or_raise(session, id_event)

    if start_date and end_date and start_date > end_date:
        raise InvalidExpenseError(
            "La date de début doit précéder la date de fin."
        )

    expenses = treasury_repo.list_expenses_by_event(
        session,
        id_event,
        category=category,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset,
    )

    return [ExpenseOut.model_validate(expense) for expense in expenses]



# ============================================================
# TRE-05 : Modifier une dépense
# ============================================================

def update_expense(
    session: Session,
    *,
    id_event: UUID,
    id_fund: UUID,
    payload: ExpenseUpdate,
    image_bytes: bytes | None = None,
) -> ExpenseOut:
    """TRE-05 : Modifie une dépense existante."""
    
    fund = _get_fund_or_raise(session, id_fund)

    if fund.id_event != id_event or fund.amount >= 0:
        raise FundNotFoundError("Dépense introuvable pour cet événement.")

    if payload.justificative and image_bytes:
        raise InvalidExpenseError(
            "Choisissez une justification textuelle ou photographique, pas les deux."
        )

    data = payload.model_dump(exclude_unset=True)

    if "amount" in data and data["amount"] is not None:
        data["amount"] = -abs(data["amount"])

    if "category" in data and data["category"] is not None:
        data["category"] = data["category"].strip()

    if image_bytes:
        data["justificative"] = _upload_expense_image(id_fund, image_bytes)

    try:
        treasury_repo.update_fund(session, fund, data)
        _commit_and_refresh(session, fund)
    except Exception:
        session.rollback()
        raise

    return ExpenseOut.model_validate(fund)


# ============================================================
# TRE-06 : Suivi budgétaire global
# ============================================================

def get_budget_summary(session: Session) -> BudgetSummaryOut:
    
    """TRE-06 : Calcule le bilan budgétaire global de la trésorerie."""
    
    donations = treasury_repo.get_global_donations_total(session)
    totals = treasury_repo.get_global_fund_totals(session)

    return BudgetSummaryOut(
        total_donations=donations,
        total_income=totals["total_income"],
        total_expenses=totals["total_expenses"],
        balance=(
            donations
            + totals["total_income"]
            - totals["total_expenses"]
        ),
    )


# ============================================================
# TRE-07 : Prépare les données destinées à l'export.
# ============================================================


def get_export_data(session: Session, export_type: str) -> dict:
    """Prépare les données du bilan budgétaire et des opérations à exporter."""

    data = {}

    if export_type in ("all", "budget"):
        data["budget"] = get_budget_summary(session).model_dump()

    if export_type in ("all", "operations"):
        operations = treasury_repo.list_all_funds(session)
        data["operations"] = [
            {
                "id_fund": str(item.id_fund),
                "amount": item.amount,
                "category": item.category,
                "transaction_at": item.transaction_at,
                "justificative": item.justificative,
                "id_event": str(item.id_event) if item.id_event else None,
            }
            for item in operations
        ]

    return data


# ============================================================
# TRE-08 : Gains d'une campagne
# ============================================================

def get_campaign_gains(
    session: Session,
    id_campaign: UUID,
) -> CampaignGainsOut:
    
    """TRE-08 : Calcule le bilan financier d'une campagne."""
    
    _get_campaign_or_raise(session, id_campaign)

    donations = treasury_repo.get_campaign_donations_total(
        session, id_campaign
    )
    totals = treasury_repo.get_campaign_fund_totals(
        session, id_campaign
    )

    return CampaignGainsOut(
        id_campaign=id_campaign,
        total_donations=donations,
        total_fund_income=totals["total_fund_income"],
        total_expenses=totals["total_expenses"],
        balance=(
            donations
            + totals["total_fund_income"]
            - totals["total_expenses"]
        ),
    )


# ============================================================
# TRE-09 : Gains des campagnes créées hors bénéficiaires.
# ============================================================

def get_system_campaigns_gains(
    session: Session,
) -> list[SystemCampaignGainsOut]:
    """TRE-09 : Gains des campagnes créées hors bénéficiaires."""

    campaigns = treasury_repo.list_system_campaigns(session)

    results = []

    for campaign in campaigns:
        donations = treasury_repo.get_campaign_donations_total(
            session, campaign.id_campaign
        )

        totals = treasury_repo.get_campaign_fund_totals(
            session, campaign.id_campaign
        )

        results.append(
            SystemCampaignGainsOut(
                id_campaign=campaign.id_campaign,
                title=campaign.title,
                total_donations=donations,
                total_fund_income=totals["total_fund_income"],
                total_expenses=totals["total_expenses"],
                balance=(
                    donations
                    + totals["total_fund_income"]
                    - totals["total_expenses"]
                ),
            )
        )

    return results


# ============================================================
# TRE-10 : Gains d'un événement d'une campagne.
# ============================================================

def get_campaign_event_gains(
    session: Session,
    id_campaign: UUID,
    id_event: UUID,
) -> EventGainsOut:
    """TRE-10 : Calcule les gains et dépenses d'un événement d'une campagne."""
    
    _get_campaign_or_raise(session, id_campaign)
    event = _get_event_or_raise(session, id_event)

    if event.id_campaign != id_campaign:
        raise EventNotFoundError(
            "Cet événement n'appartient pas à cette campagne."
        )

    totals = treasury_repo.get_event_fund_totals(session, id_event)

    return EventGainsOut(
        id_event=id_event,
        total_income=totals["total_income"],
        total_expenses=totals["total_expenses"],
        balance=totals["total_income"] - totals["total_expenses"],
    )


# ============================================================
# TRE-11 : Total des dons réussis d'une campagne
# ============================================================

def get_campaign_donations_total(
    session: Session,
    id_campaign: UUID,
) -> CampaignDonationsTotalOut:
    """TRE-11 : Calcule le total des dons réussis d'une campagne."""
    
    _get_campaign_or_raise(session, id_campaign)

    total = treasury_repo.get_campaign_donations_total(
        session, id_campaign
    )

    return CampaignDonationsTotalOut(
        id_campaign=id_campaign,
        total_donations=total,
    )



# ============================================================
# TRE-12 : Gains cumulés de tous les événements d'une campagne
# ============================================================

def get_campaign_events_gains(
    session: Session,
    id_campaign: UUID,
) -> CampaignEventsGainsOut:
    """TRE-12 : Calcule les gains cumulés de tous les événements d'une campagne."""
    
    _get_campaign_or_raise(session, id_campaign)

    totals = treasury_repo.get_campaign_events_fund_totals(
        session, id_campaign
    )

    return CampaignEventsGainsOut(
        id_campaign=id_campaign,
        total_income=totals["total_income"],
        total_expenses=totals["total_expenses"],
        balance=(
            totals["total_income"]
            - totals["total_expenses"]
        ),
    )


def get_event_gains(
    session: Session,
    id_event: UUID,
) -> EventGainsOut:
    """Calcule le bilan financier d'un événement."""
    
    _get_event_or_raise(session, id_event)

    totals = treasury_repo.get_event_fund_totals(session, id_event)

    return EventGainsOut(
        id_event=id_event,
        total_income=totals["total_income"],
        total_expenses=totals["total_expenses"],
        balance=(
            totals["total_income"]
            - totals["total_expenses"]
        ),
    )
