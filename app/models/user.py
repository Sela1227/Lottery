"""
SELA 樂透一路發 - 用戶模型
"""
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum as SQLEnum
from app.core.database import Base


class UserRole(str, Enum):
    """用戶角色"""
    MEMBER = "member"
    ADMIN = "admin"


class UserStatus(str, Enum):
    """用戶狀態（向下相容）"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


class User(Base):
    """用戶資料表"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # LINE 資料
    line_id = Column(String(100), unique=True, nullable=False, index=True)
    display_name = Column(String(100), nullable=False)
    picture_url = Column(String(500), nullable=True)
    
    # 自訂資料
    nickname = Column(String(50), nullable=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(20), nullable=True)
    
    # 角色與狀態
    role = Column(SQLEnum(UserRole), default=UserRole.MEMBER, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # 通知設定
    notify_draw_reminder = Column(Boolean, default=True, nullable=False)
    notify_win_alert = Column(Boolean, default=True, nullable=False)
    notify_settlement = Column(Boolean, default=True, nullable=False)
    
    # 時間戳記
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_login_at = Column(DateTime, nullable=True)
    
    @property
    def is_admin(self) -> bool:
        return self.role == UserRole.ADMIN
