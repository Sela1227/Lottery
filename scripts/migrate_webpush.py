"""
SELA 樂透一路發 - Web Push 資料庫遷移
執行方式: python scripts/migrate_webpush.py
"""
import os
import sys

# 添加專案根目錄到 path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.core.database import engine


def migrate():
    """建立 Web Push 相關資料表和欄位"""
    
    migrations = [
        # 建立 push_subscriptions 表
        """
        CREATE TABLE IF NOT EXISTS push_subscriptions (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            endpoint TEXT NOT NULL UNIQUE,
            p256dh_key VARCHAR(255) NOT NULL,
            auth_key VARCHAR(255) NOT NULL,
            user_agent VARCHAR(500),
            device_name VARCHAR(100),
            is_active BOOLEAN DEFAULT TRUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
            last_used_at TIMESTAMP
        );
        """,
        
        # 建立索引
        """
        CREATE INDEX IF NOT EXISTS idx_push_subscriptions_user_id 
        ON push_subscriptions(user_id);
        """,
        
        """
        CREATE INDEX IF NOT EXISTS idx_push_subscriptions_active 
        ON push_subscriptions(is_active) WHERE is_active = TRUE;
        """,
        
        # users 表新增通知設定欄位
        """
        ALTER TABLE users 
        ADD COLUMN IF NOT EXISTS notify_draw_reminder BOOLEAN DEFAULT TRUE;
        """,
        
        """
        ALTER TABLE users 
        ADD COLUMN IF NOT EXISTS notify_win_alert BOOLEAN DEFAULT TRUE;
        """,
        
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
                print(f"✅ 執行成功: {sql.strip()[:60]}...")
            except Exception as e:
                if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
                    print(f"⏭️ 已存在，跳過")
                else:
                    print(f"❌ 執行失敗: {e}")
    
    print("\n🎉 Web Push 遷移完成！")


if __name__ == "__main__":
    migrate()
