"""Logique métier du module financial_donations."""

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from app.modules.auth.models import User
from app.modules.campaigns import repository as campaign_repo
from app.modules.financial_donations import repository as don_repo
from app.modules.financial_donations.models import FinancialDon
from app.modules.financial_donations.schemas import (
    FinancialDonCreate,
    FinancialDonOut,
    PaymentInitOut,
    PaymentStatusOut,
    ReceiptOut,
)


class DonationNotFoundError(Exception):
    pass


class CampaignNotFoundError(Exception):
    pass


class DonationAlreadyPaidError(Exception):
    pass


class DonationNotSuccessfulError(Exception):
    pass


def _get_or_raise(session: Session, id_don_f: UUID) -> FinancialDon:
    don = don_repo.get_donation_by_id(session, id_don_f)
    if don is None:
        raise DonationNotFoundError(f"Don {id_don_f} introuvable")
    return don


def create_financial_donation(
    session: Session, *, user: User, payload: FinancialDonCreate
) -> FinancialDonOut:
    campaign = campaign_repo.get_campaign_by_id(session, payload.id_campaign)
    if not campaign:
        raise CampaignNotFoundError("Campagne introuvable")

    donation = FinancialDon(
        id_user=user.id_user if not payload.is_anonymous else None,
        id_campaign=payload.id_campaign,
        amount=payload.amount,
        is_anonymous=payload.is_anonymous,
        status="Pending",
    )
    don_repo.add_donation(session, donation)
    session.commit()
    session.refresh(donation)
    return FinancialDonOut.model_validate(donation)


def pay_donation(session: Session, *, user: User, id_don_f: UUID) -> PaymentInitOut:
    donation = _get_or_raise(session, id_don_f)

    if donation.status == "Success":
        raise DonationAlreadyPaidError("Ce don a déjà été payé.")

    mock_payment_url = f"https://mock-payment-gateway.com/pay/{id_don_f}"
    reference = f"PAY-{uuid.uuid4().hex[:8].upper()}"
    donation.reference_payment = reference

    don_repo.update_donation(session, donation, {"reference_payment": reference})
    session.commit()

    return PaymentInitOut(
        id_don_f=donation.id_don_f,
        payment_url=mock_payment_url,
        message="Session de paiement ouverte. Utilisez l'URL pour finaliser.",
    )


def get_payment_status(session: Session, id_don_f: UUID) -> PaymentStatusOut:
    donation = _get_or_raise(session, id_don_f)

    if donation.reference_payment and donation.status != "Success":
        donation.status = "Success"
        donation.paid_at = datetime.now(UTC)
        don_repo.update_donation(
            session,
            donation,
            {
                "status": "Success",
                "paid_at": donation.paid_at,
            },
        )
        session.commit()
        session.refresh(donation)

    return PaymentStatusOut(
        id_don_f=donation.id_don_f,
        status=donation.status,
        reference_payment=donation.reference_payment,
        paid_at=donation.paid_at,
    )


def list_my_donations(session: Session, *, user: User) -> list[FinancialDonOut]:
    dons = don_repo.list_user_donations(session, user.id_user)
    return [FinancialDonOut.model_validate(d) for d in dons]


def get_donation_detail(session: Session, id_don_f: UUID) -> FinancialDonOut:
    donation = _get_or_raise(session, id_don_f)
    return FinancialDonOut.model_validate(donation)


def generate_receipt(session: Session, id_don_f: UUID) -> ReceiptOut:
    donation = _get_or_raise(session, id_don_f)

    if donation.status != "Success":
        raise DonationNotSuccessfulError("Impossible de générer un reçu pour un don non validé.")

    mock_pdf_url = f"https://mock-storage.com/receipts/{donation.id_don_f}.pdf"

    return ReceiptOut(
        id_don_f=donation.id_don_f,
        receipt_url=mock_pdf_url,
        message="Reçu généré avec succès.",
    )


def list_donations(
    session: Session,
    *,
    status: str | None = None,
    id_campaign: UUID | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[FinancialDonOut]:
    dons = don_repo.list_all_donations(
        session,
        status=status,
        id_campaign=id_campaign,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset,
    )
    return [FinancialDonOut.model_validate(d) for d in dons]


def list_successful_donations(
    session: Session,
) -> list[FinancialDonOut]:
    dons = don_repo.list_successful_donations(session)
    return [FinancialDonOut.model_validate(d) for d in dons]


def list_successful_donations_by_campaign(
    session: Session, id_campaign: UUID
) -> list[FinancialDonOut]:
    dons = don_repo.list_successful_donations_by_campaign(session, id_campaign)
    return [FinancialDonOut.model_validate(d) for d in dons]


def get_campaign_amount_collected(session: Session, id_campaign: UUID) -> Decimal:
    """Expose le calcul du montant collecté pour une campagne."""
    return don_repo.get_campaign_amount_collected(session, id_campaign)


def get_campaigns_amounts_collected(session: Session, ids: list[UUID]) -> dict[UUID, Decimal]:
    """Expose le calcul batch des montants collectés."""
    return don_repo.get_campaigns_amounts_collected(session, ids)


def list_campaign_donations(session: Session, id_campaign: UUID) -> list[FinancialDonOut]:
    """Expose la liste des dons d'une campagne."""
    dons = don_repo.list_donations_by_campaign(session, id_campaign)
    return [FinancialDonOut.model_validate(d) for d in dons]
