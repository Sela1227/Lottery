"""
SELA 樂透一路發 - 錢包 API
"""
from typing import List, Optional
from decimal import Decimal
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.models.user import User
from app.models.member import GroupMember, MemberStatus
from app.models.series import GroupSeries
from app.models.ledger import UserLedger, AccountType, TransactionType
from app.constants import TRANSACTION_TYPE_DISPLAY


router = APIRouter(prefix="/wallet", tags=["Wallet"])


# ==================== Schema ====================

class WalletOverview(BaseModel):
    """錢包概覽"""
    wallet_balance: Decimal
    total_pool_share: Decimal
    total_assets: Decimal
    series_count: int
    currency: str = "TWD"


class SeriesPoolShare(BaseModel):
    """系列團份額"""
    series_id: int
    series_name: str
    pool_share: Decimal
    ratio: float
    status: str


class TransactionRecord(BaseModel):
    """交易記錄"""
    id: int
    transaction_type: str
    transaction_type_display: str
    account_type: str
    amount: Decimal
    balance_after: Decimal
    series_name: Optional[str] = None
    note: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class TransactionListResponse(BaseModel):
    """交易記錄列表回應"""
    transactions: List[TransactionRecord]
    total: int
    has_more: bool

# ==================== API 端點 ====================

@router.get("/overview", response_model=WalletOverview)
async def get_wallet_overview(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """取得錢包概覽"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用戶不存在")
    
    # 計算所有系列團份額總和
    total_pool_share = db.query(func.coalesce(func.sum(GroupMember.pool_share), 0)).filter(
        GroupMember.user_id == user_id,
        GroupMember.status == MemberStatus.ACTIVE
    ).scalar()
    
    # 參與的系列團數
    series_count = db.query(GroupMember).filter(
        GroupMember.user_id == user_id,
        GroupMember.status == MemberStatus.ACTIVE
    ).count()
    
    wallet_balance = user.wallet_balance or Decimal("0")
    total_pool = Decimal(str(total_pool_share))
    
    return WalletOverview(
        wallet_balance=wallet_balance,
        total_pool_share=total_pool,
        total_assets=wallet_balance + total_pool,
        series_count=series_count
    )


@router.get("/pool-shares", response_model=List[SeriesPoolShare])
async def get_pool_shares(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """取得各系列團份額"""
    members = db.query(GroupMember).filter(
        GroupMember.user_id == user_id,
        GroupMember.status == MemberStatus.ACTIVE
    ).all()
    
    result = []
    for member in members:
        series = member.series
        if series:
            # 計算比例
            total_pool = float(series.current_pool) if series.current_pool else 1
            ratio = float(member.pool_share) / total_pool if total_pool > 0 else 0
            
            result.append(SeriesPoolShare(
                series_id=series.id,
                series_name=series.name,
                pool_share=member.pool_share,
                ratio=round(ratio * 100, 2),
                status=series.status.value
            ))
    
    return result


@router.get("/transactions", response_model=TransactionListResponse)
async def get_transactions(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
    account_type: Optional[str] = Query(None, description="篩選帳戶類型: wallet, pool"),
    transaction_type: Optional[str] = Query(None, description="篩選交易類型"),
    series_id: Optional[int] = Query(None, description="篩選系列團"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100)
):
    """取得交易記錄"""
    query = db.query(UserLedger).filter(UserLedger.user_id == user_id)
    
    # 篩選帳戶類型
    if account_type:
        if account_type == "wallet":
            query = query.filter(UserLedger.account_type == AccountType.WALLET)
        elif account_type == "pool":
            query = query.filter(UserLedger.account_type == AccountType.POOL)
    
    # 篩選交易類型
    if transaction_type:
        try:
            tt = TransactionType(transaction_type)
            query = query.filter(UserLedger.transaction_type == tt)
        except ValueError:
            pass
    
    # 篩選系列團
    if series_id:
        query = query.filter(UserLedger.series_id == series_id)
    
    # 總數
    total = query.count()
    
    # 取得資料
    records = query.order_by(desc(UserLedger.created_at)).offset(skip).limit(limit + 1).all()
    
    has_more = len(records) > limit
    records = records[:limit]
    
    # 轉換為回應格式
    transactions = []
    for r in records:
        series_name = None
        if r.series_id:
            series = db.query(GroupSeries).filter(GroupSeries.id == r.series_id).first()
            if series:
                series_name = series.name
        
        transactions.append(TransactionRecord(
            id=r.id,
            transaction_type=r.transaction_type.value,
            transaction_type_display=TRANSACTION_TYPE_DISPLAY.get(r.transaction_type.value, r.transaction_type.value),
            account_type=r.account_type.value,
            amount=r.amount,
            balance_after=r.balance_after,
            series_name=series_name,
            note=r.note,
            created_at=r.created_at
        ))
    
    return TransactionListResponse(
        transactions=transactions,
        total=total,
        has_more=has_more
    )


@router.get("/transactions/summary")
async def get_transaction_summary(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """取得交易統計摘要"""
    # 總儲值
    total_deposit = db.query(func.coalesce(func.sum(UserLedger.amount), 0)).filter(
        UserLedger.user_id == user_id,
        UserLedger.transaction_type == TransactionType.DEPOSIT
    ).scalar()
    
    # 總提領
    total_withdraw = db.query(func.coalesce(func.sum(func.abs(UserLedger.amount)), 0)).filter(
        UserLedger.user_id == user_id,
        UserLedger.transaction_type == TransactionType.WITHDRAW
    ).scalar()
    
    # 總獎金
    total_prize = db.query(func.coalesce(func.sum(UserLedger.amount), 0)).filter(
        UserLedger.user_id == user_id,
        UserLedger.transaction_type == TransactionType.POOL_PRIZE
    ).scalar()
    
    # 總投資（加入 + 加碼）
    total_invested = db.query(func.coalesce(func.sum(UserLedger.amount), 0)).filter(
        UserLedger.user_id == user_id,
        UserLedger.transaction_type.in_([TransactionType.POOL_JOIN, TransactionType.POOL_TOPUP])
    ).scalar()
    
    return {
        "total_deposit": float(total_deposit),
        "total_withdraw": float(total_withdraw),
        "total_prize": float(total_prize),
        "total_invested": float(total_invested)
    }
