"""
SELA 樂透一路發 - 主入口

Railway 部署用（純 API 版本）
UI 功能之後透過前端框架（如 React/Vue）或獨立 Flet App 實現
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from app.config import settings
from app.main import app as api_app


# 建立主應用
main_app = FastAPI(
    title=settings.app_name,
    description="團購彩券系統",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS 設定
main_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 掛載 API
main_app.mount("/api", api_app)


@main_app.get("/", response_class=HTMLResponse)
async def root():
    """首頁 - 顯示系統狀態"""
    return """
    <!DOCTYPE html>
    <html lang="zh-TW">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>🎰 SELA 樂透一路發</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                color: #fff;
            }
            .container {
                text-align: center;
                padding: 40px;
                background: rgba(255,255,255,0.05);
                border-radius: 20px;
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255,255,255,0.1);
                max-width: 500px;
            }
            .logo { font-size: 64px; margin-bottom: 20px; }
            h1 {
                font-size: 32px;
                margin-bottom: 10px;
                background: linear-gradient(90deg, #FA7A35, #FFB347);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            }
            .subtitle { color: #888; margin-bottom: 30px; }
            .status {
                display: inline-block;
                padding: 8px 20px;
                background: #2ecc71;
                border-radius: 20px;
                font-size: 14px;
                margin-bottom: 30px;
            }
            .links { display: flex; gap: 15px; justify-content: center; flex-wrap: wrap; }
            .links a {
                padding: 12px 24px;
                background: #FA7A35;
                color: white;
                text-decoration: none;
                border-radius: 8px;
                transition: all 0.3s;
            }
            .links a:hover { background: #e06620; transform: translateY(-2px); }
            .links a.secondary { background: rgba(255,255,255,0.1); }
            .links a.secondary:hover { background: rgba(255,255,255,0.2); }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="logo">🎰</div>
            <h1>SELA 樂透一路發</h1>
            <p class="subtitle">團購彩券系統 API</p>
            <div class="status">✓ 系統運行中</div>
            <div class="links">
                <a href="/api/docs">📚 API 文件</a>
                <a href="/api/v1/health" class="secondary">❤️ 健康檢查</a>
            </div>
        </div>
    </body>
    </html>
    """


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
