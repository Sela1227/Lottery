"""
SELA 樂透一路發 - 用戶服務
"""
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


class UserService:
    """用戶服務"""
    
    @staticmethod
    def get_by_id(db: Session, user_id: int) -> Optional[User]:
        """依 ID 取得用戶"""
        return db.query(User).filter(User.id == user_id).first()
    
    @staticmethod
    def get_by_line_id(db: Session, line_user_id: str) -> Optional[User]:
        """依 LINE User ID 取得用戶"""
        return db.query(User).filter(User.line_user_id == line_user_id).first()
    
    @staticmethod
    def create(db: Session, data: UserCreate) -> User:
        """建立新用戶"""
        user = User(
            line_user_id=data.line_user_id,
            display_name=data.display_name,
            picture_url=data.picture_url,
            last_login_at=datetime.now(timezone.utc)
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    
    @staticmethod
    def update(db: Session, user: User, data: UserUpdate) -> User:
        """更新用戶資料"""
        update_data = data.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(user, field, value)
        
        db.commit()
        db.refresh(user)
        return user
    
    @staticmethod
    def update_login(db: Session, user: User, display_name: str, picture_url: Optional[str]) -> User:
        """更新登入資訊(每次 LINE Login 時)"""
        user.display_name = display_name
        user.picture_url = picture_url
        user.last_login_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(user)
        return user
    
    @classmethod
    def get_or_create_from_line(
        cls,
        db: Session,
        line_user_id: str,
        display_name: str,
        picture_url: Optional[str] = None
    ) -> tuple[User, bool]:
        """
        從 LINE 資料取得或建立用戶
        
        Returns:
            (User, is_new) - 用戶物件與是否為新用戶
        """
        user = cls.get_by_line_id(db, line_user_id)
        
        if user:
            # 更新登入資訊
            cls.update_login(db, user, display_name, picture_url)
            return user, False
        else:
            # 建立新用戶
            user = cls.create(db, UserCreate(
                line_user_id=line_user_id,
                display_name=display_name,
                picture_url=picture_url
            ))
            return user, True


# 全域實例
user_service = UserService()
