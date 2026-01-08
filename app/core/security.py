"""
SELA 樂透一路發 - 安全模組（JWT）
"""
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import jwt, JWTError
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.config import settings


# Bearer Token 安全方案
bearer_scheme = HTTPBearer(auto_error=False)


def create_access_token(user_id: int, extra_data: Optional[dict] = None) -> str:
    """
    建立 JWT Access Token
    
    Args:
        user_id: 用戶 ID
        extra_data: 額外資料（如 role, display_name）
    
    Returns:
        JWT Token 字串
    """
    expire = datetime.now(timezone.utc) + timedelta(seconds=settings.jwt_expires_seconds)
    
    payload = {
        "sub": str(user_id),
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access"
    }
    
    if extra_data:
        payload.update(extra_data)
    
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def verify_token(token: str) -> dict:
    """
    驗證 JWT Token
    
    Args:
        token: JWT Token 字串
    
    Returns:
        Token payload
    
    Raises:
        HTTPException: Token 無效或過期
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm]
        )
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token 無效: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"}
        )


async def get_current_user_id(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme)
) -> int:
    """
    取得目前登入用戶 ID（FastAPI 依賴注入）
    
    Returns:
        用戶 ID
    
    Raises:
        HTTPException: 未登入或 Token 無效
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="請先登入",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    payload = verify_token(credentials.credentials)
    user_id = payload.get("sub")
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token 格式錯誤"
        )
    
    return int(user_id)


async def get_optional_user_id(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme)
) -> Optional[int]:
    """
    取得目前登入用戶 ID（選擇性，未登入回傳 None）
    """
    if not credentials:
        return None
    
    try:
        payload = verify_token(credentials.credentials)
        user_id = payload.get("sub")
        return int(user_id) if user_id else None
    except HTTPException:
        return None
