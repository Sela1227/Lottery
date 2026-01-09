"""
SELA 樂透一路發 - 應用程式設定
"""
from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """應用程式設定"""
    
    # 應用程式
    app_env: str = Field(default="development")
    app_name: str = Field(default="SELA樂透一路發")
    app_url: str = Field(default="http://localhost:8000")
    port: int = Field(default=8000)
    
    # 資料庫
    database_url: str = Field(default="postgresql://user:password@localhost:5432/lottery_group")
    
    # JWT
    jwt_secret: str = Field(default="your-super-secret-key-at-least-32-characters-long")
    jwt_algorithm: str = Field(default="HS256")
    jwt_expires_in: str = Field(default="7d")
    
    # LINE Login
    line_channel_id: str = Field(default="")
    line_channel_secret: str = Field(default="")
    line_callback_url: str = Field(default="http://localhost:8000/auth/line/callback")
    
    # Cloudinary
    cloudinary_cloud_name: str = Field(default="")
    cloudinary_api_key: str = Field(default="")
    cloudinary_api_secret: str = Field(default="")
    
    # LINE Notify (Step 4)
    line_notify_client_id: str = Field(default="")
    line_notify_client_secret: str = Field(default="")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    @property
    def is_production(self) -> bool:
        return self.app_env == "production"
    
    @property
    def jwt_expires_seconds(self) -> int:
        """將 JWT 過期時間轉換為秒數"""
        expires = self.jwt_expires_in
        if expires.endswith("d"):
            return int(expires[:-1]) * 86400
        elif expires.endswith("h"):
            return int(expires[:-1]) * 3600
        elif expires.endswith("m"):
            return int(expires[:-1]) * 60
        return int(expires)


@lru_cache
def get_settings() -> Settings:
    """取得設定(快取)"""
    return Settings()


# 全域設定實例
settings = get_settings()
