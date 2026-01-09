"""
SELA 樂透一路發 - 資料庫遷移腳本

Railway 部署時自動執行
"""
import sys
import os

# 確保可以 import app 模組
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.core.database import engine, Base, check_database_connection
from app.models.user import User  # 確保 Model 被載入


def run_migrations():
    """執行資料庫遷移"""
    print("🔧 開始資料庫遷移...")
    
    # 檢查連線
    if not check_database_connection():
        print("❌ 無法連線到資料庫")
        sys.exit(1)
    
    print("✅ 資料庫連線成功")
    
    # 建立所有表格
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ 資料表建立完成")
    except Exception as e:
        print(f"❌ 資料表建立失敗: {e}")
        sys.exit(1)
    
    # 檢查表格
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """))
        tables = [row[0] for row in result]
        print(f"📋 現有資料表: {', '.join(tables) if tables else '(無)'}")
    
    print("🎉 資料庫遷移完成!")


if __name__ == "__main__":
    run_migrations()
