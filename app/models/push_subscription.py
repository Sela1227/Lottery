"""
SELA 樂透一路發 - Push 訂閱模型
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base


class PushSubscription(Base):
    """推播訂閱資料表"""
    __tablename__ = "push_subscriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # 訂閱資訊
    endpoint = Column(Text, nullable=False, unique=True)
    p256dh_key = Column(String(255), nullable=False)
    auth_key = Column(String(255), nullable=False)
    
    # 裝置資訊
    user_agent = Column(String(500), nullable=True)
    device_name = Column(String(100), nullable=True)
    
    # 狀態
    is_active = Column(Boolean, default=True, nullable=False)
    
    # 時間戳記
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_used_at = Column(DateTime, nullable=True)
    
    # 關聯
    user = relationship("User", backref="push_subscriptions")
    
    @property
    def subscription_info(self) -> dict:
        """轉換為 webpush 格式"""
        return {
            "endpoint": self.endpoint,
            "keys": {
                "p256dh": self.p256dh_key,
                "auth": self.auth_key
            }
        }
