"""
SELA 樂透一路發 - 主入口

Railway 部署用,整合 Web UI 和 FastAPI
"""
import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.config import settings
from app.main import app as api_app


# 建立主應用
main_app = FastAPI(
    title=settings.app_name,
    description="團購彩券系統",
    version="2.0.0",
    docs_url=None,
    redoc_url=None,
)

# CORS 設定
main_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 靜態檔案目錄
STATIC_DIR = Path(__file__).parent / "static"


# 掛載 API
main_app.mount("/api", api_app)


# ==================== 頁面路由 ====================

@main_app.get("/")
async def index():
    """首頁(登入頁)"""
    return FileResponse(STATIC_DIR / "index.html")


@main_app.get("/dashboard")
async def dashboard():
    """儀表板"""
    return FileResponse(STATIC_DIR / "dashboard.html")


@main_app.get("/series")
async def series_list():
    """系列團列表"""
    return FileResponse(STATIC_DIR / "series.html")


@main_app.get("/series/{series_id}")
async def series_detail(series_id: int):
    """系列團詳情"""
    return FileResponse(STATIC_DIR / "series-detail.html")


@main_app.get("/group/{group_id}")
async def group_detail(group_id: int):
    """單期團詳情"""
    return FileResponse(STATIC_DIR / "group-detail.html")


# ==================== 管理員後台 ====================

@main_app.get("/admin")
async def admin_panel():
    """管理員後台"""
    return FileResponse(STATIC_DIR / "admin.html")


# ==================== 未來頁面(Step 3+)====================

@main_app.get("/statistics")
async def statistics():
    """統計報表(Step 3)"""
    return FileResponse(STATIC_DIR / "coming-soon.html")


@main_app.get("/wallet")
async def wallet():
    """錢包(Step 3)"""
    return FileResponse(STATIC_DIR / "coming-soon.html")


@main_app.get("/personal")
async def personal():
    """個人彩券(Step 3)"""
    return FileResponse(STATIC_DIR / "coming-soon.html")


@main_app.get("/settings")
async def user_settings():
    """設定(Step 4)"""
    return FileResponse(STATIC_DIR / "coming-soon.html")


# 掛載靜態檔案(放在路由之後)
if STATIC_DIR.exists():
    main_app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.environ.get("PORT", 8000))
    
    print(f"""
    ╔══════════════════════════════════════╗
    ║   🎰 SELA 樂透一路發                 ║
    ║   ─────────────────────────────      ║
    ║   環境: {settings.app_env:<28}║
    ║   URL:  http://localhost:{port:<13}║
    ║   API:  http://localhost:{port}/api/docs  ║
    ╚══════════════════════════════════════╝
    """)
    
    uvicorn.run(
        "main:main_app",
        host="0.0.0.0",
        port=port,
        reload=not settings.is_production,
    )
