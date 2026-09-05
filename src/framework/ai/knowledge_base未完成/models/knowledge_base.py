# my-test-framework/src/framework/ai/knowledge-base/models/knowledge_base.py
from sqlalchemy import Column, String, DateTime, Boolean, JSON, Text, Integer, Float, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
import uuid
from datetime import datetime
from ..database import Base


class KnowledgeBase(Base):
    """知识库 - 企业级多租户"""
    __tablename__ = "kb_knowledge_bases"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    owner_id = Column(UUID(as_uuid=True), nullable=False, index=True)  # 🟢 关键：用户隔离
    team_id = Column(UUID(as_uuid=True), nullable=True, index=True)    # 🟢 关键：团队共享
    permission = Column(Enum('private', 'team', 'public', name='kb_permission'), default='private')
    category = Column(String(50))  # 分类：技术文档/产品手册/培训资料等
    tags = Column(JSON, default=[])  # 标签
    is_archived = Column(Boolean, default=False)
    document_count = Column(Integer, default=0)
    total_chunks = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


    # 关系
    owner = relationship("User", back_populates="knowledge_bases")
    team = relationship("Team", back_populates="knowledge_bases")
    documents = relationship("document", back_populates="knowledge_bases")

    def to_dict(self):
        return {
            'id': str(self.id),
            'name': self.name,
            'description': self.description,
            'owner_id': str(self.owner_id),
            'team_id': str(self.team_id) if self.team_id else None,
            'permission': self.permission,
            'category': self.category,
            'tags': self.tags,
            'is_archived': self.is_archived,
            'document_count': self.document_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class Document(Base):
    """文档模型"""
    __tablename__ = "kb_documents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    knowledge_base_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    file_name = Column(String(255), nullable=False)
    file_type = Column(String(20))  # txt, pdf, docx, etc.
    file_size = Column(Integer)  # bytes
    file_path = Column(String(500))  # 存储路径
    title = Column(String(200))
    author = Column(String(100))
    description = Column(Text)
    version = Column(String(20), default="1.0")
    status = Column(Enum('processing', 'ready', 'failed', name='doc_status'), default='processing')
    chunk_count = Column(Integer, default=0)
    uploader_id = Column(UUID(as_uuid=True), nullable=False)
    uploaded_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    metadata = Column(JSON, default={})

    # 关系
    knowledge_base = relationship("KnowledgeBase", back_populates="documents")
    uploader = relationship("User", back_populates="documents")
    chucks = relationship("DocumentChunk", back_populates="documents")

    def to_dict(self):
        return {
            'id': str(self.id),
            'knowledge_base_id': str(self.knowledge_base_id),
            'file_name': self.file_name,
            'file_type': self.file_type,
            'file_size': self.file_size,
            'title': self.title,
            'author': self.author,
            'description': self.description,
            'version': self.version,
            'status': self.status,
            'chunk_count': self.chunk_count,
            'uploader_id': str(self.uploader_id),
            'uploaded_at': self.uploaded_at.isoformat() if self.uploaded_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class DocumentChunk(Base):
    """文档块 - 向量存储"""
    __tablename__ = "kb_document_chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    knowledge_base_id = Column(UUID(as_uuid=True), nullable=False, index=True)  # 🟢 加速检索
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    content_length = Column(Integer)
    embedding = Column(Vector(1536))  # 使用1536维度（OpenAI embedding）
    embedding_model = Column(String(50))  # 记录使用的模型
    metadata = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.now)

    # 关系
    document = relationship("Document", back_populates="chunks")

    def to_dict(self):
        return {
            'id': str(self.id),
            'document_id': str(self.document_id),
            'knowledge_base_id': str(self.knowledge_base_id),
            'chunk_index': self.chunk_index,
            'content': self.content[:200] + '...' if self.content > 200 else self.content,
            'content_length': self.content_length,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }