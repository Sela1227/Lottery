"""
SELA 樂透一路發 - 單期團模型
"""
from sqlalchemy import Column, Integer, String, Numeric, DateTime, Date, Time, Enum as SQLEnum, JSON, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.core.database import Base


class GroupStatus(str, enum.Enum):
    """單期團狀態"""
    COLLECTING = "collecting"  # 集資中
    LOCKED = "locked"          # 已鎖定(準備購買)
    PURCHASED = "purchased"    # 已購買
    DRAWN = "drawn"            # 已開獎
    SETTLED = "settled"        # 已結算


class Group(Base):
    """單期團(單一期彩券)"""
    __tablename__ = "groups"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 所屬系列團
    series_id = Column(Integer, ForeignKey("group_series.id"), nullable=False)
    period_number = Column(Integer, nullable=False)  # 第幾期
    
    # 彩種
    lottery_type_id = Column(Integer, ForeignKey("lottery_types.id"), nullable=False)
    
    # 台彩期數資訊
    draw_term = Column(String(20), nullable=True)  # 台彩期數,如 "113000098"
    draw_date = Column(Date, nullable=True)
    draw_time = Column(Time, nullable=True)
    
    # 狀態
    status = Column(SQLEnum(GroupStatus), nullable=False, default=GroupStatus.COLLECTING)
    
    # 時間節點
    collection_deadline = Column(DateTime(timezone=True), nullable=True)  # 集資截止
    locked_at = Column(DateTime(timezone=True), nullable=True)
    purchased_at = Column(DateTime(timezone=True), nullable=True)
    drawn_at = Column(DateTime(timezone=True), nullable=True)
    settled_at = Column(DateTime(timezone=True), nullable=True)
    
    # 金額
    total_pool = Column(Numeric(14, 2), default=0)       # 本期資金池
    total_spent = Column(Numeric(14, 2), default=0)      # 實際購買金額
    total_tickets = Column(Integer, default=0)            # 購買注數
    total_carryover = Column(Numeric(14, 2), default=0)  # 滾入下期金額
    total_prize = Column(Numeric(14, 2), default=0)      # 中獎總額
    total_prize_after_tax = Column(Numeric(14, 2), default=0)  # 扣稅後
    
    # 開獎號碼(JSON)
    # 威力彩: {"first_zone": [1,5,12,23,31,38], "second_zone": 2}
    # 大樂透: {"main": [3,8,15,22,28,35], "special": 42}
    winning_numbers = Column(JSON, nullable=True)
    
    # 選擇原因(選填)
    choice_reason = Column(Text, nullable=True)
    
    # 時間戳記
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 關聯
    series = relationship("GroupSeries", back_populates="groups")
    lottery_type = relationship("LotteryType")
    tickets = relationship("Ticket", back_populates="group", lazy="dynamic")
    contributions = relationship("PeriodContribution", back_populates="group")
    
    def __repr__(self):
        return f"<Group {self.id}: {self.series.name if self.series else ''} 第{self.period_number}期>"


class PeriodContribution(Base):
    """每期成員貢獻記錄(用於結算)"""
    __tablename__ = "period_contributions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False)
    member_id = Column(Integer, ForeignKey("group_members.id"), nullable=False)
    
    # 本期份額(鎖定時的資金池份額)
    pool_share_at_lock = Column(Numeric(14, 2), nullable=False)
    
    # 計算結果
    effective_contribution = Column(Numeric(14, 2), default=0)  # 有效貢獻
    contribution_ratio = Column(Numeric(10, 8), default=0)      # 貢獻比例
    carryover_amount = Column(Numeric(14, 2), default=0)        # 滾入金額
    prize_share = Column(Numeric(14, 2), default=0)             # 獎金份額
    new_pool_share = Column(Numeric(14, 2), default=0)          # 結算後新份額
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 關聯
    group = relationship("Group", back_populates="contributions")
    member = relationship("GroupMember")
