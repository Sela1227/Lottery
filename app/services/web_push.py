"""
SELA 樂透一路發 - Web Push 通知服務
"""
import json
from typing import Optional, List
from pywebpush import webpush, WebPushException

from app.config import settings


class WebPushService:
    """Web Push 通知服務"""
    
    @classmethod
    def send_notification(
        cls,
        subscription_info: dict,
        title: str,
        body: str,
        icon: str = "/static/logo.jpg",
        url: str = "/dashboard",
        tag: str = None,
        data: dict = None
    ) -> bool:
        """
        發送 Web Push 通知
        
        Args:
            subscription_info: 用戶的推播訂閱資訊 (endpoint, keys)
            title: 通知標題
            body: 通知內容
            icon: 圖示 URL
            url: 點擊通知後開啟的 URL
            tag: 通知標籤（相同 tag 會取代舊通知）
            data: 額外資料
        
        Returns:
            是否成功
        """
        if not settings.vapid_private_key:
            print("VAPID private key not configured")
            return False
        
        payload = {
            "title": title,
            "body": body,
            "icon": icon,
            "badge": "/static/badge.png",
            "url": url,
            "timestamp": None,
        }
        
        if tag:
            payload["tag"] = tag
        
        if data:
            payload["data"] = data
        
        try:
            webpush(
                subscription_info=subscription_info,
                data=json.dumps(payload),
                vapid_private_key=settings.vapid_private_key,
                vapid_claims={
                    "sub": f"mailto:{settings.vapid_email or 'admin@example.com'}"
                }
            )
            return True
        except WebPushException as e:
            print(f"Web Push error: {e}")
            # 如果訂閱已過期或無效，回傳特殊錯誤
            if e.response and e.response.status_code in [404, 410]:
                return None  # 表示訂閱已失效，需要刪除
            return False
        except Exception as e:
            print(f"Web Push unexpected error: {e}")
            return False
    
    @classmethod
    def send_to_multiple(
        cls,
        subscriptions: List[dict],
        title: str,
        body: str,
        **kwargs
    ) -> dict:
        """
        發送給多個訂閱者
        
        Returns:
            {"success": 成功數, "failed": 失敗數, "expired": 過期數}
        """
        results = {"success": 0, "failed": 0, "expired": []}
        
        for sub in subscriptions:
            result = cls.send_notification(
                subscription_info=sub["subscription_info"],
                title=title,
                body=body,
                **kwargs
            )
            
            if result is True:
                results["success"] += 1
            elif result is None:
                results["expired"].append(sub.get("id"))
            else:
                results["failed"] += 1
        
        return results


# 通知模板
class NotificationTemplates:
    """通知訊息模板"""
    
    @staticmethod
    def draw_reminder(lottery_type: str, draw_date: str) -> dict:
        """開獎提醒"""
        return {
            "title": "🎰 開獎提醒",
            "body": f"{lottery_type} 即將開獎！\n📅 {draw_date}",
            "tag": "draw-reminder",
            "url": "/lottery"
        }
    
    @staticmethod
    def win_notification(series_name: str, period: int, prize: float) -> dict:
        """中獎通知"""
        return {
            "title": "🎉 恭喜中獎！",
            "body": f"{series_name} 第 {period} 期\n💰 獎金：${prize:,.0f}",
            "tag": f"win-{series_name}-{period}",
            "url": "/statistics"
        }
    
    @staticmethod
    def settlement_notification(series_name: str, period: int, share: float) -> dict:
        """結算通知"""
        return {
            "title": "💵 結算完成",
            "body": f"{series_name} 第 {period} 期已結算\n📊 您的分配：${share:,.0f}",
            "tag": f"settle-{series_name}-{period}",
            "url": "/wallet"
        }
    
    @staticmethod
    def broadcast(message: str) -> dict:
        """系統公告"""
        return {
            "title": "📢 系統公告",
            "body": message,
            "tag": "broadcast",
            "url": "/dashboard"
        }


# 單例
web_push = WebPushService()
templates = NotificationTemplates()
