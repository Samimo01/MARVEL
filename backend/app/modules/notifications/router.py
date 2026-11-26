from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database import get_db
from app.modules.auth.models import User
from app.modules.notifications.schemas import NotificationPageResponse
from app.modules.notifications.service import list_my_notifications

router = APIRouter(tags=["Notifications"])

DbSession = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]


@router.get(
    "/notifications/me",
    summary="Not01 Consulter mes notifications",
    description="Filtrer mes notifications par état lu/non lu et les paginer.",
    response_model=NotificationPageResponse,
)
def get_my_notifications(
    db: DbSession,
    user: CurrentUser,
    is_read: Annotated[bool | None, Query()] = None,
    read: Annotated[bool | None, Query()] = None,
    status: Annotated[str | None, Query()] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    size: Annotated[int | None, Query(ge=1, le=100)] = None,
    limit: Annotated[int | None, Query(ge=1, le=100)] = None,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    effective_is_read = is_read if is_read is not None else read

    if effective_is_read is None and status is not None:
        normalized_status = status.strip().lower()
        if normalized_status in {"read", "lu", "true", "1"}:
            effective_is_read = True
        elif normalized_status in {"unread", "non-lu", "non lu", "false", "0"}:
            effective_is_read = False

    effective_page_size = size or limit or page_size
    effective_page = (
        (offset // effective_page_size) + 1
        if offset
        else page
    )
    effective_offset = offset if offset else None

    return list_my_notifications(
        db,
        user.id_user,
        effective_is_read,
        effective_page,
        effective_page_size,
        effective_offset,
    )
