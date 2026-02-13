"""

SELA æ¨‚é€ä¸€è·¯ç™¼ - å½©åˆ¸é–‹çŽè³‡è¨Š API

"""

from typing import Optional, List

from datetime import datetime, date, timezone, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query

from sqlalchemy.orm import Session

from sqlalchemy import desc

from pydantic import BaseModel



from app.core.database import get_db

from app.core.security import get_current_user_id, require_admin

from app.services.lottery_crawler import lottery_crawler

from app.models.lottery_draw import LotteryDraw

from app.constants import LOTTERY_NAMES



# å˜—è©¦å°Žå…¥æ­·å²çˆ¬èŸ²ï¼ˆå¯èƒ½ä¸å­˜åœ¨ï¼‰

try:

    from app.services.history_crawler import history_crawler

    HAS_HISTORY_CRAWLER = True

except ImportError:

    HAS_HISTORY_CRAWLER = False



# å˜—è©¦å°Žå…¥è‡ªå‹•å°çŽæœå‹™

try:

    from app.services.auto_check import auto_check_service

    HAS_AUTO_CHECK = True

except ImportError:

    HAS_AUTO_CHECK = False





router = APIRouter(prefix="/lottery", tags=["Lottery"])



# å°ç£æ™‚å€ (GMT+8)

TW_TIMEZONE = timezone(timedelta(hours=8))





# ==================== Schema ====================



class DrawNumbers(BaseModel):

    """é–‹çŽè™Ÿç¢¼"""

    first_zone: Optional[List[int]] = None  # å¨åŠ›å½©ç¬¬ä¸€å€

    second_zone: Optional[int] = None        # å¨åŠ›å½©ç¬¬äºŒå€

    main: Optional[List[int]] = None         # å¤§æ¨‚é€ä¸»è™Ÿ

    special: Optional[int] = None            # å¤§æ¨‚é€ç‰¹åˆ¥è™Ÿ

    numbers: Optional[List[int]] = None      # ä»Šå½©539





class LatestDraw(BaseModel):

    """æœ€æ–°é–‹çŽ"""

    draw_date: str

    numbers: dict





class LotteryInfo(BaseModel):

    """å½©ç¨®è³‡è¨Š"""

    lottery_type: str

    lottery_name: str

    jackpot: Optional[int] = None

    jackpot_display: Optional[str] = None

    latest_draw: Optional[LatestDraw] = None





class SyncResult(BaseModel):

    """åŒæ­¥çµæžœ"""

    success: bool

    message: str

    updated_at: str

    data: Optional[dict] = None





# ==================== Helper ====================



def format_jackpot(amount) -> str:
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

    """è§£æžæ—¥æœŸå­—ä¸²"""

    if not date_str:

        return date.today()

    for fmt in ['%Y/%m/%d', '%Y-%m-%d', '%Y.%m.%d']:

        try:

            return datetime.strptime(date_str, fmt).date()

        except ValueError:

            continue

    return date.today()





# ==================== è³‡æ–™åº«æ“ä½œ ====================



def get_latest_from_db(db: Session, lottery_type: str) -> Optional[LotteryDraw]:

    """å¾žè³‡æ–™åº«å–å¾—æœ€æ–°ä¸€æœŸ"""

    return db.query(LotteryDraw).filter(

        LotteryDraw.lottery_type == lottery_type

    ).order_by(desc(LotteryDraw.draw_date), desc(LotteryDraw.draw_term)).first()





def save_to_db(db: Session, lottery_type: str, draw_term: str, 

               draw_date: date, numbers: dict, jackpot: Optional[int] = None):

    """å„²å­˜æˆ–æ›´æ–°é–‹çŽè¨˜éŒ„"""

    existing = db.query(LotteryDraw).filter(

        LotteryDraw.lottery_type == lottery_type,

        LotteryDraw.draw_term == draw_term

    ).first()

    

    if existing:

        # åªæ›´æ–°çŽé‡‘ï¼ˆè™Ÿç¢¼ä¸æœƒè®Šï¼‰

        if jackpot is not None:

            existing.jackpot = jackpot

            existing.updated_at = datetime.utcnow()

        return existing

    else:

        # æ–°å¢žè¨˜éŒ„

        new_draw = LotteryDraw(

            lottery_type=lottery_type,

            draw_term=draw_term,

            draw_date=draw_date,

            numbers=numbers,

            jackpot=jackpot

        )

        db.add(new_draw)

        return new_draw





# ==================== API ç«¯é»ž ====================



@router.get("/db-status")

