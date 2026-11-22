from fastapi import APIRouter

from app.api import health, public
from app.modules.auth.router import admin_router as auth_admin_router
from app.modules.auth.router import router as auth_router
from app.modules.auth.router import users_router

from app.modules.beneficiaries.router import router as beneficiaries_router
from app.modules.budget.router import router as budget_router
from app.modules.campaigns.router import (
    campaign_catalog_router,
    events_router,
    event_catalog_router,
    router as campaigns_router,
)
from app.modules.dashboard.router import router as dashboard_router
from app.modules.distributions.router import router as distributions_router
from app.modules.financial_donations.router import router as financial_donations_router

from app.modules.receipts.router import router as receipts_router
from app.modules.stock.router import router as stock_router
from app.modules.volunteers.router import router as volunteers_router
from app.modules.natural_donations.router import router as natural_donations_router, admin_router as natural_admin_router
from app.modules.treasury.router import router as treasury_router
api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(public.router)

for module_router in (
    auth_router,
    auth_admin_router,
    campaigns_router,
    campaign_catalog_router,
    events_router,
    event_catalog_router,
    financial_donations_router,
    natural_donations_router,
    natural_admin_router,
    receipts_router,
    stock_router,
    beneficiaries_router,
    distributions_router,
    budget_router,
    treasury_router,
    volunteers_router,
    dashboard_router,
    users_router,
):
    api_router.include_router(module_router)