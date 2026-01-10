"""
SELA 樂透一路發 - 成就徽章 API
"""
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from pydantic import BaseModel
from decimal import Decimal

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.models.personal import Achievement, UserAchievement, AchievementCategory
from app.models.user import User
from app.models.member import GroupMember, MemberStatus
from app.models.series import GroupSeries
from app.models.group import Group
from app.models.ticket import Ticket


router = APIRouter(prefix="/achievements", tags=["Achievements"])


# ==================== Schema ====================

class AchievementResponse(BaseModel):
    """成就回應"""
    id: int
    code: str
    name: str
    description: Optional[str] = None
    icon: str
    category: str
    threshold: int
    points: int
    progress: int = 0
    is_unlocked: bool = False
    unlocked_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class AchievementListResponse(BaseModel):
    """成就列表回應"""
    achievements: List[AchievementResponse]
    total_points: int
    unlocked_count: int
    total_count: int


class UserPointsResponse(BaseModel):
    """用戶點數回應"""
    user_id: int
    total_points: int
    unlocked_count: int
    rank: int
    next_achievement: Optional[AchievementResponse] = None


# ==================== 成就定義 ====================

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
        "description": "參與 50 期集資",
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


# ==================== Helper Functions ====================

def get_user_stats(db: Session, user_id: int) -> dict:
    """計算用戶統計數據"""
    # 參與的系列團數
    series_joined = db.query(GroupMember).filter(
        GroupMember.user_id == user_id,
        GroupMember.status == MemberStatus.ACTIVE
    ).count()
    
    # 創建的系列團數
    series_created = db.query(GroupSeries).filter(
        GroupSeries.created_by == user_id
    ).count()
    
    # 參與的期數
    periods_participated = db.query(func.count(func.distinct(Ticket.group_id))).filter(
        Ticket.user_id == user_id
    ).scalar() or 0
    
    # 中獎次數 (有獎金的期數)
    win_count = db.query(func.count(func.distinct(Group.id))).join(
        Ticket, Group.id == Ticket.group_id
    ).filter(
        Ticket.user_id == user_id,
        Group.total_prize > 0
    ).scalar() or 0
    
    # 累計投資
    total_invested = db.query(func.coalesce(func.sum(GroupMember.total_invested), 0)).filter(
        GroupMember.user_id == user_id
    ).scalar() or 0
    
    # 最大單次中獎
    max_single_prize = db.query(func.coalesce(func.max(GroupMember.total_prize_received), 0)).filter(
        GroupMember.user_id == user_id
    ).scalar() or 0
    
    # 最大團隊人數 (作為團主)
    max_team_size = db.query(func.count(GroupMember.id)).join(
        GroupSeries, GroupMember.series_id == GroupSeries.id
    ).filter(
        GroupSeries.created_by == user_id,
        GroupMember.status == MemberStatus.ACTIVE
    ).group_by(GroupSeries.id).order_by(desc(func.count(GroupMember.id))).first()
    max_team_size = max_team_size[0] if max_team_size else 0
    
    return {
        "series_joined": series_joined,
        "series_created": series_created,
        "periods_participated": periods_participated,
        "win_count": win_count,
        "total_invested": float(total_invested),
        "max_single_prize": float(max_single_prize),
        "max_team_size": max_team_size,
    }


def check_and_update_achievements(db: Session, user_id: int):
    """檢查並更新用戶成就"""
    stats = get_user_stats(db, user_id)
    achievements = db.query(Achievement).filter(Achievement.is_active == True).all()
    
    for achievement in achievements:
        # 取得或建立用戶成就記錄
        user_ach = db.query(UserAchievement).filter(
            UserAchievement.user_id == user_id,
            UserAchievement.achievement_id == achievement.id
        ).first()
        
        if not user_ach:
            user_ach = UserAchievement(
                user_id=user_id,
                achievement_id=achievement.id,
                progress=0,
                is_unlocked=False
            )
            db.add(user_ach)
        
        # 更新進度
        stat_value = stats.get(achievement.stat_field, 0)
        user_ach.progress = int(stat_value)
        
        # 檢查是否達成
        if not user_ach.is_unlocked and stat_value >= achievement.threshold:
            user_ach.is_unlocked = True
            user_ach.unlocked_at = datetime.now()
    
    db.commit()


