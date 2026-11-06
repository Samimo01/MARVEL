"""Routes PUBLIQUES (sans authentification) consommées par la vitrine (frontend-public).

Elles restent séparées des routes protégées pour que la vitrine reste disponible
et pour pouvoir les mettre en cache au niveau du reverse proxy.
"""

from fastapi import APIRouter

from app.modules.campaigns.schemas import CampaignPublic

router = APIRouter(prefix="/public", tags=["public"])


@router.get("/campaigns", response_model=list[CampaignPublic])
def list_public_campaigns() -> list[CampaignPublic]:
    """Campagnes en cours avec objectif et montant collecté (jauge de progression)."""
    # À remplacer par CampaignService.list_active(db) quand la table existera.
    return []
