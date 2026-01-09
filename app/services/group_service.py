"""
SELA 樂透一路發 - 單期團服務
"""
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from decimal import Decimal
from sqlalchemy.orm import Session

from app.models import (
    Group, GroupStatus, GroupSeries, GroupMember, MemberStatus,
    LotteryType, Ticket, PeriodContribution,
    UserLedger, AccountType, TransactionType,
    EventLog, EventCategory, ActorType, PeriodSnapshot
)
from app.schemas.group import GroupCreate, DrawResultInput


class GroupService:
    """單期團服務"""
    
    @staticmethod
    def create(
        db: Session,
        series: GroupSeries,
        data: GroupCreate,
        user_id: int
    ) -> Group:
        """建立單期團(開新期)"""
        # 取得彩種
        lottery_type = db.query(LotteryType).filter(
            LotteryType.code == data.lottery_type_code,
            LotteryType.is_active == True
        ).first()
        
        if not lottery_type:
            raise ValueError(f"彩種 {data.lottery_type_code} 不存在")
        
        if data.lottery_type_code not in series.allowed_lottery_types:
            raise ValueError(f"此系列團不允許 {lottery_type.name}")
        
        # 計算期數
        period_number = series.total_periods + 1
        
        # 建立單期團
        group = Group(
            series_id=series.id,
            period_number=period_number,
            lottery_type_id=lottery_type.id,
            draw_term=data.draw_term,
            draw_date=data.draw_date,
            collection_deadline=data.collection_deadline,
            choice_reason=data.choice_reason,
            total_pool=series.current_pool  # 繼承目前資金池
        )
        db.add(group)
        
        # 更新系列團期數
        series.total_periods = period_number
        
        # 記錄事件
        event = EventLog(
            event_type="group_created",
            category=EventCategory.GROUP,
            actor_id=user_id,
            actor_type=ActorType.USER,
            target_type="group",
            target_id=group.id,
            user_id=user_id,
            series_id=series.id,
            event_data={
                "period_number": period_number,
                "lottery_type": data.lottery_type_code,
                "total_pool": float(series.current_pool)
            }
        )
        db.add(event)
        
        db.commit()
        db.refresh(group)
        return group
    
    @staticmethod
    def get_by_id(db: Session, group_id: int) -> Optional[Group]:
        """依 ID 取得單期團"""
        return db.query(Group).filter(Group.id == group_id).first()
    
    @staticmethod
    def get_series_groups(
        db: Session,
        series_id: int,
        limit: int = 20
    ) -> List[Group]:
        """取得系列團的單期團列表"""
        return db.query(Group).filter(
            Group.series_id == series_id
        ).order_by(Group.period_number.desc()).limit(limit).all()
    
    @staticmethod
    def lock_collection(
        db: Session,
        group: Group,
        user_id: int
    ) -> Group:
        """鎖定集資"""
        if group.status != GroupStatus.COLLECTING:
            raise ValueError("只能鎖定集資中的單期團")
        
        group.status = GroupStatus.LOCKED
        group.locked_at = datetime.now(timezone.utc)
        
        # 建立每位成員的貢獻記錄
        members = db.query(GroupMember).filter(
            GroupMember.series_id == group.series_id,
            GroupMember.status == MemberStatus.ACTIVE
        ).all()
        
        for member in members:
            contribution = PeriodContribution(
                group_id=group.id,
                member_id=member.id,
                pool_share_at_lock=member.pool_share
            )
            db.add(contribution)
        
        # 記錄事件
        event = EventLog(
            event_type="group_locked",
            category=EventCategory.GROUP,
            actor_id=user_id,
            actor_type=ActorType.USER,
            target_type="group",
            target_id=group.id,
            series_id=group.series_id,
            group_id=group.id,
            event_data={"total_pool": float(group.total_pool)}
        )
        db.add(event)
        
        db.commit()
        db.refresh(group)
        return group
    
    @staticmethod
    def record_purchase(
        db: Session,
        group: Group,
        total_spent: Decimal,
        total_tickets: int,
        user_id: int
    ) -> Group:
        """記錄購買"""
        if group.status != GroupStatus.LOCKED:
            raise ValueError("只能在鎖定後記錄購買")
        
        group.status = GroupStatus.PURCHASED
        group.purchased_at = datetime.now(timezone.utc)
        group.total_spent = total_spent
        group.total_tickets = total_tickets
        group.total_carryover = group.total_pool - total_spent
        
        # 記錄事件
        event = EventLog(
            event_type="group_purchased",
            category=EventCategory.GROUP,
            actor_id=user_id,
            actor_type=ActorType.USER,
            target_type="group",
            target_id=group.id,
            series_id=group.series_id,
            group_id=group.id,
            event_data={
                "total_spent": float(total_spent),
                "total_tickets": total_tickets,
                "total_carryover": float(group.total_carryover)
            }
        )
        db.add(event)
        
        db.commit()
        db.refresh(group)
        return group
    
    @staticmethod
    def input_draw_result(
        db: Session,
        group: Group,
        data: DrawResultInput,
        user_id: int
    ) -> Group:
        """輸入開獎結果"""
        if group.status != GroupStatus.PURCHASED:
            raise ValueError("只能在已購買後輸入開獎結果")
        
        group.winning_numbers = data.winning_numbers
        group.status = GroupStatus.DRAWN
        group.drawn_at = datetime.now(timezone.utc)
        
        # 記錄事件
        event = EventLog(
            event_type="group_drawn",
            category=EventCategory.GROUP,
            actor_id=user_id,
            actor_type=ActorType.USER,
            target_type="group",
            target_id=group.id,
            series_id=group.series_id,
            group_id=group.id,
            event_data={"winning_numbers": data.winning_numbers}
        )
        db.add(event)
        
        db.commit()
        db.refresh(group)
        return group


