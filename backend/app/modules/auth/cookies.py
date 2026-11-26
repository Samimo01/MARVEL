from fastapi import Response

from app.config import settings

ACCESS_TOKEN_COOKIE = "marvel_access_token"
REFRESH_TOKEN_COOKIE = "marvel_refresh_token"


def set_access_token_cookie(
    response: Response,
    token: str,
    *,
    persistent: bool,
) -> None:
    response.set_cookie(
        key=ACCESS_TOKEN_COOKIE,
        value=token,
        max_age=settings.access_token_expire_minutes * 60 if persistent else None,
        httponly=True,
        secure=settings.auth_cookie_secure,
        samesite="lax",
        path=settings.api_prefix,
    )


def clear_access_token_cookie(response: Response) -> None:
    response.delete_cookie(
        key=ACCESS_TOKEN_COOKIE,
        httponly=True,
        secure=settings.auth_cookie_secure,
        samesite="lax",
        path=settings.api_prefix,
    )


def set_refresh_token_cookie(
    response: Response,
    token: str,
    *,
    persistent: bool,
) -> None:
    response.set_cookie(
        key=REFRESH_TOKEN_COOKIE,
        value=token,
        max_age=settings.refresh_token_expire_days * 24 * 60 * 60 if persistent else None,
        httponly=True,
        secure=settings.auth_cookie_secure,
        samesite="lax",
        path=f"{settings.api_prefix}/auth",
    )


def clear_refresh_token_cookie(response: Response) -> None:
    response.delete_cookie(
        key=REFRESH_TOKEN_COOKIE,
        httponly=True,
        secure=settings.auth_cookie_secure,
        samesite="lax",
        path=f"{settings.api_prefix}/auth",
    )
