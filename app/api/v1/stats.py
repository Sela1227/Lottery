"""
SELA 樂透一路發 - 號碼統計 API
"""
from typing import Optional, List, Dict
from datetime import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from collections import Counter

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.models.lottery_draw import LotteryDraw
from app.constants import NUMBER_RANGES, LOTTERY_NAMES


router = APIRouter(prefix="/stats", tags=["Statistics"])


def get_all_numbers(lottery_type: str, draws: List[LotteryDraw]) -> List[int]:
    """從開獎記錄中提取所有號碼"""
    all_numbers = []
    
    for draw in draws:
        numbers = draw.numbers
        if not numbers:
            continue
        
        if lottery_type == "power":
            if numbers.get("first_zone"):
                all_numbers.extend(numbers["first_zone"])
        elif lottery_type == "super":
            if numbers.get("main"):
                all_numbers.extend(numbers["main"])
        elif lottery_type == "daily539":
            if numbers.get("numbers"):
                all_numbers.extend(numbers["numbers"])
    
    return all_numbers


def calculate_missing_periods(lottery_type: str, draws: List[LotteryDraw], number_range: tuple) -> Dict[int, int]:
    """計算每個號碼的遺漏期數（多少期沒開出）"""
    missing = {}
    min_num, max_num = number_range
    
    # 初始化所有號碼
    for num in range(min_num, max_num + 1):
        missing[num] = 0
    
    # 按日期排序（最新的在前）
    sorted_draws = sorted(draws, key=lambda d: d.draw_date, reverse=True)
    
    # 記錄每個號碼最後出現的期數
    found = set()
    
    for period, draw in enumerate(sorted_draws):
        numbers = draw.numbers
        if not numbers:
            continue
        
        current_numbers = []
        if lottery_type == "power":
            current_numbers = numbers.get("first_zone", [])
        elif lottery_type == "super":
            current_numbers = numbers.get("main", [])
        elif lottery_type == "daily539":
            current_numbers = numbers.get("numbers", [])
        
        for num in current_numbers:
            if num not in found:
                missing[num] = period
                found.add(num)
    
    # 還沒找到的號碼，遺漏期數就是總期數
    total_periods = len(sorted_draws)
    for num in range(min_num, max_num + 1):
        if num not in found:
            missing[num] = total_periods
    
    return missing


@router.get("/numbers/{lottery_type}")
async def get_number_stats(
    lottery_type: str,
    limit: int = Query(100, ge=10, le=500, description="分析期數"),
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """
    取得號碼統計分析
    
    - lottery_type: power (威力彩), super (大樂透), daily539 (今彩539)
    - limit: 分析最近幾期的資料
    
    返回：熱門號碼、冷門號碼、遺漏期數
    """
    if lottery_type not in NUMBER_RANGES:
        return {"error": "不支援的彩種"}
    
    # 取得歷史資料
    draws = db.query(LotteryDraw).filter(
        LotteryDraw.lottery_type == lottery_type
    ).order_by(desc(LotteryDraw.draw_date)).limit(limit).all()
    
    if not draws:
        return {
            "lottery_type": lottery_type,
            "lottery_name": LOTTERY_NAMES.get(lottery_type),
            "total_draws": 0,
            "message": "尚無歷史資料"
        }
    
    # 取得號碼範圍
    if lottery_type == "power":
        number_range = NUMBER_RANGES["power"]["first_zone"]
    elif lottery_type == "super":
        number_range = NUMBER_RANGES["super"]["main"]
    else:
        number_range = NUMBER_RANGES["daily539"]["numbers"]
    
    min_num, max_num = number_range
    
    # 統計出現次數
    all_numbers = get_all_numbers(lottery_type, draws)
    counter = Counter(all_numbers)
    
    # 確保所有號碼都有統計（包含 0 次的）
    for num in range(min_num, max_num + 1):
        if num not in counter:
            counter[num] = 0
    
    # 計算遺漏期數
    missing_periods = calculate_missing_periods(lottery_type, draws, number_range)
    
    # 排序
    hot_numbers = counter.most_common(10)  # 最熱門 10 個
    cold_numbers = counter.most_common()[-10:][::-1]  # 最冷門 10 個
    
    # 遺漏最久的號碼
    overdue_numbers = sorted(missing_periods.items(), key=lambda x: x[1], reverse=True)[:10]
    
    # 組裝完整統計
    full_stats = []
    for num in range(min_num, max_num + 1):
        full_stats.append({
            "number": num,
            "count": counter.get(num, 0),
            "missing": missing_periods.get(num, 0)
        })
    
    return {
        "lottery_type": lottery_type,
        "lottery_name": LOTTERY_NAMES.get(lottery_type),
        "total_draws": len(draws),
        "analyzed_range": f"最近 {len(draws)} 期",
        "hot_numbers": [{"number": n, "count": c} for n, c in hot_numbers],
        "cold_numbers": [{"number": n, "count": c} for n, c in cold_numbers],
        "overdue_numbers": [{"number": n, "missing": m} for n, m in overdue_numbers],
        "full_stats": full_stats
    }


@router.get("/special/{lottery_type}")
async def get_special_number_stats(
    lottery_type: str,
    limit: int = Query(100, ge=10, le=500),
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """
    取得特別號/第二區統計（威力彩第二區、大樂透特別號）
    """
    if lottery_type not in ["power", "super"]:
        return {"error": "此彩種沒有特別號"}
    
    draws = db.query(LotteryDraw).filter(
        LotteryDraw.lottery_type == lottery_type
    ).order_by(desc(LotteryDraw.draw_date)).limit(limit).all()
    
    if not draws:
        return {"message": "尚無歷史資料"}
    
    # 取得特別號
    special_numbers = []
    for draw in draws:
        numbers = draw.numbers
        if not numbers:
            continue
        
        if lottery_type == "power":
            if numbers.get("second_zone"):
                special_numbers.append(numbers["second_zone"])
        elif lottery_type == "super":
            if numbers.get("special"):
                special_numbers.append(numbers["special"])
    
    counter = Counter(special_numbers)
    
    # 號碼範圍
    if lottery_type == "power":
        min_num, max_num = 1, 8
        label = "第二區"
    else:
        min_num, max_num = 1, 49
        label = "特別號"
    
    # 完整統計
    full_stats = []
    for num in range(min_num, max_num + 1):
        full_stats.append({
            "number": num,
            "count": counter.get(num, 0)
        })
    
    hot = counter.most_common(5)
    cold = counter.most_common()[-5:][::-1] if len(counter) >= 5 else []
    
    return {
        "lottery_type": lottery_type,
        "lottery_name": LOTTERY_NAMES.get(lottery_type),
        "label": label,
        "total_draws": len(draws),
        "hot_numbers": [{"number": n, "count": c} for n, c in hot],
        "cold_numbers": [{"number": n, "count": c} for n, c in cold],
        "full_stats": full_stats
    }
