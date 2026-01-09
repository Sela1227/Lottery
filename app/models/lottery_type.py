"""
SELA 樂透一路發 - 彩種模型
"""
from sqlalchemy import Column, Integer, String, Numeric, Boolean, JSON, Text
from app.core.database import Base


class LotteryType(Base):
    """彩種定義"""
    __tablename__ = "lottery_types"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 基本資訊
    code = Column(String(20), unique=True, nullable=False)  # power, super, daily539
    name = Column(String(50), nullable=False)               # 威力彩, 大樂透, 今彩539
    description = Column(Text, nullable=True)
    
    # 價格與規則
    price_per_bet = Column(Numeric(10, 2), nullable=False)  # 每注價格
    
    # 號碼規則(JSON 格式)
    # 例如威力彩: {"first_zone": {"min": 1, "max": 38, "pick": 6}, "second_zone": {"min": 1, "max": 8, "pick": 1}}
    number_rules = Column(JSON, nullable=False)
    
    # 獎金結構(JSON 格式)
    # 例如: [{"level": "頭獎", "match": "6+1", "prize": 0, "is_jackpot": true}, ...]
    prize_structure = Column(JSON, nullable=False)
    
    # 開獎時間
    draw_days = Column(JSON, nullable=False)    # [1, 4] 表示週一、週四
    draw_time = Column(String(10), nullable=False)  # "20:30"
    
    # 狀態
    is_active = Column(Boolean, default=True, nullable=False)
    
    # 顯示順序
    sort_order = Column(Integer, default=0)


# 預設彩種資料
DEFAULT_LOTTERY_TYPES = [
    {
        "code": "power",
        "name": "威力彩",
        "description": "第一區選6個號碼(1-38),第二區選1個號碼(1-8)",
        "price_per_bet": 100,
        "number_rules": {
            "first_zone": {"min": 1, "max": 38, "pick": 6},
            "second_zone": {"min": 1, "max": 8, "pick": 1}
        },
        "prize_structure": [
            {"level": "頭獎", "match": "6+1", "prize": 0, "is_jackpot": True},
            {"level": "貳獎", "match": "6+0", "prize": 150000, "is_jackpot": False},
            {"level": "參獎", "match": "5+1", "prize": 20000, "is_jackpot": False},
            {"level": "肆獎", "match": "5+0", "prize": 4000, "is_jackpot": False},
            {"level": "伍獎", "match": "4+1", "prize": 800, "is_jackpot": False},
            {"level": "陸獎", "match": "4+0", "prize": 400, "is_jackpot": False},
            {"level": "柒獎", "match": "3+1", "prize": 200, "is_jackpot": False},
            {"level": "捌獎", "match": "2+1", "prize": 100, "is_jackpot": False},
            {"level": "普獎", "match": "1+1", "prize": 100, "is_jackpot": False},
        ],
        "draw_days": [1, 4],  # 週一、週四
        "draw_time": "20:30",
        "sort_order": 1
    },
    {
        "code": "super",
        "name": "大樂透",
        "description": "選6個號碼(1-49),另開出1個特別號",
        "price_per_bet": 50,
        "number_rules": {
            "main": {"min": 1, "max": 49, "pick": 6},
            "special": {"from_remaining": True}
        },
        "prize_structure": [
            {"level": "頭獎", "match": "6", "prize": 0, "is_jackpot": True},
            {"level": "貳獎", "match": "5+特", "prize": 150000, "is_jackpot": False},
            {"level": "參獎", "match": "5", "prize": 25000, "is_jackpot": False},
            {"level": "肆獎", "match": "4+特", "prize": 12500, "is_jackpot": False},
            {"level": "伍獎", "match": "4", "prize": 2000, "is_jackpot": False},
            {"level": "陸獎", "match": "3+特", "prize": 1000, "is_jackpot": False},
            {"level": "柒獎", "match": "2+特", "prize": 400, "is_jackpot": False},
            {"level": "普獎", "match": "3", "prize": 400, "is_jackpot": False},
        ],
        "draw_days": [2, 5],  # 週二、週五
        "draw_time": "20:30",
        "sort_order": 2
    },
    {
        "code": "daily539",
        "name": "今彩539",
        "description": "選5個號碼(1-39)",
        "price_per_bet": 50,
        "number_rules": {
            "main": {"min": 1, "max": 39, "pick": 5}
        },
        "prize_structure": [
            {"level": "頭獎", "match": "5", "prize": 8000000, "is_jackpot": False},
            {"level": "貳獎", "match": "4", "prize": 20000, "is_jackpot": False},
            {"level": "參獎", "match": "3", "prize": 300, "is_jackpot": False},
            {"level": "肆獎", "match": "2", "prize": 50, "is_jackpot": False},
        ],
        "draw_days": [1, 2, 3, 4, 5, 6, 0],  # 每天
        "draw_time": "20:30",
        "sort_order": 3
    }
]
