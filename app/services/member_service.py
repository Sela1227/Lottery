"""
SELA 樂透一路發 - 成員異動服務
處理減碼、退出申請的業務邏輯
"""
from decimal import Decimal
from datetime import datetime
from typing import Optional, Tuple
from sqlalchemy.orm import Session

from app.models.member import GroupMember, MemberStatus
from app.models.member_request import MemberRequest, RequestType, RequestStatus
from app.models.ledger import UserLedger, AccountType, TransactionType
from app.models.series import GroupSeries


class MemberService:
    """成員異動服務"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_member(self, series_id: int, user_id: int) -> Optional[GroupMember]:
        """取得成員資料"""
        return self.db.query(GroupMember).filter(
            GroupMember.series_id == series_id,
            GroupMember.user_id == user_id,
            GroupMember.status == MemberStatus.ACTIVE
        ).first()
    
    def has_pending_request(self, series_id: int, user_id: int) -> bool:
        """檢查是否有待處理的申請"""
        return self.db.query(MemberRequest).filter(
            MemberRequest.series_id == series_id,
            MemberRequest.user_id == user_id,
            MemberRequest.status == RequestStatus.PENDING
        ).first() is not None
    
    def create_reduce_request(
        self,
        series_id: int,
        user_id: int,
        amount: Decimal,
        reason: Optional[str] = None
    ) -> Tuple[bool, str, Optional[int], bool]:
        """
        建立減碼申請
        
        Returns:
            (success, message, request_id, auto_approved)
        """
        # 檢查成員
        member = self.get_member(series_id, user_id)
        if not member:
            return False, "您不是此集資的成員", None, False
        
        # 檢查是否有待處理的申請（非管理員才需要檢查）
        if not member.is_admin and self.has_pending_request(series_id, user_id):
            return False, "您已有待審核的申請,請等待處理", None, False
        
        # 檢查金額
        if amount <= 0:
            return False, "減碼金額必須大於 0", None, False
        
        if amount >= member.pool_share:
            return False, f"減碼金額不可超過目前份額 ${member.pool_share},如要全額退出請使用退出功能", None, False
        
        # 檢查剩餘金額是否足夠(至少保留 50 元)
        remaining = member.pool_share - amount
        if remaining < 50:
            return False, "減碼後份額至少需保留 50 元,如要全額退出請使用退出功能", None, False
        
        # 建立申請
        request = MemberRequest(
            series_id=series_id,
            user_id=user_id,
            request_type=RequestType.REDUCE,
            amount=amount,
            pool_share_before=member.pool_share,
            reason=reason
        )
        
        self.db.add(request)
        self.db.commit()
        self.db.refresh(request)
        
        # 管理員自動核准
        if member.is_admin:
            success, msg, actual = self.review_request(
                request_id=request.id,
                reviewer_id=user_id,
                approved=True,
                note="管理員自動核准"
            )
            return True, f"減碼 ${amount} 已執行", request.id, True
        
        return True, "減碼申請已送出,請等待管理員審核", request.id, False
    
    def create_withdraw_request(
        self,
        series_id: int,
        user_id: int,
        reason: Optional[str] = None
    ) -> Tuple[bool, str, Optional[int]]:
        """
        建立退出申請
        
        Returns:
            (success, message, request_id)
        """
        # 檢查成員
        member = self.get_member(series_id, user_id)
        if not member:
            return False, "您不是此集資的成員", None
        
        # 檢查是否為管理員
        if member.is_admin:
            return False, "集資管理員無法退出,請先轉移管理權限", None
        
        # 檢查是否有待處理的申請
        if self.has_pending_request(series_id, user_id):
            return False, "您已有待審核的申請,請等待處理", None
        
        # 建立申請(退出時 amount 為 NULL,表示全額)
        request = MemberRequest(
            series_id=series_id,
            user_id=user_id,
            request_type=RequestType.WITHDRAW,
            amount=None,
            pool_share_before=member.pool_share,
            reason=reason
        )
        
        self.db.add(request)
        self.db.commit()
        self.db.refresh(request)
        
        return True, "退出申請已送出,請等待管理員審核", request.id
    
    def cancel_request(self, request_id: int, user_id: int) -> Tuple[bool, str]:
        """
        取消申請(僅限申請人)
        """
        request = self.db.query(MemberRequest).filter(
            MemberRequest.id == request_id
        ).first()
        
        if not request:
            return False, "找不到此申請"
        
        if request.user_id != user_id:
            return False, "您只能取消自己的申請"
        
        if request.status != RequestStatus.PENDING:
            return False, "只能取消待審核的申請"
        
        request.status = RequestStatus.CANCELLED
        self.db.commit()
        
        return True, "申請已取消"
    
    def review_request(
        self,
        request_id: int,
        reviewer_id: int,
        approved: bool,
        note: Optional[str] = None
    ) -> Tuple[bool, str, Optional[Decimal]]:
        """
        審核申請
        
        Returns:
            (success, message, actual_amount)
        """
        request = self.db.query(MemberRequest).filter(
            MemberRequest.id == request_id
        ).first()
        
        if not request:
            return False, "找不到此申請", None
        
        if request.status != RequestStatus.PENDING:
            return False, "此申請已處理過", None
        
        # 檢查審核者是否為該集資的管理員
        reviewer_member = self.db.query(GroupMember).filter(
            GroupMember.series_id == request.series_id,
            GroupMember.user_id == reviewer_id,
            GroupMember.status == MemberStatus.ACTIVE
        ).first()
        
        if not reviewer_member or not reviewer_member.is_admin:
            return False, "您沒有審核權限", None
        
        # 取得申請者的成員資料
        member = self.get_member(request.series_id, request.user_id)
        if not member:
            request.status = RequestStatus.REJECTED
            request.reviewed_by = reviewer_id
            request.reviewed_at = datetime.now()
            request.review_note = "成員已不存在"
            self.db.commit()
            return False, "成員已不存在", None
        
        # 更新審核資訊
        request.reviewed_by = reviewer_id
        request.reviewed_at = datetime.now()
        request.review_note = note
        
        if not approved:
            # 拒絕
            request.status = RequestStatus.REJECTED
            self.db.commit()
            return True, "已拒絕此申請", None
        
        # 核准 - 執行減碼或退出
        actual_amount = self._execute_request(request, member)
        
        request.status = RequestStatus.APPROVED
        request.actual_amount = actual_amount
        self.db.commit()
        
        action = "減碼" if request.request_type == RequestType.REDUCE else "退出"
        return True, f"已核准{action}申請,金額 ${actual_amount}", actual_amount
    
    def _execute_request(self, request: MemberRequest, member: GroupMember) -> Decimal:
        """
        執行減碼或退出
        
        Returns:
            actual_amount: 實際減碼/退出金額
        """
        series = self.db.query(GroupSeries).filter(
            GroupSeries.id == request.series_id
        ).first()
        
        if request.request_type == RequestType.REDUCE:
            # 減碼
            actual_amount = min(request.amount, member.pool_share)
            new_share = member.pool_share - actual_amount
            
            # 更新成員份額
            member.pool_share = new_share
            
            # 更新集資總池
            series.current_pool -= actual_amount
            
            # 記錄帳本
            self._record_ledger(
                user_id=member.user_id,
                series_id=request.series_id,
                transaction_type=TransactionType.POOL_WITHDRAW,
                amount=-actual_amount,
                balance_after=new_share,
                reference_type="member_request",
                reference_id=request.id,
                note=f"減碼申請 #{request.id}"
            )
            
        else:
            # 退出
            actual_amount = member.pool_share
            
            # 更新集資總池
            series.current_pool -= actual_amount
            
            # 更新成員狀態
            member.pool_share = Decimal('0')
            member.status = MemberStatus.EXITED
            member.exited_at = datetime.now()
            member.exit_reason = request.reason or "主動申請退出"
            
            # 記錄帳本
            self._record_ledger(
                user_id=member.user_id,
                series_id=request.series_id,
                transaction_type=TransactionType.POOL_EXIT,
                amount=-actual_amount,
                balance_after=Decimal('0'),
                reference_type="member_request",
                reference_id=request.id,
                note=f"退出申請 #{request.id}"
            )
        
        return actual_amount
    
    def _record_ledger(
        self,
        user_id: int,
        series_id: int,
        transaction_type: TransactionType,
        amount: Decimal,
        balance_after: Decimal,
        reference_type: str,
        reference_id: int,
        note: str
    ):
        """記錄帳本"""
        ledger = UserLedger(
            user_id=user_id,
            account_type=AccountType.POOL,
            series_id=series_id,
            transaction_type=transaction_type,
            amount=amount,
            balance_after=balance_after,
            reference_type=reference_type,
            reference_id=reference_id,
            note=note
        )
        self.db.add(ledger)
    
    def get_pending_requests(self, series_id: int) -> list:
        """取得待審核的申請"""
        return self.db.query(MemberRequest).filter(
            MemberRequest.series_id == series_id,
            MemberRequest.status == RequestStatus.PENDING
        ).order_by(MemberRequest.created_at.desc()).all()
    
    def get_all_requests(self, series_id: int, limit: int = 50) -> list:
        """取得所有申請"""
        return self.db.query(MemberRequest).filter(
            MemberRequest.series_id == series_id
        ).order_by(MemberRequest.created_at.desc()).limit(limit).all()
    
    def get_user_requests(self, user_id: int, series_id: Optional[int] = None) -> list:
        """取得用戶的申請"""
        query = self.db.query(MemberRequest).filter(
            MemberRequest.user_id == user_id
        )
        if series_id:
            query = query.filter(MemberRequest.series_id == series_id)
        return query.order_by(MemberRequest.created_at.desc()).all()