"""
SELA 樂透一路發 - 通知 API (Web Push)
"""
from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.models.user import User
from app.models.push_subscription import PushSubscription
from app.services.web_push import web_push, templates
from app.config import settings


router = APIRouter(prefix="/notify", tags=["Notifications"])


# ==================== Schema ====================

class NotifySettingsResponse(BaseModel):
    """通知設定回應"""
    push_enabled: bool  # 系統是否啟用 push
    subscribed: bool    # 用戶是否已訂閱
    subscription_count: int
    notify_draw_reminder: bool
    notify_win_alert: bool
    notify_settlement: bool
    vapid_public_key: Optional[str] = None


class NotifySettingsUpdate(BaseModel):
    """通知設定更新"""
    notify_draw_reminder: Optional[bool] = None
    notify_win_alert: Optional[bool] = None
    notify_settlement: Optional[bool] = None


class PushSubscriptionCreate(BaseModel):
    """建立推播訂閱"""
    endpoint: str
    p256dh: str
    auth: str
    device_name: Optional[str] = None


class SubscriptionResponse(BaseModel):
    """訂閱回應"""
    id: int
    device_name: Optional[str]
    created_at: datetime
    last_used_at: Optional[datetime]
    is_active: bool


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
    
    # 計算訂閱數
    subscription_count = db.query(PushSubscription).filter(
        PushSubscription.user_id == user_id,
        PushSubscription.is_active == True
    ).count()
    
    # 檢查系統是否啟用 push
    push_enabled = bool(settings.vapid_public_key and settings.vapid_private_key)
    
    return NotifySettingsResponse(
        push_enabled=push_enabled,
        subscribed=subscription_count > 0,
        subscription_count=subscription_count,
        notify_draw_reminder=user.notify_draw_reminder if hasattr(user, 'notify_draw_reminder') else True,
        notify_win_alert=user.notify_win_alert if hasattr(user, 'notify_win_alert') else True,
        notify_settlement=user.notify_settlement if hasattr(user, 'notify_settlement') else True,
        vapid_public_key=settings.vapid_public_key if push_enabled else None
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


@router.post("/subscribe")
async def subscribe_push(
    data: PushSubscriptionCreate,
    request: Request,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    訂閱推播通知
    """
    # 檢查是否已存在相同 endpoint
    existing = db.query(PushSubscription).filter(
        PushSubscription.endpoint == data.endpoint
    ).first()
    
    if existing:
        # 更新現有訂閱
        existing.user_id = user_id
        existing.p256dh_key = data.p256dh
        existing.auth_key = data.auth
        existing.is_active = True
        existing.last_used_at = datetime.utcnow()
        if data.device_name:
            existing.device_name = data.device_name
        db.commit()
        
        return {"success": True, "message": "訂閱已更新", "id": existing.id}
    
    # 建立新訂閱
    subscription = PushSubscription(
        user_id=user_id,
        endpoint=data.endpoint,
        p256dh_key=data.p256dh,
        auth_key=data.auth,
        device_name=data.device_name,
        user_agent=request.headers.get("user-agent"),
        is_active=True
    )
    
    db.add(subscription)
    db.commit()
    db.refresh(subscription)
    
    # 發送歡迎通知
    web_push.send_notification(
        subscription_info=subscription.subscription_info,
        title="🎰 SELA 樂透一路發",
        body="通知已啟用！您將收到開獎提醒、中獎通知等重要訊息。",
        url="/dashboard"
    )
    
    return {"success": True, "message": "訂閱成功", "id": subscription.id}


@router.delete("/subscribe")
async def unsubscribe_push(
    endpoint: str = Query(..., description="訂閱 endpoint"),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    取消推播訂閱
    """
    subscription = db.query(PushSubscription).filter(
        PushSubscription.endpoint == endpoint,
        PushSubscription.user_id == user_id
    ).first()
    
    if subscription:
        subscription.is_active = False
        db.commit()
    
    return {"success": True, "message": "已取消訂閱"}


@router.get("/subscriptions", response_model=List[SubscriptionResponse])
async def list_subscriptions(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    列出用戶的所有訂閱
    """
    subscriptions = db.query(PushSubscription).filter(
        PushSubscription.user_id == user_id,
        PushSubscription.is_active == True
    ).order_by(PushSubscription.created_at.desc()).all()
    
    return [
        SubscriptionResponse(
            id=s.id,
            device_name=s.device_name or "未命名裝置",
            created_at=s.created_at,
            last_used_at=s.last_used_at,
            is_active=s.is_active
        )
        for s in subscriptions
    ]


@router.delete("/subscriptions/{subscription_id}")
async def delete_subscription(
    subscription_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    刪除特定訂閱
    """
    subscription = db.query(PushSubscription).filter(
        PushSubscription.id == subscription_id,
        PushSubscription.user_id == user_id
    ).first()
    
    if not subscription:
        raise HTTPException(status_code=404, detail="訂閱不存在")
    
    db.delete(subscription)
    db.commit()
    
    return {"success": True, "message": "已刪除訂閱"}


@router.post("/test")
async def send_test_notification(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    發送測試通知
    """
    subscriptions = db.query(PushSubscription).filter(
        PushSubscription.user_id == user_id,
        PushSubscription.is_active == True
    ).all()
    
    if not subscriptions:
        raise HTTPException(status_code=400, detail="尚未啟用推播通知")
    
    success_count = 0
    for sub in subscriptions:
        result = web_push.send_notification(
            subscription_info=sub.subscription_info,
            title="🔔 測試通知",
            body=f"這是一則測試訊息\n時間：{datetime.now().strftime('%H:%M:%S')}",
            url="/settings"
        )
        if result:
            success_count += 1
            sub.last_used_at = datetime.utcnow()
    
    db.commit()
    
    return {
        "success": True,
        "message": f"已發送 {success_count}/{len(subscriptions)} 則通知"
    }


# ==================== 通知發送工具函式 ====================

async def send_draw_reminder(db: Session, lottery_type: str, draw_date: str):
    """
    發送開獎提醒給所有訂閱用戶
    """
    template = templates.draw_reminder(lottery_type, draw_date)
    
    # 取得所有啟用開獎提醒的用戶訂閱
    subscriptions = db.query(PushSubscription).join(User).filter(
        PushSubscription.is_active == True,
        User.is_active == True,
        User.notify_draw_reminder == True
    ).all()
    
    results = web_push.send_to_multiple(
        [{"id": s.id, "subscription_info": s.subscription_info} for s in subscriptions],
        **template
    )
    
    # 清理過期訂閱
    if results["expired"]:
        db.query(PushSubscription).filter(
            PushSubscription.id.in_(results["expired"])
        ).update({"is_active": False}, synchronize_session=False)
        db.commit()
    
    return results


async def send_win_notification(db: Session, user_id: int, series_name: str, period: int, prize: float):
    """
    發送中獎通知給特定用戶
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not getattr(user, 'notify_win_alert', True):
        return
    
    template = templates.win_notification(series_name, period, prize)
    
    subscriptions = db.query(PushSubscription).filter(
        PushSubscription.user_id == user_id,
        PushSubscription.is_active == True
    ).all()
    
    for sub in subscriptions:
        web_push.send_notification(
            subscription_info=sub.subscription_info,
            **template
        )


async def send_settlement_notification(db: Session, user_id: int, series_name: str, period: int, share: float):
    """
    發送結算通知給特定用戶
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not getattr(user, 'notify_settlement', True):
        return
    
    template = templates.settlement_notification(series_name, period, share)
    
    subscriptions = db.query(PushSubscription).filter(
        PushSubscription.user_id == user_id,
        PushSubscription.is_active == True
    ).all()
    
    for sub in subscriptions:
        web_push.send_notification(
            subscription_info=sub.subscription_info,
            **template
        )


async def send_broadcast(db: Session, message: str, admin_only: bool = False):
    """
    發送系統公告給所有用戶
    """
    template = templates.broadcast(message)
    
    query = db.query(PushSubscription).join(User).filter(
        PushSubscription.is_active == True,
        User.is_active == True
    )
    
    if admin_only:
        query = query.filter(User.role == "admin")
    
    subscriptions = query.all()
    
    return web_push.send_to_multiple(
        [{"id": s.id, "subscription_info": s.subscription_info} for s in subscriptions],
        **template
    )
