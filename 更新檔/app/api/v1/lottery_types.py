"""
SELA 樂透一路發 - 彩種 API
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.models import LotteryType


router = APIRouter(prefix="/lottery-types", tags=["彩種"])


class LotteryTypeResponse(BaseModel):
    """彩種回應"""
    code: str
    name: str
    description: str
    price_per_bet: int
    number_rules: dict
    prize_structure: dict
    draw_days: list
    draw_time: str
    sort_order: int
    is_active: bool
    
    class Config:
        from_attributes = True


@router.get("", response_model=List[LotteryTypeResponse])
async def get_lottery_types(db: Session = Depends(get_db)):
    """取得所有彩種"""
    lottery_types = db.query(LotteryType).filter(
        LotteryType.is_active == True
    ).order_by(LotteryType.sort_order).all()
    
    return lottery_types


@router.get("/{code}", response_model=LotteryTypeResponse)
async def get_lottery_type(code: str, db: Session = Depends(get_db)):
    """取得單一彩種"""
    lottery_type = db.query(LotteryType).filter(
        LotteryType.code == code
    ).first()
    
    if not lottery_type:
        raise HTTPException(status_code=404, detail="彩種不存在")
    
    return lottery_type
