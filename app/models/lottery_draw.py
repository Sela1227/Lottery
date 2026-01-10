"""
SELA 樂透一路發 - 開獎記錄模型
放在 models 目錄，應用啟動時會自動建表
"""
from sqlalchemy import Column, Integer, BigInteger, String, Date, DateTime, JSON, UniqueConstraint, Index
from sqlalchemy.sql import func

from app.core.database import Base


class LotteryDraw(Base):
    """開獎記錄"""
    __tablename__ = "lottery_draws"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 彩種 ('power', 'super', 'daily539')
    lottery_type = Column(String(20), nullable=False, index=True)
    
    # 期數 (例如 '114000001')
    draw_term = Column(String(20), nullable=False)
    
    # 開獎日期
    draw_date = Column(Date, nullable=False, index=True)
    
    # 開獎號碼 (JSON 格式)
    numbers = Column(JSON, nullable=False)
    
    # 頭獎金額
    jackpot = Column(BigInteger, nullable=True)
    
    # 時間戳記
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 唯一約束
    __table_args__ = (
        UniqueConstraint('lottery_type', 'draw_term', name='uq_lottery_draw_term'),
    )
    
    def __repr__(self):
        return f"<LotteryDraw {self.lottery_type} {self.draw_term}>"
    
    @property
    def lottery_name(self) -> str:
        """取得彩種中文名稱"""
        names = {
            'power': '威力彩',
            'super': '大樂透',
            'daily539': '今彩539'
        }
        return names.get(self.lottery_type, self.lottery_type)
