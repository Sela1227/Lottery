"""
SELA 樂透一路發 - 系列團 Schema
"""
from datetime import datetime
from typing import Optional, List
from decimal import Decimal
from pydantic import BaseModel, Field

from app.models.series import WithdrawalPolicy, SeriesStatus


# ==================== 系列團 ====================

class SeriesCreate(BaseModel):
    """建立系列團"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    allowed_lottery_types: List[str] = Field(default=["power", "super"])
    withdrawal_policy: WithdrawalPolicy = WithdrawalPolicy.NO_WITHDRAW
    end_condition: Optional[dict] = None
    initial_pool_share: Decimal = Field(..., gt=0, description="初始投入金額")


class SeriesUpdate(BaseModel):
    """更新系列團"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    end_condition: Optional[dict] = None


class SeriesResponse(BaseModel):
    """系列團回應"""
    id: int
    name: str
    description: Optional[str]
    allowed_lottery_types: List[str]
    withdrawal_policy: WithdrawalPolicy
    end_condition: Optional[dict]
    status: SeriesStatus
    total_periods: int
    current_pool: Decimal
    total_invested: Decimal
    total_prize: Decimal
    creator_id: int
    created_at: datetime
    ended_at: Optional[datetime]
    
    # 額外資訊
    member_count: Optional[int] = None
    my_pool_share: Optional[Decimal] = None
    my_role: Optional[str] = None
    
    class Config:
        from_attributes = True


class SeriesListResponse(BaseModel):
    """系列團列表回應"""
    id: int
    name: str
    status: SeriesStatus
    current_pool: Decimal
    total_periods: int
    member_count: int
    my_pool_share: Decimal
    my_role: str
    lottery_types: List[str]
    
    class Config:
        from_attributes = True


# ==================== 邀請碼 ====================

class InvitationCreate(BaseModel):
    """建立邀請碼"""
    max_uses: Optional[int] = None
    expires_in_days: Optional[int] = None


class InvitationResponse(BaseModel):
    """邀請碼回應"""
    id: int
    code: str
    max_uses: Optional[int]
    used_count: int
    expires_at: Optional[datetime]
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class JoinByInvitation(BaseModel):
    """透過邀請碼加入"""
    code: str
    initial_pool_share: Decimal = Field(..., gt=0)


# ==================== 成員 ====================

class MemberResponse(BaseModel):
    """成員回應"""
    id: int
    user_id: int
    display_name: str
    picture_url: Optional[str]
    role: str
    status: str
    pool_share: Decimal
    ratio: float
    total_invested: Decimal
    total_prize_received: Decimal
    joined_at: datetime
    
    class Config:
        from_attributes = True


class MemberPoolUpdate(BaseModel):
    """更新成員資金池（加碼）"""
    amount: Decimal = Field(..., gt=0)
