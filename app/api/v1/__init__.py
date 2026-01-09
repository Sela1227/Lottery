"""
SELA 樂透一路發 - API v1 路由
"""
from app.api.v1.health import router as health_router
from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router
from app.api.v1.series import router as series_router
from app.api.v1.groups import router as groups_router
from app.api.v1.admin import router as admin_router
from app.api.v1.wallet import router as wallet_router
from app.api.v1.statistics import router as statistics_router

__all__ = [
    "health_router",
    "auth_router",
    "users_router",
    "series_router",
    "groups_router",
    "admin_router",
    "wallet_router",
    "statistics_router",
]
