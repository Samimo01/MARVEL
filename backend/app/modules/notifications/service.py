from math import ceil
from uuid import UUID

from sqlalchemy.orm import Session

from app.modules.notifications import repository


def list_my_notifications(
    db: Session,
    user_id: UUID,
    is_read: bool | None,
    page: int,
    page_size: int,
    offset: int | None = None,
) -> dict:
    items, total = repository.list_notifications(
        db,
        user_id,
        is_read,
        page,
        page_size,
        offset,
    )
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": ceil(total / page_size) if total else 0,
    }
