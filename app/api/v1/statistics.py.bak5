"""
SELA 樂透一路發 - 統計報表 API
"""
from typing import List, Optional
from decimal import Decimal
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, extract
from pydantic import BaseModel

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.models.user import User
from app.models.member import GroupMember, MemberStatus
from app.models.series import GroupSeries
from app.models.group import Group, GroupStatus, PeriodContribution
from app.models.ticket import Ticket
from app.models.ledger import UserLedger, TransactionType


router = APIRouter(prefix="/statistics", tags=["Statistics"])


# ==================== Schema ====================

class OverallStats(BaseModel):
    """整體統計"""
    total_invested: Decimal
    total_prize: Decimal
    total_profit: Decimal
    roi_percent: float
    series_count: int
    periods_participated: int
    winning_periods: int
    win_rate: float


class SeriesPerformance(BaseModel):
    """系列團績效"""
    series_id: int
    series_name: str
    status: str
    invested: Decimal
    prize_received: Decimal
    profit: Decimal
    roi_percent: float
    periods_count: int
    current_pool_share: Decimal


class WinningRecord(BaseModel):
    """中獎記錄"""
    group_id: int
    series_name: str
    period_number: int
    lottery_type: str
    draw_date: Optional[str]
    prize_amount: Decimal
    my_share: Decimal
    settled_at: Optional[datetime]


class MonthlyStats(BaseModel):
    """月度統計"""
    year_month: str
    invested: Decimal
    prize: Decimal
    profit: Decimal
    periods: int


class LotteryTypeStats(BaseModel):
    """彩種統計"""
    lottery_type: str
    lottery_name: str
    periods: int
    invested: Decimal
    prize: Decimal
    roi_percent: float


# ==================== API 端點 ====================

