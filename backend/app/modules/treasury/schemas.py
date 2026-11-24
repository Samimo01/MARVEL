"""Schémas Pydantic du module treasury."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

# ============================================================
# Opérations financières
# ============================================================


class FundOut(BaseModel):
    """TRE-02 : Détail d'une opération financière."""

    id_fund: UUID
    amount: Decimal
    category: str | None
    transaction_at: datetime
    justificative: str | None
    id_event: UUID | None
    id_user: UUID | None

    model_config = ConfigDict(from_attributes=True)


# ============================================================
# Dépenses
# ============================================================


class ExpenseCreate(BaseModel):
    """TRE-03 : Enregistrement d'une dépense."""

    amount: Decimal = Field(..., gt=0)
    category: str = Field(..., min_length=1)
    transaction_at: datetime
    justificative: str | None = None


class ExpenseUpdate(BaseModel):
    """TRE-05 : Modification d'une dépense."""

    amount: Decimal | None = Field(default=None, gt=0)
    category: str | None = Field(default=None, min_length=1)
    transaction_at: datetime | None = None
    justificative: str | None = None

    @model_validator(mode="after")
    def check_at_least_one_field(self):
        if not self.model_fields_set:
            raise ValueError("Au moins un champ doit être fourni.")
        return self


class ExpenseOut(BaseModel):
    """Représentation d'une dépense."""

    id_fund: UUID
    amount: Decimal
    category: str | None
    transaction_at: datetime
    justificative: str | None
    id_event: UUID | None
    id_user: UUID | None

    model_config = ConfigDict(from_attributes=True)


# ============================================================
# Suivi budgétaire
# ============================================================


class BudgetSummaryOut(BaseModel):
    """TRE-06 : Bilan budgétaire."""

    total_donations: Decimal
    total_income: Decimal
    total_expenses: Decimal
    balance: Decimal


# ============================================================
# Gains des campagnes
# ============================================================


class CampaignGainsOut(BaseModel):
    """TRE-08 : Bilan financier d'une campagne."""

    id_campaign: UUID
    total_donations: Decimal
    total_fund_income: Decimal
    total_expenses: Decimal
    balance: Decimal


class CampaignDonationsTotalOut(BaseModel):
    """TRE-11 : Total des dons réussis d'une campagne."""

    id_campaign: UUID
    total_donations: Decimal


# ============================================================
# Gains des événements
# ============================================================


class EventGainsOut(BaseModel):
    """TRE-10 : Bilan financier d'un événement."""

    id_event: UUID
    total_income: Decimal
    total_expenses: Decimal
    balance: Decimal


class CampaignEventsGainsOut(BaseModel):
    """TRE-12 : Gains cumulés de tous les événements d'une campagne."""

    id_campaign: UUID
    total_income: Decimal
    total_expenses: Decimal
    balance: Decimal


class SystemCampaignGainsOut(BaseModel):
    """TRE-09 : Gains d'une campagne créée hors bénéficiaire."""

    id_campaign: UUID
    title: str
    total_donations: Decimal
    total_fund_income: Decimal
    total_expenses: Decimal
    balance: Decimal
