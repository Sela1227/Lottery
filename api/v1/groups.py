"""
SELA 樂透一路發 - 單期團 API
"""
from typing import List
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.models import LotteryType, Group, GroupStatus, MemberStatus, Ticket
from app.schemas.group import (
    LotteryTypeResponse, GroupCreate, GroupResponse, GroupListResponse,
    DrawResultInput, TicketCreate, TicketUpdate, TicketResponse,
    SettlementPreview, SettlementResult
)
from app.services.series_service import series_service
from app.services.group_service import group_service, ticket_service, prize_checker
from app.services.settlement_service import settlement_service


router = APIRouter(tags=["Groups"])


# ==================== 彩種 ====================

@router.get("/lottery-types", response_model=List[LotteryTypeResponse])
async def list_lottery_types(
    db: Session = Depends(get_db)
):
    """取得所有彩種"""
    types = db.query(LotteryType).filter(
        LotteryType.is_active == True
    ).order_by(LotteryType.sort_order).all()
    
    return [LotteryTypeResponse.model_validate(t) for t in types]


# ==================== 單期團 ====================

@router.post("/series/{series_id}/groups", response_model=GroupResponse, status_code=status.HTTP_201_CREATED)
async def create_group(
    series_id: int,
    data: GroupCreate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """建立單期團（開新期）"""
    series = series_service.get_by_id(db, series_id)
    if not series:
        raise HTTPException(status_code=404, detail="系列團不存在")
    
    if not series_service.is_admin(db, series_id, user_id):
        raise HTTPException(status_code=403, detail="只有管理員可以開新期")
    
    # 檢查是否有未結算的單期團
    active_group = db.query(Group).filter(
        Group.series_id == series_id,
        Group.status.notin_([GroupStatus.SETTLED])
    ).first()
    
    if active_group:
        raise HTTPException(
            status_code=400,
            detail=f"第{active_group.period_number}期尚未結算，無法開新期"
        )
    
    try:
        group = group_service.create(db, series, data, user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    return GroupResponse.model_validate(group)


@router.get("/series/{series_id}/groups", response_model=List[GroupListResponse])
async def list_groups(
    series_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """取得系列團的單期團列表"""
    series = series_service.get_by_id(db, series_id)
    if not series:
        raise HTTPException(status_code=404, detail="系列團不存在")
    
    member = series_service.get_member(db, series_id, user_id)
    if not member or member.status != MemberStatus.ACTIVE:
        raise HTTPException(status_code=403, detail="您不是此系列團的成員")
    
    groups = group_service.get_series_groups(db, series_id)
    
    result = []
    for g in groups:
        result.append(GroupListResponse(
            id=g.id,
            period_number=g.period_number,
            lottery_type_code=g.lottery_type.code,
            lottery_type_name=g.lottery_type.name,
            draw_term=g.draw_term,
            draw_date=g.draw_date,
            status=g.status,
            total_pool=g.total_pool,
            total_spent=g.total_spent,
            total_prize=g.total_prize
        ))
    
    return result


@router.get("/groups/{group_id}", response_model=GroupResponse)
async def get_group(
    group_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """取得單期團詳情"""
    group = group_service.get_by_id(db, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="單期團不存在")
    
    member = series_service.get_member(db, group.series_id, user_id)
    if not member or member.status != MemberStatus.ACTIVE:
        raise HTTPException(status_code=403, detail="您不是此系列團的成員")
    
    return GroupResponse.model_validate(group)


@router.post("/groups/{group_id}/lock")
async def lock_group(
    group_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """鎖定集資"""
    group = group_service.get_by_id(db, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="單期團不存在")
    
    if not series_service.is_admin(db, group.series_id, user_id):
        raise HTTPException(status_code=403, detail="只有管理員可以鎖定")
    
    try:
        group = group_service.lock_collection(db, group, user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    return {"success": True, "message": "已鎖定集資", "status": group.status.value}


@router.post("/groups/{group_id}/purchase")
async def record_purchase(
    group_id: int,
    total_spent: Decimal,
    total_tickets: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """記錄購買"""
    group = group_service.get_by_id(db, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="單期團不存在")
    
    if not series_service.is_admin(db, group.series_id, user_id):
        raise HTTPException(status_code=403, detail="只有管理員可以記錄購買")
    
    if total_spent > group.total_pool:
        raise HTTPException(status_code=400, detail="購買金額不能超過資金池")
    
    try:
        group = group_service.record_purchase(db, group, total_spent, total_tickets, user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    return {
        "success": True,
        "message": "已記錄購買",
        "total_spent": float(total_spent),
        "total_carryover": float(group.total_carryover)
    }


@router.post("/groups/{group_id}/draw")
async def input_draw_result(
    group_id: int,
    data: DrawResultInput,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """輸入開獎結果"""
    group = group_service.get_by_id(db, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="單期團不存在")
    
    if not series_service.is_admin(db, group.series_id, user_id):
        raise HTTPException(status_code=403, detail="只有管理員可以輸入開獎結果")
    
    try:
        group = group_service.input_draw_result(db, group, data, user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    return {"success": True, "message": "已輸入開獎結果", "winning_numbers": data.winning_numbers}


@router.post("/groups/{group_id}/check-tickets")
async def check_all_tickets(
    group_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """對獎所有彩券"""
    group = group_service.get_by_id(db, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="單期團不存在")
    
    if not series_service.is_admin(db, group.series_id, user_id):
        raise HTTPException(status_code=403, detail="只有管理員可以對獎")
    
    try:
        total_prize = prize_checker.check_all_tickets(db, group)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    return {
        "success": True,
        "total_prize": float(total_prize),
        "total_prize_after_tax": float(group.total_prize_after_tax)
    }


# ==================== 彩券 ====================

@router.post("/groups/{group_id}/tickets", response_model=TicketResponse, status_code=status.HTTP_201_CREATED)
async def create_ticket(
    group_id: int,
    data: TicketCreate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """建立彩券"""
    group = group_service.get_by_id(db, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="單期團不存在")
    
    if not series_service.is_admin(db, group.series_id, user_id):
        raise HTTPException(status_code=403, detail="只有管理員可以新增彩券")
    
    if group.status not in [GroupStatus.LOCKED, GroupStatus.PURCHASED]:
        raise HTTPException(status_code=400, detail="只能在鎖定後新增彩券")
    
    ticket = ticket_service.create(db, group, data.numbers, data.bet_count, data.cost)
    return TicketResponse.model_validate(ticket)


@router.get("/groups/{group_id}/tickets", response_model=List[TicketResponse])
async def list_tickets(
    group_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """取得單期團的所有彩券"""
    group = group_service.get_by_id(db, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="單期團不存在")
    
    member = series_service.get_member(db, group.series_id, user_id)
    if not member or member.status != MemberStatus.ACTIVE:
        raise HTTPException(status_code=403, detail="您不是此系列團的成員")
    
    tickets = ticket_service.get_group_tickets(db, group_id)
    return [TicketResponse.model_validate(t) for t in tickets]


@router.put("/tickets/{ticket_id}", response_model=TicketResponse)
async def update_ticket(
    ticket_id: int,
    data: TicketUpdate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """更新彩券"""
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="彩券不存在")
    
    if not series_service.is_admin(db, ticket.group.series_id, user_id):
        raise HTTPException(status_code=403, detail="只有管理員可以更新彩券")
    
    ticket = ticket_service.update(db, ticket, data.numbers, data.image_url)
    return TicketResponse.model_validate(ticket)


# ==================== 結算 ====================

@router.get("/groups/{group_id}/settlement-preview", response_model=SettlementPreview)
async def preview_settlement(
    group_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """結算預覽"""
    group = group_service.get_by_id(db, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="單期團不存在")
    
    member = series_service.get_member(db, group.series_id, user_id)
    if not member or member.status != MemberStatus.ACTIVE:
        raise HTTPException(status_code=403, detail="您不是此系列團的成員")
    
    try:
        preview = settlement_service.calculate_settlement(db, group)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    return SettlementPreview(**preview)


@router.post("/groups/{group_id}/settle", response_model=SettlementResult)
async def execute_settlement(
    group_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """執行結算"""
    group = group_service.get_by_id(db, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="單期團不存在")
    
    if not series_service.is_admin(db, group.series_id, user_id):
        raise HTTPException(status_code=403, detail="只有管理員可以結算")
    
    try:
        snapshot = settlement_service.execute_settlement(db, group, user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    return SettlementResult(
        group_id=group_id,
        success=True,
        message="結算完成",
        snapshot_id=snapshot.id
    )
