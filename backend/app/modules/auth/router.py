from fastapi import APIRouter, HTTPException, status

from app.modules.auth.schemas import LoginRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest) -> TokenResponse:
    """Connexion : à implémenter (vérification du mot de passe haché, émission du JWT)."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Authentification non implémentée",
    )
