"""
SELA 樂透一路發 - 彩券模型
"""
from sqlalchemy import Column, Integer, String, Numeric, DateTime, Boolean, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Ticket(Base):
    """彩券"""
    __tablename__ = "tickets"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 所屬單期團
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False)
    
    # 彩券資訊
    ticket_index = Column(Integer, nullable=False)  # 第幾張
    
    # 彩券照片
    image_url = Column(String(500), nullable=True)
    
    # 號碼(JSON 陣列,每個元素代表一注)
    # 威力彩範例:
    # [
    #   {"first_zone": [1,5,12,23,31,38], "second_zone": 2},
    #   {"first_zone": [3,8,15,22,28,35], "second_zone": 5}
    # ]
    numbers = Column(JSON, nullable=True)
    
    # 注數與金額
    bet_count = Column(Integer, default=1)
    cost = Column(Numeric(10, 2), nullable=False)
    
    # 對獎狀態
    is_checked = Column(Boolean, default=False)
    checked_at = Column(DateTime(timezone=True), nullable=True)
    
    # 中獎資訊(JSON 陣列)
    # [
    #   {"bet_index": 0, "level": "柒獎", "prize": 200},
    #   {"bet_index": 1, "level": "普獎", "prize": 100}
    # ]
    prize_results = Column(JSON, nullable=True)
    prize_amount = Column(Numeric(14, 2), default=0)  # 中獎總金額
    
    # 兌獎狀態
    is_redeemed = Column(Boolean, default=False)
    redeemed_at = Column(DateTime(timezone=True), nullable=True)
    redeemed_amount = Column(Numeric(14, 2), default=0)  # 實際兌換金額
    
    # 時間戳記
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 關聯
    group = relationship("Group", back_populates="tickets")
    
    def __repr__(self):
        return f"<Ticket {self.id}: group={self.group_id} #{self.ticket_index}>"
