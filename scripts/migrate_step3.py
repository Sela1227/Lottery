"""
SELA 樂透一路發 - Step 3 資料庫遷移
建立個人彩券和成就徽章相關資料表
"""
import os
import sys

# 確保可以 import app 模組
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.core.database import engine, SessionLocal
from app.models.personal import (
    PersonalTicket, PersonalTicketStatus,
    Achievement, UserAchievement, AchievementCategory
)

# 預設成就資料
DEFAULT_ACHIEVEMENTS = [
    # 新手成就
    {
        "code": "first_join",
        "name": "新手上路",
        "description": "加入第一個系列團",
        "icon": "🎯",
        "category": AchievementCategory.BEGINNER,
        "threshold": 1,
        "stat_field": "series_joined",
        "points": 10,
        "sort_order": 1
    },
    {
        "code": "first_win",
        "name": "初試啼聲",
        "description": "第一次中獎",
        "icon": "🎉",
        "category": AchievementCategory.BEGINNER,
        "threshold": 1,
        "stat_field": "win_count",
        "points": 20,
        "sort_order": 2
    },
    
    # 參與成就
    {
        "code": "team_player_5",
        "name": "團隊好夥伴",
        "description": "參與 5 個系列團",
        "icon": "🤝",
        "category": AchievementCategory.PARTICIPATION,
        "threshold": 5,
        "stat_field": "series_joined",
        "points": 30,
        "sort_order": 10
    },
    {
        "code": "team_player_10",
        "name": "資深團員",
        "description": "參與 10 個系列團",
        "icon": "⭐",
        "category": AchievementCategory.PARTICIPATION,
        "threshold": 10,
        "stat_field": "series_joined",
        "points": 50,
        "sort_order": 11
    },
    {
        "code": "period_50",
        "name": "堅持不懈",
        "description": "參與 50 期團購",
        "icon": "💪",
        "category": AchievementCategory.PARTICIPATION,
        "threshold": 50,
        "stat_field": "periods_participated",
        "points": 100,
        "sort_order": 12
    },
    
    # 幸運成就
    {
        "code": "lucky_3",
        "name": "三連星",
        "description": "累計中獎 3 次",
        "icon": "🌟",
        "category": AchievementCategory.LUCKY,
        "threshold": 3,
        "stat_field": "win_count",
        "points": 30,
        "sort_order": 20
    },
    {
        "code": "lucky_10",
        "name": "幸運之星",
        "description": "累計中獎 10 次",
        "icon": "✨",
        "category": AchievementCategory.LUCKY,
        "threshold": 10,
        "stat_field": "win_count",
        "points": 80,
        "sort_order": 21
    },
    {
        "code": "big_win_1000",
        "name": "小確幸",
        "description": "單次中獎超過 $1,000",
        "icon": "💰",
        "category": AchievementCategory.LUCKY,
        "threshold": 1000,
        "stat_field": "max_single_prize",
        "points": 50,
        "sort_order": 22
    },
    {
        "code": "big_win_10000",
        "name": "大豐收",
        "description": "單次中獎超過 $10,000",
        "icon": "💎",
        "category": AchievementCategory.LUCKY,
        "threshold": 10000,
        "stat_field": "max_single_prize",
        "points": 150,
        "sort_order": 23
    },
    
    # 投資成就
    {
        "code": "invest_1000",
        "name": "小資族",
        "description": "累計投資達 $1,000",
        "icon": "📈",
        "category": AchievementCategory.INVESTMENT,
        "threshold": 1000,
        "stat_field": "total_invested",
        "points": 20,
        "sort_order": 30
    },
    {
        "code": "invest_10000",
        "name": "投資達人",
        "description": "累計投資達 $10,000",
        "icon": "🏆",
        "category": AchievementCategory.INVESTMENT,
        "threshold": 10000,
        "stat_field": "total_invested",
        "points": 80,
        "sort_order": 31
    },
    {
        "code": "invest_50000",
        "name": "金主爸爸",
        "description": "累計投資達 $50,000",
        "icon": "👑",
        "category": AchievementCategory.INVESTMENT,
        "threshold": 50000,
        "stat_field": "total_invested",
        "points": 200,
        "sort_order": 32
    },
    
    # 社交成就
    {
        "code": "creator",
        "name": "開團達人",
        "description": "建立第一個系列團",
        "icon": "🚀",
        "category": AchievementCategory.SOCIAL,
        "threshold": 1,
        "stat_field": "series_created",
        "points": 30,
        "sort_order": 40
    },
    {
        "code": "popular_5",
        "name": "人氣團主",
        "description": "管理的系列團有 5 位成員",
        "icon": "🔥",
        "category": AchievementCategory.SOCIAL,
        "threshold": 5,
        "stat_field": "max_team_size",
        "points": 50,
        "sort_order": 41
    },
]


def migrate():
    """執行遷移"""
    print("=" * 60)
    print("SELA 樂透一路發 - Step 3 資料庫遷移")
    print("=" * 60)
    
    with engine.connect() as conn:
        # 1. 建立個人彩券表
        print("\n[1/4] 建立 personal_tickets 表...")
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS personal_tickets (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id),
                lottery_type_id INTEGER NOT NULL REFERENCES lottery_types(id),
                numbers JSONB NOT NULL,
                special_number INTEGER,
                draw_term VARCHAR(20),
                draw_date VARCHAR(20),
                cost NUMERIC(10, 0) DEFAULT 100,
                prize NUMERIC(12, 0) DEFAULT 0,
                status VARCHAR(20) DEFAULT 'pending',
                match_count INTEGER DEFAULT 0,
                prize_tier VARCHAR(20),
                note TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                checked_at TIMESTAMP
            )
        """))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_personal_tickets_user ON personal_tickets(user_id)"))
        print("   ✓ personal_tickets 表已建立")
        
        # 2. 建立成就定義表
        print("\n[2/4] 建立 achievements 表...")
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS achievements (
                id SERIAL PRIMARY KEY,
                code VARCHAR(50) UNIQUE NOT NULL,
                name VARCHAR(100) NOT NULL,
                description TEXT,
                icon VARCHAR(10) DEFAULT '🏆',
                category VARCHAR(20) DEFAULT 'beginner',
                threshold INTEGER DEFAULT 1,
                stat_field VARCHAR(50),
                points INTEGER DEFAULT 10,
                sort_order INTEGER DEFAULT 0,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        print("   ✓ achievements 表已建立")
        
        # 3. 建立用戶成就記錄表
        print("\n[3/4] 建立 user_achievements 表...")
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS user_achievements (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id),
                achievement_id INTEGER NOT NULL REFERENCES achievements(id),
                progress INTEGER DEFAULT 0,
                is_unlocked BOOLEAN DEFAULT FALSE,
                unlocked_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, achievement_id)
            )
        """))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_user_achievements_user ON user_achievements(user_id)"))
        print("   ✓ user_achievements 表已建立")
        
        conn.commit()
    
    # 4. 初始化預設成就
    print("\n[4/4] 初始化預設成就...")
    db = SessionLocal()
    try:
        created = 0
        for ach_data in DEFAULT_ACHIEVEMENTS:
            existing = db.query(Achievement).filter(Achievement.code == ach_data["code"]).first()
            if not existing:
                ach = Achievement(**ach_data)
                db.add(ach)
                created += 1
                print(f"   + {ach_data['icon']} {ach_data['name']}")
        
        db.commit()
        print(f"   ✓ 已建立 {created} 個成就")
    finally:
        db.close()
    
    print("\n" + "=" * 60)
    print("Step 3 遷移完成！")
    print("=" * 60)


if __name__ == "__main__":
    migrate()
