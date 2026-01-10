"""
SELA 樂透一路發 - 自動對獎服務
"""
from datetime import datetime, timezone, date
from typing import List, Dict, Any, Optional
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.group import Group, GroupStatus
from app.models.ticket import Ticket
from app.models.lottery_type import LotteryType
from app.models.lottery_draw import LotteryDraw
from app.services.group_service import PrizeChecker

# 嘗試導入自動結算服務
try:
    from app.services.auto_settle import auto_settle_service
    HAS_AUTO_SETTLE = True
except ImportError:
    HAS_AUTO_SETTLE = False


class AutoCheckService:
    """自動對獎服務"""
    
    @staticmethod
    def get_winning_numbers(db: Session, lottery_type_code: str, draw_term: str) -> Optional[dict]:
        """
        從 LotteryDraw 取得開獎號碼
        
        Args:
            lottery_type_code: 彩種代碼 (power/super/daily539)
            draw_term: 期數
        
        Returns:
            開獎號碼 dict 或 None
        """
        draw = db.query(LotteryDraw).filter(
            LotteryDraw.lottery_type == lottery_type_code,
            LotteryDraw.draw_term == draw_term
        ).first()
        
        if draw and draw.numbers:
            return draw.numbers
        
        return None
    
    @staticmethod
    def get_winning_numbers_by_date(db: Session, lottery_type_code: str, draw_date: date) -> Optional[dict]:
        """
        依日期從 LotteryDraw 取得開獎號碼
        """
        draw = db.query(LotteryDraw).filter(
            LotteryDraw.lottery_type == lottery_type_code,
            LotteryDraw.draw_date == draw_date
        ).order_by(LotteryDraw.id.desc()).first()
        
        if draw and draw.numbers:
            return draw.numbers
        
        return None
    
    @classmethod
    def check_group(
        cls,
        db: Session,
        group: Group,
        winning_numbers: Optional[dict] = None,
        auto_settle: bool = False,
        admin_user_id: int = 1
    ) -> Dict[str, Any]:
        """
        對獎單一 Group
        
        Args:
            db: 資料庫 Session
            group: 要對獎的 Group
            winning_numbers: 開獎號碼（可選，若未提供則自動查詢）
            auto_settle: 對獎後是否自動結算
            admin_user_id: 執行結算的管理員 ID
        
        Returns:
            對獎結果
        """
        # 檢查狀態
        if group.status not in [GroupStatus.PURCHASED, GroupStatus.DRAWN]:
            return {
                "success": False,
                "group_id": group.id,
                "message": f"狀態不符：{group.status.value}",
                "tickets_checked": 0,
                "total_prize": 0
            }
        
        # 取得彩種
        lottery_type = db.query(LotteryType).filter(
            LotteryType.id == group.lottery_type_id
        ).first()
        
        if not lottery_type:
            return {
                "success": False,
                "group_id": group.id,
                "message": "找不到彩種",
                "tickets_checked": 0,
                "total_prize": 0
            }
        
        # 取得開獎號碼
        if not winning_numbers:
            if group.draw_term:
                winning_numbers = cls.get_winning_numbers(db, lottery_type.code, group.draw_term)
            elif group.draw_date:
                winning_numbers = cls.get_winning_numbers_by_date(db, lottery_type.code, group.draw_date)
        
        if not winning_numbers:
            return {
                "success": False,
                "group_id": group.id,
                "message": "找不到開獎號碼",
                "tickets_checked": 0,
                "total_prize": 0
            }
        
        # 設定 winning_numbers 到 group（PrizeChecker 需要）
        group.winning_numbers = winning_numbers
        
        # 執行對獎
        try:
            total_prize = PrizeChecker.check_all_tickets(db, group)
            
            # 更新狀態
            group.status = GroupStatus.DRAWN
            group.drawn_at = datetime.now(timezone.utc)
            db.commit()
            
            # 統計結果
            tickets = db.query(Ticket).filter(Ticket.group_id == group.id).all()
            winning_tickets = [t for t in tickets if t.prize_amount and t.prize_amount > 0]
            
            result = {
                "success": True,
                "group_id": group.id,
                "message": "對獎完成",
                "tickets_checked": len(tickets),
                "winning_tickets": len(winning_tickets),
                "total_prize": float(total_prize),
                "winning_numbers": winning_numbers,
                "settled": False
            }
            
            # 自動結算
            if auto_settle and HAS_AUTO_SETTLE:
                try:
                    settle_result = auto_settle_service.settle_group(db, group, admin_user_id)
                    result["settled"] = settle_result.get("success", False)
                    result["settle_result"] = settle_result
                    if settle_result.get("success"):
                        result["message"] = "對獎並結算完成"
                except Exception as e:
                    result["settle_error"] = str(e)
            
            return result
            
        except Exception as e:
            db.rollback()
            return {
                "success": False,
                "group_id": group.id,
                "message": f"對獎失敗：{str(e)}",
                "tickets_checked": 0,
                "total_prize": 0
            }
    
    @classmethod
    def auto_check_by_lottery_type(
        cls,
        db: Session,
        lottery_type_code: str,
        draw_term: Optional[str] = None,
        draw_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        自動對獎指定彩種的所有未對獎 Group
        
        Args:
            lottery_type_code: 彩種代碼
            draw_term: 期數（可選）
            draw_date: 開獎日期（可選）
        
        Returns:
            對獎結果摘要
        """
        # 取得彩種
        lottery_type = db.query(LotteryType).filter(
            LotteryType.code == lottery_type_code
        ).first()
        
        if not lottery_type:
            return {
                "success": False,
                "message": f"找不到彩種：{lottery_type_code}",
                "groups_checked": 0
            }
        
        # 取得開獎號碼
        if draw_term:
            winning_numbers = cls.get_winning_numbers(db, lottery_type_code, draw_term)
        elif draw_date:
            winning_numbers = cls.get_winning_numbers_by_date(db, lottery_type_code, draw_date)
        else:
            return {
                "success": False,
                "message": "需要提供 draw_term 或 draw_date",
                "groups_checked": 0
            }
        
        if not winning_numbers:
            return {
                "success": False,
                "message": "找不到開獎號碼",
                "groups_checked": 0
            }
        
        # 查詢符合條件的 Group
        query = db.query(Group).filter(
            Group.lottery_type_id == lottery_type.id,
            Group.status == GroupStatus.PURCHASED
        )
        
        if draw_term:
            query = query.filter(Group.draw_term == draw_term)
        elif draw_date:
            query = query.filter(Group.draw_date == draw_date)
        
        groups = query.all()
        
        if not groups:
            return {
                "success": True,
                "message": "沒有需要對獎的團",
                "groups_checked": 0,
                "total_prize": 0
            }
        
        # 逐一對獎
        results = []
        total_prize = Decimal("0")
        
        for group in groups:
            result = cls.check_group(db, group, winning_numbers)
            results.append(result)
            if result["success"]:
                total_prize += Decimal(str(result["total_prize"]))
        
        success_count = sum(1 for r in results if r["success"])
        
        return {
            "success": True,
            "message": f"對獎完成：{success_count}/{len(groups)} 團",
            "lottery_type": lottery_type_code,
            "draw_term": draw_term,
            "draw_date": str(draw_date) if draw_date else None,
            "groups_checked": len(groups),
            "groups_success": success_count,
            "total_prize": float(total_prize),
            "details": results
        }
    
    @classmethod
    def auto_check_all_pending(
        cls,
        db: Session,
        auto_settle: bool = False,
        admin_user_id: int = 1
    ) -> Dict[str, Any]:
        """
        自動對獎所有待對獎的 Group
        
        掃描所有狀態為 PURCHASED 的 Group，
        嘗試從 LotteryDraw 取得對應的開獎號碼並對獎
        
        Args:
            db: 資料庫 Session
            auto_settle: 對獎後是否自動結算
            admin_user_id: 執行結算的管理員 ID
        """
        # 查詢所有待對獎的 Group
        groups = db.query(Group).filter(
            Group.status == GroupStatus.PURCHASED
        ).all()
        
        if not groups:
            return {
                "success": True,
                "message": "沒有需要對獎的團",
                "groups_checked": 0
            }
        
        results = []
        total_checked = 0
        total_success = 0
        total_settled = 0
        total_prize = Decimal("0")
        
        for group in groups:
            result = cls.check_group(db, group, auto_settle=auto_settle, admin_user_id=admin_user_id)
            
            if result["success"]:
                total_success += 1
                total_prize += Decimal(str(result["total_prize"]))
                if result.get("settled"):
                    total_settled += 1
                results.append(result)
            elif "找不到開獎號碼" not in result["message"]:
                # 只記錄非「找不到開獎號碼」的錯誤
                results.append(result)
            
            total_checked += 1
        
        message = f"掃描完成：{total_success}/{total_checked} 團對獎成功"
        if auto_settle and total_settled > 0:
            message += f"，{total_settled} 團已結算"
        
        return {
            "success": True,
            "message": message,
            "groups_checked": total_checked,
            "groups_success": total_success,
            "groups_settled": total_settled,
            "groups_pending": total_checked - total_success,
            "total_prize": float(total_prize),
            "details": results
        }


# 全域實例
auto_check_service = AutoCheckService()
