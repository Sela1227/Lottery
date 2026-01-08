"""
SELA 樂透一路發 - LINE Login 服務
"""
import secrets
from typing import Optional
import httpx

from app.config import settings


class LineAuthService:
    """LINE Login 服務"""
    
    AUTH_URL = "https://access.line.me/oauth2/v2.1/authorize"
    TOKEN_URL = "https://api.line.me/oauth2/v2.1/token"
    PROFILE_URL = "https://api.line.me/v2/profile"
    
    @staticmethod
    def generate_state() -> str:
        """產生 CSRF 防護用的 state 參數"""
        return secrets.token_urlsafe(32)
    
    @classmethod
    def get_auth_url(cls, state: str) -> str:
        """
        產生 LINE 授權 URL
        
        Args:
            state: CSRF 防護用的隨機字串
        
        Returns:
            LINE 授權頁面 URL
        """
        params = {
            "response_type": "code",
            "client_id": settings.line_channel_id,
            "redirect_uri": settings.line_callback_url,
            "state": state,
            "scope": "profile openid",
        }
        query = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{cls.AUTH_URL}?{query}"
    
    @classmethod
    async def get_token(cls, code: str) -> Optional[dict]:
        """
        用授權碼換取 Access Token
        
        Args:
            code: LINE 回傳的授權碼
        
        Returns:
            Token 資訊，包含 access_token, id_token 等
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    cls.TOKEN_URL,
                    data={
                        "grant_type": "authorization_code",
                        "code": code,
                        "redirect_uri": settings.line_callback_url,
                        "client_id": settings.line_channel_id,
                        "client_secret": settings.line_channel_secret,
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    print(f"LINE Token 取得失敗: {response.status_code} - {response.text}")
                    return None
                    
            except httpx.RequestError as e:
                print(f"LINE Token 請求錯誤: {e}")
                return None
    
    @classmethod
    async def get_profile(cls, access_token: str) -> Optional[dict]:
        """
        取得用戶資料
        
        Args:
            access_token: LINE Access Token
        
        Returns:
            用戶資料，包含 userId, displayName, pictureUrl 等
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    cls.PROFILE_URL,
                    headers={"Authorization": f"Bearer {access_token}"},
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    print(f"LINE Profile 取得失敗: {response.status_code} - {response.text}")
                    return None
                    
            except httpx.RequestError as e:
                print(f"LINE Profile 請求錯誤: {e}")
                return None


# 全域實例
line_auth = LineAuthService()
