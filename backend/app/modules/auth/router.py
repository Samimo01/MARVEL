from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import require_administrator
from app.database import get_db
from app.modules.auth import service
from app.modules.auth.models import User
from app.modules.auth.schemas import (
    LoginRequest,
    RegistrationRequest,
    RegistrationResponse,
    RoleAssignmentRequest,
    RoleAssignmentResponse,
    RoleName,
    TokenResponse,
)
from app.modules.auth.service import (
    CannotRevokeLastAdministratorError,
    DuplicateAccountError,
    InvalidCredentialsError,
    ManagedUserNotFoundError,
)

router = APIRouter(prefix="/auth", tags=["auth"])
admin_router = APIRouter(prefix="/admin", tags=["admin roles"])
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


@admin_router.get("/roles", response_model=list[RoleName])
def list_roles(admin: User = Depends(require_administrator)) -> list[RoleName]:
    return list(RoleName)


@admin_router.get(
    "/users/{id_user}/roles",
    response_model=list[RoleAssignmentResponse],
)
def list_user_roles(
    id_user: UUID,
    db: DbSession,
    admin: User = Depends(require_administrator),
) -> list[RoleAssignmentResponse]:
    try:
        return service.list_user_role_assignments(db, id_user)
    except ManagedUserNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc


@admin_router.post(
    "/users/{id_user}/roles/{role_name}",
    response_model=RoleAssignmentResponse,
)
def set_user_role(
    id_user: UUID,
    role_name: RoleName,
    payload: RoleAssignmentRequest,
    db: DbSession,
    admin: User = Depends(require_administrator),
) -> RoleAssignmentResponse:
    try:
        return service.set_user_role_assignment(
            db, user_id=id_user, role_name=role_name, payload=payload
        )
    except ManagedUserNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    except CannotRevokeLastAdministratorError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
