"""
SELA 樂透一路發 - 全域常量定義

集中管理系統中重複使用的常量，避免多處定義造成不一致
"""

# ==================== 彩種名稱 ====================
LOTTERY_NAMES = {
    "power": "威力彩",
    "super": "大樂透",
    "daily539": "今彩539",
}

# ==================== 彩種價格（每注） ====================
LOTTERY_PRICES = {
    "power": 100,
    "super": 50,
    "daily539": 50,
}

# ==================== 號碼範圍 ====================
NUMBER_RANGES = {
    "power": {
        "first_zone": (1, 38),   # 第一區：1-38 選 6
        "second_zone": (1, 8),   # 第二區：1-8 選 1
    },
    "super": {
        "main": (1, 49),         # 主號：1-49 選 6
        "special": (1, 49),      # 特別號：1-49 選 1
    },
    "daily539": {
        "numbers": (1, 39),      # 1-39 選 5
    },
}

# ==================== 開獎時間 ====================
DRAW_SCHEDULES = {
    "power": {
        "days": [1, 4],          # 週一、週四
        "time": "20:30",
    },
    "super": {
        "days": [2, 5],          # 週二、週五
        "time": "20:30",
    },
    "daily539": {
        "days": [0, 1, 2, 3, 4, 5, 6],  # 每天
        "time": "20:30",
    },
}

# ==================== 交易類型顯示名稱 ====================
TRANSACTION_TYPE_DISPLAY = {
    "deposit": "儲值",
    "withdraw": "提領",
    "transfer_out": "轉出",
    "transfer_in": "轉入",
    "pool_join": "加入系列團",
    "pool_topup": "加碼",
    "pool_withdraw": "減碼",
    "pool_purchase": "購買扣除",
    "pool_carryover": "滾入",
    "pool_prize": "獎金分配",
    "pool_exit": "退出結算",
    "adjustment": "調整",
}
