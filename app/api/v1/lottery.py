"""
SELA 樂透一路發 - 彩券開獎資訊 API
"""
from typing import Optional, List
from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from pydantic import BaseModel

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.api.v1.admin import require_admin
from app.services.lottery_crawler import lottery_crawler
from app.models.lottery_draw import LotteryDraw


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

LOTTERY_NAMES = {
    'power': '威力彩',
    'super': '大樂透',
    'daily539': '今彩539'
}


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


def parse_date(date_str: str) -> date:
    """解析日期字串"""
    if not date_str:
        return date.today()
    for fmt in ['%Y/%m/%d', '%Y-%m-%d', '%Y.%m.%d']:
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    return date.today()


# ==================== 資料庫操作 ====================

def get_latest_from_db(db: Session, lottery_type: str) -> Optional[LotteryDraw]:
    """從資料庫取得最新一期"""
    return db.query(LotteryDraw).filter(
        LotteryDraw.lottery_type == lottery_type
    ).order_by(desc(LotteryDraw.draw_date), desc(LotteryDraw.draw_term)).first()


def save_to_db(db: Session, lottery_type: str, draw_term: str, 
               draw_date: date, numbers: dict, jackpot: Optional[int] = None):
    """儲存或更新開獎記錄"""
    existing = db.query(LotteryDraw).filter(
        LotteryDraw.lottery_type == lottery_type,
        LotteryDraw.draw_term == draw_term
    ).first()
    
    if existing:
        # 只更新獎金（號碼不會變）
        if jackpot is not None:
            existing.jackpot = jackpot
            existing.updated_at = datetime.utcnow()
        return existing
    else:
        # 新增記錄
        new_draw = LotteryDraw(
            lottery_type=lottery_type,
            draw_term=draw_term,
            draw_date=draw_date,
            numbers=numbers,
            jackpot=jackpot
        )
        db.add(new_draw)
        return new_draw


# ==================== API 端點 ====================

