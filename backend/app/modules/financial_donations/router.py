"""Endpoints HTTP du module financial_donations."""

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_campaign_editor
from app.database import get_db
from app.modules.auth.models import User
from app.modules.financial_donations import service as don_service
from app.modules.financial_donations.schemas import (
    FinancialDonCreate,
    FinancialDonOut,
    PaymentInitOut,
    PaymentStatusOut,
)
from app.modules.financial_donations.service import (
    CampaignNotFoundError,
    DonationAlreadyPaidError,
    DonationNotFoundError,
    DonationNotSuccessfulError,
)

router = APIRouter(prefix="/dons", tags=["Financial Donations"])

DbSession = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]
CampaignEditor = Annotated[User, Depends(require_campaign_editor)]


@router.get("/me", response_model=list[FinancialDonOut])
def don04_list_my_donations(
    session: DbSession,
    user: CurrentUser,
):
    """DON-04 : Historique de mes dons."""
    return don_service.list_my_donations(session, user=user)


@router.get("/succeed", response_model=list[FinancialDonOut])
def don08_list_successful_donations(
    session: DbSession,
    user: CampaignEditor,
):
    """DON-08 : Tous les dons réussis."""
    return don_service.list_successful_donations(session)


@router.get(
    "/{id_campaign}/succeed",
    response_model=list[FinancialDonOut],
)
def don09_list_successful_donations_by_campaign(
    id_campaign: UUID,
    session: DbSession,
    user: CampaignEditor,
):
    """DON-09 : Tous les dons réussis d'une campagne."""
    return don_service.list_successful_donations_by_campaign(session, id_campaign)


@router.post(
    "/financiers",
    response_model=FinancialDonOut,
    status_code=status.HTTP_201_CREATED,
)
def don01_create_financial_donation(
    payload: FinancialDonCreate,
    session: DbSession,
    user: CurrentUser,
):
    """DON-01 : Créer un don financier."""
    try:
        return don_service.create_financial_donation(session, user=user, payload=payload)
    except CampaignNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc


@router.post(
    "/financiers/{id_don_f}/pay",
    response_model=PaymentInitOut,
)
def don02_pay_financial_donation(
    id_don_f: UUID,
    session: DbSession,
    user: CurrentUser,
):
    """DON-02 : Payer un don financier (Simulation)."""
    try:
        return don_service.pay_donation(session, user=user, id_don_f=id_don_f)
    except DonationNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    except DonationAlreadyPaidError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc


@router.get(
    "/financiers/{id_don_f}/payment-status",
    response_model=PaymentStatusOut,
)
def don03_get_payment_status(
    id_don_f: UUID,
    session: DbSession,
    user: CurrentUser,
):
    """DON-03 : Statut du paiement."""
    try:
        return don_service.get_payment_status(session, id_don_f)
    except DonationNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc


@router.get("", response_model=list[FinancialDonOut])
def don07_list_all_donations(
    session: DbSession,
    user: CampaignEditor,
    status: str | None = None,
    id_campaign: UUID | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    limit: int = 50,
    offset: int = 0,
):
    """DON-07 : Liste globale des dons avec filtres."""
    return don_service.list_donations(
        session,
        status=status,
        id_campaign=id_campaign,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset,
    )


@router.get("/{id_don_f}", response_model=FinancialDonOut)
def don05_get_donation_detail(
    id_don_f: UUID,
    session: DbSession,
    user: CurrentUser,
):
    """DON-05 : Détail d'un don."""
    try:
        return don_service.get_donation_detail(session, id_don_f)
    except DonationNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc


# ============================================================
# DON-06 — GET unique : génère et renvoie le PDF en mémoire
# ============================================================
@router.get(
    "/{id_don_f}/receipt",
    responses={200: {"content": {"application/pdf": {}}}},
)
def don06_download_receipt(
    id_don_f: UUID,
    session: DbSession,
    user: CurrentUser,
):
    """
    DON-06 : Télécharge le reçu PDF (généré à la volée, en mémoire).

    - Aucun fichier n'est stocké sur le disque.
    - Le don doit être au statut 'Success'.
    - Accessible à tout utilisateur authentifié (donateur ou admin).
    """
    try:
        pdf_bytes, filename = don_service.build_receipt(session, id_don_f)
    except DonationNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    except DonationNotSuccessfulError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'inline; filename="{filename}"',
            "Content-Length": str(len(pdf_bytes)),
            "Cache-Control": "no-store",
            "X-Content-Type-Options": "nosniff",
        },
    )