from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.notifications.models import Notification


def list_notifications(
    db: Session,
    user_id: UUID,
    is_read: bool | None,
    page: int,
    page_size: int,
    offset: int | None = None,
) -> tuple[list[Notification], int]:
    query = select(Notification).where(Notification.id_user == user_id)

    if is_read is not None:
        query = query.where(Notification.is_read.is_(is_read))

    count_query = select(func.count()).select_from(query.subquery())
    total = db.scalar(count_query) or 0

    effective_offset = (
        offset if offset is not None else (page - 1) * page_size
    )
    query = query.order_by(
        Notification.sent_at.desc().nullsfirst(),
        Notification.created_at.desc(),
    )
    items = list(db.scalars(query.offset(effective_offset).limit(page_size)).all())
    return items, total
