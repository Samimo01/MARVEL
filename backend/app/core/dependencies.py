"""Dépendances partagées : session DB, authentification et autorisations."""

from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.database import get_db
from app.modules.auth import repository as auth_repo
from app.modules.auth.models import User

# Configuration du schéma de sécurité (Bearer Token)
security = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: Session = Depends(get_db)
) -> User:
    """Valide le JWT (émis par Supabase) et récupère l'utilisateur en DB."""
    try:
        # Utilisation de la fonction centralisée dans security.py
        payload = decode_token(credentials.credentials)
        
        user_id = payload.get("sub")
        if not isinstance(user_id, str) or not user_id:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token sans identifiant")
        user_id = UUID(user_id)

    except (jwt.PyJWTError, ValueError) as exc:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, "Token invalide ou expiré"
        ) from exc

    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Utilisateur introuvable")
    return user

def require_campaign_editor(
    user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> User:
    """Autorise la gestion des campagnes aux gestionnaires de collecte et administrateurs."""
    for role_name in ("Collection_Manager", "Administrator"):
        assignment = auth_repo.get_latest_role_assignment(
            session, user.id_user, role_name
        )
        if assignment is not None and assignment.assignment_type == "assigned":
            return user

    raise HTTPException(
        status.HTTP_403_FORBIDDEN,
        "Rôle requis : Collection_Manager ou Administrator.",
    )


def require_administrator(
    user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> User:
    """Réserve l'administration des rôles aux administrateurs actifs."""
    assignment = auth_repo.get_latest_role_assignment(
        session, user.id_user, "Administrator"
    )
    if assignment is None or assignment.assignment_type != "assigned":
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "Rôle requis : Administrator.",
        )
    return user
