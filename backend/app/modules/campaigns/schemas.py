"""Schémas Pydantic du module campaigns."""

from decimal import Decimal

from pydantic import BaseModel


class CampaignPublic(BaseModel):
    """Campagne telle qu'exposée publiquement (montants en Decimal, jamais en float)."""

    id: int
    title: str
    description: str
    goal_amount: Decimal
    collected_amount: Decimal
