"""
SELA 樂透一路發 - 種子資料腳本

初始化測試資料
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal, check_database_connection
from app.models.user import User, UserStatus, UserRole


def seed_users():
    """建立測試用戶"""
    db = SessionLocal()
    
    try:
        # 檢查是否已有用戶
        if db.query(User).count() > 0:
            print("⏭️  用戶資料已存在，跳過")
            return
        
        # 建立測試用戶
        test_users = [
            User(
                line_user_id="U_admin_001",
                display_name="系統管理員",
                nickname="Admin",
                email="admin@sela.tw",
                role=UserRole.ADMIN,
                wallet_balance=10000,
            ),
            User(
                line_user_id="U_user_001",
                display_name="測試用戶一",
                nickname="小明",
                wallet_balance=5000,
            ),
            User(
                line_user_id="U_user_002",
                display_name="測試用戶二",
                nickname="小華",
                wallet_balance=3000,
            ),
            User(
                line_user_id="U_user_003",
                display_name="測試用戶三",
                wallet_balance=2000,
            ),
        ]
        
        for user in test_users:
            db.add(user)
        
        db.commit()
        print(f"✅ 建立了 {len(test_users)} 個測試用戶")
        
    except Exception as e:
        db.rollback()
        print(f"❌ 建立測試用戶失敗: {e}")
        raise
    finally:
        db.close()


def run_seed():
    """執行種子資料"""
    print("🌱 開始建立種子資料...")
    
    if not check_database_connection():
        print("❌ 無法連線到資料庫")
        sys.exit(1)
    
    seed_users()
    
    print("🎉 種子資料建立完成！")


if __name__ == "__main__":
    run_seed()
