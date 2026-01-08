"""
SELA 樂透一路發 - 用戶模型
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Numeric, DateTime, Enum as SQLEnum
from sqlalchemy.sql import func
import enum

from app.core.database import Base


class UserStatus(str, enum.Enum):
    """用戶狀態"""
    ACTIVE = "active"          # 正常
    SUSPENDED = "suspended"    # 停權


class UserRole(str, enum.Enum):
    """用戶角色"""
    USER = "user"              # 一般用戶
    ADMIN = "admin"            # 系統管理員


class User(Base):
    """用戶模型"""
    __tablename__ = "users"
    
    # 主鍵
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # LINE 登入資訊
    line_user_id = Column(String(64), unique=True, nullable=False, index=True)
    display_name = Column(String(100), nullable=False)
    picture_url = Column(String(500), nullable=True)
    
    # 個人資訊（選填）
    email = Column(String(255), nullable=True)
    phone = Column(String(20), nullable=True)
    nickname = Column(String(50), nullable=True)  # 自訂暱稱
    
    # 狀態與角色
    status = Column(
        SQLEnum(UserStatus),
        nullable=False,
        default=UserStatus.ACTIVE
    )
    role = Column(
        SQLEnum(UserRole),
        nullable=False,
        default=UserRole.USER
    )
    
    # 錢包餘額（個人錢包，非團資金池）
    wallet_balance = Column(
        Numeric(precision=12, scale=2),
        nullable=False,
        default=0
    )
    
    # 時間戳記
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    
    def __repr__(self):
        return f"<User {self.id}: {self.display_name}>"
    
    @property
    def is_admin(self) -> bool:
        """是否為管理員"""
        return self.role == UserRole.ADMIN
    
    @property
    def is_active(self) -> bool:
        """帳號是否正常"""
        return self.status == UserStatus.ACTIVE
