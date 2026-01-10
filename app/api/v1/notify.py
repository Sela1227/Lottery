"""
SELA 樂透一路發 - 通知 API
"""
from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.models.user import User
from app.services.line_notify import line_notify
from app.config import settings


router = APIRouter(prefix="/notify", tags=["Notifications"])


# 暫存 state（正式環境應用 Redis）
_state_store: dict[str, int] = {}  # state -> user_id


# ==================== Schema ====================

class NotifySettingsResponse(BaseModel):
    """通知設定回應"""
    line_notify_enabled: bool
    line_notify_connected: bool
    notify_draw_reminder: bool
    notify_win_alert: bool
    notify_settlement: bool
    connected_at: Optional[datetime] = None


class NotifySettingsUpdate(BaseModel):
    """通知設定更新"""
    notify_draw_reminder: Optional[bool] = None
    notify_win_alert: Optional[bool] = None
    notify_settlement: Optional[bool] = None


class SendNotifyRequest(BaseModel):
    """發送通知請求"""
    message: str
    user_ids: Optional[List[int]] = None  # None = 發給所有人


# ==================== API 端點 ====================

@router.get("/settings", response_model=NotifySettingsResponse)
async def get_notify_settings(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """取得通知設定"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用戶不存在")
    
    # 檢查是否已設定 LINE Notify
    line_notify_enabled = bool(settings.line_notify_client_id)
    line_notify_connected = bool(user.line_notify_token)
    
    return NotifySettingsResponse(
        line_notify_enabled=line_notify_enabled,
        line_notify_connected=line_notify_connected,
        notify_draw_reminder=user.notify_draw_reminder if hasattr(user, 'notify_draw_reminder') else True,
        notify_win_alert=user.notify_win_alert if hasattr(user, 'notify_win_alert') else True,
        notify_settlement=user.notify_settlement if hasattr(user, 'notify_settlement') else True,
        connected_at=user.line_notify_connected_at if hasattr(user, 'line_notify_connected_at') else None
    )


@router.put("/settings", response_model=NotifySettingsResponse)
async def update_notify_settings(
    data: NotifySettingsUpdate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """更新通知設定"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用戶不存在")
    
    # 更新設定
    if data.notify_draw_reminder is not None and hasattr(user, 'notify_draw_reminder'):
        user.notify_draw_reminder = data.notify_draw_reminder
    if data.notify_win_alert is not None and hasattr(user, 'notify_win_alert'):
        user.notify_win_alert = data.notify_win_alert
    if data.notify_settlement is not None and hasattr(user, 'notify_settlement'):
        user.notify_settlement = data.notify_settlement
    
    db.commit()
    db.refresh(user)
    
    return await get_notify_settings(user_id, db)


@router.get("/line/connect")
async def connect_line_notify(
    user_id: int = Depends(get_current_user_id)
):
    """
    開始 LINE Notify 連結流程
    
    重導向到 LINE Notify 授權頁面
    """
    if not settings.line_notify_client_id:
        raise HTTPException(status_code=503, detail="LINE Notify 尚未設定")
    
    state = line_notify.generate_state()
    _state_store[state] = user_id
    
    auth_url = line_notify.get_auth_url(state)
    return RedirectResponse(url=auth_url)


@router.get("/callback")
async def line_notify_callback(
    code: str = Query(None),
    state: str = Query(None),
    error: str = Query(None),
    error_description: str = Query(None),
    db: Session = Depends(get_db)
):
    """
    LINE Notify 授權回調
    """
    # 錯誤處理
    if error:
        return RedirectResponse(
            url=f"/settings?notify_error={error_description or error}"
        )
    
    if not code or not state:
        return RedirectResponse(url="/settings?notify_error=missing_params")
    
    # 驗證 state
    user_id = _state_store.pop(state, None)
    if not user_id:
        return RedirectResponse(url="/settings?notify_error=invalid_state")
    
    # 取得 access token
    access_token = await line_notify.get_access_token(code)
    if not access_token:
        return RedirectResponse(url="/settings?notify_error=token_failed")
    
    # 儲存 token
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.line_notify_token = access_token
        if hasattr(user, 'line_notify_connected_at'):
            user.line_notify_connected_at = datetime.utcnow()
        db.commit()
        
        # 發送歡迎訊息
        await line_notify.send_notify(
            access_token,
            "\n🎰 SELA 樂透一路發\n\n✅ LINE Notify 連結成功！\n\n您將收到：\n• 開獎提醒\n• 中獎通知\n• 結算通知\n\n祝您好運！🍀"
        )
    
    return RedirectResponse(url="/settings?notify_success=1")


