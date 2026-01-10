"""
SELA 樂透一路發 - 對獎與結算 API
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

# 嘗試導入自動結算服務
try:
    from app.services.auto_settle import auto_settle_service
    HAS_AUTO_SETTLE = True
except ImportError:
    HAS_AUTO_SETTLE = False


router = APIRouter(prefix="/check", tags=["Prize Check & Settlement"])


# ==================== Schema ====================

class CheckGroupRequest(BaseModel):
    """對獎單一團請求"""
    group_id: int
    auto_settle: bool = False  # 對獎後是否自動結算


class CheckByLotteryRequest(BaseModel):
    """依彩種對獎請求"""
    lottery_type: str  # power / super / daily539
    draw_term: Optional[str] = None
    draw_date: Optional[str] = None  # YYYY-MM-DD
    auto_settle: bool = False


class SettleGroupRequest(BaseModel):
    """結算單一團請求"""
    group_id: int


class CheckResult(BaseModel):
    """對獎結果"""
    success: bool
    message: str
    groups_checked: int = 0
    groups_success: int = 0
    groups_settled: int = 0
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
    settled: bool = False


class SettleResult(BaseModel):
    """結算結果"""
    success: bool
    message: str
    groups_settled: int = 0
    total_prize: float = 0
    details: Optional[List[dict]] = None


# ==================== 對獎 API ====================

@router.post("/group", response_model=GroupCheckResult)
async def check_single_group(
    data: CheckGroupRequest,
    admin_id: int = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    對獎單一團（管理員）
    
    手動對獎指定的 Group，可選擇對獎後自動結算
    """
    group = db.query(Group).filter(Group.id == data.group_id).first()
    
    if not group:
        raise HTTPException(status_code=404, detail="找不到此團")
    
    result = auto_check_service.check_group(
        db, group,
        auto_settle=data.auto_settle,
        admin_user_id=admin_id
    )
    
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
    auto_settle: bool = Query(False, description="對獎後是否自動結算"),
    admin_id: int = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    自動對獎所有待對獎團（管理員）
    
    掃描所有狀態為「已購買」的團，
    自動比對開獎資料庫中的號碼進行對獎，
    可選擇對獎後自動結算
    """
    result = auto_check_service.auto_check_all_pending(
        db,
        auto_settle=auto_settle,
        admin_user_id=admin_id
    )
    
    return CheckResult(**result)


@router.get("/pending")
async def get_pending_groups(
    admin_id: int = Depends(require_admin),
    db: Session = Depends(get_db),
    lottery_type: Optional[str] = Query(None, description="彩種篩選"),
    status: Optional[str] = Query(None, description="狀態篩選：purchased/drawn")
):
    """
    取得待處理團列表（管理員）
    
    - purchased: 待對獎
    - drawn: 待結算
    """
    query = db.query(Group)
    
    # 狀態篩選
    if status == "purchased":
        query = query.filter(Group.status == GroupStatus.PURCHASED)
    elif status == "drawn":
        query = query.filter(Group.status == GroupStatus.DRAWN)
    else:
        # 預設顯示待對獎和待結算
        query = query.filter(Group.status.in_([GroupStatus.PURCHASED, GroupStatus.DRAWN]))
    
    # 彩種篩選
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
            "total_prize": float(g.total_prize or 0),
            "ticket_count": len(g.tickets) if g.tickets else 0
        })
    
    return {
        "total": len(result),
        "groups": result
    }


# ==================== 結算 API ====================

@router.post("/settle/group", response_model=SettleResult)
async def settle_single_group(
    data: SettleGroupRequest,
    admin_id: int = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    結算單一團（管理員）
    
    對已開獎的團執行結算，分配獎金給成員
    """
    if not HAS_AUTO_SETTLE:
        raise HTTPException(status_code=500, detail="結算服務未啟用")
    
    group = db.query(Group).filter(Group.id == data.group_id).first()
    
    if not group:
        raise HTTPException(status_code=404, detail="找不到此團")
    
    result = auto_settle_service.settle_group(db, group, admin_id)
    
    return SettleResult(
        success=result.get("success", False),
        message=result.get("message", ""),
        groups_settled=1 if result.get("success") else 0,
        total_prize=result.get("total_prize_after_tax", 0),
        details=[result]
    )


@router.post("/settle/auto", response_model=SettleResult)
async def auto_settle_all(
    admin_id: int = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    自動結算所有已開獎團（管理員）
    
    掃描所有狀態為「已開獎」的團並執行結算
    """
    if not HAS_AUTO_SETTLE:
        raise HTTPException(status_code=500, detail="結算服務未啟用")
    
    result = auto_settle_service.auto_settle_all_drawn(db, admin_id)
    
    return SettleResult(**result)


@router.post("/settle/series/{series_id}", response_model=SettleResult)
async def settle_by_series(
    series_id: int,
    admin_id: int = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    結算指定系列團的所有已開獎期別（管理員）
    """
    if not HAS_AUTO_SETTLE:
        raise HTTPException(status_code=500, detail="結算服務未啟用")
    
    result = auto_settle_service.settle_by_series(db, series_id, admin_id)
    
    return SettleResult(**result)


# ==================== 統計 API ====================

@router.get("/stats")
async def get_check_stats(
    admin_id: int = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    取得對獎與結算統計（管理員）
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
    
    # 已結算獎金
    settled_prize = db.query(func.sum(Group.total_prize_after_tax)).filter(
        Group.status == GroupStatus.SETTLED
    ).scalar() or 0
    
    return {
        "status_counts": stats,
        "pending_check": stats.get("purchased", 0),
        "pending_settle": stats.get("drawn", 0),
        "settled": stats.get("settled", 0),
        "total_prize": float(total_prize),
        "settled_prize": float(settled_prize)
    }
