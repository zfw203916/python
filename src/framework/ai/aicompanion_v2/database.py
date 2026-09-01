# my-test-framework/src/framework/ai/aicompanion_v2/database.py

from sqlalchemy import create_engine, Column, String, DateTime, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import UUID
from pgvector.sqlalchemy import Vector
import uuid
from datetime import datetime
import os
from dotenv import load_dotenv
from sqlalchemy import text
from pathlib import Path
from sqlalchemy import Boolean

# 指定 .env 文件路径（项目根目录）
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

Base = declarative_base()


class SessionModel(Base):
    __tablename__ = "ai_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_name = Column(String(50), nullable=False)
    nick_name = Column(String(50), default="小甜甜")
    nature = Column(Text, default="活泼开朗的台湾姑娘")
    extra_rules = Column(Text, default="")  # 新增：存储额外规则
    system_str = Column(Text)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    messages = Column(JSON, default=[])  # 存储消息历史
    # 用于向量检索的消息向量（可选）
    messages_embedding = Column(Vector(1024))  # OpenAI embedding维度
    is_pinned = Column(Boolean, default=False)

class MessageModel(Base):
    __tablename__ = "ai_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), nullable=False)
    role = Column(String(20), nullable=False)  # user, assistant
    content = Column(Text, nullable=False)
    embedding = Column(Vector(1024))  # 消息向量
    created_at = Column(DateTime, default=datetime.now)


DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/ai_companion"
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """初始化数据库，创建表和pgvector扩展"""
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))

        # 新增：创建向量索引加速检索,直接sql
        conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS idx_ai_messages_embedding ON ai_messages USING ivfflat (embedding vector_cosine_ops) WITH (lists=100)"
            )
        )
        conn.commit()
        Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