@router.get("/db-status")
async def check_db_status(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """檢查資料庫狀態（測試用）"""
    try:
        count = db.query(LotteryDraw).count()
        latest = get_latest_from_db(db, 'power')
        return {
            "status": "ok",
            "table": "lottery_draws",
            "total_records": count,
            "latest_power": {
                "term": latest.draw_term,
                "date": latest.draw_date.isoformat()
            } if latest else None
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.get("/latest/{lottery_type}", response_model=LotteryInfo)
async def get_latest_draw(
    lottery_type: str,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """
    取得特定彩種最新開獎資訊
    
    - lottery_type: power (威力彩), super (大樂透), daily539 (今彩539)
    """
    if lottery_type not in ["power", "super", "daily539"]:
        raise HTTPException(status_code=400, detail="不支援的彩種")
    
    # 先嘗試從資料庫讀取
    db_record = get_latest_from_db(db, lottery_type)
    if db_record:
        return LotteryInfo(
            lottery_type=lottery_type,
            lottery_name=db_record.lottery_name,
            jackpot=db_record.jackpot,
            jackpot_display=format_jackpot(db_record.jackpot),
            latest_draw=LatestDraw(
                draw_date=db_record.draw_date.isoformat(),
                numbers=db_record.numbers
            )
        )
    
    # 資料庫沒有，即時爬取（Fallback）
    try:
        data = lottery_crawler.get_latest(lottery_type)
        if not data:
            raise HTTPException(status_code=404, detail="無法取得開獎資訊")
        
        return LotteryInfo(
            lottery_type=data["lottery_type"],
            lottery_name=data["lottery_name"],
            jackpot=data.get("jackpot"),
            jackpot_display=format_jackpot(data.get("jackpot")),
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
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """取得所有彩種最新開獎資訊"""
    result = {}
    
    for lottery_type in ["power", "super", "daily539"]:
        # 先從資料庫讀
        db_record = get_latest_from_db(db, lottery_type)
        if db_record:
            result[lottery_type] = {
                "lottery_type": lottery_type,
                "lottery_name": db_record.lottery_name,
                "jackpot": db_record.jackpot,
                "jackpot_display": format_jackpot(db_record.jackpot),
                "latest_draw": {
                    "draw_date": db_record.draw_date.isoformat(),
                    "numbers": db_record.numbers
                }
            }
        else:
            # Fallback 到即時爬取
            try:
                data = lottery_crawler.get_latest(lottery_type)
                if data:
                    result[lottery_type] = {
                        "lottery_type": data["lottery_type"],
                        "lottery_name": data["lottery_name"],
                        "jackpot": data.get("jackpot"),
                        "jackpot_display": format_jackpot(data.get("jackpot")),
                        "latest_draw": data.get("latest_draw")
                    }
            except:
                pass  # 忽略錯誤，繼續下一個
    
    return {
        "updated_at": datetime.now().isoformat(),
        "lotteries": result
    }


@router.post("/sync", response_model=SyncResult)
async def sync_lottery_data(
    db: Session = Depends(get_db),
    admin_id: int = Depends(require_admin)
):
    """
    同步所有彩種開獎資訊（僅管理員）
    
    從外部來源抓取最新開獎號碼並儲存到資料庫
    """
    try:
        data = lottery_crawler.fetch_all()
        synced = []
        
        # 處理威力彩
        if data.get("power") and data["power"].get("numbers"):
            power = data["power"]
            draw_date = parse_date(power.get("date", ""))
            draw_term = power.get("term", f"power_{draw_date}")
            numbers = power["numbers"]
            if isinstance(numbers, dict):
                save_to_db(db, "power", draw_term, draw_date, numbers, power.get("jackpot"))
                synced.append("威力彩")
        
        # 處理大樂透
        if data.get("super") and data["super"].get("numbers"):
            super_lotto = data["super"]
            draw_date = parse_date(super_lotto.get("date", ""))
            draw_term = super_lotto.get("term", f"super_{draw_date}")
            numbers = super_lotto["numbers"]
            if isinstance(numbers, dict):
                save_to_db(db, "super", draw_term, draw_date, numbers, super_lotto.get("jackpot"))
                synced.append("大樂透")
        
        # 處理今彩539
        if data.get("daily539") and data["daily539"].get("numbers"):
            daily = data["daily539"]
            draw_date = parse_date(daily.get("date", ""))
            draw_term = daily.get("term", f"daily539_{draw_date}")
            nums = daily["numbers"]
            # 統一格式
            if isinstance(nums, list):
                numbers = {"numbers": nums}
            else:
                numbers = nums
            save_to_db(db, "daily539", draw_term, draw_date, numbers, daily.get("jackpot"))
            synced.append("今彩539")
        
        db.commit()
        
        return SyncResult(
            success=True,
            message=f"成功同步: {', '.join(synced)}" if synced else "無新資料",
            updated_at=datetime.now().isoformat(),
            data={"synced_types": synced}
        )
    except Exception as e:
        db.rollback()
        return SyncResult(
            success=False,
            message=f"同步失敗: {str(e)}",
            updated_at=datetime.now().isoformat()
        )


@router.get("/history/{lottery_type}")
async def get_draw_history(
    lottery_type: str,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """取得開獎歷史記錄"""
    if lottery_type not in ["power", "super", "daily539"]:
        raise HTTPException(status_code=400, detail="不支援的彩種")
    
    # 查詢資料庫
    draws = db.query(LotteryDraw).filter(
        LotteryDraw.lottery_type == lottery_type
    ).order_by(desc(LotteryDraw.draw_date), desc(LotteryDraw.draw_term)).offset(offset).limit(limit).all()
    
    total = db.query(LotteryDraw).filter(
        LotteryDraw.lottery_type == lottery_type
    ).count()
    
    return {
        "lottery_type": lottery_type,
        "lottery_name": LOTTERY_NAMES.get(lottery_type, lottery_type),
        "total_count": total,
        "items": [
            {
                "id": d.id,
                "draw_term": d.draw_term,
                "draw_date": d.draw_date.isoformat(),
                "numbers": d.numbers,
                "jackpot": d.jackpot,
                "jackpot_display": format_jackpot(d.jackpot)
            }
            for d in draws
        ]
    }
