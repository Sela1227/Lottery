"""
SELA 樂透一路發 - FastAPI 主入口
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.core.database import init_database
from app.api.v1 import health, auth, users


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


# 註冊路由（前綴改為 /v1，因為外層已經有 /api）
app.include_router(health.router, prefix="/v1")
app.include_router(auth.router, prefix="/v1")
app.include_router(users.router, prefix="/v1")


@app.on_event("startup")
async def startup():
    """應用啟動時執行"""
    print(f"🎰 {settings.app_name} API 啟動中...")
    print(f"   環境: {settings.app_env}")
    
    # 初始化資料庫（建立表格）
    init_database()
    print("   資料庫: 已連線")


@app.on_event("shutdown")
async def shutdown():
    """應用關閉時執行"""
    print(f"🎰 {settings.app_name} API 已關閉")


@app.get("/")
async def root():
    """API 根路徑"""
    return {
        "app": settings.app_name,
        "version": "1.0.0",
        "status": "running",
        "docs": "/api/docs"
    }
