# my-test-framework/src/framework/ai/aicompanion_v2/database.py

from sqlalchemy import create_engine, Column, String, Integer, DateTime, Text, JSON, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.dialects.postgresql import UUID
from pgvector.sqlalchemy import Vector
import uuid
from datetime import datetime
import os
from dotenv import load_dotenv
from sqlalchemy import text
load_dotenv()

Base = declarative_base()

class SessionModel(Base):
    __tablename__ = "ai_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_name = Column(String(50), unique=True, nullable=False)
    nick_name = Column(String(50), default="小甜甜")
    nature = Column(Text, default="活泼开朗的台湾姑娘")
    extra_rules = Column(Text, default="")  # 新增：存储额外规则
    system_str = Column(Text)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    messages = Column(JSON, default=[])  # 存储消息历史
    # 用于向量检索的消息向量（可选）
    messages_embedding = Column(Vector(1536)) # OpenAI embedding维度

class MessageModel(Base):
    __tablename__ = "ai_messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), nullable=False)
    role = Column(String(20), nullable=False)  # user, assistant
    content = Column(Text, nullable=False)
    embedding = Column(Vector(1536))  # 消息向量
    created_at = Column(DateTime, default=datetime.now)


DATABASE_URL = os.environ.get("DATABASE_URL","postgresql://postgres:postgres@localhost:5432/ai_companion")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine) 

def init_db():
    """初始化数据库，创建表和pgvector扩展"""
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()
        Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()