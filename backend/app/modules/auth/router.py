from typing import Annotated
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Request,
    Response,
    UploadFile,
    status,
)
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.dependencies import (
    get_access_token,
    get_current_user,
    require_administrator,
    validate_cookie_origin,
)
from app.database import get_db
from app.modules.auth import service
from app.modules.auth.cookies import (
    REFRESH_TOKEN_COOKIE,
    clear_access_token_cookie,
    clear_refresh_token_cookie,
    set_access_token_cookie,
    set_refresh_token_cookie,
)
from app.modules.auth.models import User
from app.modules.auth.schemas import (
    AuthResponse,
    AuthSessionResponse,
    LoginRequest,
    LogoutResponse,
    RegistrationRequest,
    RegistrationResponse,
    RoleAssignmentRequest,
    RoleAssignmentResponse,
    RoleName,
    UserOut,
    UserProfileUpdate,
)
from app.modules.auth.service import (
    CannotRevokeLastAdministratorError,
    DuplicateAccountError,
    ImageAlreadyExistsError,
    InvalidCredentialsError,
    InvalidRefreshTokenError,
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


@router.post("/login", response_model=AuthResponse)
def login(
    payload: LoginRequest,
    response: Response,
    db: DbSession,
) -> AuthResponse:
    try:
        tokens = service.authenticate_user(db, payload)
    except InvalidCredentialsError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    set_access_token_cookie(
        response,
        tokens.access_token,
        persistent=payload.remember_me,
    )
    set_refresh_token_cookie(
        response,
        tokens.refresh_token,
        persistent=tokens.persistent,
    )
    return AuthResponse(message="Connexion réussie.")


@router.post("/refresh", response_model=AuthResponse)
def refresh(
    request: Request,
    response: Response,
    db: DbSession,
) -> AuthResponse | JSONResponse:
    validate_cookie_origin(request)
    token = request.cookies.get(REFRESH_TOKEN_COOKIE)
    if not token:
        return _invalid_refresh_response()

    try:
        tokens = service.rotate_refresh_token(db, token)
    except InvalidRefreshTokenError:
        return _invalid_refresh_response()

    set_access_token_cookie(
        response,
        tokens.access_token,
        persistent=tokens.persistent,
    )
    set_refresh_token_cookie(
        response,
        tokens.refresh_token,
        persistent=tokens.persistent,
    )
    return AuthResponse(message="Session renouvelée.")


def _invalid_refresh_response() -> JSONResponse:
    response = JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"detail": "Refresh token invalide ou expiré."},
    )
    clear_access_token_cookie(response)
    clear_refresh_token_cookie(response)
    return response


@router.post("/logout", response_model=LogoutResponse)
def logout(
    request: Request,
    response: Response,
    token: Annotated[str, Depends(get_access_token)],
    db: DbSession,
    current_user: CurrentUser,
) -> LogoutResponse:
    service.revoke_access_token(
        db,
        token=token,
        user_id=current_user.id_user,
    )
    refresh_token = request.cookies.get(REFRESH_TOKEN_COOKIE)
    if refresh_token:
        service.revoke_refresh_token(
            db,
            token=refresh_token,
            user_id=current_user.id_user,
        )
    clear_access_token_cookie(response)
    clear_refresh_token_cookie(response)
    return LogoutResponse(message="Déconnexion réussie.")


@users_router.get("/me", response_model=AuthSessionResponse)
def current_session(
    db: DbSession,
    current_user: Annotated[User, Depends(get_current_user)],
) -> AuthSessionResponse:
    return AuthSessionResponse(
        id_user=current_user.id_user,
        user=UserOut.model_validate(current_user),
        roles=service.list_active_user_roles(db, current_user.id_user),
    )


@users_router.patch("/me", response_model=UserOut)
def update_current_user(
    request: Request,
    payload: UserProfileUpdate,
    db: DbSession,
    current_user: CurrentUser,
) -> UserOut:
    validate_cookie_origin(request)
    try:
        user = service.update_user_profile(
            db,
            user=current_user,
            payload=payload,
        )
    except DuplicateAccountError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    return UserOut.model_validate(user)


@router.post(
    "/register",
    response_model=RegistrationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    payload: Annotated[RegistrationRequest, Form()],
    response: Response,
    db: DbSession,
    image: Annotated[
        UploadFile | None,
        File(description="Photo de profil (optionnelle)"),
    ] = None,
) -> RegistrationResponse:
    image_bytes = await image.read() if image is not None else None
    if image_bytes is not None and not (image.content_type or "").startswith("image/"):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Le fichier fourni n'est pas une image.",
        )
    try:
        user, tokens = service.register_user(db, payload, image_bytes=image_bytes)
    except DuplicateAccountError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except ImageAlreadyExistsError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc

    set_access_token_cookie(response, tokens.access_token, persistent=tokens.persistent)
    set_refresh_token_cookie(response, tokens.refresh_token, persistent=tokens.persistent)
    return RegistrationResponse(
        message="Compte créé.",
        id_user=user.id_user,
        nickname=user.nickname,
        image_url=user.image_url,
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


@router.post("/{id_user}/image", response_model=UserOut)
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


@router.patch("/{id_user}/image", response_model=UserOut)
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
