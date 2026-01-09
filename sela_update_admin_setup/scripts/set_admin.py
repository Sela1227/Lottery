#!/usr/bin/env python3
"""
SELA 樂透一路發 - 設定管理員腳本

用法:
    python scripts/set_admin.py              # 將第一個用戶設為管理員
    python scripts/set_admin.py --user-id=1  # 將指定用戶設為管理員
    python scripts/set_admin.py --list       # 列出所有用戶
"""
import sys
import os
import argparse

# 確保可以 import app 模組
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal, check_database_connection
from app.models.user import User, UserRole


def list_users(db):
    """列出所有用戶"""
    users = db.query(User).order_by(User.id).all()
    
    if not users:
        print("📭 目前沒有任何用戶")
        return
    
    print("\n📋 用戶列表:")
    print("-" * 60)
    print(f"{'ID':<6} {'角色':<10} {'名稱':<20} {'LINE ID':<20}")
    print("-" * 60)
    
    for user in users:
        role_display = "👑 管理員" if user.role == UserRole.ADMIN else "👤 一般"
        print(f"{user.id:<6} {role_display:<10} {user.display_name:<20} {user.line_user_id[:15]+'...':<20}")
    
    print("-" * 60)
    print(f"共 {len(users)} 位用戶\n")


def set_admin(db, user_id: int = None):
    """設定管理員"""
    if user_id:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            print(f"❌ 找不到 ID 為 {user_id} 的用戶")
            return False
    else:
        # 取第一個用戶
        user = db.query(User).order_by(User.id).first()
        if not user:
            print("❌ 目前沒有任何用戶，請先登入系統")
            return False
    
    if user.role == UserRole.ADMIN:
        print(f"ℹ️  用戶 {user.display_name} (ID: {user.id}) 已經是管理員")
        return True
    
    # 設定為管理員
    user.role = UserRole.ADMIN
    db.commit()
    
    print(f"✅ 成功將 {user.display_name} (ID: {user.id}) 設為系統管理員")
    return True


def main():
    parser = argparse.ArgumentParser(description="SELA 樂透一路發 - 管理員設定工具")
    parser.add_argument("--user-id", type=int, help="指定用戶 ID")
    parser.add_argument("--list", action="store_true", help="列出所有用戶")
    
    args = parser.parse_args()
    
    print("🔧 SELA 管理員設定工具")
    print("=" * 40)
    
    # 檢查資料庫連線
    if not check_database_connection():
        print("❌ 無法連線到資料庫")
        sys.exit(1)
    
    print("✅ 資料庫連線成功")
    
    db = SessionLocal()
    try:
        if args.list:
            list_users(db)
        else:
            set_admin(db, args.user_id)
            print("\n📋 目前用戶狀態:")
            list_users(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()
