"""
SELA 樂透一路發 - 資料庫連線管理
"""
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager

from app.config import settings


# 建立資料庫引擎
engine = create_engine(
    settings.database_url,
    poolclass=QueuePool,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,  # 自動檢查連線是否有效
    echo=not settings.is_production  # 開發模式顯示 SQL
)

# Session 工廠
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# 宣告基底類別
Base = declarative_base()


def get_db():
    """取得資料庫 Session(FastAPI 依賴注入用)"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_session():
    """取得資料庫 Session(Context Manager)"""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def check_database_connection() -> bool:
    """檢查資料庫連線"""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        print(f"資料庫連線失敗: {e}")
        return False


def init_database():
    """初始化資料庫(建立所有表)"""
    Base.metadata.create_all(bind=engine)
