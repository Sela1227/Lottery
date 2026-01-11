"""
SELA 樂透一路發 - 系列團 API
"""
from typing import List
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.models import GroupMember, MemberStatus, SeriesStatus
from app.models.series import GroupSeries, SeriesInvitation
from app.schemas.series import (
    SeriesCreate, SeriesUpdate, SeriesResponse, SeriesListResponse,
    InvitationCreate, InvitationResponse, JoinByInvitation,
    MemberResponse, MemberPoolUpdate
)
from app.services.series_service import series_service


router = APIRouter(prefix="/series", tags=["Series"])


@router.post("", response_model=SeriesResponse, status_code=status.HTTP_201_CREATED)
async def create_series(
    data: SeriesCreate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """建立系列團"""
    series = series_service.create(db, user_id, data)
    
    # 補充回應資料
    response = SeriesResponse.model_validate(series)
    response.member_count = 1
    response.my_pool_share = data.initial_pool_share
    response.my_role = "admin"
    return response


@router.get("", response_model=List[SeriesListResponse])
async def list_my_series(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """取得我參與的系列團"""
    series_list = series_service.get_user_series(db, user_id)
    
    result = []
    for series in series_list:
        member = series_service.get_member(db, series.id, user_id)
        member_count = db.query(GroupMember).filter(
            GroupMember.series_id == series.id,
            GroupMember.status == MemberStatus.ACTIVE
        ).count()
        
        result.append(SeriesListResponse(
            id=series.id,
            name=series.name,
            status=series.status,
            current_pool=series.current_pool,
            total_periods=series.total_periods,
            member_count=member_count,
            my_pool_share=member.pool_share if member else Decimal("0"),
            my_role=member.role.value if member else "none",
            lottery_types=series.allowed_lottery_types
        ))
    
    return result


@router.get("/{series_id}", response_model=SeriesResponse)
async def get_series(
    series_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """取得系列團詳情"""
    series = series_service.get_by_id(db, series_id)
    if not series:
        raise HTTPException(status_code=404, detail="系列團不存在")
    
    # 檢查權限(必須是成員)
    member = series_service.get_member(db, series_id, user_id)
    if not member or member.status != MemberStatus.ACTIVE:
        raise HTTPException(status_code=403, detail="您不是此系列團的成員")
    
    member_count = db.query(GroupMember).filter(
        GroupMember.series_id == series_id,
        GroupMember.status == MemberStatus.ACTIVE
    ).count()
    
    response = SeriesResponse.model_validate(series)
    response.member_count = member_count
    response.my_pool_share = member.pool_share
    response.my_role = member.role.value
    return response


@router.put("/{series_id}", response_model=SeriesResponse)
async def update_series(
    series_id: int,
    data: SeriesUpdate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """更新系列團"""
    series = series_service.get_by_id(db, series_id)
    if not series:
        raise HTTPException(status_code=404, detail="系列團不存在")
    
    # 檢查權限(必須是管理員)
    if not series_service.is_admin(db, series_id, user_id):
        raise HTTPException(status_code=403, detail="只有管理員可以修改")
    
    series = series_service.update(db, series, data, user_id)
    return SeriesResponse.model_validate(series)


@router.post("/{series_id}/end")
async def end_series(
    series_id: int,
    reason: str = "手動結束",
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """結束系列團"""
    series = series_service.get_by_id(db, series_id)
    if not series:
        raise HTTPException(status_code=404, detail="系列團不存在")
    
    if not series_service.is_admin(db, series_id, user_id):
        raise HTTPException(status_code=403, detail="只有管理員可以結束")
    
    if series.status == SeriesStatus.ENDED:
        raise HTTPException(status_code=400, detail="系列團已結束")
    
    series = series_service.end_series(db, series, user_id, reason)
    return {"success": True, "message": "系列團已結束"}


# ==================== 邀請碼 ====================

@router.post("/{series_id}/invitations", response_model=InvitationResponse)
async def create_invitation(
    series_id: int,
    data: InvitationCreate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """建立邀請碼"""
    series = series_service.get_by_id(db, series_id)
    if not series:
        raise HTTPException(status_code=404, detail="系列團不存在")
    
    if not series_service.is_admin(db, series_id, user_id):
        raise HTTPException(status_code=403, detail="只有管理員可以建立邀請碼")
    
    invitation = series_service.create_invitation(db, series_id, user_id, data)
    return InvitationResponse.model_validate(invitation)


@router.post("/join", response_model=MemberResponse)
async def join_by_invitation(
    data: JoinByInvitation,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """透過邀請碼加入系列團"""
    invitation = series_service.get_invitation_by_code(db, data.code)
    if not invitation:
        raise HTTPException(status_code=404, detail="邀請碼不存在")
    
    if not invitation.is_valid:
        raise HTTPException(status_code=400, detail="邀請碼已失效")
    
    series = invitation.series
    if series.status != SeriesStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="系列團已結束或暫停")
    
    member, is_new = series_service.add_member(
        db, series, user_id, data.initial_pool_share, invitation
    )
    
    if not is_new:
        raise HTTPException(status_code=400, detail="您已是此系列團的成員")
    
    return MemberResponse(
        id=member.id,
        user_id=member.user_id,
        display_name=member.user.nickname or member.user.display_name,
        picture_url=member.user.picture_url,
        role=member.role.value,
        status=member.status.value,
        pool_share=member.pool_share,
        ratio=member.current_ratio,
        total_invested=member.total_invested,
        total_prize_received=member.total_prize_received,
        joined_at=member.joined_at
    )


# ==================== 成員 ====================

@router.get("/{series_id}/members", response_model=List[MemberResponse])
async def list_members(
    series_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """取得系列團成員列表"""
    series = series_service.get_by_id(db, series_id)
    if not series:
        raise HTTPException(status_code=404, detail="系列團不存在")
    
    # 檢查權限
    my_member = series_service.get_member(db, series_id, user_id)
    if not my_member or my_member.status != MemberStatus.ACTIVE:
        raise HTTPException(status_code=403, detail="您不是此系列團的成員")
    
    members = series_service.get_members(db, series_id)
    
    result = []
    for member in members:
        result.append(MemberResponse(
            id=member.id,
            user_id=member.user_id,
            display_name=member.user.nickname or member.user.display_name,
            picture_url=member.user.picture_url,
            role=member.role.value,
            status=member.status.value,
            pool_share=member.pool_share,
            ratio=member.current_ratio,
            total_invested=member.total_invested,
            total_prize_received=member.total_prize_received,
            joined_at=member.joined_at
        ))
    
    return result


@router.post("/{series_id}/members/me/topup", response_model=MemberResponse)
async def topup_my_pool(
    series_id: int,
    data: MemberPoolUpdate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """加碼(增加我的資金池份額)"""
    series = series_service.get_by_id(db, series_id)
    if not series:
        raise HTTPException(status_code=404, detail="系列團不存在")
    
    if series.status != SeriesStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="系列團已結束或暫停")
    
    member = series_service.get_member(db, series_id, user_id)
    if not member or member.status != MemberStatus.ACTIVE:
        raise HTTPException(status_code=403, detail="您不是此系列團的成員")
    
    member = series_service.topup_member(db, member, data.amount, user_id)
    
    return MemberResponse(
        id=member.id,
        user_id=member.user_id,
        display_name=member.user.nickname or member.user.display_name,
        picture_url=member.user.picture_url,
        role=member.role.value,
        status=member.status.value,
        pool_share=member.pool_share,
        ratio=member.current_ratio,
        total_invested=member.total_invested,
        total_prize_received=member.total_prize_received,
        joined_at=member.joined_at
    )

@router.delete("/{series_id}")
async def delete_series(
    series_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """刪除集資（僅限管理員且成員數為1時）- 實際為軟刪除，標記為已結束"""
    series = db.query(GroupSeries).filter(GroupSeries.id == series_id).first()
    
    if not series:
        raise HTTPException(status_code=404, detail="集資不存在")
    
    # 檢查是否為管理員
    member = db.query(GroupMember).filter(
        GroupMember.series_id == series_id,
        GroupMember.user_id == user_id,
        GroupMember.status == MemberStatus.ACTIVE
    ).first()
    
    if not member or not member.is_admin:
        raise HTTPException(status_code=403, detail="只有管理員可以刪除集資")
    
    # 檢查成員數
    active_members = db.query(GroupMember).filter(
        GroupMember.series_id == series_id,
        GroupMember.status == MemberStatus.ACTIVE
    ).count()
    
    if active_members > 1:
        raise HTTPException(status_code=400, detail="集資還有其他成員，無法刪除")
    
    # 軟刪除：標記集資為已結束，成員為已退出
    series.status = SeriesStatus.ENDED
    member.status = MemberStatus.LEFT
    
    db.commit()
    
    return {"success": True, "message": "集資已刪除"}
