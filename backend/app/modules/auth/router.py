from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.modules.auth import service
from app.modules.auth.schemas import (
    LoginRequest,
    RegistrationRequest,
    RegistrationResponse,
    TokenResponse,
)
from app.modules.auth.service import DuplicateAccountError, InvalidCredentialsError

router = APIRouter(prefix="/auth", tags=["auth"])
DbSession = Annotated[Session, Depends(get_db)]


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: DbSession) -> TokenResponse:
    try:
        access_token = service.authenticate_user(db, payload)
    except InvalidCredentialsError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    return TokenResponse(access_token=access_token)


@router.post(
    "/register",
    response_model=RegistrationResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(payload: RegistrationRequest, db: DbSession) -> RegistrationResponse:
    try:
        user, access_token = service.register_user(db, payload)
    except DuplicateAccountError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return RegistrationResponse(
        message="Compte créé.",
        id_user=user.id_user,
        nickname=user.nickname,
        access_token=access_token,
    )
