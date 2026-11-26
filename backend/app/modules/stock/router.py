"""Endpoints HTTP du module stock."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.dependencies import require_stock_manager_or_admin
from app.database import get_db
from app.modules.auth.models import User
from app.modules.stock import service as stock_service
from app.modules.stock.schemas import StockItemOut

router = APIRouter(prefix="/stocks", tags=["stock"])

DbSession = Annotated[Session, Depends(get_db)]
StockStaff = Annotated[User, Depends(require_stock_manager_or_admin)]


@router.get("", response_model=list[StockItemOut])
def stk01_list_stock_items(
    session: DbSession,
    user: StockStaff,
    object_type_id: Annotated[UUID | None, Query()] = None,
    category: Annotated[str | None, Query(min_length=1)] = None,
    search: Annotated[str | None, Query(min_length=1)] = None,
):
    """STK-01 : Liste les articles en stock avec filtres par type et recherche."""
    return stock_service.list_stock_items(
        session,
        object_type_id=object_type_id,
        category=category,
        search=search,
    )
