# src/framework/ai/knowledge_simple/models.py
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class DocumentUpload(BaseModel):
    """文档上传请求"""
    title: Optional[str] = None


class DocumentResponse(BaseModel):
    """文档响应"""
    id: str
    title: str
    filename: str
    file_type: str
    chunk_count: int
    created_at: datetime


class ChunkResponse(BaseModel):
    """分块响应"""
    content: str
    chunk_index: int
    similarity: Optional[float] = None


class SearchRequest(BaseModel):
    """搜索请求"""
    query: str
    top_k: int = 5


class SearchResult(BaseModel):
    """搜索结果"""
    document_id: str
    document_title: str
    chunks: List[ChunkResponse]


class SimpleSearchResponse(BaseModel):
    """简单搜索结果"""
    content: str
    similarity: float
    document_id: str
    document_title: Optional[str] = None