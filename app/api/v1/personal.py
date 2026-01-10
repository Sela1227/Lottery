"""
SELA 樂透一路發 - 個人彩券 API
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
from app.models.personal import PersonalTicket, PersonalTicketStatus
from app.models.lottery_type import LotteryType


router = APIRouter(prefix="/personal", tags=["Personal Lottery"])


# ==================== Schema ====================

class PersonalTicketCreate(BaseModel):
    """建立個人彩券"""
    lottery_type_id: int
    numbers: List[int]
    special_number: Optional[int] = None
    draw_term: Optional[str] = None
    draw_date: Optional[str] = None
    cost: int = 100
    note: Optional[str] = None


class PersonalTicketResponse(BaseModel):
    """個人彩券回應"""
    id: int
    lottery_type_id: int
    lottery_type_name: str
    lottery_type_code: str
    numbers: List[int]
    special_number: Optional[int] = None
    draw_term: Optional[str] = None
    draw_date: Optional[str] = None
    cost: Decimal
    prize: Decimal
    status: str
    match_count: int
    prize_tier: Optional[str] = None
    note: Optional[str] = None
    created_at: datetime
    checked_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class PersonalTicketListResponse(BaseModel):
    """個人彩券列表回應"""
    tickets: List[PersonalTicketResponse]
    total: int
    pending_count: int
    won_count: int
    total_cost: Decimal
    total_prize: Decimal


class CheckResultResponse(BaseModel):
    """對獎結果回應"""
    ticket_id: int
    status: str
    match_count: int
    prize_tier: Optional[str] = None
    prize: Decimal
    winning_numbers: Optional[List[int]] = None
    special_number: Optional[int] = None


class PersonalStats(BaseModel):
    """個人彩券統計"""
    total_tickets: int
    pending_count: int
    won_count: int
    lost_count: int
    total_cost: Decimal
    total_prize: Decimal
    profit: Decimal
    win_rate: float
    best_prize: Decimal
    lottery_type_breakdown: List[dict]


# ==================== API 端點 ====================

@router.get("/tickets", response_model=PersonalTicketListResponse)
async def get_my_tickets(
    status: Optional[str] = Query(None, description="狀態篩選: pending, won, lost"),
    lottery_type_id: Optional[int] = Query(None, description="彩種篩選"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """取得我的個人彩券列表"""
    query = db.query(PersonalTicket).filter(PersonalTicket.user_id == user_id)
    
    # 狀態篩選
    if status:
        try:
            status_enum = PersonalTicketStatus(status)
            query = query.filter(PersonalTicket.status == status_enum)
        except ValueError:
            pass
    
    # 彩種篩選
    if lottery_type_id:
        query = query.filter(PersonalTicket.lottery_type_id == lottery_type_id)
    
    # 統計
    total = query.count()
    pending_count = query.filter(PersonalTicket.status == PersonalTicketStatus.PENDING).count()
    won_count = db.query(PersonalTicket).filter(
        PersonalTicket.user_id == user_id,
        PersonalTicket.status == PersonalTicketStatus.WON
    ).count()
    
    total_cost = db.query(func.coalesce(func.sum(PersonalTicket.cost), 0)).filter(
        PersonalTicket.user_id == user_id
    ).scalar()
    
    total_prize = db.query(func.coalesce(func.sum(PersonalTicket.prize), 0)).filter(
        PersonalTicket.user_id == user_id
    ).scalar()
    
    # 取得資料
    tickets = query.order_by(desc(PersonalTicket.created_at)).offset(skip).limit(limit).all()
    
    result = []
    for t in tickets:
        result.append(PersonalTicketResponse(
            id=t.id,
            lottery_type_id=t.lottery_type_id,
            lottery_type_name=t.lottery_type.name if t.lottery_type else "",
            lottery_type_code=t.lottery_type.code if t.lottery_type else "",
            numbers=t.numbers or [],
            special_number=t.special_number,
            draw_term=t.draw_term,
            draw_date=t.draw_date,
            cost=t.cost,
            prize=t.prize,
            status=t.status.value,
            match_count=t.match_count or 0,
            prize_tier=t.prize_tier,
            note=t.note,
            created_at=t.created_at,
            checked_at=t.checked_at
        ))
    
    return PersonalTicketListResponse(
        tickets=result,
        total=total,
        pending_count=pending_count,
        won_count=won_count,
        total_cost=Decimal(str(total_cost)),
        total_prize=Decimal(str(total_prize))
    )


@router.post("/tickets", response_model=PersonalTicketResponse, status_code=status.HTTP_201_CREATED)
async def create_ticket(
    data: PersonalTicketCreate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """建立個人彩券"""
    # 驗證彩種
    lottery_type = db.query(LotteryType).filter(LotteryType.id == data.lottery_type_id).first()
    if not lottery_type:
        raise HTTPException(status_code=400, detail="無效的彩種")
    
    # 驗證號碼數量
    expected_count = {
        "super_lotto": 6,  # 威力彩第一區 6 個
        "lotto649": 6,     # 大樂透 6 個
        "daily_cash": 5,   # 今彩539 5 個
    }
    code = lottery_type.code
    if code in expected_count and len(data.numbers) != expected_count[code]:
        raise HTTPException(
            status_code=400, 
            detail=f"{lottery_type.name}需要 {expected_count[code]} 個號碼"
        )
    
    # 建立彩券
    ticket = PersonalTicket(
        user_id=user_id,
        lottery_type_id=data.lottery_type_id,
        numbers=data.numbers,
        special_number=data.special_number,
        draw_term=data.draw_term,
        draw_date=data.draw_date,
        cost=data.cost,
        note=data.note,
        status=PersonalTicketStatus.PENDING
    )
    
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    
    return PersonalTicketResponse(
        id=ticket.id,
        lottery_type_id=ticket.lottery_type_id,
        lottery_type_name=lottery_type.name,
        lottery_type_code=lottery_type.code,
        numbers=ticket.numbers or [],
        special_number=ticket.special_number,
        draw_term=ticket.draw_term,
        draw_date=ticket.draw_date,
        cost=ticket.cost,
        prize=ticket.prize,
        status=ticket.status.value,
        match_count=ticket.match_count or 0,
        prize_tier=ticket.prize_tier,
        note=ticket.note,
        created_at=ticket.created_at,
        checked_at=ticket.checked_at
    )


@router.get("/tickets/{ticket_id}", response_model=PersonalTicketResponse)
async def get_ticket(
    ticket_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """取得單張彩券詳情"""
    ticket = db.query(PersonalTicket).filter(
        PersonalTicket.id == ticket_id,
        PersonalTicket.user_id == user_id
    ).first()
    
    if not ticket:
        raise HTTPException(status_code=404, detail="彩券不存在")
    
    return PersonalTicketResponse(
        id=ticket.id,
        lottery_type_id=ticket.lottery_type_id,
        lottery_type_name=ticket.lottery_type.name if ticket.lottery_type else "",
        lottery_type_code=ticket.lottery_type.code if ticket.lottery_type else "",
        numbers=ticket.numbers or [],
        special_number=ticket.special_number,
        draw_term=ticket.draw_term,
        draw_date=ticket.draw_date,
        cost=ticket.cost,
        prize=ticket.prize,
        status=ticket.status.value,
        match_count=ticket.match_count or 0,
        prize_tier=ticket.prize_tier,
        note=ticket.note,
        created_at=ticket.created_at,
        checked_at=ticket.checked_at
    )


@router.delete("/tickets/{ticket_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ticket(
    ticket_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """刪除彩券"""
    ticket = db.query(PersonalTicket).filter(
        PersonalTicket.id == ticket_id,
        PersonalTicket.user_id == user_id
    ).first()
    
    if not ticket:
        raise HTTPException(status_code=404, detail="彩券不存在")
    
    db.delete(ticket)
    db.commit()


@router.post("/tickets/{ticket_id}/check", response_model=CheckResultResponse)
async def check_ticket(
    ticket_id: int,
    winning_numbers: List[int],
    special_number: Optional[int] = None,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """手動對獎"""
    ticket = db.query(PersonalTicket).filter(
        PersonalTicket.id == ticket_id,
        PersonalTicket.user_id == user_id
    ).first()
    
    if not ticket:
        raise HTTPException(status_code=404, detail="彩券不存在")
    
    # 計算中獎號碼數
    user_numbers = set(ticket.numbers or [])
    winning_set = set(winning_numbers)
    matched = user_numbers & winning_set
    match_count = len(matched)
    
    # 檢查特別號
    special_matched = False
    if ticket.special_number and special_number:
        special_matched = ticket.special_number == special_number
    
    # 計算獎項 (簡化版，實際需根據彩種規則)
    prize_tier = None
    prize = Decimal("0")
    lottery_code = ticket.lottery_type.code if ticket.lottery_type else ""
    
    if lottery_code == "super_lotto":
        # 威力彩獎項判定
        if match_count == 6 and special_matched:
            prize_tier = "頭獎"
            prize = Decimal("100000000")  # 範例值
        elif match_count == 6:
            prize_tier = "貳獎"
            prize = Decimal("1500000")
        elif match_count == 5 and special_matched:
            prize_tier = "參獎"
            prize = Decimal("100000")
        elif match_count == 5:
            prize_tier = "肆獎"
            prize = Decimal("20000")
        elif match_count == 4 and special_matched:
            prize_tier = "伍獎"
            prize = Decimal("4000")
        elif match_count == 4:
            prize_tier = "陸獎"
            prize = Decimal("800")
        elif match_count == 3 and special_matched:
            prize_tier = "柒獎"
            prize = Decimal("400")
        elif match_count == 2 and special_matched:
            prize_tier = "捌獎"
            prize = Decimal("200")
        elif match_count == 3:
            prize_tier = "玖獎"
            prize = Decimal("100")
            
    elif lottery_code == "lotto649":
        # 大樂透獎項判定
        if match_count == 6:
            prize_tier = "頭獎"
            prize = Decimal("50000000")
        elif match_count == 5:
            prize_tier = "貳獎"
            prize = Decimal("25000")
        elif match_count == 4:
            prize_tier = "參獎"
            prize = Decimal("2000")
        elif match_count == 3:
            prize_tier = "肆獎"
            prize = Decimal("400")
        elif match_count == 2:
            prize_tier = "普獎"
            prize = Decimal("50")
            
    elif lottery_code == "daily_cash":
        # 今彩539獎項判定
        if match_count == 5:
            prize_tier = "頭獎"
            prize = Decimal("8000000")
        elif match_count == 4:
            prize_tier = "貳獎"
            prize = Decimal("20000")
        elif match_count == 3:
            prize_tier = "參獎"
            prize = Decimal("300")
        elif match_count == 2:
            prize_tier = "肆獎"
            prize = Decimal("50")
    
    # 更新狀態
    ticket.match_count = match_count
    ticket.prize_tier = prize_tier
    ticket.prize = prize
    ticket.status = PersonalTicketStatus.WON if prize > 0 else PersonalTicketStatus.LOST
    ticket.checked_at = datetime.now()
    
    db.commit()
    
    return CheckResultResponse(
        ticket_id=ticket.id,
        status=ticket.status.value,
        match_count=match_count,
        prize_tier=prize_tier,
        prize=prize,
        winning_numbers=winning_numbers,
        special_number=special_number
    )


@router.get("/stats", response_model=PersonalStats)
async def get_personal_stats(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """取得個人彩券統計"""
    base_query = db.query(PersonalTicket).filter(PersonalTicket.user_id == user_id)
    
    total_tickets = base_query.count()
    pending_count = base_query.filter(PersonalTicket.status == PersonalTicketStatus.PENDING).count()
    won_count = base_query.filter(PersonalTicket.status == PersonalTicketStatus.WON).count()
    lost_count = base_query.filter(PersonalTicket.status == PersonalTicketStatus.LOST).count()
    
    total_cost = db.query(func.coalesce(func.sum(PersonalTicket.cost), 0)).filter(
        PersonalTicket.user_id == user_id
    ).scalar()
    
    total_prize = db.query(func.coalesce(func.sum(PersonalTicket.prize), 0)).filter(
        PersonalTicket.user_id == user_id
    ).scalar()
    
    best_prize = db.query(func.coalesce(func.max(PersonalTicket.prize), 0)).filter(
        PersonalTicket.user_id == user_id
    ).scalar()
    
    # 勝率計算
    checked_count = won_count + lost_count
    win_rate = (won_count / checked_count * 100) if checked_count > 0 else 0
    
    # 彩種分布
    breakdown = db.query(
        LotteryType.name,
        func.count(PersonalTicket.id).label('count'),
        func.sum(PersonalTicket.cost).label('cost'),
        func.sum(PersonalTicket.prize).label('prize')
    ).join(
        PersonalTicket, LotteryType.id == PersonalTicket.lottery_type_id
    ).filter(
        PersonalTicket.user_id == user_id
    ).group_by(LotteryType.name).all()
    
    lottery_type_breakdown = [
        {
            "name": item[0],
            "count": item[1],
            "cost": float(item[2] or 0),
            "prize": float(item[3] or 0)
        }
        for item in breakdown
    ]
    
    return PersonalStats(
        total_tickets=total_tickets,
        pending_count=pending_count,
        won_count=won_count,
        lost_count=lost_count,
        total_cost=Decimal(str(total_cost)),
        total_prize=Decimal(str(total_prize)),
        profit=Decimal(str(total_prize)) - Decimal(str(total_cost)),
        win_rate=round(win_rate, 2),
        best_prize=Decimal(str(best_prize)),
        lottery_type_breakdown=lottery_type_breakdown
    )
