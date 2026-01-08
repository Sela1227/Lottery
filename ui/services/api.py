"""
SELA 樂透一路發 - API 呼叫服務
"""
import httpx
from typing import Optional, Any
from dataclasses import dataclass


@dataclass
class ApiResponse:
    """API 回應"""
    success: bool
    data: Optional[dict] = None
    error: Optional[str] = None
    status_code: int = 0


class ApiService:
    """API 呼叫服務"""
    
    def __init__(self, base_url: str = ""):
        self.base_url = base_url or "/api/v1"
        self.token: Optional[str] = None
    
    def set_token(self, token: str):
        """設定 JWT Token"""
        self.token = token
    
    def clear_token(self):
        """清除 Token"""
        self.token = None
    
    @property
    def _headers(self) -> dict:
        """取得請求標頭"""
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[dict] = None,
        params: Optional[dict] = None,
    ) -> ApiResponse:
        """發送請求"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.request(
                    method=method,
                    url=url,
                    json=data,
                    params=params,
                    headers=self._headers,
                    timeout=30.0,
                )
                
                if response.status_code >= 200 and response.status_code < 300:
                    return ApiResponse(
                        success=True,
                        data=response.json() if response.text else None,
                        status_code=response.status_code,
                    )
                else:
                    error_data = response.json() if response.text else {}
                    return ApiResponse(
                        success=False,
                        error=error_data.get("detail", f"錯誤 {response.status_code}"),
                        status_code=response.status_code,
                    )
                    
        except httpx.TimeoutException:
            return ApiResponse(success=False, error="請求逾時")
        except httpx.RequestError as e:
            return ApiResponse(success=False, error=f"網路錯誤: {str(e)}")
        except Exception as e:
            return ApiResponse(success=False, error=f"未知錯誤: {str(e)}")
    
    async def get(self, endpoint: str, params: Optional[dict] = None) -> ApiResponse:
        """GET 請求"""
        return await self._request("GET", endpoint, params=params)
    
    async def post(self, endpoint: str, data: Optional[dict] = None) -> ApiResponse:
        """POST 請求"""
        return await self._request("POST", endpoint, data=data)
    
    async def put(self, endpoint: str, data: Optional[dict] = None) -> ApiResponse:
        """PUT 請求"""
        return await self._request("PUT", endpoint, data=data)
    
    async def delete(self, endpoint: str) -> ApiResponse:
        """DELETE 請求"""
        return await self._request("DELETE", endpoint)
    
    # ========== 認證相關 ==========
    
    async def get_line_login_url(self) -> ApiResponse:
        """取得 LINE 登入 URL"""
        return await self.get("/auth/line/url")
    
    async def get_current_user(self) -> ApiResponse:
        """取得目前登入用戶"""
        return await self.get("/users/me")
    
    async def update_user(self, data: dict) -> ApiResponse:
        """更新用戶資料"""
        return await self.put("/users/me", data)
    
    async def get_wallet(self) -> ApiResponse:
        """取得錢包餘額"""
        return await self.get("/users/me/wallet")
    
    # ========== 健康檢查 ==========
    
    async def health_check(self) -> ApiResponse:
        """健康檢查"""
        return await self.get("/health")


# 全域 API 服務實例
api = ApiService()
