"""
SELA 樂透一路發 - 用戶 API
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.services.auth.user_service import user_service
from app.schemas.user import UserResponse, UserUpdate


router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """取得目前登入用戶資料"""
    user = user_service.get_by_id(db, user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用戶不存在"
        )
    
    return user


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    data: UserUpdate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """更新目前登入用戶資料"""
    user = user_service.get_by_id(db, user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用戶不存在"
        )
    
    updated_user = user_service.update(db, user, data)
    return updated_user


@router.get("/me/wallet")
async def get_wallet_balance(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """取得錢包餘額"""
    user = user_service.get_by_id(db, user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用戶不存在"
        )
    
    return {
        "balance": float(user.wallet_balance),
        "currency": "TWD"
    }