@router.get("/overall", response_model=OverallStats)
async def get_overall_stats(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """取得整體統計"""
    # 取得所有會員資格
    members = db.query(GroupMember).filter(
        GroupMember.user_id == user_id
    ).all()
    
    total_invested = Decimal("0")
    total_prize = Decimal("0")
    series_ids = set()
    
    for m in members:
        total_invested += m.total_invested or Decimal("0")
        total_prize += m.total_prize_received or Decimal("0")
        series_ids.add(m.series_id)
    
    # 計算參與的期數
    periods_participated = db.query(PeriodContribution).join(
        GroupMember, PeriodContribution.member_id == GroupMember.id
    ).filter(
        GroupMember.user_id == user_id
    ).count()
    
    # 計算有獎金的期數
    winning_periods = db.query(PeriodContribution).join(
        GroupMember, PeriodContribution.member_id == GroupMember.id
    ).filter(
        GroupMember.user_id == user_id,
        PeriodContribution.prize_share > 0
    ).count()
    
    # 計算
    total_profit = total_prize - total_invested
    roi_percent = float(total_profit / total_invested * 100) if total_invested > 0 else 0
    win_rate = float(winning_periods / periods_participated * 100) if periods_participated > 0 else 0
    
    return OverallStats(
        total_invested=total_invested,
        total_prize=total_prize,
        total_profit=total_profit,
        roi_percent=round(roi_percent, 2),
        series_count=len(series_ids),
        periods_participated=periods_participated,
        winning_periods=winning_periods,
        win_rate=round(win_rate, 2)
    )


@router.get("/series-performance", response_model=List[SeriesPerformance])
async def get_series_performance(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """取得各系列團績效"""
    members = db.query(GroupMember).filter(
        GroupMember.user_id == user_id,
        GroupMember.status == MemberStatus.ACTIVE
    ).all()
    
    result = []
    for m in members:
        series = m.series
        if not series:
            continue
        
        # 計算參與期數
        periods_count = db.query(PeriodContribution).filter(
            PeriodContribution.member_id == m.id
        ).count()
        
        invested = m.total_invested or Decimal("0")
        prize = m.total_prize_received or Decimal("0")
        profit = prize - invested
        roi = float(profit / invested * 100) if invested > 0 else 0
        
        result.append(SeriesPerformance(
            series_id=series.id,
            series_name=series.name,
            status=series.status.value,
            invested=invested,
            prize_received=prize,
            profit=profit,
            roi_percent=round(roi, 2),
            periods_count=periods_count,
            current_pool_share=m.pool_share
        ))
    
    # 按 ROI 排序
    result.sort(key=lambda x: x.roi_percent, reverse=True)
    return result


@router.get("/winning-records", response_model=List[WinningRecord])
async def get_winning_records(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
    limit: int = Query(20, ge=1, le=100)
):
    """取得中獎記錄"""
    # 找有獎金的貢獻記錄
    contributions = db.query(PeriodContribution).join(
        GroupMember, PeriodContribution.member_id == GroupMember.id
    ).filter(
        GroupMember.user_id == user_id,
        PeriodContribution.prize_share > 0
    ).order_by(desc(PeriodContribution.created_at)).limit(limit).all()
    
    result = []
    for c in contributions:
        group = c.group
        series = group.series
        lottery_type = group.lottery_type
        
        result.append(WinningRecord(
            group_id=group.id,
            series_name=series.name if series else "未知",
            period_number=group.period_number,
            lottery_type=lottery_type.name if lottery_type else "未知",
            draw_date=group.draw_date.isoformat() if group.draw_date else None,
            prize_amount=group.total_prize_after_tax,
            my_share=c.prize_share,
            settled_at=group.settled_at
        ))
    
    return result


@router.get("/monthly", response_model=List[MonthlyStats])
async def get_monthly_stats(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
    months: int = Query(6, ge=1, le=24)
):
    """取得月度統計"""
    result = []
    now = datetime.now()
    
    for i in range(months):
        # 計算月份
        target_date = now - timedelta(days=i * 30)
        year = target_date.year
        month = target_date.month
        year_month = f"{year}-{month:02d}"
        
        # 該月投資（加入 + 加碼）
        invested = db.query(func.coalesce(func.sum(UserLedger.amount), 0)).filter(
            UserLedger.user_id == user_id,
            UserLedger.transaction_type.in_([
                TransactionType.POOL_JOIN,
                TransactionType.POOL_TOPUP
            ]),
            extract('year', UserLedger.created_at) == year,
            extract('month', UserLedger.created_at) == month
        ).scalar()
        
        # 該月獎金
        prize = db.query(func.coalesce(func.sum(UserLedger.amount), 0)).filter(
            UserLedger.user_id == user_id,
            UserLedger.transaction_type == TransactionType.POOL_PRIZE,
            extract('year', UserLedger.created_at) == year,
            extract('month', UserLedger.created_at) == month
        ).scalar()
        
        # 該月參與期數
        periods = db.query(PeriodContribution).join(
            GroupMember, PeriodContribution.member_id == GroupMember.id
        ).join(
            Group, PeriodContribution.group_id == Group.id
        ).filter(
            GroupMember.user_id == user_id,
            extract('year', Group.created_at) == year,
            extract('month', Group.created_at) == month
        ).count()
        
        invested_val = Decimal(str(invested))
        prize_val = Decimal(str(prize))
        
        result.append(MonthlyStats(
            year_month=year_month,
            invested=invested_val,
            prize=prize_val,
            profit=prize_val - invested_val,
            periods=periods
        ))
    
    return result


@router.get("/by-lottery-type", response_model=List[LotteryTypeStats])
async def get_lottery_type_stats(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """取得各彩種統計"""
    from app.models.lottery_type import LotteryType
    
    # 取得用戶參與的所有貢獻記錄，按彩種分組
    contributions = db.query(PeriodContribution).join(
        GroupMember, PeriodContribution.member_id == GroupMember.id
    ).filter(
        GroupMember.user_id == user_id
    ).all()
    
    # 按彩種統計
    stats_by_type = {}
    for c in contributions:
        group = c.group
        lottery_type = group.lottery_type
        if not lottery_type:
            continue
        
        code = lottery_type.code
        if code not in stats_by_type:
            stats_by_type[code] = {
                "lottery_type": code,
                "lottery_name": lottery_type.name,
                "periods": 0,
                "invested": Decimal("0"),
                "prize": Decimal("0")
            }
        
        stats_by_type[code]["periods"] += 1
        stats_by_type[code]["invested"] += c.effective_contribution or Decimal("0")
        stats_by_type[code]["prize"] += c.prize_share or Decimal("0")
    
    result = []
    for code, data in stats_by_type.items():
        invested = data["invested"]
        prize = data["prize"]
        roi = float((prize - invested) / invested * 100) if invested > 0 else 0
        
        result.append(LotteryTypeStats(
            lottery_type=data["lottery_type"],
            lottery_name=data["lottery_name"],
            periods=data["periods"],
            invested=invested,
            prize=prize,
            roi_percent=round(roi, 2)
        ))
    
    # 按期數排序
    result.sort(key=lambda x: x.periods, reverse=True)
    return result
