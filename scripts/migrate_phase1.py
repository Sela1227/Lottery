"""
SELA 樂透一路發 - Phase 1 資料庫遷移
新增 member_requests 表
"""
import os
import sys

# 添加專案根目錄到 path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.core.database import engine


def migrate():
    """執行 Phase 1 遷移"""
    
    print("🔄 Phase 1 資料庫遷移開始...")
    
    with engine.connect() as conn:
        # 檢查 member_requests 表是否存在
        result = conn.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'member_requests'
            );
        """))
        exists = result.scalar()
        
        if exists:
            print("✅ member_requests 表已存在，跳過建立")
        else:
            print("📝 建立 member_requests 表...")
            
            conn.execute(text("""
                CREATE TABLE member_requests (
                    id SERIAL PRIMARY KEY,
                    series_id INTEGER NOT NULL REFERENCES group_series(id),
                    user_id INTEGER NOT NULL REFERENCES users(id),
                    request_type VARCHAR(20) NOT NULL,
                    amount NUMERIC(14, 2),
                    pool_share_before NUMERIC(14, 2) NOT NULL,
                    status VARCHAR(20) NOT NULL DEFAULT 'pending',
                    reason TEXT,
                    reviewed_by INTEGER REFERENCES users(id),
                    reviewed_at TIMESTAMP WITH TIME ZONE,
                    review_note TEXT,
                    actual_amount NUMERIC(14, 2),
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
            """))
            
            # 建立索引
            conn.execute(text("""
                CREATE INDEX idx_member_requests_series ON member_requests(series_id);
            """))
            conn.execute(text("""
                CREATE INDEX idx_member_requests_user ON member_requests(user_id);
            """))
            conn.execute(text("""
                CREATE INDEX idx_member_requests_status ON member_requests(status);
            """))
            
            conn.commit()
            print("✅ member_requests 表建立完成")
        
        print("🎉 Phase 1 遷移完成！")


if __name__ == "__main__":
    migrate()
