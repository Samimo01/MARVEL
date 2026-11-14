"""Schémas Pydantic du module campaigns."""

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
# Entrées
# ============================================================
class CampaignCreate(CampaignBase):
    """CAT-07 — POST /campaigns."""


class CampaignUpdate(BaseModel):
    """CAT-08 — PUT /campaigns/{id}. Tous optionnels."""

    title: str | None = Field(None, min_length=3, max_length=200)
    description: str | None = None
    goal: Decimal | None = Field(None, ge=0)
    start_at: datetime | None = None
    finish_at: datetime | None = None
    categories: list[str] | None = None
    image_url: str | None = None
    closure_reason: str | None = None


class PublicationIn(BaseModel):
    """CAT-09 — PATCH /campaigns/{id}/publication."""

    est_publier: bool
    date_publication: datetime | None = None  # accepté mais ignoré


# ============================================================
# Sorties
# ============================================================
class CampaignOut(CampaignBase):
    """Sortie complète (gestion / admin)."""
    id_campaign: UUID
    status: str
    closed_at: datetime | None
    closure_reason: str | None
    created_at: datetime
    updated_at: datetime
    id_user: UUID

    model_config = ConfigDict(from_attributes=True)


# 👇 AJOUTEZ CETTE CLASSE MANQUANTE 👇
class CampaignPublic(BaseModel):
    """Schéma public de base pour une campagne."""
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
    """CAT-01 / CAT-02 — campagne publique avec jauge (hérite de CampaignPublic)."""
    progress_percent: float = Field(0.0, ge=0, le=100)