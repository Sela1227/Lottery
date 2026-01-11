"""
SELA 樂透一路發 - 成員異動申請 API
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.models.user import User
from app.models.member import GroupMember, MemberStatus
from app.models.member_request import MemberRequest, RequestStatus
from app.schemas.member_request import (
    ReduceRequest, WithdrawRequest, ReviewRequest,
    MemberRequestResponse, MemberRequestListResponse,
    MemberRequestCreateResponse, MemberRequestReviewResponse
)
from app.services.member_service import MemberService


router = APIRouter(prefix="/member-requests", tags=["成員異動"])


def get_user(db: Session, user_id: int) -> User:
    """取得用戶"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用戶不存在")
    return user


def _to_response(request: MemberRequest, db: Session) -> MemberRequestResponse:
    """轉換為回應格式"""
    # 取得用戶名稱
    user_name = None
    if request.user:
        user_name = request.user.nickname or request.user.display_name
    
    # 取得審核者名稱
    reviewer_name = None
    if request.reviewer:
        reviewer_name = request.reviewer.nickname or request.reviewer.display_name
    
    # 取得集資名稱
    series_name = None
    if request.series:
        series_name = request.series.name
    
    return MemberRequestResponse(
        id=request.id,
        series_id=request.series_id,
        series_name=series_name,
        user_id=request.user_id,
        user_name=user_name,
        request_type=request.request_type.value,
        request_type_display=request.type_display,
        amount=request.amount,
        pool_share_before=request.pool_share_before,
        status=request.status.value,
        status_display=request.status_display,
        reason=request.reason,
        reviewed_by=request.reviewed_by,
        reviewer_name=reviewer_name,
        reviewed_at=request.reviewed_at,
        review_note=request.review_note,
        actual_amount=request.actual_amount,
        created_at=request.created_at
    )


# ==================== 申請人 API ====================

@router.post("/series/{series_id}/reduce")
async def create_reduce_request(
    series_id: int,
    data: ReduceRequest,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """申請減碼"""
    service = MemberService(db)
    success, message, request_id, auto_approved = service.create_reduce_request(
        series_id=series_id,
        user_id=user_id,
        amount=data.amount,
        reason=data.reason
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    return {
        "success": True,
        "message": message,
        "request_id": request_id,
        "auto_approved": auto_approved
    }


@router.post("/series/{series_id}/withdraw", response_model=MemberRequestCreateResponse)
async def create_withdraw_request(
    series_id: int,
    data: WithdrawRequest,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """申請退出"""
    service = MemberService(db)
    success, message, request_id = service.create_withdraw_request(
        series_id=series_id,
        user_id=user_id,
        reason=data.reason
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    return MemberRequestCreateResponse(
        success=True,
        message=message,
        request_id=request_id
    )


@router.post("/{request_id}/cancel")
async def cancel_request(
    request_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """取消申請"""
    service = MemberService(db)
    success, message = service.cancel_request(request_id, user_id)
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    return {"success": True, "message": message}


@router.get("/my", response_model=list[MemberRequestResponse])
async def get_my_requests(
    series_id: Optional[int] = Query(None),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """取得我的申請"""
    service = MemberService(db)
    requests = service.get_user_requests(user_id, series_id)
    return [_to_response(r, db) for r in requests]


# ==================== 管理員 API ====================

@router.get("/series/{series_id}", response_model=MemberRequestListResponse)
async def get_series_requests(
    series_id: int,
    status: Optional[str] = Query(None),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """取得集資的所有申請(管理員)"""
    # 檢查是否為管理員
    member = db.query(GroupMember).filter(
        GroupMember.series_id == series_id,
        GroupMember.user_id == user_id,
        GroupMember.status == MemberStatus.ACTIVE
    ).first()
    
    if not member or not member.is_admin:
        raise HTTPException(status_code=403, detail="您沒有權限查看")
    
    service = MemberService(db)
    
    if status == "pending":
        requests = service.get_pending_requests(series_id)
    else:
        requests = service.get_all_requests(series_id)
    
    pending_count = len([r for r in requests if r.status == RequestStatus.PENDING])
    
    return MemberRequestListResponse(
        requests=[_to_response(r, db) for r in requests],
        total=len(requests),
        pending_count=pending_count
    )


@router.post("/{request_id}/review", response_model=MemberRequestReviewResponse)
async def review_request(
    request_id: int,
    data: ReviewRequest,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """審核申請(管理員)"""
    service = MemberService(db)
    success, message, actual_amount = service.review_request(
        request_id=request_id,
        reviewer_id=user_id,
        approved=data.approved,
        note=data.note
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    # 取得更新後的申請
    request = db.query(MemberRequest).filter(MemberRequest.id == request_id).first()
    
    return MemberRequestReviewResponse(
        success=True,
        message=message,
        request_id=request_id,
        new_status=request.status.value,
        actual_amount=actual_amount
    )


@router.get("/series/{series_id}/pending-count")
async def get_pending_count(
    series_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """取得待審核數量"""
    count = db.query(MemberRequest).filter(
        MemberRequest.series_id == series_id,
        MemberRequest.status == RequestStatus.PENDING
    ).count()
    
    return {"pending_count": count}