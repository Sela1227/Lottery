"""
SELA 樂透一路發 - LINE Notify 服務
"""
import secrets
from typing import Optional
import httpx

from app.config import settings


class LineNotifyService:
    """LINE Notify 服務"""
    
    AUTH_URL = "https://notify-bot.line.me/oauth/authorize"
    TOKEN_URL = "https://notify-bot.line.me/oauth/token"
    NOTIFY_URL = "https://notify-api.line.me/api/notify"
    STATUS_URL = "https://notify-api.line.me/api/status"
    REVOKE_URL = "https://notify-api.line.me/api/revoke"
    
    @staticmethod
    def generate_state() -> str:
        """產生 CSRF 防護用的 state 參數"""
        return secrets.token_urlsafe(32)
    
    @classmethod
    def get_auth_url(cls, state: str, callback_url: str = None) -> str:
        """
        產生 LINE Notify 授權 URL
        
        Args:
            state: CSRF 防護用的隨機字串
            callback_url: 回調 URL（可選）
        
        Returns:
            LINE Notify 授權頁面 URL
        """
        redirect_uri = callback_url or f"{settings.app_url}/api/v1/notify/callback"
        
        params = {
            "response_type": "code",
            "client_id": settings.line_notify_client_id,
            "redirect_uri": redirect_uri,
            "scope": "notify",
            "state": state,
        }
        query = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{cls.AUTH_URL}?{query}"
    
    @classmethod
    async def get_access_token(cls, code: str, callback_url: str = None) -> Optional[str]:
        """
        用授權碼換取 access token
        
        Args:
            code: LINE Notify 授權碼
            callback_url: 回調 URL（必須與授權時相同）
        
        Returns:
            access token 或 None
        """
        redirect_uri = callback_url or f"{settings.app_url}/api/v1/notify/callback"
        
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "client_id": settings.line_notify_client_id,
            "client_secret": settings.line_notify_client_secret,
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    cls.TOKEN_URL,
                    data=data,
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result.get("access_token")
                else:
                    print(f"LINE Notify token error: {response.status_code} - {response.text}")
                    return None
            except Exception as e:
                print(f"LINE Notify token exception: {e}")
                return None
    
    @classmethod
    async def check_status(cls, access_token: str) -> Optional[dict]:
        """
        檢查 token 狀態
        
        Returns:
            狀態資訊或 None
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    cls.STATUS_URL,
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                
                if response.status_code == 200:
                    return response.json()
                return None
            except Exception as e:
                print(f"LINE Notify status error: {e}")
                return None
    
    @classmethod
    async def send_notify(
        cls,
        access_token: str,
        message: str,
        image_url: str = None,
        sticker_package_id: int = None,
        sticker_id: int = None
    ) -> bool:
        """
        發送 LINE Notify 通知
        
        Args:
            access_token: 用戶的 LINE Notify token
            message: 訊息內容（最多 1000 字元）
            image_url: 圖片 URL（可選）
            sticker_package_id: 貼圖包 ID（可選）
            sticker_id: 貼圖 ID（可選）
        
        Returns:
            是否成功
        """
        data = {"message": message[:1000]}
        
        if image_url:
            data["imageThumbnail"] = image_url
            data["imageFullsize"] = image_url
        
        if sticker_package_id and sticker_id:
            data["stickerPackageId"] = sticker_package_id
            data["stickerId"] = sticker_id
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    cls.NOTIFY_URL,
                    data=data,
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Content-Type": "application/x-www-form-urlencoded"
                    }
                )
                
                return response.status_code == 200
            except Exception as e:
                print(f"LINE Notify send error: {e}")
                return False
    
    @classmethod
    async def revoke_token(cls, access_token: str) -> bool:
        """
        撤銷 access token
        
        Returns:
            是否成功
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    cls.REVOKE_URL,
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Content-Type": "application/x-www-form-urlencoded"
                    }
                )
                
                return response.status_code == 200
            except Exception as e:
                print(f"LINE Notify revoke error: {e}")
                return False


# 單例
line_notify = LineNotifyService()
