"""
SELA 樂透一路發 - API 應用程式
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.health import router as health_router
from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router
from app.api.v1.series import router as series_router
from app.api.v1.groups import router as groups_router
from app.api.v1.admin import router as admin_router
from app.api.v1.lottery import router as lottery_router
from app.api.v1.lottery_types import router as lottery_types_router  # 新增
from app.api.v1.statistics import router as statistics_router
from app.api.v1.wallet import router as wallet_router
from app.api.v1.personal import router as personal_router
from app.api.v1.achievements import router as achievements_router
from app.api.v1.stats import router as stats_router
from app.api.v1.check import router as check_router  # 自動對獎


def create_api_app() -> FastAPI:
    """創建 API FastAPI 應用"""
    application = FastAPI(
        title="SELA 樂透一路發 API",
        description="線上彩券集資系統 API",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )
    
    # CORS
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 註冊路由
    application.include_router(health_router, prefix="/v1")
    application.include_router(auth_router, prefix="/v1")
    application.include_router(users_router, prefix="/v1")
    application.include_router(series_router, prefix="/v1")
    application.include_router(groups_router, prefix="/v1")
    application.include_router(admin_router, prefix="/v1")
    application.include_router(lottery_router, prefix="/v1")
    application.include_router(lottery_types_router, prefix="/v1")  # 新增：彩種 API
    application.include_router(statistics_router, prefix="/v1")
    application.include_router(wallet_router, prefix="/v1")
    application.include_router(personal_router, prefix="/v1")
    application.include_router(achievements_router, prefix="/v1")
    application.include_router(stats_router, prefix="/v1")
    application.include_router(check_router, prefix="/v1")  # 自動對獎
    
    return application


# 匯出為 app（根目錄 main.py 期望這個名稱）
app = create_api_app()

# 也保留 api_app 作為別名
api_app = app
