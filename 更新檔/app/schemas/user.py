"""
SELA 樂透一路發 - 用戶 Schema
"""
from datetime import datetime
from typing import Optional
from decimal import Decimal
from pydantic import BaseModel, Field

from app.models.user import UserStatus, UserRole


class UserBase(BaseModel):
    """用戶基礎 Schema"""
    display_name: str
    nickname: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None


class UserCreate(BaseModel):
    """建立用戶(LINE Login 後)"""
    line_user_id: str
    display_name: str
    picture_url: Optional[str] = None


class UserUpdate(BaseModel):
    """更新用戶資料"""
    nickname: Optional[str] = Field(None, max_length=50)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)


class UserResponse(BaseModel):
    """用戶回應"""
    id: int
    line_user_id: str
    display_name: str
    picture_url: Optional[str]
    nickname: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    status: UserStatus
    role: UserRole
    wallet_balance: Decimal
    created_at: datetime
    last_login_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class UserPublicResponse(BaseModel):
    """用戶公開資訊(給其他成員看)"""
    id: int
    display_name: str
    picture_url: Optional[str]
    nickname: Optional[str]
    
    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """Token 回應"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse
