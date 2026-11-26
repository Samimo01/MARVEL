"""Schémas Pydantic du module financial_donations."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# ============================================================
# Entrées
# ============================================================
class FinancialDonCreate(BaseModel):
    """DON-01 : Création d'un don financier."""

    amount: Decimal = Field(..., gt=0)
    id_campaign: UUID
    is_anonymous: bool = False


# ============================================================
# Sorties
# ============================================================
class FinancialDonOut(BaseModel):
    """Représentation complète d'un don financier."""

    id_don_f: UUID
    is_anonymous: bool
    amount: Decimal
    status: str
    failure_reason: str | None
    reference_payment: str | None
    paid_at: datetime | None = None
    created_at: datetime
    id_user: UUID | None
    id_campaign: UUID
    id_ben_file: str | None

    model_config = ConfigDict(from_attributes=True)


class PaymentInitOut(BaseModel):
    """DON-02 : Réponse de l'initialisation du paiement."""

    id_don_f: UUID
    payment_url: str
    message: str


class PaymentStatusOut(BaseModel):
    """DON-03 : Statut du paiement."""

    id_don_f: UUID
    status: str
    reference_payment: str | None
    paid_at: datetime | None = None

