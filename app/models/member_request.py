"""
SELA 樂透一路發 - 成員異動申請模型
"""
from sqlalchemy import Column, Integer, Numeric, DateTime, Enum as SQLEnum, ForeignKey, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.core.database import Base


class RequestType(str, enum.Enum):
    """申請類型"""
    REDUCE = "reduce"      # 減碼
    WITHDRAW = "withdraw"  # 退出


class RequestStatus(str, enum.Enum):
    """申請狀態"""
    PENDING = "pending"    # 待審核
    APPROVED = "approved"  # 已核准
    REJECTED = "rejected"  # 已拒絕
    CANCELLED = "cancelled"  # 已取消


class MemberRequest(Base):
    """成員異動申請"""
    __tablename__ = "member_requests"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 關聯
    series_id = Column(Integer, ForeignKey("group_series.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # 申請類型與金額
    request_type = Column(SQLEnum(RequestType), nullable=False)
    amount = Column(Numeric(14, 2), nullable=True)  # 減碼金額（退出時為 NULL，表示全額）
    
    # 申請時的快照
    pool_share_before = Column(Numeric(14, 2), nullable=False)  # 申請時的份額
    
    # 狀態
    status = Column(SQLEnum(RequestStatus), nullable=False, default=RequestStatus.PENDING)
    
    # 申請資訊
    reason = Column(Text, nullable=True)  # 申請原因
    
    # 審核資訊
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    review_note = Column(Text, nullable=True)  # 審核備註
    
    # 執行結果
    actual_amount = Column(Numeric(14, 2), nullable=True)  # 實際減碼/退出金額
    
    # 時間
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 關聯
    series = relationship("GroupSeries")
    user = relationship("User", foreign_keys=[user_id])
    reviewer = relationship("User", foreign_keys=[reviewed_by])
    
    def __repr__(self):
        return f"<MemberRequest {self.id}: {self.request_type.value} {self.amount}>"
    
    @property
    def is_pending(self) -> bool:
        return self.status == RequestStatus.PENDING
    
    @property
    def type_display(self) -> str:
        """顯示用的申請類型"""
        return "減碼" if self.request_type == RequestType.REDUCE else "退出"
    
    @property
    def status_display(self) -> str:
        """顯示用的狀態"""
        mapping = {
            RequestStatus.PENDING: "待審核",
            RequestStatus.APPROVED: "已核准",
            RequestStatus.REJECTED: "已拒絕",
            RequestStatus.CANCELLED: "已取消",
        }
        return mapping.get(self.status, str(self.status.value))
