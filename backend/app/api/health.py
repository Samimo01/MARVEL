from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, str]:
    """Vérifie que l'API répond (utilisé par Docker, Uptime Kuma et les frontends)."""
    return {"status": "ok"}
