# src/shared/database.py
"""
共享数据库连接池

所有服务复用同一个 engine，避免连接池重复。
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from pathlib import Path
from dotenv import load_dotenv
import os

# ========== 加载 .env ==========
# src/shared/database.py → 上溯 3 层到项目根目录
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)


# ========== 数据库 URL ==========
DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/ai_companion"
)

# ========== 全局唯一 engine ==========
engine = create_engine(
    DATABASE_URL,
    pool_size=10,  # 连接池大小
    max_overflow=20,  # 超出 pool_size 时最多再创建 20 个
    pool_timeout=30,  # 等待连接的超时时间（秒）
    pool_recycle=3600,  # 连接回收时间（1 小时）
    pool_pre_ping=True,  # 使用前 ping 一下，避免死连接
    echo=False,  # 不打印 SQL
)


# ========== 全局唯一会话工厂 ==========
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


# ========== 全局唯一 Base ==========
Base = declarative_base()


# ========== FastAPI 依赖 ==========
def get_db():
    """FastAPI 依赖：获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