async def check_db_status(

    db: Session = Depends(get_db),

    user_id: int = Depends(get_current_user_id)

):

    """æª¢æŸ¥è³‡æ–™åº«ç‹€æ…‹ï¼ˆæ¸¬è©¦ç”¨ï¼‰"""

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

    å–å¾—ç‰¹å®šå½©ç¨®æœ€æ–°é–‹çŽè³‡è¨Š

    

    - lottery_type: power (å¨åŠ›å½©), super (å¤§æ¨‚é€), daily539 (ä»Šå½©539)

    """

    if lottery_type not in ["power", "super", "daily539"]:

        raise HTTPException(status_code=400, detail="ä¸æ”¯æ´çš„å½©ç¨®")

    

    # å…ˆå˜—è©¦å¾žè³‡æ–™åº«è®€å–

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

    

    # è³‡æ–™åº«æ²’æœ‰ï¼Œå³æ™‚çˆ¬å–ï¼ˆFallbackï¼‰

    try:

        data = lottery_crawler.get_latest(lottery_type)

        if not data:

            raise HTTPException(status_code=404, detail="ç„¡æ³•å–å¾—é–‹çŽè³‡è¨Š")

        

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

        raise HTTPException(status_code=500, detail=f"å–å¾—é–‹çŽè³‡è¨Šå¤±æ•—: {str(e)}")





@router.get("/latest", response_model=dict)

async def get_all_latest(

    db: Session = Depends(get_db),

    user_id: int = Depends(get_current_user_id)

):

    """å–å¾—æ‰€æœ‰å½©ç¨®æœ€æ–°é–‹çŽè³‡è¨Š"""

    result = {}

    

    for lottery_type in ["power", "super", "daily539"]:

        # å…ˆå¾žè³‡æ–™åº«è®€

        db_record = get_latest_from_db(db, lottery_type)

        if db_record:

            # æ ¼å¼åŒ–æ›´æ–°æ™‚é–“ (è½‰æ›ç‚ºå°ç£æ™‚é–“ GMT+8)

            updated_at_str = None

            if db_record.updated_at:

                # å‡è¨­ DB å­˜çš„æ˜¯ UTCï¼Œè½‰æ›æˆå°ç£æ™‚é–“

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

            # Fallback åˆ°å³æ™‚çˆ¬å–

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

                pass  # å¿½ç•¥éŒ¯èª¤ï¼Œç¹¼çºŒä¸‹ä¸€å€‹

    

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
    同步所有彩種開獎資料（管理員）
    從台灣彩券官方 API 抓取當月+上月資料
    """
    try:
        items = lottery_crawler.fetch_months(2)

        if not items:
            return SyncResult(
                success=False,
                message="無法連線台灣彩券 API，請稍後再試",
                updated_at=datetime.now().isoformat()
            )

        imported = 0
        updated = 0
        skipped = 0

        for item in items:
            try:
                existing = db.query(LotteryDraw).filter(
                    LotteryDraw.lottery_type == item["lottery_type"],
                    LotteryDraw.draw_term == item["draw_term"]
                ).first()

                if existing:
                    changed = False
                    if item.get("jackpot") and existing.jackpot != item["jackpot"]:
                        existing.jackpot = item["jackpot"]
                        changed = True
                    if item.get("numbers") and existing.numbers != item["numbers"]:
                        existing.numbers = item["numbers"]
                        changed = True
                    if changed:
                        updated += 1
                    else:
                        skipped += 1
                    continue

                draw_date = parse_date(item["draw_date"])
                new_draw = LotteryDraw(
                    lottery_type=item["lottery_type"],
                    draw_term=item["draw_term"],
                    draw_date=draw_date,
                    numbers=item["numbers"],
                    jackpot=item.get("jackpot")
                )
                db.add(new_draw)
                imported += 1
            except Exception as e:
                logger.error(f"同步單筆失敗 {item.get('draw_term')}: {e}")

        db.commit()

        # 自動對獎
        auto_check_result = None
        if HAS_AUTO_CHECK and (imported > 0 or updated > 0):
            try:
                auto_check_result = auto_check_service.auto_check_all_pending(db)
            except Exception as e:
                logger.error(f"自動對獎失敗: {e}")

        power_count = sum(1 for i in items if i["lottery_type"] == "power")
        super_count = sum(1 for i in items if i["lottery_type"] == "super")
        daily_count = sum(1 for i in items if i["lottery_type"] == "daily539")

        msg = f"同步完成！新增 {imported} 筆、更新 {updated} 筆、跳過 {skipped} 筆\n"
        msg += f"威力彩 {power_count} 筆、大樂透 {super_count} 筆、今彩539 {daily_count} 筆"

        return SyncResult(
            success=True,
            message=msg,
            updated_at=datetime.now().isoformat(),
            auto_check_result=auto_check_result
        )

    except Exception as e:
        logger.error(f"同步失敗: {e}")
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

    """å–å¾—é–‹çŽæ­·å²è¨˜éŒ„"""

    if lottery_type not in ["power", "super", "daily539"]:

        raise HTTPException(status_code=400, detail="ä¸æ”¯æ´çš„å½©ç¨®")

    

    # æŸ¥è©¢è³‡æ–™åº«

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

    lottery_type: str = Query(None, description="æŒ‡å®šå½©ç¨® (power/super/daily539)ï¼Œä¸æŒ‡å®šå‰‡å…¨éƒ¨åŒ¯å…¥"),

    limit: int = Query(30, ge=10, le=100, description="æ¯ç¨®å½©åˆ¸åŒ¯å…¥ç­†æ•¸"),

    db: Session = Depends(get_db),

    admin_id: int = Depends(require_admin)

):

    """

    åŒ¯å…¥æ­·å²é–‹çŽè³‡æ–™ï¼ˆåƒ…ç®¡ç†å“¡ï¼‰

    

    å¾žå¤–éƒ¨ä¾†æºçˆ¬å–æ­·å²é–‹çŽè¨˜éŒ„ä¸¦å„²å­˜åˆ°è³‡æ–™åº«

    """

    if not HAS_HISTORY_CRAWLER:

        return SyncResult(

            success=False,

            message="æ­·å²çˆ¬èŸ²æœå‹™æœªå®‰è£",

            updated_at=datetime.now().isoformat()

        )

    

    try:

        imported_counts = {"power": 0, "super": 0, "daily539": 0}

        types_to_import = [lottery_type] if lottery_type else ["power", "super", "daily539"]

        

        for ltype in types_to_import:

            if ltype not in ["power", "super", "daily539"]:

                continue

            

            # æ ¹æ“šå½©ç¨®å‘¼å«å°æ‡‰çš„çˆ¬èŸ²

            if ltype == "power":

                history_data = history_crawler.fetch_power_history(limit)

            elif ltype == "super":

                history_data = history_crawler.fetch_super_history(limit)

            else:

                history_data = history_crawler.fetch_daily539_history(limit)

            

            # å„²å­˜åˆ°è³‡æ–™åº«

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

                    logger.warning(f"å„²å­˜æ­·å²è¨˜éŒ„å¤±æ•—: {e}")

                    continue

        

        db.commit()

        

        # çµ±è¨ˆçµæžœ

        total_imported = sum(imported_counts.values())

        details = []

        for ltype, count in imported_counts.items():

            if count > 0:

                details.append(f"{LOTTERY_NAMES[ltype]} {count}ç­†")

        

        return SyncResult(

            success=True,

            message=f"æˆåŠŸåŒ¯å…¥ {total_imported} ç­†: {', '.join(details)}" if total_imported > 0 else "ç„¡æ–°è³‡æ–™åŒ¯å…¥ï¼ˆå¯èƒ½è³‡æ–™å·²å­˜åœ¨ï¼‰",

            updated_at=datetime.now().isoformat(),

            data={"imported": imported_counts, "total": total_imported}

        )

    

    except Exception as e:

        db.rollback()

        return SyncResult(

            success=False,

            message=f"åŒ¯å…¥å¤±æ•—: {str(e)}",

            updated_at=datetime.now().isoformat()

        )





