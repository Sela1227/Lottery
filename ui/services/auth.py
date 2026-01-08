"""
SELA 樂透一路發 - 認證狀態管理
"""
from typing import Optional, Callable
from dataclasses import dataclass, field
import json


@dataclass
class User:
    """用戶資料"""
    id: int
    line_user_id: str
    display_name: str
    picture_url: Optional[str] = None
    nickname: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    role: str = "user"
    wallet_balance: float = 0.0
    
    @classmethod
    def from_dict(cls, data: dict) -> "User":
        """從字典建立"""
        return cls(
            id=data.get("id", 0),
            line_user_id=data.get("line_user_id", ""),
            display_name=data.get("display_name", ""),
            picture_url=data.get("picture_url"),
            nickname=data.get("nickname"),
            email=data.get("email"),
            phone=data.get("phone"),
            role=data.get("role", "user"),
            wallet_balance=float(data.get("wallet_balance", 0)),
        )
    
    @property
    def display(self) -> str:
        """顯示名稱（優先使用暱稱）"""
        return self.nickname or self.display_name
    
    @property
    def is_admin(self) -> bool:
        """是否為管理員"""
        return self.role == "admin"


@dataclass
class AuthState:
    """認證狀態"""
    is_authenticated: bool = False
    user: Optional[User] = None
    token: Optional[str] = None
    _listeners: list = field(default_factory=list)
    
    def add_listener(self, callback: Callable):
        """新增狀態變更監聽器"""
        self._listeners.append(callback)
    
    def remove_listener(self, callback: Callable):
        """移除狀態變更監聽器"""
        if callback in self._listeners:
            self._listeners.remove(callback)
    
    def _notify_listeners(self):
        """通知所有監聽器"""
        for callback in self._listeners:
            try:
                callback(self)
            except Exception as e:
                print(f"監聽器錯誤: {e}")
    
    def login(self, token: str, user_data: dict):
        """登入"""
        self.token = token
        self.user = User.from_dict(user_data)
        self.is_authenticated = True
        self._notify_listeners()
    
    def logout(self):
        """登出"""
        self.token = None
        self.user = None
        self.is_authenticated = False
        self._notify_listeners()
    
    def update_user(self, user_data: dict):
        """更新用戶資料"""
        if self.user:
            self.user = User.from_dict(user_data)
            self._notify_listeners()
    
    def to_storage_dict(self) -> dict:
        """轉換為可儲存的字典"""
        return {
            "token": self.token,
            "user": {
                "id": self.user.id,
                "line_user_id": self.user.line_user_id,
                "display_name": self.user.display_name,
                "picture_url": self.user.picture_url,
                "nickname": self.user.nickname,
                "email": self.user.email,
                "phone": self.user.phone,
                "role": self.user.role,
                "wallet_balance": self.user.wallet_balance,
            } if self.user else None,
        }
    
    def from_storage_dict(self, data: dict):
        """從儲存的字典還原"""
        if data.get("token") and data.get("user"):
            self.token = data["token"]
            self.user = User.from_dict(data["user"])
            self.is_authenticated = True
        else:
            self.logout()


class AuthManager:
    """認證管理器"""
    
    STORAGE_KEY = "sela_auth"
    
    def __init__(self):
        self.state = AuthState()
    
    def save_to_storage(self, page) -> bool:
        """儲存到 client storage"""
        try:
            data = json.dumps(self.state.to_storage_dict())
            page.client_storage.set(self.STORAGE_KEY, data)
            return True
        except Exception as e:
            print(f"儲存認證狀態失敗: {e}")
            return False
    
    def load_from_storage(self, page) -> bool:
        """從 client storage 載入"""
        try:
            data = page.client_storage.get(self.STORAGE_KEY)
            if data:
                self.state.from_storage_dict(json.loads(data))
                return self.state.is_authenticated
        except Exception as e:
            print(f"載入認證狀態失敗: {e}")
        return False
    
    def clear_storage(self, page):
        """清除 client storage"""
        try:
            page.client_storage.remove(self.STORAGE_KEY)
        except Exception:
            pass
    
    def login(self, token: str, user_data: dict, page=None):
        """登入"""
        self.state.login(token, user_data)
        if page:
            self.save_to_storage(page)
    
    def logout(self, page=None):
        """登出"""
        self.state.logout()
        if page:
            self.clear_storage(page)
    
    @property
    def is_authenticated(self) -> bool:
        return self.state.is_authenticated
    
    @property
    def user(self) -> Optional[User]:
        return self.state.user
    
    @property
    def token(self) -> Optional[str]:
        return self.state.token


# 全域認證管理器
auth_manager = AuthManager()
