"""Dépendances partagées : session DB,
authentification et autorisations."""

from typing import Annotated
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.config import settings
from app.core.security import decode_token, token_revocation_id
from app.database import get_db
from app.modules.auth import repository as auth_repo
from app.modules.auth.cookies import ACCESS_TOKEN_COOKIE
from app.modules.auth.models import User

# Configuration du schéma de sécurité (Bearer Token)
security = HTTPBearer(auto_error=False)


def validate_cookie_origin(request: Request) -> None:
    if request.method not in {"GET", "HEAD", "OPTIONS"}:
        origin = request.headers.get("origin")
        if origin not in settings.cors_origin_list:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                "Origine non autorisée pour une requête authentifiée.",
            )


def get_access_token(
    request: Request,
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Depends(security)
    ],
) -> str:
    if credentials is not None:
        return credentials.credentials

    token = request.cookies.get(ACCESS_TOKEN_COOKIE)
    if not token:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    validate_cookie_origin(request)
    return token



def get_current_user(
    token: Annotated[str, Depends(get_access_token)],
    session: Annotated[Session, Depends(get_db)],
) -> User:
    """Valide le JWT (émis par Supabase) et récupère l'utilisateur en DB."""
    try:
        # Utilisation de la fonction centralisée dans security.py
        payload = decode_token(token)
        token_id = token_revocation_id(token, payload)
        if auth_repo.is_token_revoked(session, token_id):
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token révoqué")

        user_id = payload.get("sub")
        if not isinstance(user_id, str) or not user_id:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token sans identifiant")
        user_id = UUID(user_id)

    except (jwt.PyJWTError, ValueError) as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token invalide ou expiré") from exc

    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Utilisateur introuvable")
    return user


def require_campaign_editor(
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db)],
) -> User:
    """Autorise la gestion des campagnes aux gestionnaires de collecte et administrateurs."""
    for role_name in ("Collection_Manager", "Administrator"):
        assignment = auth_repo.get_latest_role_assignment(session, user.id_user, role_name)
        if assignment is not None and assignment.assignment_type == "assigned":
            return user

    raise HTTPException(
        status.HTTP_403_FORBIDDEN,
        "Rôle requis : Collection_Manager ou Administrator.",
    )


def require_administrator(
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db)],
) -> User:
    """Réserve l'administration des rôles aux administrateurs actifs."""
    assignment = auth_repo.get_latest_role_assignment(session, user.id_user, "Administrator")
    if assignment is None or assignment.assignment_type != "assigned":
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "Rôle requis : Administrator.",
        )
    return user


def require_natural_donation_staff(
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db)],
) -> User:
    """Autorise les rôles liés aux dons naturels."""
    for role_name in ("Stock_Manager", "Collection_Manager", "Administrator"):
        assignment = auth_repo.get_latest_role_assignment(session, user.id_user, role_name)
        if assignment is not None and assignment.assignment_type == "assigned":
            return user

    raise HTTPException(
        status.HTTP_403_FORBIDDEN,
        "Rôle requis : Stock_Manager, Collection_Manager ou Administrator.",
    )


def require_stock_manager_or_admin(
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db)],
) -> User:
    """Autorise uniquement Stock_Manager et Administrator."""
    for role_name in ("Stock_Manager", "Administrator"):
        assignment = auth_repo.get_latest_role_assignment(session, user.id_user, role_name)
        if assignment is not None and assignment.assignment_type == "assigned":
            return user

    raise HTTPException(
        status.HTTP_403_FORBIDDEN,
        "Rôle requis : Stock_Manager ou Administrator.",
    )


def require_volunteer(
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db)],
) -> User:
    """Autorise uniquement les bénévoles ayant un rôle actif."""
    assignment = auth_repo.get_latest_role_assignment(session, user.id_user, "Volunteer")

    if assignment is None or assignment.assignment_type != "assigned":
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "Rôle requis : Volunteer.",
        )

    return user

def require_treasury_staff(
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db)],
) -> User:
    """Autorise les trésoriers et les administrateurs."""
    for role_name in ("Treasurer", "Administrator"):
        assignment = auth_repo.get_latest_role_assignment(
            session, user.id_user, role_name
        )

        if assignment is not None and assignment.assignment_type == "assigned":
            return user

    raise HTTPException(
        status.HTTP_403_FORBIDDEN,
        "Rôle requis : Treasurer ou Administrator.",
    )