"""
SELA 樂透一路發 - 帳本與事件日誌模型
"""
from sqlalchemy import Column, Integer, BigInteger, String, Numeric, DateTime, Enum as SQLEnum, JSON, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.core.database import Base


class AccountType(str, enum.Enum):
    """帳戶類型"""
    WALLET = "wallet"  # 個人錢包
    POOL = "pool"      # 系列團資金池


class TransactionType(str, enum.Enum):
    """交易類型"""
    # 錢包相關
    DEPOSIT = "deposit"           # 儲值
    WITHDRAW = "withdraw"         # 提領
    TRANSFER_OUT = "transfer_out" # 轉出
    TRANSFER_IN = "transfer_in"   # 轉入
    
    # 資金池相關
    POOL_JOIN = "pool_join"           # 加入資金池
    POOL_TOPUP = "pool_topup"         # 加碼
    POOL_WITHDRAW = "pool_withdraw"   # 減碼
    POOL_PURCHASE = "pool_purchase"   # 購買扣除
    POOL_CARRYOVER = "pool_carryover" # 滾入
    POOL_PRIZE = "pool_prize"         # 獎金分配
    POOL_EXIT = "pool_exit"           # 退出結算
    
    # 調整
    ADJUSTMENT = "adjustment"  # 調整（修正用）


class UserLedger(Base):
    """用戶帳本（所有金流記錄）"""
    __tablename__ = "user_ledger"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # 帳戶類型
    account_type = Column(SQLEnum(AccountType), nullable=False)
    series_id = Column(Integer, ForeignKey("group_series.id"), nullable=True)  # pool 類型才需要
    
    # 交易類型
    transaction_type = Column(SQLEnum(TransactionType), nullable=False)
    
    # 金額（正=增加，負=減少）
    amount = Column(Numeric(14, 2), nullable=False)
    balance_after = Column(Numeric(14, 2), nullable=False)  # 交易後餘額
    
    # 關聯資訊
    reference_type = Column(String(50), nullable=True)  # group, ticket, request...
    reference_id = Column(Integer, nullable=True)
    
    # 詳細資料
    details = Column(JSON, nullable=True)
    note = Column(String(255), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # 關聯
    user = relationship("User")
    series = relationship("GroupSeries")
    
    def __repr__(self):
        return f"<UserLedger {self.id}: {self.transaction_type.value} {self.amount}>"


class EventCategory(str, enum.Enum):
    """事件類別"""
    AUTH = "auth"          # 認證
    USER = "user"          # 用戶
    SERIES = "series"      # 系列團
    GROUP = "group"        # 單期團
    MEMBER = "member"      # 成員
    TICKET = "ticket"      # 彩券
    SETTLEMENT = "settlement"  # 結算
    SYSTEM = "system"      # 系統


class ActorType(str, enum.Enum):
    """執行者類型"""
    USER = "user"
    ADMIN = "admin"
    SYSTEM = "system"


class EventLog(Base):
    """事件日誌"""
    __tablename__ = "event_logs"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    
    # 事件資訊
    event_type = Column(String(50), nullable=False, index=True)
    category = Column(SQLEnum(EventCategory), nullable=False)
    
    # 執行者
    actor_id = Column(Integer, nullable=True)
    actor_type = Column(SQLEnum(ActorType), nullable=False)
    
    # 目標
    target_type = Column(String(50), nullable=True)
    target_id = Column(Integer, nullable=True)
    
    # 關聯 ID（方便查詢）
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    series_id = Column(Integer, ForeignKey("group_series.id"), nullable=True, index=True)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=True, index=True)
    
    # 事件資料
    event_data = Column(JSON, nullable=True)
    
    # 結果
    result = Column(String(20), default="success")  # success, failed
    error_message = Column(Text, nullable=True)
    
    # IP（可選）
    ip_address = Column(String(45), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    def __repr__(self):
        return f"<EventLog {self.id}: {self.event_type}>"


class PeriodSnapshot(Base):
    """每期快照（結算時保存完整狀態）"""
    __tablename__ = "period_snapshots"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False, unique=True)
    series_id = Column(Integer, ForeignKey("group_series.id"), nullable=False)
    
    # 快照資料（完整結算狀態）
    snapshot_data = Column(JSON, nullable=False)
    # {
    #   "period_number": 5,
    #   "lottery_type": "power",
    #   "total_pool": 2000,
    #   "total_spent": 1400,
    #   "total_prize": 4000,
    #   "total_prize_after_tax": 3200,
    #   "winning_numbers": {...},
    #   "tickets": [...],
    #   "members": [
    #     {
    #       "user_id": 1,
    #       "display_name": "王小明",
    #       "pool_share_before": 500,
    #       "effective_contribution": 350,
    #       "ratio": 0.25,
    #       "carryover": 150,
    #       "prize_share": 800,
    #       "pool_share_after": 950
    #     },
    #     ...
    #   ]
    # }
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 關聯
    group = relationship("Group")
    series = relationship("GroupSeries")
