# src/framework/ai/knowledge_simple/database.py
import logging
from sqlalchemy import Column, String, DateTime, Text, Integer, ForeignKey, text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from pgvector.sqlalchemy import Vector
import uuid
from datetime import datetime
from ....shared.database import engine, SessionLocal, Base, get_db

logger = logging.getLogger(__name__)


class KnowledgeDocument(Base):
    """知识库文档表"""

    __tablename__ = "knowledge_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(200), nullable=False)
    filename = Column(String(255), nullable=False)
    file_type = Column(String(20), nullable=False)  # txt, pdf, docx
    content = Column(Text, nullable=False)
    chunk_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # 关联分块
    chunks = relationship(
        "KnowledgeChunk", back_populates="document", cascade="all, delete-orphan"
    )


class KnowledgeChunk(Base):
    """知识库分块表（向量存储）"""

    __tablename__ = "knowledge_chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(
        UUID(as_uuid=True),
        ForeignKey("knowledge_documents.id", ondelete="CASCADE"),
        nullable=False,
    )
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    embedding = Column(Vector(1024))  # 向量
    created_at = Column(DateTime, default=datetime.now)

    # 关联文档
    document = relationship("KnowledgeDocument", back_populates="chunks")


def init_db():
    """初始化知识库表"""
    with engine.connect() as conn:
        # 创建 vector 扩展（如果不存在）
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        # 为知识库分块创建向量索引，加速检索
        conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_embedding ON knowledge_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists=100)"
            )
        )
        conn.commit()

        # 创建表
        Base.metadata.create_all(bind=engine)
        logger.info("✅ 知识库表创建成功")
