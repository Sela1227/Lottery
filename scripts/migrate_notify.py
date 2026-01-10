"""
SELA 樂透一路發 - LINE Notify 欄位遷移
執行方式: python scripts/migrate_notify.py
"""
import os
import sys

# 添加專案根目錄到 path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.core.database import engine


def migrate():
    """新增 LINE Notify 相關欄位到 users 表"""
    
    migrations = [
        # LINE Notify token
        """
        ALTER TABLE users 
        ADD COLUMN IF NOT EXISTS line_notify_token VARCHAR(255) DEFAULT NULL;
        """,
        
        # LINE Notify 連結時間
        """
        ALTER TABLE users 
        ADD COLUMN IF NOT EXISTS line_notify_connected_at TIMESTAMP DEFAULT NULL;
        """,
        
        # 開獎提醒開關
        """
        ALTER TABLE users 
        ADD COLUMN IF NOT EXISTS notify_draw_reminder BOOLEAN DEFAULT TRUE;
        """,
        
        # 中獎通知開關
        """
        ALTER TABLE users 
        ADD COLUMN IF NOT EXISTS notify_win_alert BOOLEAN DEFAULT TRUE;
        """,
        
        # 結算通知開關
        """
        ALTER TABLE users 
        ADD COLUMN IF NOT EXISTS notify_settlement BOOLEAN DEFAULT TRUE;
        """,
    ]
    
    with engine.connect() as conn:
        for sql in migrations:
            try:
                conn.execute(text(sql))
                conn.commit()
                print(f"✅ 執行成功: {sql.strip()[:50]}...")
            except Exception as e:
                if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
                    print(f"⏭️ 欄位已存在，跳過")
                else:
                    print(f"❌ 執行失敗: {e}")
    
    print("\n🎉 LINE Notify 遷移完成！")


if __name__ == "__main__":
    migrate()
