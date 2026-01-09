"""
SELA 樂透一路發 - 系列團成員模型
"""
from sqlalchemy import Column, Integer, Numeric, DateTime, Enum as SQLEnum, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.core.database import Base


class MemberRole(str, enum.Enum):
    """成員角色"""
    ADMIN = "admin"    # 管理員
    MEMBER = "member"  # 一般成員


class MemberStatus(str, enum.Enum):
    """成員狀態"""
    ACTIVE = "active"    # 正常
    EXITED = "exited"    # 已退出


class GroupMember(Base):
    """系列團成員"""
    __tablename__ = "group_members"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    series_id = Column(Integer, ForeignKey("group_series.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # 角色與狀態
    role = Column(SQLEnum(MemberRole), nullable=False, default=MemberRole.MEMBER)
    status = Column(SQLEnum(MemberStatus), nullable=False, default=MemberStatus.ACTIVE)
    
    # 資金池份額
    pool_share = Column(Numeric(14, 2), default=0)  # 目前資金池份額
    
    # 統計
    total_invested = Column(Numeric(14, 2), default=0)       # 累計投入
    total_prize_received = Column(Numeric(14, 2), default=0) # 累計獲得獎金
    
    # 時間
    joined_at = Column(DateTime(timezone=True), server_default=func.now())
    exited_at = Column(DateTime(timezone=True), nullable=True)
    exit_reason = Column(String(255), nullable=True)
    
    # 關聯
    series = relationship("GroupSeries", back_populates="members")
    user = relationship("User", backref="memberships")
    
    # 確保同一用戶在同一系列團只能有一筆記錄
    __table_args__ = (
        UniqueConstraint('series_id', 'user_id', name='uq_series_user'),
    )
    
    def __repr__(self):
        return f"<GroupMember series={self.series_id} user={self.user_id}>"
    
    @property
    def current_ratio(self) -> float:
        """計算目前佔比(需要總池金額)"""
        if self.series and self.series.current_pool > 0:
            return float(self.pool_share / self.series.current_pool)
        return 0.0
    
    @property
    def is_admin(self) -> bool:
        return self.role == MemberRole.ADMIN
    
    @property
    def is_active(self) -> bool:
        return self.status == MemberStatus.ACTIVE
