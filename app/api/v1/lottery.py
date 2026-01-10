"""
SELA 樂透一路發 - 彩券開獎資訊 API
"""
from typing import Optional, List
from datetime import datetime, date, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from pydantic import BaseModel

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.api.v1.admin import require_admin
from app.services.lottery_crawler import lottery_crawler
from app.models.lottery_draw import LotteryDraw

# 嘗試導入歷史爬蟲（可能不存在）
try:
    from app.services.history_crawler import history_crawler
    HAS_HISTORY_CRAWLER = True
except ImportError:
    HAS_HISTORY_CRAWLER = False

# 嘗試導入自動對獎服務
try:
    from app.services.auto_check import auto_check_service
    HAS_AUTO_CHECK = True
except ImportError:
    HAS_AUTO_CHECK = False


router = APIRouter(prefix="/lottery", tags=["Lottery"])

# 台灣時區 (GMT+8)
TW_TIMEZONE = timezone(timedelta(hours=8))


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
            # 格式化更新時間 (轉換為台灣時間 GMT+8)
            updated_at_str = None
            if db_record.updated_at:
                # 假設 DB 存的是 UTC，轉換成台灣時間
                utc_time = db_record.updated_at.replace(tzinfo=timezone.utc)
                tw_time = utc_time.astimezone(TW_TIMEZONE)
                updated_at_str = tw_time.strftime("%m/%d %H:%M")
            
            result[lottery_type] = {
                "lottery_type": lottery_type,
                "lottery_name": db_record.lottery_name,
                "jackpot": db_record.jackpot,
                "jackpot_display": format_jackpot(db_record.jackpot),
                "updated_at": updated_at_str,
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
                    now_tw = datetime.now(TW_TIMEZONE)
                    result[lottery_type] = {
                        "lottery_type": data["lottery_type"],
                        "lottery_name": data["lottery_name"],
                        "jackpot": data.get("jackpot"),
                        "jackpot_display": format_jackpot(data.get("jackpot")),
                        "updated_at": now_tw.strftime("%m/%d %H:%M"),
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
    
    從外部來源抓取最新開獎號碼並儲存到資料庫，
    同步完成後自動對獎所有待對獎的團
    """
    try:
        data = lottery_crawler.fetch_all()
        synced = []
        
        # 爬蟲返回格式映射
        # super_lotto -> power (威力彩)
        # lotto649 -> super (大樂透)  
        # daily_cash -> daily539 (今彩539)
        
        # 處理威力彩
        if data.get("super_lotto") and data["super_lotto"].get("draws"):
            item = data["super_lotto"]
            draw = item["draws"][0]
            draw_date = parse_date(draw.get("draw_date", ""))
            draw_term = f"power_{draw_date}"
            numbers = draw.get("numbers", {})
            save_to_db(db, "power", draw_term, draw_date, numbers, item.get("jackpot"))
            synced.append("威力彩")
        
        # 處理大樂透
        if data.get("lotto649") and data["lotto649"].get("draws"):
            item = data["lotto649"]
            draw = item["draws"][0]
            draw_date = parse_date(draw.get("draw_date", ""))
            draw_term = f"super_{draw_date}"
            numbers = draw.get("numbers", {})
            save_to_db(db, "super", draw_term, draw_date, numbers, item.get("jackpot"))
            synced.append("大樂透")
        
        # 處理今彩539
        if data.get("daily_cash") and data["daily_cash"].get("draws"):
            item = data["daily_cash"]
            draw = item["draws"][0]
            draw_date = parse_date(draw.get("draw_date", ""))
            draw_term = f"daily539_{draw_date}"
            nums = draw.get("numbers", [])
            # 統一格式
            if isinstance(nums, list):
                numbers = {"numbers": nums}
            else:
                numbers = nums
            save_to_db(db, "daily539", draw_term, draw_date, numbers, item.get("jackpot"))
            synced.append("今彩539")
        
        db.commit()
        
        # === 自動對獎 ===
        auto_check_result = None
        if HAS_AUTO_CHECK and synced:
            try:
                auto_check_result = auto_check_service.auto_check_all_pending(db)
                if auto_check_result.get("groups_success", 0) > 0:
                    synced.append(f"對獎 {auto_check_result['groups_success']} 團")
            except Exception as e:
                print(f"⚠️ 自動對獎失敗: {e}")
        # === 自動對獎結束 ===
        
        return SyncResult(
            success=True,
            message=f"成功同步: {', '.join(synced)}" if synced else "無新資料",
            updated_at=datetime.now().isoformat(),
            data={
                "synced_types": synced,
                "auto_check": auto_check_result
            }
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


@router.post("/import-history", response_model=SyncResult)
async def import_history_data(
    lottery_type: str = Query(None, description="指定彩種 (power/super/daily539)，不指定則全部匯入"),
    limit: int = Query(30, ge=10, le=100, description="每種彩券匯入筆數"),
    db: Session = Depends(get_db),
    admin_id: int = Depends(require_admin)
):
    """
    匯入歷史開獎資料（僅管理員）
    
    從外部來源爬取歷史開獎記錄並儲存到資料庫
    """
    if not HAS_HISTORY_CRAWLER:
        return SyncResult(
            success=False,
            message="歷史爬蟲服務未安裝",
            updated_at=datetime.now().isoformat()
        )
    
    try:
        imported_counts = {"power": 0, "super": 0, "daily539": 0}
        types_to_import = [lottery_type] if lottery_type else ["power", "super", "daily539"]
        
        for ltype in types_to_import:
            if ltype not in ["power", "super", "daily539"]:
                continue
            
            # 根據彩種呼叫對應的爬蟲
            if ltype == "power":
                history_data = history_crawler.fetch_power_history(limit)
            elif ltype == "super":
                history_data = history_crawler.fetch_super_history(limit)
            else:
                history_data = history_crawler.fetch_daily539_history(limit)
            
            # 儲存到資料庫
            for item in history_data:
                try:
                    existing = db.query(LotteryDraw).filter(
                        LotteryDraw.lottery_type == item["lottery_type"],
                        LotteryDraw.draw_term == item["draw_term"]
                    ).first()
                    
                    if not existing:
                        new_draw = LotteryDraw(
                            lottery_type=item["lottery_type"],
                            draw_term=item["draw_term"],
                            draw_date=item["draw_date"],
                            numbers=item["numbers"],
                            jackpot=item.get("jackpot")
                        )
                        db.add(new_draw)
                        imported_counts[ltype] += 1
                except Exception as e:
                    logger.warning(f"儲存歷史記錄失敗: {e}")
                    continue
        
        db.commit()
        
        # 統計結果
        total_imported = sum(imported_counts.values())
        details = []
        for ltype, count in imported_counts.items():
            if count > 0:
                details.append(f"{LOTTERY_NAMES[ltype]} {count}筆")
        
        return SyncResult(
            success=True,
            message=f"成功匯入 {total_imported} 筆: {', '.join(details)}" if total_imported > 0 else "無新資料匯入（可能資料已存在）",
            updated_at=datetime.now().isoformat(),
            data={"imported": imported_counts, "total": total_imported}
        )
    
    except Exception as e:
        db.rollback()
        return SyncResult(
            success=False,
            message=f"匯入失敗: {str(e)}",
            updated_at=datetime.now().isoformat()
        )


# 加入 logger
import logging
logger = logging.getLogger(__name__)


class BatchImportItem(BaseModel):
    """批量匯入項目"""
    lottery_type: str
    draw_term: str
    draw_date: str  # YYYY-MM-DD
    numbers: dict
    jackpot: Optional[int] = None


class BatchImportRequest(BaseModel):
    """批量匯入請求"""
    items: List[BatchImportItem]


@router.post("/batch-import")
async def batch_import_draws(
    request: BatchImportRequest,
    db: Session = Depends(get_db),
    admin_id: int = Depends(require_admin)
):
    """
    批量匯入開獎資料（僅管理員）
    
    用於從本地腳本上傳歷史資料
    """
    imported = 0
    skipped = 0
    errors = []
    
    for item in request.items:
        try:
            # 檢查是否已存在
            existing = db.query(LotteryDraw).filter(
                LotteryDraw.lottery_type == item.lottery_type,
                LotteryDraw.draw_term == item.draw_term
            ).first()
            
            if existing:
                skipped += 1
                continue
            
            # 解析日期
            draw_date = parse_date(item.draw_date)
            
            # 新增記錄
            new_draw = LotteryDraw(
                lottery_type=item.lottery_type,
                draw_term=item.draw_term,
                draw_date=draw_date,
                numbers=item.numbers,
                jackpot=item.jackpot
            )
            db.add(new_draw)
            imported += 1
            
        except Exception as e:
            errors.append(f"{item.draw_term}: {str(e)}")
    
    db.commit()
    
    return {
        "success": True,
        "imported": imported,
        "skipped": skipped,
        "errors": errors[:10] if errors else [],
        "message": f"匯入完成：新增 {imported} 筆，略過 {skipped} 筆（已存在）"
    }
