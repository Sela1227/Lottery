"""
SELA 樂透一路發 - 種子資料腳本
"""
import sys
import os

# 加入專案根目錄到 path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal, engine, Base
from app.models import LotteryType
from app.models.lottery_type import DEFAULT_LOTTERY_TYPES


def seed_lottery_types(db):
    """初始化彩種資料"""
    print("📝 初始化彩種資料...")
    
    for type_data in DEFAULT_LOTTERY_TYPES:
        # 檢查是否已存在
        existing = db.query(LotteryType).filter(
            LotteryType.code == type_data["code"]
        ).first()
        
        if existing:
            print(f"  ⏭️  {type_data['name']} 已存在，跳過")
            continue
        
        lottery_type = LotteryType(
            code=type_data["code"],
            name=type_data["name"],
            description=type_data["description"],
            price_per_bet=type_data["price_per_bet"],
            number_rules=type_data["number_rules"],
            prize_structure=type_data["prize_structure"],
            draw_days=type_data["draw_days"],
            draw_time=type_data["draw_time"],
            sort_order=type_data["sort_order"],
            is_active=True
        )
        db.add(lottery_type)
        print(f"  ✅ {type_data['name']} 已建立")
    
    db.commit()
    print("✨ 彩種資料初始化完成！")


def main():
    """執行種子資料初始化"""
    print("🌱 開始初始化種子資料...")
    print("=" * 50)
    
    # 建立所有表
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        seed_lottery_types(db)
    finally:
        db.close()
    
    print("=" * 50)
    print("🎉 種子資料初始化完成！")


if __name__ == "__main__":
    main()