# åŠ å…¥ logger

import logging

logger = logging.getLogger(__name__)





class BatchImportItem(BaseModel):

    """æ‰¹é‡åŒ¯å…¥é …ç›®"""

    lottery_type: str

    draw_term: str

    draw_date: str  # YYYY-MM-DD

    numbers: dict

    jackpot: Optional[int] = None





class BatchImportRequest(BaseModel):

    """æ‰¹é‡åŒ¯å…¥è«‹æ±‚"""

    items: List[BatchImportItem]





@router.post("/batch-import")

async def batch_import_draws(

    request: BatchImportRequest,

    db: Session = Depends(get_db),

    admin_id: int = Depends(require_admin)

):

    """

    æ‰¹é‡åŒ¯å…¥é–‹çŽè³‡æ–™ï¼ˆåƒ…ç®¡ç†å“¡ï¼‰

    

    ç”¨æ–¼å¾žæœ¬åœ°è…³æœ¬ä¸Šå‚³æ­·å²è³‡æ–™

    """

    imported = 0

    skipped = 0

    errors = []

    

    for item in request.items:

        try:

            # æª¢æŸ¥æ˜¯å¦å·²å­˜åœ¨

            existing = db.query(LotteryDraw).filter(

                LotteryDraw.lottery_type == item.lottery_type,

                LotteryDraw.draw_term == item.draw_term

            ).first()

            

            if existing:

                # 更新已存在記錄的 jackpot 和 numbers

                updated = False

                if item.jackpot is not None and existing.jackpot != item.jackpot:

                    existing.jackpot = item.jackpot

                    updated = True

                if item.numbers and existing.numbers != item.numbers:

                    existing.numbers = item.numbers

                    updated = True

                if updated:

                    imported += 1

                else:

                    skipped += 1

                continue

            

            # è§£æžæ—¥æœŸ

            draw_date = parse_date(item.draw_date)

            

            # æ–°å¢žè¨˜éŒ„

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

        "message": f"åŒ¯å…¥å®Œæˆï¼šæ–°å¢ž {imported} ç­†ï¼Œç•¥éŽ {skipped} ç­†ï¼ˆå·²å­˜åœ¨ï¼‰"

    }

