"""
SELA 樂透一路發 - FastAPI 主入口
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from app.config import settings
from app.core.database import init_database
from app.api.v1 import health, auth, users
from app.api.v1.series import router as series_router
from app.api.v1.groups import router as groups_router
from app.api.v1.admin import router as admin_router
from app.api.v1.lottery import router as lottery_router
from app.api.v1.stats import router as stats_router

# 可選的 router（檔案可能不存在）
try:
    from app.api.v1.statistics import router as statistics_router
    HAS_STATISTICS = True
except ImportError:
    HAS_STATISTICS = False

try:
    from app.api.v1.wallet import router as wallet_router
    HAS_WALLET = True
except ImportError:
    HAS_WALLET = False

try:
    from app.api.v1.personal import router as personal_router
    HAS_PERSONAL = True
except ImportError:
    HAS_PERSONAL = False

try:
    from app.api.v1.achievements import router as achievements_router
    HAS_ACHIEVEMENTS = True
except ImportError:
    HAS_ACHIEVEMENTS = False


# 建立 FastAPI 應用
app = FastAPI(
    title=settings.app_name,
    description="集資彩券系統 API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS 設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 啟動事件
@app.on_event("startup")
async def startup_event():
    """應用啟動時初始化"""
    init_database()


# 註冊路由
app.include_router(health.router, prefix="/v1")
app.include_router(auth.router, prefix="/v1")
app.include_router(users.router, prefix="/v1")
app.include_router(series_router, prefix="/v1")
app.include_router(groups_router, prefix="/v1")
app.include_router(admin_router, prefix="/v1")
app.include_router(lottery_router, prefix="/v1")
app.include_router(stats_router, prefix="/v1")  # Step 4-3: 號碼統計

# 可選路由
if HAS_STATISTICS:
    app.include_router(statistics_router, prefix="/v1")
if HAS_WALLET:
    app.include_router(wallet_router, prefix="/v1")
if HAS_PERSONAL:
    app.include_router(personal_router, prefix="/v1")
if HAS_ACHIEVEMENTS:
    app.include_router(achievements_router, prefix="/v1")
