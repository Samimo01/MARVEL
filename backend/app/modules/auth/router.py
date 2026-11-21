from typing import Annotated
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Response,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from app.core.dependencies import get_access_token, get_current_user, require_administrator
from app.database import get_db
from app.modules.auth import service
from app.modules.auth.cookies import clear_access_token_cookie, set_access_token_cookie
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
DbSession = Annotated[Session, Depends(get_db)]
users_router = APIRouter(prefix="/users", tags=["users"])

@router.post("/login", response_model=AuthResponse)
def login(
    payload: LoginRequest,
    response: Response,
    db: DbSession,
) -> AuthResponse:
    try:
        access_token = service.authenticate_user(db, payload)
    except InvalidCredentialsError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    set_access_token_cookie(
        response,
        access_token,
        persistent=payload.remember_me,
    )
    return AuthResponse(message="Connexion réussie.")


@router.post("/logout", response_model=LogoutResponse)
def logout(
    response: Response,
    token: Annotated[str, Depends(get_access_token)],
    db: DbSession,
    current_user: Annotated[User, Depends(get_current_user)],
) -> LogoutResponse:
    service.revoke_access_token(
        db,
        token=token,
        user_id=current_user.id_user,
    )
    clear_access_token_cookie(response)
    return LogoutResponse(message="Déconnexion réussie.")


@router.get("/me", response_model=AuthSessionResponse)
def current_session(
    db: DbSession,
    current_user: Annotated[User, Depends(get_current_user)],
) -> AuthSessionResponse:
    return AuthSessionResponse(
        id_user=current_user.id_user,
        roles=service.list_active_user_roles(db, current_user.id_user),
    )


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
        File(description="Photo de profil facultative"),
    ] = None,
) -> RegistrationResponse:
    image_bytes = None
    if image is not None:
        if image.content_type is None or not image.content_type.startswith("image/"):
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                "Le fichier fourni n'est pas une image.",
            )
        image_bytes = await image.read()

    try:
        user, access_token = service.register_user(
            db,
            payload,
            image_bytes=image_bytes,
        )
    except DuplicateAccountError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    set_access_token_cookie(response, access_token, persistent=True)
    return RegistrationResponse(
        message="Compte créé.",
        id_user=user.id_user,
        nickname=user.nickname,
        image_url=user.image_url,
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

# ============================================================
# AUT-09 : POST /auth/{id_user}/image (public)
# ============================================================
@router.post("/{id_user}/image", response_model=UserOut)
async def aut09_upload_user_image(
    id_user: UUID,
    image: UploadFile = File(..., description="Photo de profil"),
    db: DbSession = None,
) -> UserOut:
    """AUT-09 : Upload public de la photo d'un utilisateur."""
    if not image.content_type.startswith("image/"):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Le fichier fourni n'est pas une image.",
        )

    image_bytes = await image.read()
    try:
        user = service.upload_user_image(db, id_user=id_user, image_bytes=image_bytes)
        return UserOut.model_validate(user)
    except UserNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    except ImageAlreadyExistsError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc


# ============================================================
# AUT-10 : PATCH /users/{id_user}/image (authentifié)
# ============================================================
@users_router.patch("/{id_user}/image", response_model=UserOut)
async def aut10_replace_user_image(
    id_user: UUID,
    image: UploadFile = File(..., description="Nouvelle photo de profil"),
    db: DbSession = None,
    current_user: User = Depends(get_current_user),
) -> UserOut:
    """AUT-10 : Remplace la photo d'un utilisateur."""
    if not image.content_type.startswith("image/"):
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
