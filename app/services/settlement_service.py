"""
SELA 樂透一路發 - 結算服務
"""
from datetime import datetime, timezone
from typing import List, Dict, Any
from decimal import Decimal, ROUND_DOWN
from sqlalchemy.orm import Session

from app.models import (
    Group, GroupStatus, GroupSeries, GroupMember, MemberStatus,
    PeriodContribution, PeriodSnapshot,
    UserLedger, AccountType, TransactionType,
    EventLog, EventCategory, ActorType
)


class SettlementService:
    """結算服務"""
    
    @staticmethod
    def calculate_settlement(
        db: Session,
        group: Group
    ) -> Dict[str, Any]:
        """
        計算結算(預覽)
        
        Returns:
            {
                "total_pool": 2000,
                "total_spent": 1400,
                "total_carryover": 600,
                "total_prize": 4000,
                "total_prize_after_tax": 3200,
                "members": [
                    {
                        "member_id": 1,
                        "user_id": 1,
                        "display_name": "王小明",
                        "pool_share_before": 500,
                        "effective_contribution": 350,
                        "ratio": 0.25,
                        "carryover": 150,
                        "prize_share": 800,
                        "pool_share_after": 950
                    }
                ]
            }
        """
        if group.status not in [GroupStatus.DRAWN, GroupStatus.SETTLED]:
            raise ValueError("只能在開獎後結算")
        
        # 取得貢獻記錄
        contributions = db.query(PeriodContribution).filter(
            PeriodContribution.group_id == group.id
        ).all()
        
        if not contributions:
            raise ValueError("找不到貢獻記錄,請先鎖定集資")
        
        # 基礎數據
        total_pool = group.total_pool
        total_spent = group.total_spent
        total_carryover = total_pool - total_spent
        total_prize = group.total_prize
        total_prize_after_tax = group.total_prize_after_tax
        
        # 計算比例
        # spending_ratio = 實際花費 / 總資金池
        if total_pool > 0:
            spending_ratio = total_spent / total_pool
        else:
            spending_ratio = Decimal("0")
        
        # 計算每位成員
        members_data = []
        total_effective = Decimal("0")
        
        for contrib in contributions:
            member = contrib.member
            user = member.user
            
            pool_share_before = contrib.pool_share_at_lock
            
            # 有效貢獻 = 份額 × spending_ratio
            effective_contribution = (pool_share_before * spending_ratio).quantize(
                Decimal("0.01"), rounding=ROUND_DOWN
            )
            total_effective += effective_contribution
            
            members_data.append({
                "contribution_id": contrib.id,
                "member_id": member.id,
                "user_id": user.id,
                "display_name": user.nickname or user.display_name,
                "pool_share_before": pool_share_before,
                "effective_contribution": effective_contribution,
            })
        
        # 計算比例和分配
        for data in members_data:
            effective = data["effective_contribution"]
            
            # 貢獻比例
            if total_effective > 0:
                ratio = float(effective / total_effective)
            else:
                ratio = 0.0
            
            # 滾入金額 = 份額 - 有效貢獻
            carryover = data["pool_share_before"] - effective
            
            # 獎金份額 = 總獎金(扣稅後) × 比例
            prize_share = (total_prize_after_tax * Decimal(str(ratio))).quantize(
                Decimal("0.01"), rounding=ROUND_DOWN
            )
            
            # 結算後份額 = 滾入 + 獎金
            pool_share_after = carryover + prize_share
            
            data["ratio"] = round(ratio, 6)
            data["carryover"] = carryover
            data["prize_share"] = prize_share
            data["pool_share_after"] = pool_share_after
        
        return {
            "group_id": group.id,
            "period_number": group.period_number,
            "total_pool": total_pool,
            "total_spent": total_spent,
            "total_carryover": total_carryover,
            "total_prize": total_prize,
            "total_prize_after_tax": total_prize_after_tax,
            "members": members_data
        }
    
    @classmethod
    def execute_settlement(
        cls,
        db: Session,
        group: Group,
        user_id: int
    ) -> PeriodSnapshot:
        """執行結算"""
        if group.status != GroupStatus.DRAWN:
            raise ValueError("只能在開獎後結算")
        
        # 計算結算
        settlement_data = cls.calculate_settlement(db, group)
        
        # 更新每位成員
        for member_data in settlement_data["members"]:
            # 更新貢獻記錄
            contrib = db.query(PeriodContribution).filter(
                PeriodContribution.id == member_data["contribution_id"]
            ).first()
            
            contrib.effective_contribution = member_data["effective_contribution"]
            contrib.contribution_ratio = Decimal(str(member_data["ratio"]))
            contrib.carryover_amount = member_data["carryover"]
            contrib.prize_share = member_data["prize_share"]
            contrib.new_pool_share = member_data["pool_share_after"]
            
            # 更新成員份額
            member = contrib.member
            old_share = member.pool_share
            member.pool_share = member_data["pool_share_after"]
            member.total_prize_received += member_data["prize_share"]
            
            # 記錄帳本 - 購買扣除
            if member_data["effective_contribution"] > 0:
                ledger1 = UserLedger(
                    user_id=member.user_id,
                    account_type=AccountType.POOL,
                    series_id=group.series_id,
                    transaction_type=TransactionType.POOL_PURCHASE,
                    amount=-member_data["effective_contribution"],
                    balance_after=member_data["carryover"],
                    reference_type="group",
                    reference_id=group.id,
                    note=f"第{group.period_number}期購買"
                )
                db.add(ledger1)
            
            # 記錄帳本 - 獎金分配
            if member_data["prize_share"] > 0:
                ledger2 = UserLedger(
                    user_id=member.user_id,
                    account_type=AccountType.POOL,
                    series_id=group.series_id,
                    transaction_type=TransactionType.POOL_PRIZE,
                    amount=member_data["prize_share"],
                    balance_after=member_data["pool_share_after"],
                    reference_type="group",
                    reference_id=group.id,
                    note=f"第{group.period_number}期獎金"
                )
                db.add(ledger2)
        
        # 更新系列團資金池
        series = group.series
        new_pool = sum(m["pool_share_after"] for m in settlement_data["members"])
        series.current_pool = Decimal(str(new_pool))
        series.total_prize += group.total_prize_after_tax
        
        # 更新單期團狀態
        group.status = GroupStatus.SETTLED
        group.settled_at = datetime.now(timezone.utc)
        
        # 建立快照
        snapshot = PeriodSnapshot(
            group_id=group.id,
            series_id=group.series_id,
            snapshot_data={
                "period_number": group.period_number,
                "lottery_type": group.lottery_type.code,
                "draw_term": group.draw_term,
                "winning_numbers": group.winning_numbers,
                "total_pool": float(settlement_data["total_pool"]),
                "total_spent": float(settlement_data["total_spent"]),
                "total_carryover": float(settlement_data["total_carryover"]),
                "total_prize": float(settlement_data["total_prize"]),
                "total_prize_after_tax": float(settlement_data["total_prize_after_tax"]),
                "tickets": [
                    {
                        "id": t.id,
                        "numbers": t.numbers,
                        "prize_results": t.prize_results,
                        "prize_amount": float(t.prize_amount)
                    }
                    for t in group.tickets
                ],
                "members": [
                    {
                        k: float(v) if isinstance(v, Decimal) else v
                        for k, v in m.items()
                    }
                    for m in settlement_data["members"]
                ]
            }
        )
        db.add(snapshot)
        
        # 記錄事件
        event = EventLog(
            event_type="group_settled",
            category=EventCategory.SETTLEMENT,
            actor_id=user_id,
            actor_type=ActorType.USER,
            target_type="group",
            target_id=group.id,
            series_id=group.series_id,
            group_id=group.id,
            event_data={
                "total_prize": float(group.total_prize),
                "total_prize_after_tax": float(group.total_prize_after_tax),
                "new_pool": float(new_pool)
            }
        )
        db.add(event)
        
        db.commit()
        db.refresh(snapshot)
        return snapshot


# 全域實例
settlement_service = SettlementService()
