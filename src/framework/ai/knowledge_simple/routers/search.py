# src/framework/ai/knowledge_simple/routers/search.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from ..database import get_db, KnowledgeDocument
from ..models import SearchRequest, SearchResult, ChunkResponse, SimpleSearchResponse
from ..services.document_service import DocumentService

router = APIRouter(prefix="/api/knowledge/search", tags=["knowledge-search"])
document_service = DocumentService()


@router.post("/", response_model=List[SearchResult])
async def search_knowledge(
    request: SearchRequest,
    db: Session = Depends(get_db)
):
    """搜索知识库（完整版，按文档分组）"""
    if not request.query or not request.query.strip():
        return []
    
    results = document_service.search_similar(
        db, 
        request.query.strip(), 
        top_k=request.top_k
    )
    
    if not results:
        return []
    
    # 按文档分组
    doc_chunks = {}
    for chunk, similarity in results:
        doc_id = str(chunk.document_id)
        if doc_id not in doc_chunks:
            doc = db.query(KnowledgeDocument).filter(
                KnowledgeDocument.id == chunk.document_id
            ).first()
            doc_chunks[doc_id] = {
                "document_id": doc_id,
                "document_title": doc.title if doc else "未知文档",
                "chunks": []
            }
        
        doc_chunks[doc_id]["chunks"].append(
            ChunkResponse(
                content=chunk.content,
                chunk_index=chunk.chunk_index,
                similarity=similarity
            )
        )
    
    # 按最高相似度排序
    sorted_results = sorted(
        doc_chunks.values(),
        key=lambda x: max([c.similarity or 0 for c in x["chunks"]]),
        reverse=True
    )
    
    return [
        SearchResult(
            document_id=v["document_id"],
            document_title=v["document_title"],
            chunks=v["chunks"][:3]  # 每个文档最多返回3块
        )
        for v in sorted_results
    ]


@router.post("/simple", response_model=dict)
async def search_simple(
    request: SearchRequest,
    db: Session = Depends(get_db)
):
    """简单搜索 - 返回文本列表（更简洁的格式）"""
    if not request.query or not request.query.strip():
        return {"results": [], "query": request.query}
    
    results = document_service.search_similar(
        db, 
        request.query.strip(), 
        top_k=request.top_k
    )
    
    if not results:
        return {"results": [], "query": request.query}
    
    # 获取文档标题
    doc_titles = {}
    for chunk, _ in results:
        doc_id = str(chunk.document_id)
        if doc_id not in doc_titles:
            doc = db.query(KnowledgeDocument).filter(
                KnowledgeDocument.id == chunk.document_id
            ).first()
            doc_titles[doc_id] = doc.title if doc else "未知文档"
    
    return {
        "query": request.query,
        "results": [
            {
                "content": chunk.content,
                "similarity": round(similarity, 4) if similarity else 0,
                "document_id": str(chunk.document_id),
                "document_title": doc_titles.get(str(chunk.document_id), "未知文档"),
                "chunk_index": chunk.chunk_index
            }
            for chunk, similarity in results
        ]
    }


@router.get("/stats")
async def get_stats(db: Session = Depends(get_db)):
    """获取知识库统计信息"""
    doc_count = db.query(KnowledgeDocument).count()
    chunk_count = db.query(KnowledgeChunk).count()
    
    # 检查是否有向量
    from sqlalchemy import text
    has_vector = False
    try:
        result = db.execute(text("SELECT COUNT(*) FROM knowledge_chunks WHERE embedding IS NOT NULL LIMIT 1"))
        has_vector_count = result.scalar() > 0
        has_vector = has_vector_count
    except:
        pass
    
    return {
        "document_count": doc_count,
        "chunk_count": chunk_count,
        "has_vector": has_vector,
        "embedding_enabled": document_service.use_embedding
    }