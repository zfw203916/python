# src/framework/ai/knowledge_simple/database.py
from sqlalchemy import create_engine, Column, String, DateTime, Text, Integer, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.dialects.postgresql import UUID
from pgvector.sqlalchemy import Vector
import uuid
from datetime import datetime
import os
from dotenv import load_dotenv
from pathlib import Path


env_path = Path(__file__).parent.parent.parent.parent / ".env"

Base = declarative_base()

class KnowledgeDocument(Base):
    """知识库文档表"""
    __tablename__ = "knowledge_documents"

    id = Column(UUID(as_uuid=True),primary_key=True, default=uuid.uuid4)
    title = Column(String(200), nullable=False)
    filename = Column(String(255), nullable=False)
    file_type = Column(String(20), nullable=False)  # txt, pdf, docx
    content = Column(Text, nullable=False)
    chunk_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # 关联分块
    chunks = relationship("KnowledgeChunk",back_populates = "document", cascade="all, delete-orphan")

class KnowledgeChunk(Base):
    """知识库分块表（向量存储）"""
    __tablename__ = "knowledge_chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("knowledge_documents.id", ondelete="CASCADE"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    embedding = Column(Vector(1024))  # 向量
    created_at = Column(DateTime, default=datetime.now)

    # 关联文档
    document = relationship("KnowledgeDocument", back_populates="chunks")


# 使用同一个数据库 - ai_companion
DATABASE_URL = os.environ.get("DATABASE_URL","postgresql://postgres:postgres@localhost:5432/ai_companion")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """初始化知识库表"""
    with engine.connect() as conn:
        from sqlalchemy import text
        # 创建 vector 扩展（如果不存在）
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        # 为知识库分块创建向量索引，加速检索
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_embedding ON knowledge_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists=100)"))
        conn.commit()

        # 创建表
        Base.metadata.create_all(bind=engine)
        print("✅ 知识库表创建成功")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()