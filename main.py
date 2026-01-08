"""
SELA 樂透一路發 - 主入口

Railway 部署用，整合 Flet UI 和 FastAPI
"""
import os
import flet as ft
import flet.fastapi as flet_fastapi
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.main import app as api_app


# 建立主應用
main_app = FastAPI(
    title=settings.app_name,
    description="團購彩券系統",
    version="1.0.0",
    docs_url=None,  # 使用 API 子應用的 docs
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


# Flet UI 主函數（Flet 0.70+ 需要 async）
async def flet_main(page: ft.Page):
    """Flet 主函數"""
    from ui.main import App
    App(page)


# Flet before_main 函數（可選的初始化）
async def before_main(page: ft.Page):
    """Flet 頁面初始化前的設定"""
    pass


# 掛載 API
main_app.mount("/api", api_app)

# 掛載 Flet UI（Flet 0.70+ 語法）
main_app.mount("/", flet_fastapi.app(flet_main, before_main))


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.environ.get("PORT", 8000))
    
    print(f"""
    ╔══════════════════════════════════════╗
    ║   🎰 SELA 樂透一路發                 ║
    ║   ─────────────────────────          ║
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
