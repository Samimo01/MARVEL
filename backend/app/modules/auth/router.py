from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_administrator, security
from app.database import get_db
from app.modules.auth import service
from app.modules.auth.models import User
from app.modules.auth.schemas import (
    LoginRequest,
    LogoutResponse,
    RegistrationRequest,
    RegistrationResponse,
    RoleAssignmentRequest,
    RoleAssignmentResponse,
    RoleName,
    TokenResponse,
    UserOut,
)
from app.modules.auth.service import (
    CannotRevokeLastAdministratorError,
    DuplicateAccountError,
    ImageAlreadyExistsError,
    InvalidCredentialsError,
    ManagedUserNotFoundError,
    UnauthorizedImageActionError,
    UserNotFoundError,
)

router = APIRouter(prefix="/auth", tags=["auth"])
admin_router = APIRouter(prefix="/admin", tags=["admin roles"])
users_router = APIRouter(prefix="/users", tags=["users"])

DbSession = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]
AdminUser = Annotated[User, Depends(require_administrator)]


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


@router.post("/logout", response_model=LogoutResponse)
def logout(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: DbSession,
    current_user: CurrentUser,
) -> LogoutResponse:
    service.revoke_access_token(
        db,
        token=credentials.credentials,
        user_id=current_user.id_user,
    )
    return LogoutResponse(message="Déconnexion réussie.")


@router.post(
    "/register",
    response_model=RegistrationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    payload: Annotated[RegistrationRequest, Form()],
    db: DbSession,
    image: Annotated[
        UploadFile | None,
        File(description="Photo de profil (optionnelle)"),
    ] = None,
) -> RegistrationResponse:
    image_bytes = await image.read() if image is not None else None
    if image_bytes is not None and not (image.content_type or "").startswith(
        "image/"
    ):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Le fichier fourni n'est pas une image.",
        )
    try:
        user, access_token = service.register_user(
            db, payload, image_bytes=image_bytes
        )
    except DuplicateAccountError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
    except ImageAlreadyExistsError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc

    return RegistrationResponse(
        message="Compte créé.",
        id_user=user.id_user,
        nickname=user.nickname,
        image_url=user.image_url,
        access_token=access_token,
    )


@admin_router.get("/roles", response_model=list[RoleName])
def list_roles(admin: AdminUser) -> list[RoleName]:
    return list(RoleName)


@admin_router.get(
    "/users/{id_user}/roles",
    response_model=list[RoleAssignmentResponse],
)
def list_user_role_assignments(
    id_user: UUID,
    db: DbSession,
    admin: AdminUser,
) -> list[RoleAssignmentResponse]:
    try:
        return service.list_user_role_assignments(db, id_user)
    except ManagedUserNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc


@admin_router.post(
    "/users/{id_user}/roles/{role_name}",
    response_model=RoleAssignmentResponse,
)
def assign_role(
    id_user: UUID,
    role_name: RoleName,
    payload: RoleAssignmentRequest,
    db: DbSession,
    admin: AdminUser,
) -> RoleAssignmentResponse:
    try:
        return service.set_user_role_assignment(
            db,
            user_id=id_user,
            role_name=role_name,
            payload=payload,
        )
    except ManagedUserNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    except CannotRevokeLastAdministratorError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc


@users_router.post("/{id_user}/image", response_model=UserOut)
async def aut09_upload_user_image(
    id_user: UUID,
    image: Annotated[UploadFile, File(..., description="Photo de profil")],
    db: DbSession,
) -> UserOut:
    if not (image.content_type or "").startswith("image/"):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Le fichier fourni n'est pas une image.",
        )
    image_bytes = await image.read()
    try:
        user = service.upload_user_image(
            db,
            id_user=id_user,
            image_bytes=image_bytes,
        )
        return UserOut.model_validate(user)
    except UserNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    except ImageAlreadyExistsError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc


@users_router.patch("/{id_user}/image", response_model=UserOut)
async def aut10_replace_user_image(
    id_user: UUID,
    image: Annotated[
        UploadFile,
        File(..., description="Nouvelle photo de profil"),
    ],
    db: DbSession,
    current_user: CurrentUser,
) -> UserOut:
    """AUT-10 : Remplace la photo d'un utilisateur."""
    if not (image.content_type or "").startswith("image/"):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Le fichier fourni n'est pas une image.",
        )

    image_bytes = await image.read()
    try:
        user = service.replace_user_image(
            db,
            current_user=current_user,
            id_user=id_user,
            image_bytes=image_bytes,
        )
        return UserOut.model_validate(user)
    except UserNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    except UnauthorizedImageActionError as exc:
        raise HTTPException(status.HTTP_403_FORBIDDEN, str(exc)) from exc