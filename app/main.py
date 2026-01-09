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
from app.api.v1.wallet import router as wallet_router
from app.api.v1.statistics import router as statistics_router


# 建立 FastAPI 應用
app = FastAPI(
    title=settings.app_name,
    description="團購彩券系統 API",
    version="1.0.0",
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
)

# CORS 設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if not settings.is_production else [settings.app_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 註冊 API 路由(前綴 /v1)
app.include_router(health.router, prefix="/v1")
app.include_router(auth.router, prefix="/v1")
app.include_router(users.router, prefix="/v1")
app.include_router(series_router, prefix="/v1")
app.include_router(groups_router, prefix="/v1")
app.include_router(admin_router, prefix="/v1")
app.include_router(wallet_router, prefix="/v1")
app.include_router(statistics_router, prefix="/v1")


@app.on_event("startup")
async def startup():
    """應用啟動時執行"""
    print(f"🎰 {settings.app_name} API 啟動中...")
    print(f"   環境: {settings.app_env}")
    
    # 初始化資料庫
    init_database()
    print("   資料庫: 已連線")
    
    # 初始化種子資料(彩種)
    from app.core.database import SessionLocal
    from app.models import LotteryType
    from app.models.lottery_type import DEFAULT_LOTTERY_TYPES
    
    db = SessionLocal()
    try:
        # 檢查是否需要初始化彩種
        count = db.query(LotteryType).count()
        if count == 0:
            print("   初始化彩種資料...")
            for lt_data in DEFAULT_LOTTERY_TYPES:
                lt = LotteryType(**lt_data)
                db.add(lt)
            db.commit()
            print(f"   彩種: 已建立 {len(DEFAULT_LOTTERY_TYPES)} 種")
        else:
            print(f"   彩種: 已存在 {count} 種")
    finally:
        db.close()
    
    print("   ✅ API 啟動完成")
