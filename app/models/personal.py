"""
SELA 樂透一路發 - 個人彩券與成就徽章資料模型
"""
import enum
from datetime import datetime
from decimal import Decimal
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, ForeignKey, 
    Numeric, Enum, Boolean, JSON
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


# ==================== 個人彩券 ====================

class PersonalTicketStatus(enum.Enum):
    """個人彩券狀態"""
    PENDING = "pending"      # 待開獎
    WON = "won"              # 中獎
    LOST = "lost"            # 未中獎


class PersonalTicket(Base):
    """個人彩券"""
    __tablename__ = "personal_tickets"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    lottery_type_id = Column(Integer, ForeignKey("lottery_types.id"), nullable=False)
    
    # 號碼
    numbers = Column(JSON, nullable=False)           # 主號碼列表 [1,2,3,4,5,6]
    special_number = Column(Integer, nullable=True)  # 特別號 (威力彩第二區)
    
    # 期別資訊
    draw_term = Column(String(20), nullable=True)    # 台彩期數
    draw_date = Column(String(20), nullable=True)    # 開獎日期
    
    # 金額
    cost = Column(Numeric(10, 0), default=100)       # 購買金額
    prize = Column(Numeric(12, 0), default=0)        # 中獎金額
    
    # 狀態
    status = Column(
        Enum(PersonalTicketStatus), 
        default=PersonalTicketStatus.PENDING,
        nullable=False
    )
    
    # 對獎結果
    match_count = Column(Integer, default=0)         # 中幾個號碼
    prize_tier = Column(String(20), nullable=True)   # 獎項等級
    
    # 備註
    note = Column(Text, nullable=True)
    
    # 時間戳
    created_at = Column(DateTime, server_default=func.now())
    checked_at = Column(DateTime, nullable=True)     # 對獎時間
    
    # 關聯
    user = relationship("User", backref="personal_tickets")
    lottery_type = relationship("LotteryType")


# ==================== 成就徽章 ====================

class AchievementCategory(enum.Enum):
    """成就類別"""
    BEGINNER = "beginner"      # 新手成就
    PARTICIPATION = "participation"  # 參與成就
    LUCKY = "lucky"            # 幸運成就
    INVESTMENT = "investment"  # 投資成就
    SOCIAL = "social"          # 社交成就


class Achievement(Base):
    """成就定義"""
    __tablename__ = "achievements"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(50), unique=True, nullable=False)  # 成就代碼
    name = Column(String(100), nullable=False)              # 成就名稱
    description = Column(Text, nullable=True)               # 成就描述
    icon = Column(String(10), default="🏆")                 # 圖示 emoji
    
    category = Column(
        Enum(AchievementCategory),
        default=AchievementCategory.BEGINNER
    )
    
    # 達成條件
    threshold = Column(Integer, default=1)      # 門檻值
    stat_field = Column(String(50), nullable=True)  # 統計欄位
    
    # 獎勵
    points = Column(Integer, default=10)        # 獲得點數
    
    # 排序
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, server_default=func.now())


class UserAchievement(Base):
    """用戶成就記錄"""
    __tablename__ = "user_achievements"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    achievement_id = Column(Integer, ForeignKey("achievements.id"), nullable=False)
    
    # 進度
    progress = Column(Integer, default=0)       # 當前進度
    is_unlocked = Column(Boolean, default=False)
    unlocked_at = Column(DateTime, nullable=True)
    
    # 時間戳
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # 關聯
    user = relationship("User", backref="achievements")
    achievement = relationship("Achievement")
    
    class Config:
        # 確保每個用戶每個成就只有一筆記錄
        __table_args__ = (
            {'extend_existing': True}
        )
