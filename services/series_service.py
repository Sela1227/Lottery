"""
SELA 樂透一路發 - 系列團服務
"""
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Tuple
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models import (
    GroupSeries, SeriesInvitation, GroupMember,
    MemberRole, MemberStatus, SeriesStatus,
    UserLedger, AccountType, TransactionType,
    EventLog, EventCategory, ActorType
)
from app.schemas.series import SeriesCreate, SeriesUpdate, InvitationCreate


class SeriesService:
    """系列團服務"""
    
    @staticmethod
    def create(
        db: Session,
        user_id: int,
        data: SeriesCreate
    ) -> GroupSeries:
        """建立系列團"""
        # 建立系列團
        series = GroupSeries(
            name=data.name,
            description=data.description,
            allowed_lottery_types=data.allowed_lottery_types,
            withdrawal_policy=data.withdrawal_policy,
            end_condition=data.end_condition,
            creator_id=user_id,
            current_pool=data.initial_pool_share,
            total_invested=data.initial_pool_share
        )
        db.add(series)
        db.flush()  # 取得 series.id
        
        # 建立者成為管理員
        member = GroupMember(
            series_id=series.id,
            user_id=user_id,
            role=MemberRole.ADMIN,
            pool_share=data.initial_pool_share,
            total_invested=data.initial_pool_share
        )
        db.add(member)
        
        # 記錄帳本
        ledger = UserLedger(
            user_id=user_id,
            account_type=AccountType.POOL,
            series_id=series.id,
            transaction_type=TransactionType.POOL_JOIN,
            amount=data.initial_pool_share,
            balance_after=data.initial_pool_share,
            reference_type="series",
            reference_id=series.id,
            note=f"建立系列團「{data.name}」"
        )
        db.add(ledger)
        
        # 記錄事件
        event = EventLog(
            event_type="series_created",
            category=EventCategory.SERIES,
            actor_id=user_id,
            actor_type=ActorType.USER,
            target_type="series",
            target_id=series.id,
            user_id=user_id,
            series_id=series.id,
            event_data={
                "name": data.name,
                "initial_pool": float(data.initial_pool_share)
            }
        )
        db.add(event)
        
        db.commit()
        db.refresh(series)
        return series
    
    @staticmethod
    def get_by_id(db: Session, series_id: int) -> Optional[GroupSeries]:
        """依 ID 取得系列團"""
        return db.query(GroupSeries).filter(GroupSeries.id == series_id).first()
    
    @staticmethod
    def get_user_series(db: Session, user_id: int) -> List[GroupSeries]:
        """取得用戶參與的系列團"""
        return db.query(GroupSeries).join(GroupMember).filter(
            GroupMember.user_id == user_id,
            GroupMember.status == MemberStatus.ACTIVE
        ).all()
    
    @staticmethod
    def update(
        db: Session,
        series: GroupSeries,
        data: SeriesUpdate,
        user_id: int
    ) -> GroupSeries:
        """更新系列團"""
        update_data = data.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(series, field, value)
        
        # 記錄事件
        event = EventLog(
            event_type="series_updated",
            category=EventCategory.SERIES,
            actor_id=user_id,
            actor_type=ActorType.USER,
            target_type="series",
            target_id=series.id,
            series_id=series.id,
            event_data=update_data
        )
        db.add(event)
        
        db.commit()
        db.refresh(series)
        return series
    
    @staticmethod
    def end_series(
        db: Session,
        series: GroupSeries,
        user_id: int,
        reason: str
    ) -> GroupSeries:
        """結束系列團"""
        series.status = SeriesStatus.ENDED
        series.ended_at = datetime.now(timezone.utc)
        series.end_reason = reason
        
        # 記錄事件
        event = EventLog(
            event_type="series_ended",
            category=EventCategory.SERIES,
            actor_id=user_id,
            actor_type=ActorType.USER,
            target_type="series",
            target_id=series.id,
            series_id=series.id,
            event_data={"reason": reason}
        )
        db.add(event)
        
        db.commit()
        db.refresh(series)
        return series
    
    # ==================== 邀請碼 ====================
    
    @staticmethod
    def create_invitation(
        db: Session,
        series_id: int,
        user_id: int,
        data: InvitationCreate
    ) -> SeriesInvitation:
        """建立邀請碼"""
        # 產生唯一邀請碼
        while True:
            code = secrets.token_urlsafe(6)[:8].upper()
            existing = db.query(SeriesInvitation).filter(
                SeriesInvitation.code == code
            ).first()
            if not existing:
                break
        
        expires_at = None
        if data.expires_in_days:
            expires_at = datetime.now(timezone.utc) + timedelta(days=data.expires_in_days)
        
        invitation = SeriesInvitation(
            series_id=series_id,
            code=code,
            max_uses=data.max_uses,
            expires_at=expires_at,
            created_by=user_id
        )
        db.add(invitation)
        db.commit()
        db.refresh(invitation)
        return invitation
    
    @staticmethod
    def get_invitation_by_code(db: Session, code: str) -> Optional[SeriesInvitation]:
        """依邀請碼取得邀請"""
        return db.query(SeriesInvitation).filter(
            SeriesInvitation.code == code.upper()
        ).first()
    
    @staticmethod
    def use_invitation(
        db: Session,
        invitation: SeriesInvitation
    ) -> bool:
        """使用邀請碼（增加使用次數）"""
        if not invitation.is_valid:
            return False
        
        invitation.used_count += 1
        db.commit()
        return True
    
    # ==================== 成員 ====================
    
    @staticmethod
    def get_member(
        db: Session,
        series_id: int,
        user_id: int
    ) -> Optional[GroupMember]:
        """取得成員"""
        return db.query(GroupMember).filter(
            GroupMember.series_id == series_id,
            GroupMember.user_id == user_id
        ).first()
    
    @staticmethod
    def get_members(db: Session, series_id: int) -> List[GroupMember]:
        """取得系列團所有成員"""
        return db.query(GroupMember).filter(
            GroupMember.series_id == series_id,
            GroupMember.status == MemberStatus.ACTIVE
        ).all()
    
    @staticmethod
    def add_member(
        db: Session,
        series: GroupSeries,
        user_id: int,
        initial_pool_share: Decimal,
        invitation: Optional[SeriesInvitation] = None
    ) -> Tuple[GroupMember, bool]:
        """
        加入成員
        Returns: (member, is_new)
        """
        # 檢查是否已是成員
        existing = db.query(GroupMember).filter(
            GroupMember.series_id == series.id,
            GroupMember.user_id == user_id
        ).first()
        
        if existing:
            if existing.status == MemberStatus.ACTIVE:
                return existing, False
            # 重新加入
            existing.status = MemberStatus.ACTIVE
            existing.pool_share = initial_pool_share
            existing.total_invested += initial_pool_share
            existing.exited_at = None
            existing.exit_reason = None
            member = existing
        else:
            member = GroupMember(
                series_id=series.id,
                user_id=user_id,
                role=MemberRole.MEMBER,
                pool_share=initial_pool_share,
                total_invested=initial_pool_share
            )
            db.add(member)
        
        # 更新系列團資金池
        series.current_pool += initial_pool_share
        series.total_invested += initial_pool_share
        
        # 使用邀請碼
        if invitation:
            invitation.used_count += 1
        
        # 記錄帳本
        db.flush()
        ledger = UserLedger(
            user_id=user_id,
            account_type=AccountType.POOL,
            series_id=series.id,
            transaction_type=TransactionType.POOL_JOIN,
            amount=initial_pool_share,
            balance_after=member.pool_share,
            reference_type="series",
            reference_id=series.id,
            note=f"加入系列團「{series.name}」"
        )
        db.add(ledger)
        
        # 記錄事件
        event = EventLog(
            event_type="member_joined",
            category=EventCategory.MEMBER,
            actor_id=user_id,
            actor_type=ActorType.USER,
            target_type="member",
            target_id=member.id,
            user_id=user_id,
            series_id=series.id,
            event_data={
                "initial_pool_share": float(initial_pool_share),
                "invitation_code": invitation.code if invitation else None
            }
        )
        db.add(event)
        
        db.commit()
        db.refresh(member)
        return member, True
    
    @staticmethod
    def topup_member(
        db: Session,
        member: GroupMember,
        amount: Decimal,
        user_id: int
    ) -> GroupMember:
        """成員加碼"""
        member.pool_share += amount
        member.total_invested += amount
        
        # 更新系列團
        series = member.series
        series.current_pool += amount
        series.total_invested += amount
        
        # 記錄帳本
        ledger = UserLedger(
            user_id=member.user_id,
            account_type=AccountType.POOL,
            series_id=series.id,
            transaction_type=TransactionType.POOL_TOPUP,
            amount=amount,
            balance_after=member.pool_share,
            reference_type="member",
            reference_id=member.id,
            note=f"加碼 ${amount}"
        )
        db.add(ledger)
        
        # 記錄事件
        event = EventLog(
            event_type="member_topup",
            category=EventCategory.MEMBER,
            actor_id=user_id,
            actor_type=ActorType.USER,
            target_type="member",
            target_id=member.id,
            user_id=member.user_id,
            series_id=series.id,
            event_data={"amount": float(amount)}
        )
        db.add(event)
        
        db.commit()
        db.refresh(member)
        return member
    
    @staticmethod
    def is_admin(db: Session, series_id: int, user_id: int) -> bool:
        """檢查是否為管理員"""
        member = db.query(GroupMember).filter(
            GroupMember.series_id == series_id,
            GroupMember.user_id == user_id,
            GroupMember.status == MemberStatus.ACTIVE
        ).first()
        return member and member.role == MemberRole.ADMIN


# 全域實例
series_service = SeriesService()
