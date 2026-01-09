"""
SELA 樂透一路發 - 安全模組
"""
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.config import settings
from app.core.database import get_db


bearer_scheme = HTTPBearer(auto_error=False)


def create_access_token(user_id: int, extra_data: dict = None) -> str:
    """
    建立 JWT Access Token
    
    Args:
        user_id: 用戶 ID
        extra_data: 額外資料(如 display_name, role)
    
    Returns:
        JWT Token 字串
    """
    expire = datetime.now(timezone.utc) + timedelta(seconds=settings.jwt_expires_seconds)
    
    payload = {
        "sub": str(user_id),
        "exp": expire,
        "iat": datetime.now(timezone.utc),
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
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token 無效或已過期",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)
) -> int:
    """
    取得目前登入用戶 ID
    
    依賴注入用,驗證 Token 並回傳用戶 ID
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供認證資訊",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    payload = verify_token(credentials.credentials)
    user_id = payload.get("sub")
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token 格式錯誤"
        )
    
    return int(user_id)


async def get_current_user_with_role(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)
) -> dict:
    """
    取得目前登入用戶 ID 和角色
    
    Returns:
        {"user_id": int, "role": str}
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供認證資訊",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    payload = verify_token(credentials.credentials)
    user_id = payload.get("sub")
    role = payload.get("role", "user")
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token 格式錯誤"
        )
    
    return {"user_id": int(user_id), "role": role}


async def require_admin(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db)
) -> int:
    """
    要求管理員權限
    
    從資料庫即時查詢用戶角色，確保角色變更後立即生效
    
    Returns:
        管理員的用戶 ID
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供認證資訊",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    payload = verify_token(credentials.credentials)
    user_id = payload.get("sub")
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token 格式錯誤"
        )
    
    # 從資料庫查詢用戶角色（而非僅依賴 Token）
    from app.models.user import User, UserRole
    user = db.query(User).filter(User.id == int(user_id)).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用戶不存在"
        )
    
    if user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理員權限"
        )
    
    return int(user_id)


async def get_optional_user_id(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme)
) -> Optional[int]:
    """
    取得目前登入用戶 ID(選擇性,未登入回傳 None)
    """
    if not credentials:
        return None
    
    try:
        payload = verify_token(credentials.credentials)
        user_id = payload.get("sub")
        return int(user_id) if user_id else None
    except HTTPException:
        return None