class TicketService:
    """彩券服務"""
    
    @staticmethod
    def create(
        db: Session,
        group: Group,
        numbers: Optional[List[dict]],
        bet_count: int,
        cost: Decimal
    ) -> Ticket:
        """建立彩券"""
        # 計算票券序號
        ticket_count = db.query(Ticket).filter(Ticket.group_id == group.id).count()
        
        ticket = Ticket(
            group_id=group.id,
            ticket_index=ticket_count + 1,
            numbers=numbers,
            bet_count=bet_count,
            cost=cost
        )
        db.add(ticket)
        db.commit()
        db.refresh(ticket)
        return ticket
    
    @staticmethod
    def get_group_tickets(db: Session, group_id: int) -> List[Ticket]:
        """取得單期團的所有彩券"""
        return db.query(Ticket).filter(
            Ticket.group_id == group_id
        ).order_by(Ticket.ticket_index).all()
    
    @staticmethod
    def update(
        db: Session,
        ticket: Ticket,
        numbers: Optional[List[dict]] = None,
        image_url: Optional[str] = None
    ) -> Ticket:
        """更新彩券"""
        if numbers is not None:
            ticket.numbers = numbers
        if image_url is not None:
            ticket.image_url = image_url
        
        db.commit()
        db.refresh(ticket)
        return ticket


