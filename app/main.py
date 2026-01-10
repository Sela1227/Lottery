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
from app.api.v1.statistics import router as statistics_router
from app.api.v1.wallet import router as wallet_router


# 建立 FastAPI 應用
app = FastAPI(
    title=settings.app_name,
    description="團購彩券系統 API",
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
app.include_router(statistics_router, prefix="/v1")  # Step 3: 統計報表
app.include_router(wallet_router, prefix="/v1")      # Step 3: 錢包功能
