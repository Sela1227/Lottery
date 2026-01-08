"""
SELA 樂透一路發 - 單期團與彩券 Schema
"""
from datetime import datetime, date, time
from typing import Optional, List, Any
from decimal import Decimal
from pydantic import BaseModel, Field

from app.models.group import GroupStatus


# ==================== 彩種 ====================

class LotteryTypeResponse(BaseModel):
    """彩種回應"""
    id: int
    code: str
    name: str
    description: Optional[str]
    price_per_bet: Decimal
    number_rules: dict
    prize_structure: List[dict]
    draw_days: List[int]
    draw_time: str
    is_active: bool
    
    class Config:
        from_attributes = True


# ==================== 單期團 ====================

class GroupCreate(BaseModel):
    """建立單期團（開新期）"""
    lottery_type_code: str
    draw_term: Optional[str] = None
    draw_date: Optional[date] = None
    collection_deadline: Optional[datetime] = None
    choice_reason: Optional[str] = None


class GroupResponse(BaseModel):
    """單期團回應"""
    id: int
    series_id: int
    period_number: int
    lottery_type: LotteryTypeResponse
    draw_term: Optional[str]
    draw_date: Optional[date]
    status: GroupStatus
    collection_deadline: Optional[datetime]
    locked_at: Optional[datetime]
    purchased_at: Optional[datetime]
    drawn_at: Optional[datetime]
    settled_at: Optional[datetime]
    total_pool: Decimal
    total_spent: Decimal
    total_tickets: int
    total_prize: Decimal
    total_prize_after_tax: Decimal
    winning_numbers: Optional[dict]
    choice_reason: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class GroupListResponse(BaseModel):
    """單期團列表回應"""
    id: int
    period_number: int
    lottery_type_code: str
    lottery_type_name: str
    draw_term: Optional[str]
    draw_date: Optional[date]
    status: GroupStatus
    total_pool: Decimal
    total_spent: Decimal
    total_prize: Decimal
    
    class Config:
        from_attributes = True


class DrawResultInput(BaseModel):
    """輸入開獎結果"""
    winning_numbers: dict
    # 威力彩: {"first_zone": [1,5,12,23,31,38], "second_zone": 2}
    # 大樂透: {"main": [3,8,15,22,28,35], "special": 42}


# ==================== 彩券 ====================

class TicketCreate(BaseModel):
    """建立彩券"""
    numbers: Optional[List[dict]] = None
    bet_count: int = Field(default=1, ge=1)
    cost: Decimal


class TicketUpdate(BaseModel):
    """更新彩券"""
    numbers: Optional[List[dict]] = None
    image_url: Optional[str] = None


class TicketResponse(BaseModel):
    """彩券回應"""
    id: int
    group_id: int
    ticket_index: int
    image_url: Optional[str]
    numbers: Optional[List[dict]]
    bet_count: int
    cost: Decimal
    is_checked: bool
    checked_at: Optional[datetime]
    prize_results: Optional[List[dict]]
    prize_amount: Decimal
    is_redeemed: bool
    redeemed_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True


class CheckTicketResponse(BaseModel):
    """對獎結果回應"""
    ticket_id: int
    is_winner: bool
    prize_results: List[dict]
    total_prize: Decimal


# ==================== 結算 ====================

class SettlementPreview(BaseModel):
    """結算預覽"""
    group_id: int
    period_number: int
    total_pool: Decimal
    total_spent: Decimal
    total_carryover: Decimal
    total_prize: Decimal
    total_prize_after_tax: Decimal
    members: List[dict]
    # members: [
    #   {
    #     "user_id": 1,
    #     "display_name": "王小明",
    #     "pool_share_before": 500,
    #     "effective_contribution": 350,
    #     "ratio": 0.25,
    #     "carryover": 150,
    #     "prize_share": 800,
    #     "pool_share_after": 950
    #   }
    # ]


class SettlementResult(BaseModel):
    """結算結果"""
    group_id: int
    success: bool
    message: str
    snapshot_id: Optional[int] = None
