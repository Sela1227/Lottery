"""
SELA 樂透一路發 - 彩券開獎資訊 API
"""
from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.api.v1.admin import require_admin
from app.services.lottery_crawler import lottery_crawler


router = APIRouter(prefix="/lottery", tags=["Lottery"])


# ==================== Schema ====================

class DrawNumbers(BaseModel):
    """開獎號碼"""
    first_zone: Optional[List[int]] = None  # 威力彩第一區
    second_zone: Optional[int] = None        # 威力彩第二區
    main: Optional[List[int]] = None         # 大樂透主號
    special: Optional[int] = None            # 大樂透特別號
    numbers: Optional[List[int]] = None      # 今彩539


class LatestDraw(BaseModel):
    """最新開獎"""
    draw_date: str
    numbers: dict


class LotteryInfo(BaseModel):
    """彩種資訊"""
    lottery_type: str
    lottery_name: str
    jackpot: Optional[int] = None
    jackpot_display: Optional[str] = None
    latest_draw: Optional[LatestDraw] = None


class SyncResult(BaseModel):
    """同步結果"""
    success: bool
    message: str
    updated_at: str
    data: Optional[dict] = None


# ==================== Helper ====================

def format_jackpot(amount: Optional[int]) -> Optional[str]:
    """格式化獎金顯示"""
    if amount is None:
        return None
    if amount >= 100000000:
        return f"{amount / 100000000:.1f} 億"
    elif amount >= 10000:
        return f"{amount / 10000:.0f} 萬"
    else:
        return f"{amount:,}"


# ==================== API 端點 ====================

@router.get("/latest/{lottery_type}", response_model=LotteryInfo)
async def get_latest_draw(
    lottery_type: str,
    user_id: int = Depends(get_current_user_id)
):
    """
    取得特定彩種最新開獎資訊
    
    - lottery_type: power (威力彩), super (大樂透), daily539 (今彩539)
    """
    if lottery_type not in ["power", "super", "daily539"]:
        raise HTTPException(status_code=400, detail="不支援的彩種")
    
    try:
        data = lottery_crawler.get_latest(lottery_type)
        if not data:
            raise HTTPException(status_code=404, detail="無法取得開獎資訊")
        
        return LotteryInfo(
            lottery_type=data["lottery_type"],
            lottery_name=data["lottery_name"],
            jackpot=data["jackpot"],
            jackpot_display=format_jackpot(data["jackpot"]),
            latest_draw=LatestDraw(
                draw_date=data["latest_draw"]["draw_date"],
                numbers=data["latest_draw"]["numbers"]
            ) if data.get("latest_draw") else None
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"取得開獎資訊失敗: {str(e)}")


@router.get("/latest", response_model=dict)
async def get_all_latest(
    user_id: int = Depends(get_current_user_id)
):
    """取得所有彩種最新開獎資訊"""
    try:
        result = {}
        
        for lottery_type in ["power", "super", "daily539"]:
            data = lottery_crawler.get_latest(lottery_type)
            if data:
                result[lottery_type] = {
                    "lottery_type": data["lottery_type"],
                    "lottery_name": data["lottery_name"],
                    "jackpot": data["jackpot"],
                    "jackpot_display": format_jackpot(data["jackpot"]),
                    "latest_draw": data.get("latest_draw")
                }
        
        return {
            "updated_at": datetime.now().isoformat(),
            "lotteries": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"取得開獎資訊失敗: {str(e)}")


@router.post("/sync", response_model=SyncResult)
async def sync_lottery_data(
    admin_id: int = Depends(require_admin)
):
    """
    同步所有彩種開獎資訊（僅管理員）
    
    從 pilio.idv.tw 抓取最新開獎號碼和累積獎金
    """
    try:
        data = lottery_crawler.fetch_all()
        
        # 統計結果
        success_count = 0
        results = {}
        
        for key in ["super_lotto", "lotto649", "daily_cash"]:
            if data.get(key) and data[key].get("draws"):
                success_count += 1
                lottery_data = data[key]
                results[key] = {
                    "name": lottery_data["lottery_name"],
                    "jackpot": lottery_data["jackpot"],
                    "jackpot_display": format_jackpot(lottery_data["jackpot"]),
                    "latest_date": lottery_data["draws"][0]["draw_date"] if lottery_data["draws"] else None,
                    "draw_count": len(lottery_data["draws"])
                }
        
        return SyncResult(
            success=success_count > 0,
            message=f"成功同步 {success_count} 個彩種",
            updated_at=data["updated_at"],
            data=results
        )
    except Exception as e:
        return SyncResult(
            success=False,
            message=f"同步失敗: {str(e)}",
            updated_at=datetime.now().isoformat(),
            data=None
        )


@router.get("/history/{lottery_type}")
async def get_draw_history(
    lottery_type: str,
    limit: int = Query(10, ge=1, le=50),
    user_id: int = Depends(get_current_user_id)
):
    """
    取得開獎歷史記錄
    
    - lottery_type: power (威力彩), super (大樂透), daily539 (今彩539)
    - limit: 筆數限制 (1-50)
    """
    if lottery_type not in ["power", "super", "daily539"]:
        raise HTTPException(status_code=400, detail="不支援的彩種")
    
    try:
        if lottery_type == "power":
            data = lottery_crawler.fetch_super_lotto()
        elif lottery_type == "super":
            data = lottery_crawler.fetch_lotto649()
        else:
            data = lottery_crawler.fetch_daily_cash()
        
        if not data:
            raise HTTPException(status_code=404, detail="無法取得開獎資訊")
        
        return {
            "lottery_type": data["lottery_type"],
            "lottery_name": data["lottery_name"],
            "jackpot": data["jackpot"],
            "jackpot_display": format_jackpot(data["jackpot"]),
            "draws": data["draws"][:limit]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"取得開獎歷史失敗: {str(e)}")
