"""SchÃ©mas Pydantic du module campaigns."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# ============================================================
# Base commune
# ============================================================
class CampaignBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    description: str | None = None
    goal: Decimal | None = Field(None, ge=0)
    start_at: datetime | None = None
    finish_at: datetime | None = None
    categories: list[str] | None = None
    image_url: str | None = None


# ============================================================
# EntrÃ©es
# ============================================================
class CampaignCreate(CampaignBase):
    """CAT-07 â€” POST /campaigns."""

class CampaignUpdate(BaseModel):
    """CAT-08 â€” PUT /campaigns/{id}. Tous optionnels."""

    title: str | None = Field(None, min_length=3, max_length=200)
    description: str | None = None
    goal: Decimal | None = Field(None, ge=0)
    start_at: datetime | None = None
    finish_at: datetime | None = None
    categories: list[str] | None = None
    image_url: str | None = None
    closure_reason: str | None = None


# ============================================================
# Sorties
# ============================================================
class CampaignOut(CampaignBase):
    """Sortie complÃ¨te (gestion / admin)."""
    id_campaign: UUID
    status: str
    closed_at: datetime | None
    closure_reason: str | None
    created_at: datetime
    updated_at: datetime
    id_user: UUID

    model_config = ConfigDict(from_attributes=True)


class CampaignPublic(BaseModel):
    """SchÃ©ma public de base pour une campagne."""
    id_campaign: UUID
    title: str
    description: str | None
    goal: Decimal | None
    collected_amount: Decimal = Decimal(0)
    start_at: datetime | None
    finish_at: datetime | None
    categories: list[str] | None
    image_url: str | None
    status: str


class CampaignProgressOut(CampaignPublic):
    """Campagne publique avec jauge."""
    progress_percent: float = Field(0.0, ge=0, le=100)


class GaugeOut(BaseModel):
    """CAM-05 : Jauge de progression."""
    id_campaign: UUID
    goal: Decimal | None
    collected: Decimal
    percentage: float


class FinancialDonOut(BaseModel):
    """CAM-06 : Dons rattachÃ©s Ã  une campagne."""
    id_don_f: UUID
    amount: Decimal
    status: str
    created_at: datetime
    is_anonymous: bool

    model_config = ConfigDict(from_attributes=True)

# ============================================================
# Ã‰vÃ©nements de collecte
# ============================================================

class EventCreate(BaseModel):
    """CAM-10 â€” CrÃ©ation d'un Ã©vÃ©nement."""

    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = None                 
    expected_donation_types: str | None = None
    event_at: datetime | None = None
    place: str | None = None
    goal: Decimal | None = Field(None, ge=0)


class EventUpdate(BaseModel):
    """CAM-13 â€” Modification d'un Ã©vÃ©nement."""

    title: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None                 
    expected_donation_types: str | None = None
    event_at: datetime | None = None
    place: str | None = None
    goal: Decimal | None = Field(None, ge=0)


class EventOut(BaseModel):
    """Sortie complÃ¨te d'un Ã©vÃ©nement."""

    id_event: UUID
    id_campaign: UUID
    title: str
    description: str | None                  
    expected_donation_types: str | None 
    event_at: datetime | None
    place: str | None
    goal: Decimal | None
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)