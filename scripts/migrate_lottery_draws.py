"""
SELA 樂透一路發 - 新增 lottery_draws 資料表
執行方式: python scripts/migrate_lottery_draws.py
"""
import os
import sys

# 加入專案根目錄
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.core.database import engine


def migrate():
    """建立 lottery_draws 資料表"""
    
    print("=" * 50)
    print("SELA - 建立 lottery_draws 資料表")
    print("=" * 50)
    
    with engine.connect() as conn:
        # 檢查表是否已存在
        check_sql = text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'lottery_draws'
            )
        """)
        result = conn.execute(check_sql)
        exists = result.scalar()
        
        if exists:
            print("⚠️  lottery_draws 資料表已存在，跳過建立")
        else:
            print("📦 正在建立 lottery_draws 資料表...")
            
            create_sql = text("""
                CREATE TABLE lottery_draws (
                    id SERIAL PRIMARY KEY,
                    lottery_type VARCHAR(20) NOT NULL,
                    draw_term VARCHAR(20) NOT NULL,
                    draw_date DATE NOT NULL,
                    numbers JSONB NOT NULL,
                    jackpot BIGINT,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    CONSTRAINT uq_lottery_draw_term UNIQUE (lottery_type, draw_term)
                )
            """)
            conn.execute(create_sql)
            conn.commit()
            print("✅ 資料表建立完成")
            
            # 建立索引
            print("📦 正在建立索引...")
            conn.execute(text("CREATE INDEX ix_lottery_draws_type ON lottery_draws(lottery_type)"))
            conn.execute(text("CREATE INDEX ix_lottery_draws_date ON lottery_draws(draw_date)"))
            conn.commit()
            print("✅ 索引建立完成")
        
        # 顯示表結構
        print("\n📋 資料表結構:")
        print("-" * 40)
        struct_sql = text("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'lottery_draws'
            ORDER BY ordinal_position
        """)
        result = conn.execute(struct_sql)
        for row in result:
            nullable = "" if row[2] == "YES" else " NOT NULL"
            print(f"  {row[0]:<15} {row[1]}{nullable}")
        
        print("-" * 40)
        print("✅ 完成！")


if __name__ == "__main__":
    migrate()
