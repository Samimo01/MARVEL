"""Endpoints HTTP du module financial_donations."""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_campaign_editor # Adapter selon vos rôles
from app.database import get_db
from app.modules.auth.models import User
from app.modules.financial_donations import service as don_service
from app.modules.financial_donations.schemas import (
    FinancialDonCreate, FinancialDonOut, PaymentInitOut, PaymentStatusOut, ReceiptOut
)
from app.modules.financial_donations.service import (
    DonationNotFoundError, CampaignNotFoundError, 
    DonationAlreadyPaidError, DonationNotSuccessfulError
)

router = APIRouter(prefix="/dons", tags=["Financial Donations"])

# ============================================================
# ROUTES SPÉCIFIQUES (doivent être avant /{id_don})
# ============================================================

@router.get("/me", response_model=list[FinancialDonOut])
def don04_list_my_donations(
    session: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """DON-04 : Historique de mes dons."""
    return don_service.list_my_donations(session, user=user)

@router.get("/succeed", response_model=list[FinancialDonOut])
def don08_list_successful_donations(
    session: Session = Depends(get_db),
    user: User = Depends(require_campaign_editor) # Resp, Trésorier, Admin
):
    """DON-08 : Tous les dons réussis."""
    return don_service.list_successful_donations(session)

@router.get("/{id_campaign}/succeed", response_model=list[FinancialDonOut])
def don09_list_successful_donations_by_campaign(
    id_campaign: UUID,
    session: Session = Depends(get_db),
    user: User = Depends(require_campaign_editor)
):
    """DON-09 : Tous les dons réussis d'une campagne."""
    return don_service.list_successful_donations_by_campaign(session, id_campaign)


# ============================================================
# ROUTES FINANCIÈRES
# ============================================================

@router.post("/financiers", response_model=FinancialDonOut, status_code=status.HTTP_201_CREATED)
def don01_create_financial_donation(
    payload: FinancialDonCreate,
    session: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """DON-01 : Créer un don financier."""
    try:
        return don_service.create_financial_donation(session, user=user, payload=payload)
    except CampaignNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc

@router.post("/financiers/{id_don_f}/pay", response_model=PaymentInitOut)
def don02_pay_financial_donation(
    id_don_f: UUID,
    session: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """DON-02 : Payer un don financier (Simulation)."""
    try:
        return don_service.pay_donation(session, user=user, id_don_f=id_don_f)
    except DonationNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    except DonationAlreadyPaidError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc

@router.get("/financiers/{id_don_f}/payment-status", response_model=PaymentStatusOut)
def don03_get_payment_status(
    id_don_f: UUID,
    session: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """DON-03 : Statut du paiement."""
    try:
        return don_service.get_payment_status(session, id_don_f)
    except DonationNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc


# ============================================================
# ROUTES GLOBALES ET DÉTAILS (doivent être après)
# ============================================================

@router.get("", response_model=list[FinancialDonOut])
def don07_list_all_donations(
    status: str | None = None,
    id_campaign: UUID | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    limit: int = 50,
    offset: int = 0,
    session: Session = Depends(get_db),
    user: User = Depends(require_campaign_editor)
):
    """DON-07 : Liste globale des dons avec filtres."""
    return don_service.list_donations(
        session, status=status, id_campaign=id_campaign, 
        start_date=start_date, end_date=end_date, limit=limit, offset=offset
    )

@router.get("/{id_don_f}", response_model=FinancialDonOut)
def don05_get_donation_detail(
    id_don_f: UUID,
    session: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """DON-05 : Détail d'un don."""
    try:
        return don_service.get_donation_detail(session, id_don_f)
    except DonationNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc

@router.post("/{id_don_f}/receipt", response_model=ReceiptOut)
def don06_generate_receipt(
    id_don_f: UUID,
    session: Session = Depends(get_db),
    user: User = Depends(require_campaign_editor)
):
    """DON-06 : Générer le reçu d'un don."""
    try:
        return don_service.generate_receipt(session, id_don_f)
    except DonationNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    except DonationNotSuccessfulError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc