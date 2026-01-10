"""
SELA 樂透一路發 - 對獎 API
"""
from typing import Optional, List
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.core.security import require_admin, get_current_user_id
from app.models.group import Group, GroupStatus
from app.models.lottery_type import LotteryType
from app.services.auto_check import auto_check_service


router = APIRouter(prefix="/check", tags=["Prize Check"])


# ==================== Schema ====================

class CheckGroupRequest(BaseModel):
    """對獎單一團請求"""
    group_id: int


class CheckByLotteryRequest(BaseModel):
    """依彩種對獎請求"""
    lottery_type: str  # power / super / daily539
    draw_term: Optional[str] = None
    draw_date: Optional[str] = None  # YYYY-MM-DD


class CheckResult(BaseModel):
    """對獎結果"""
    success: bool
    message: str
    groups_checked: int = 0
    groups_success: int = 0
    total_prize: float = 0
    details: Optional[List[dict]] = None


class GroupCheckResult(BaseModel):
    """單團對獎結果"""
    success: bool
    group_id: int
    message: str
    tickets_checked: int = 0
    winning_tickets: int = 0
    total_prize: float = 0
    winning_numbers: Optional[dict] = None


# ==================== API 端點 ====================

@router.post("/group", response_model=GroupCheckResult)
async def check_single_group(
    data: CheckGroupRequest,
    admin_id: int = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    對獎單一團（管理員）
    
    手動對獎指定的 Group
    """
    group = db.query(Group).filter(Group.id == data.group_id).first()
    
    if not group:
        raise HTTPException(status_code=404, detail="找不到此團")
    
    result = auto_check_service.check_group(db, group)
    
    return GroupCheckResult(**result)


@router.post("/by-lottery", response_model=CheckResult)
async def check_by_lottery_type(
    data: CheckByLotteryRequest,
    admin_id: int = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    依彩種對獎（管理員）
    
    對獎指定彩種、指定期數或日期的所有待對獎團
    """
    draw_date_parsed = None
    if data.draw_date:
        try:
            draw_date_parsed = date.fromisoformat(data.draw_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="日期格式錯誤，請用 YYYY-MM-DD")
    
    if not data.draw_term and not draw_date_parsed:
        raise HTTPException(status_code=400, detail="需要提供 draw_term 或 draw_date")
    
    result = auto_check_service.auto_check_by_lottery_type(
        db,
        lottery_type_code=data.lottery_type,
        draw_term=data.draw_term,
        draw_date=draw_date_parsed
    )
    
    return CheckResult(**result)


@router.post("/auto", response_model=CheckResult)
async def auto_check_all(
    admin_id: int = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    自動對獎所有待對獎團（管理員）
    
    掃描所有狀態為「已購買」的團，
    自動比對開獎資料庫中的號碼進行對獎
    """
    result = auto_check_service.auto_check_all_pending(db)
    
    return CheckResult(**result)


@router.get("/pending")
async def get_pending_groups(
    admin_id: int = Depends(require_admin),
    db: Session = Depends(get_db),
    lottery_type: Optional[str] = Query(None, description="彩種篩選")
):
    """
    取得待對獎團列表（管理員）
    """
    query = db.query(Group).filter(Group.status == GroupStatus.PURCHASED)
    
    if lottery_type:
        lt = db.query(LotteryType).filter(LotteryType.code == lottery_type).first()
        if lt:
            query = query.filter(Group.lottery_type_id == lt.id)
    
    groups = query.order_by(Group.draw_date.desc()).all()
    
    result = []
    for g in groups:
        lt = db.query(LotteryType).filter(LotteryType.id == g.lottery_type_id).first()
        result.append({
            "id": g.id,
            "series_id": g.series_id,
            "period_number": g.period_number,
            "lottery_type": lt.code if lt else None,
            "lottery_name": lt.name if lt else None,
            "draw_term": g.draw_term,
            "draw_date": str(g.draw_date) if g.draw_date else None,
            "status": g.status.value,
            "ticket_count": len(g.tickets) if g.tickets else 0
        })
    
    return {
        "total": len(result),
        "groups": result
    }


@router.get("/stats")
async def get_check_stats(
    admin_id: int = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    取得對獎統計（管理員）
    """
    from sqlalchemy import func
    
    # 各狀態數量
    status_counts = db.query(
        Group.status,
        func.count(Group.id)
    ).group_by(Group.status).all()
    
    stats = {s.value: 0 for s in GroupStatus}
    for status, count in status_counts:
        stats[status.value] = count
    
    # 總獎金
    total_prize = db.query(func.sum(Group.total_prize)).filter(
        Group.status.in_([GroupStatus.DRAWN, GroupStatus.SETTLED])
    ).scalar() or 0
    
    return {
        "status_counts": stats,
        "pending_check": stats.get("purchased", 0),
        "checked": stats.get("drawn", 0) + stats.get("settled", 0),
        "total_prize": float(total_prize)
    }
