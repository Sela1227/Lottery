"""
SELA 樂透一路發 - 成員異動申請 Schema
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field


# ==================== 請求 Schema ====================

class ReduceRequest(BaseModel):
    """減碼申請請求"""
    amount: Decimal = Field(..., gt=0, description="減碼金額")
    reason: Optional[str] = Field(None, max_length=500, description="申請原因")


class WithdrawRequest(BaseModel):
    """退出申請請求"""
    reason: Optional[str] = Field(None, max_length=500, description="申請原因")


class ReviewRequest(BaseModel):
    """審核請求"""
    approved: bool = Field(..., description="是否核准")
    note: Optional[str] = Field(None, max_length=500, description="審核備註")


# ==================== 回應 Schema ====================

class MemberRequestResponse(BaseModel):
    """成員異動申請回應"""
    id: int
    series_id: int
    series_name: Optional[str] = None
    user_id: int
    user_name: Optional[str] = None
    request_type: str
    request_type_display: str
    amount: Optional[Decimal] = None
    pool_share_before: Decimal
    status: str
    status_display: str
    reason: Optional[str] = None
    reviewed_by: Optional[int] = None
    reviewer_name: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    review_note: Optional[str] = None
    actual_amount: Optional[Decimal] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class MemberRequestListResponse(BaseModel):
    """成員異動申請列表回應"""
    requests: List[MemberRequestResponse]
    total: int
    pending_count: int


class MemberRequestCreateResponse(BaseModel):
    """建立申請回應"""
    success: bool
    message: str
    request_id: Optional[int] = None


class MemberRequestReviewResponse(BaseModel):
    """審核申請回應"""
    success: bool
    message: str
    request_id: int
    new_status: str
    actual_amount: Optional[Decimal] = None