class PrizeChecker:
    """對獎服務"""
    
    @staticmethod
    def check_power(
        bet_numbers: dict,
        winning_numbers: dict
    ) -> Optional[Dict[str, Any]]:
        """
        威力彩對獎
        bet_numbers: {"first_zone": [1,5,12,23,31,38], "second_zone": 2}
        winning_numbers: {"first_zone": [1,5,12,23,31,38], "second_zone": 2}
        """
        first_match = len(set(bet_numbers["first_zone"]) & set(winning_numbers["first_zone"]))
        second_match = bet_numbers["second_zone"] == winning_numbers["second_zone"]
        
        # 對獎表
        prize_table = [
            (6, True, "頭獎", 0),      # 頭獎為累積獎金
            (6, False, "貳獎", 150000),
            (5, True, "參獎", 20000),
            (5, False, "肆獎", 4000),
            (4, True, "伍獎", 800),
            (4, False, "陸獎", 400),
            (3, True, "柒獎", 200),
            (2, True, "捌獎", 100),
            (1, True, "普獎", 100),
        ]
        
        for first_req, second_req, level, prize in prize_table:
            if first_match == first_req and second_match == second_req:
                return {"level": level, "prize": prize, "is_jackpot": prize == 0}
        
        return None
    
    @staticmethod
    def check_super(
        bet_numbers: dict,
        winning_numbers: dict
    ) -> Optional[Dict[str, Any]]:
        """
        大樂透對獎
        bet_numbers: {"main": [3,8,15,22,28,35]}
        winning_numbers: {"main": [3,8,15,22,28,35], "special": 42}
        """
        main_match = len(set(bet_numbers["main"]) & set(winning_numbers["main"]))
        special_match = winning_numbers["special"] in bet_numbers["main"]
        
        # 對獎表
        prize_table = [
            (6, False, "頭獎", 0),      # 頭獎為累積獎金
            (5, True, "貳獎", 150000),
            (5, False, "參獎", 25000),
            (4, True, "肆獎", 12500),
            (4, False, "伍獎", 2000),
            (3, True, "陸獎", 1000),
            (2, True, "柒獎", 400),
            (3, False, "普獎", 400),
        ]
        
        for main_req, special_req, level, prize in prize_table:
            if main_match == main_req and special_match == special_req:
                return {"level": level, "prize": prize, "is_jackpot": prize == 0}
        
        return None
    
    @staticmethod
    def check_daily539(
        bet_numbers: dict,
        winning_numbers: dict
    ) -> Optional[Dict[str, Any]]:
        """
        今彩539對獎
        bet_numbers: {"main": [1,5,12,23,31]}
        winning_numbers: {"main": [1,5,12,23,31]}
        """
        match_count = len(set(bet_numbers["main"]) & set(winning_numbers["main"]))
        
        prize_table = [
            (5, "頭獎", 8000000),
            (4, "貳獎", 20000),
            (3, "參獎", 300),
            (2, "肆獎", 50),
        ]
        
        for req, level, prize in prize_table:
            if match_count == req:
                return {"level": level, "prize": prize, "is_jackpot": False}
        
        return None
    
    @classmethod
    def check_ticket(
        cls,
        db: Session,
        ticket: Ticket,
        winning_numbers: dict
    ) -> Ticket:
        """對獎單張彩券"""
        if not ticket.numbers:
            return ticket
        
        # 取得彩種
        group = ticket.group
        lottery_type = group.lottery_type
        
        # 選擇對獎方法
        checker_map = {
            "power": cls.check_power,
            "super": cls.check_super,
            "daily539": cls.check_daily539,
        }
        
        checker = checker_map.get(lottery_type.code)
        if not checker:
            raise ValueError(f"不支援的彩種: {lottery_type.code}")
        
        # 對獎每一注
        prize_results = []
        total_prize = Decimal("0")
        
        for idx, bet in enumerate(ticket.numbers):
            result = checker(bet, winning_numbers)
            if result:
                prize_results.append({
                    "bet_index": idx,
                    "level": result["level"],
                    "prize": result["prize"],
                    "is_jackpot": result.get("is_jackpot", False)
                })
                total_prize += Decimal(str(result["prize"]))
        
        # 更新彩券
        ticket.is_checked = True
        ticket.checked_at = datetime.now(timezone.utc)
        ticket.prize_results = prize_results if prize_results else None
        ticket.prize_amount = total_prize
        
        db.commit()
        db.refresh(ticket)
        return ticket
    
    @classmethod
    def check_all_tickets(
        cls,
        db: Session,
        group: Group
    ) -> Decimal:
        """對獎所有彩券"""
        if not group.winning_numbers:
            raise ValueError("尚未輸入開獎號碼")
        
        tickets = db.query(Ticket).filter(Ticket.group_id == group.id).all()
        total_prize = Decimal("0")
        
        for ticket in tickets:
            cls.check_ticket(db, ticket, group.winning_numbers)
            total_prize += ticket.prize_amount
        
        # 更新單期團總獎金
        group.total_prize = total_prize
        
        # 計算扣稅後金額(超過5000扣20%)
        if total_prize > 5000:
            group.total_prize_after_tax = total_prize * Decimal("0.8")
        else:
            group.total_prize_after_tax = total_prize
        
        db.commit()
        return total_prize


# 全域實例
group_service = GroupService()
ticket_service = TicketService()
prize_checker = PrizeChecker()
