from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_notif: UUID
    title: str | None
    message: str
    sent_at: datetime | None
    entity_type: str | None
    entity_id: UUID | None
    is_read: bool
    created_at: datetime
    updated_at: datetime


class NotificationPageResponse(BaseModel):
    items: list[NotificationResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
