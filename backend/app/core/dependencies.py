"""Dépendances partagées : session DB, authentification et autorisations."""

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.modules.auth.models import User
from app.core.security import decode_token

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
        if not user_id:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token sans identifiant")
            
    except jwt.PyJWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token invalide ou expiré")
        
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Utilisateur introuvable")
    return user

def require_campaign_editor(user: User = Depends(get_current_user)) -> User:
    """Vérifie si l'utilisateur a le droit de gérer les campagnes (Resp, Admin, Bénéf)."""
    # NOTE: Ici, vous devriez vérifier les rôles plus tard.
    # Pour l'instant, on autorise tout utilisateur connecté pour ne pas bloquer le développement.
    return user