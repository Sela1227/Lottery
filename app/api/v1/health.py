"""
SELA 樂透一路發 - 健康檢查 API
"""
from fastapi import APIRouter
from datetime import datetime, timezone

from app.core.database import check_database_connection
from app.config import settings


router = APIRouter(prefix="/health", tags=["Health"])


@router.get("")
async def health_check():
    """健康檢查"""
    db_ok = check_database_connection()
    
    return {
        "status": "healthy" if db_ok else "unhealthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "app": settings.app_name,
        "environment": settings.app_env,
        "database": "connected" if db_ok else "disconnected"
    }


@router.get("/ping")
async def ping():
    """簡單的 ping 測試"""
    return {"pong": True}