# ==================== API 端點 ====================

@router.get("/", response_model=AchievementListResponse)
async def get_achievements(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """取得所有成就及用戶進度"""
    # 先更新成就進度
    check_and_update_achievements(db, user_id)
    
    # 取得所有成就
    achievements = db.query(Achievement).filter(
        Achievement.is_active == True
    ).order_by(Achievement.sort_order).all()
    
    result = []
    total_points = 0
    unlocked_count = 0
    
    for ach in achievements:
        # 取得用戶進度
        user_ach = db.query(UserAchievement).filter(
            UserAchievement.user_id == user_id,
            UserAchievement.achievement_id == ach.id
        ).first()
        
        progress = user_ach.progress if user_ach else 0
        is_unlocked = user_ach.is_unlocked if user_ach else False
        unlocked_at = user_ach.unlocked_at if user_ach else None
        
        if is_unlocked:
            total_points += ach.points
            unlocked_count += 1
        
        result.append(AchievementResponse(
            id=ach.id,
            code=ach.code,
            name=ach.name,
            description=ach.description,
            icon=ach.icon,
            category=ach.category.value,
            threshold=ach.threshold,
            points=ach.points,
            progress=progress,
            is_unlocked=is_unlocked,
            unlocked_at=unlocked_at
        ))
    
    return AchievementListResponse(
        achievements=result,
        total_points=total_points,
        unlocked_count=unlocked_count,
        total_count=len(achievements)
    )


@router.get("/points", response_model=UserPointsResponse)
async def get_my_points(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """取得我的點數與排名"""
    # 更新成就
    check_and_update_achievements(db, user_id)
    
    # 計算總點數
    unlocked = db.query(UserAchievement).join(Achievement).filter(
        UserAchievement.user_id == user_id,
        UserAchievement.is_unlocked == True
    ).all()
    
    total_points = sum(ua.achievement.points for ua in unlocked)
    unlocked_count = len(unlocked)
    
    # 計算排名 (依總點數)
    all_users_points = db.query(
        UserAchievement.user_id,
        func.sum(Achievement.points).label('points')
    ).join(Achievement).filter(
        UserAchievement.is_unlocked == True
    ).group_by(UserAchievement.user_id).order_by(desc('points')).all()
    
    rank = 1
    for i, (uid, pts) in enumerate(all_users_points):
        if uid == user_id:
            rank = i + 1
            break
    
    # 找下一個未解鎖的成就
    next_ach = db.query(Achievement).outerjoin(
        UserAchievement, 
        (UserAchievement.achievement_id == Achievement.id) & 
        (UserAchievement.user_id == user_id)
    ).filter(
        Achievement.is_active == True,
        (UserAchievement.is_unlocked == False) | (UserAchievement.id == None)
    ).order_by(Achievement.sort_order).first()
    
    next_achievement = None
    if next_ach:
        user_ach = db.query(UserAchievement).filter(
            UserAchievement.user_id == user_id,
            UserAchievement.achievement_id == next_ach.id
        ).first()
        
        next_achievement = AchievementResponse(
            id=next_ach.id,
            code=next_ach.code,
            name=next_ach.name,
            description=next_ach.description,
            icon=next_ach.icon,
            category=next_ach.category.value,
            threshold=next_ach.threshold,
            points=next_ach.points,
            progress=user_ach.progress if user_ach else 0,
            is_unlocked=False
        )
    
    return UserPointsResponse(
        user_id=user_id,
        total_points=total_points,
        unlocked_count=unlocked_count,
        rank=rank,
        next_achievement=next_achievement
    )


@router.post("/init")
async def init_achievements(
    db: Session = Depends(get_db)
):
    """初始化預設成就 (管理員用)"""
    created = 0
    for ach_data in DEFAULT_ACHIEVEMENTS:
        existing = db.query(Achievement).filter(Achievement.code == ach_data["code"]).first()
        if not existing:
            ach = Achievement(**ach_data)
            db.add(ach)
            created += 1
    
    db.commit()
    return {"message": f"已建立 {created} 個成就", "total": len(DEFAULT_ACHIEVEMENTS)}