@router.post("/line/disconnect")
async def disconnect_line_notify(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    解除 LINE Notify 連結
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用戶不存在")
    
    if user.line_notify_token:
        # 撤銷 token
        await line_notify.revoke_token(user.line_notify_token)
        user.line_notify_token = None
        if hasattr(user, 'line_notify_connected_at'):
            user.line_notify_connected_at = None
        db.commit()
    
    return {"success": True, "message": "已解除連結"}


@router.post("/test")
async def send_test_notify(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    發送測試通知
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.line_notify_token:
        raise HTTPException(status_code=400, detail="尚未連結 LINE Notify")
    
    success = await line_notify.send_notify(
        user.line_notify_token,
        f"\n🔔 測試通知\n\n這是一則來自 SELA 樂透一路發的測試訊息。\n\n時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    
    if success:
        return {"success": True, "message": "測試通知已發送"}
    else:
        raise HTTPException(status_code=500, detail="發送失敗")


# ==================== 通知發送工具函式 ====================

async def send_draw_reminder(db: Session, lottery_type: str, draw_date: str):
    """
    發送開獎提醒
    
    Args:
        db: 資料庫 session
        lottery_type: 彩種名稱
        draw_date: 開獎日期
    """
    message = f"\n🎰 開獎提醒\n\n{lottery_type} 即將開獎！\n📅 {draw_date}\n\n祝您好運！🍀"
    
    users = db.query(User).filter(
        User.line_notify_token.isnot(None),
        User.is_active == True
    ).all()
    
    for user in users:
        if hasattr(user, 'notify_draw_reminder') and not user.notify_draw_reminder:
            continue
        await line_notify.send_notify(user.line_notify_token, message)


async def send_win_notification(db: Session, user_id: int, series_name: str, period: int, prize: float):
    """
    發送中獎通知
    
    Args:
        db: 資料庫 session
        user_id: 用戶 ID
        series_name: 系列團名稱
        period: 期數
        prize: 獎金
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.line_notify_token:
        return
    
    if hasattr(user, 'notify_win_alert') and not user.notify_win_alert:
        return
    
    message = f"\n🎉 恭喜中獎！\n\n{series_name} 第 {period} 期\n💰 您的獎金：${prize:,.0f}\n\n快去查看詳情吧！"
    
    await line_notify.send_notify(user.line_notify_token, message)


async def send_settlement_notification(db: Session, user_id: int, series_name: str, period: int, share: float):
    """
    發送結算通知
    
    Args:
        db: 資料庫 session
        user_id: 用戶 ID
        series_name: 系列團名稱
        period: 期數
        share: 分配金額
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.line_notify_token:
        return
    
    if hasattr(user, 'notify_settlement') and not user.notify_settlement:
        return
    
    message = f"\n💵 結算通知\n\n{series_name} 第 {period} 期已結算\n📊 您的分配：${share:,.0f}\n\n查看詳情請登入系統。"
    
    await line_notify.send_notify(user.line_notify_token, message)


async def send_broadcast(db: Session, message: str, admin_only: bool = False):
    """
    發送系統公告
    
    Args:
        db: 資料庫 session
        message: 公告內容
        admin_only: 是否只發給管理員
    """
    query = db.query(User).filter(
        User.line_notify_token.isnot(None),
        User.is_active == True
    )
    
    if admin_only:
        query = query.filter(User.role == "admin")
    
    users = query.all()
    
    full_message = f"\n📢 系統公告\n\n{message}"
    
    for user in users:
        await line_notify.send_notify(user.line_notify_token, full_message)
