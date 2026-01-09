"""
SELA 樂透一路發 - 系列團模型
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Numeric, DateTime, Enum as SQLEnum, JSON, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.core.database import Base


class WithdrawalPolicy(str, enum.Enum):
    """提領政策"""
    FLEXIBLE = "flexible"      # 彈性模式(允許減碼/退出)
    NO_WITHDRAW = "no_withdraw"  # 死戰到底(只進不出)


class SeriesStatus(str, enum.Enum):
    """系列團狀態"""
    ACTIVE = "active"      # 進行中
    PAUSED = "paused"      # 暫停
    ENDED = "ended"        # 已結束


class GroupSeries(Base):
    """系列團"""
    __tablename__ = "group_series"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 基本資訊
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    
    # 設定
    allowed_lottery_types = Column(JSON, nullable=False)  # ["power", "super"]
    withdrawal_policy = Column(
        SQLEnum(WithdrawalPolicy),
        nullable=False,
        default=WithdrawalPolicy.NO_WITHDRAW
    )
    
    # 結束條件(JSON)
    # {"type": "jackpot", "threshold": 10000000}  中頭獎就結束
    # {"type": "periods", "max_periods": 100}     最多100期
    # {"type": "manual"}                          手動結束
    end_condition = Column(JSON, nullable=True)
    
    # 狀態
    status = Column(
        SQLEnum(SeriesStatus),
        nullable=False,
        default=SeriesStatus.ACTIVE
    )
    
    # 統計
    total_periods = Column(Integer, default=0)
    current_pool = Column(Numeric(14, 2), default=0)      # 目前資金池
    total_invested = Column(Numeric(14, 2), default=0)    # 累計投入
    total_prize = Column(Numeric(14, 2), default=0)       # 累計獎金
    
    # 建立者
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # 時間戳記
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    ended_at = Column(DateTime(timezone=True), nullable=True)
    end_reason = Column(String(255), nullable=True)
    
    # 關聯
    creator = relationship("User", backref="created_series")
    members = relationship("GroupMember", back_populates="series", lazy="dynamic")
    groups = relationship("Group", back_populates="series", lazy="dynamic")
    invitations = relationship("SeriesInvitation", back_populates="series")
    
    def __repr__(self):
        return f"<GroupSeries {self.id}: {self.name}>"


class SeriesInvitation(Base):
    """系列團邀請碼"""
    __tablename__ = "series_invitations"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    series_id = Column(Integer, ForeignKey("group_series.id"), nullable=False)
    
    # 邀請碼(8位英數字)
    code = Column(String(20), unique=True, nullable=False, index=True)
    
    # 使用限制
    max_uses = Column(Integer, nullable=True)  # None = 無限
    used_count = Column(Integer, default=0)
    
    # 有效期
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # 建立者
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 狀態
    is_active = Column(Integer, default=1)  # 1=有效, 0=停用
    
    # 關聯
    series = relationship("GroupSeries", back_populates="invitations")
    creator = relationship("User")
    
    @property
    def is_valid(self) -> bool:
        """邀請碼是否有效"""
        if not self.is_active:
            return False
        if self.expires_at and datetime.now() > self.expires_at:
            return False
        if self.max_uses and self.used_count >= self.max_uses:
            return False
        return True
