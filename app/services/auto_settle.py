"""
SELA 樂透一路發 - 自動結算服務
"""
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from decimal import Decimal
from sqlalchemy.orm import Session

from app.models.group import Group, GroupStatus
from app.models.series import GroupSeries
from app.services.settlement_service import settlement_service


class AutoSettleService:
    """自動結算服務"""
    
    @classmethod
    def settle_group(
        cls,
        db: Session,
        group: Group,
        admin_user_id: int = 1  # 系統管理員 ID
    ) -> Dict[str, Any]:
        """
        結算單一 Group
        
        Args:
            db: 資料庫 Session
            group: 要結算的 Group
            admin_user_id: 執行結算的管理員 ID
        
        Returns:
            結算結果
        """
        # 檢查狀態
        if group.status != GroupStatus.DRAWN:
            return {
                "success": False,
                "group_id": group.id,
                "message": f"狀態不符：{group.status.value}，只能在開獎後結算",
                "settled": False
            }
        
        try:
            # 執行結算
            snapshot = settlement_service.execute_settlement(db, group, admin_user_id)
            
            return {
                "success": True,
                "group_id": group.id,
                "series_id": group.series_id,
                "period_number": group.period_number,
                "message": "結算完成",
                "settled": True,
                "snapshot_id": snapshot.id,
                "total_prize": float(group.total_prize or 0),
                "total_prize_after_tax": float(group.total_prize_after_tax or 0)
            }
            
        except ValueError as e:
            return {
                "success": False,
                "group_id": group.id,
                "message": f"結算失敗：{str(e)}",
                "settled": False
            }
        except Exception as e:
            db.rollback()
            return {
                "success": False,
                "group_id": group.id,
                "message": f"結算錯誤：{str(e)}",
                "settled": False
            }
    
    @classmethod
    def auto_settle_all_drawn(
        cls,
        db: Session,
        admin_user_id: int = 1
    ) -> Dict[str, Any]:
        """
        自動結算所有已開獎的 Group
        
        掃描所有狀態為 DRAWN 的 Group 並執行結算
        """
        # 查詢所有已開獎未結算的 Group
        groups = db.query(Group).filter(
            Group.status == GroupStatus.DRAWN
        ).all()
        
        if not groups:
            return {
                "success": True,
                "message": "沒有需要結算的團",
                "groups_settled": 0,
                "total_prize": 0
            }
        
        results = []
        total_settled = 0
        total_prize = Decimal("0")
        
        for group in groups:
            result = cls.settle_group(db, group, admin_user_id)
            results.append(result)
            
            if result["success"]:
                total_settled += 1
                total_prize += Decimal(str(result.get("total_prize_after_tax", 0)))
        
        return {
            "success": True,
            "message": f"結算完成：{total_settled}/{len(groups)} 團",
            "groups_checked": len(groups),
            "groups_settled": total_settled,
            "groups_failed": len(groups) - total_settled,
            "total_prize": float(total_prize),
            "details": results
        }
    
    @classmethod
    def settle_by_series(
        cls,
        db: Session,
        series_id: int,
        admin_user_id: int = 1
    ) -> Dict[str, Any]:
        """
        結算指定系列團的所有已開獎期別
        """
        # 查詢該系列所有已開獎的 Group
        groups = db.query(Group).filter(
            Group.series_id == series_id,
            Group.status == GroupStatus.DRAWN
        ).order_by(Group.period_number).all()
        
        if not groups:
            return {
                "success": True,
                "message": "該系列沒有需要結算的期別",
                "series_id": series_id,
                "groups_settled": 0
            }
        
        results = []
        total_settled = 0
        total_prize = Decimal("0")
        
        for group in groups:
            result = cls.settle_group(db, group, admin_user_id)
            results.append(result)
            
            if result["success"]:
                total_settled += 1
                total_prize += Decimal(str(result.get("total_prize_after_tax", 0)))
        
        return {
            "success": True,
            "message": f"系列結算完成：{total_settled}/{len(groups)} 期",
            "series_id": series_id,
            "groups_checked": len(groups),
            "groups_settled": total_settled,
            "total_prize": float(total_prize),
            "details": results
        }


# 全域實例
auto_settle_service = AutoSettleService()
