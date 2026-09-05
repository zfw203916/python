# my-test-framework/src/framework/ai/knowledge-base/services/search_service.py
# 搜索服务（混合检索）

from sqlalchemy.orm import Session
from sqlalchemy import text, and_, or_
from typing import List, Dict, Any, Optional
import uuid
from loguru import logger
from .embedding_service import EmbeddingService
from ..models.document import DocumentChunk, Document, KnowledgeBase
from ..core.cache import CacheService

class SearchService:
    """企业级搜索服务 - 混合检索"""
    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.cache = CacheService()

    def hybrid_search(
        self,
        db: Session,
        query: str,
        knowledge_base_id: Optional[str] = None,
        user_id: Optional[str] = None,
        team_id: Optional[str] = None,
        limit: int = 10,
        threshold: float = 0.5,
        use_cache: bool = True) -> List[Dict[str, Any]]:
        """
        混合搜索：向量相似度 + 关键词匹配
        企业级特性：
        - 多租户隔离
        - 缓存加速
        - 权重调整
        """
        # 1. 检查缓存
        cache_key = f"search:{query}:{knowledge_base_id}:{limit}"
        if use_cache:
            cached = self.cache.get(cache_key)
            if cached:
                logger.inof(f"📦 命中缓存: {cache_key}")
                return cached


        # 2. 获取查询向量
        query_embedding = self.embedding_service(query)
        if not query_embedding:
            return []

        # 3. 构建权限过滤
        filter_conditions = self._build_permission_filter(user_id, team_id, knowledge_base_id)

        # 4. 向量搜索
        vector_results = self._vector_search(db, query_embedding, filter_conditions, limit * 2, threshold)

        # 5. 关键词搜索（全文检索）
        keyword_results = self._keyword_search(
            db, query, filter_conditions, limit * 2
        )

        # 6. 融合结果（RRF - Reciprocal Rank Fusion）
        merged_results = self._merge_results(vector_results, keyword_results, limit)

        # 7. 缓存结果
        if use_cache and merged_results:
            self.set(cache_key, merged_results, ttl = 300)  # 5分钟缓存

        logger.info(f"🔍 搜索完成: query='{query}', results={len(merged_results)}")
        return merged_results
    
    def _build_permission_filter(self, user_id, team_id, kb_id):
        """构建权限过滤条件"""
        conditions = []

        #企业级权限控制
        if user_id:
            # 用户自己的知识库
            conditions.append("(kb.permission = 'private' and kb.owner_id = :user_id)")
        if user_id and team_id:
            # 团队知识库
            conditions.append("""kb.permission = 'team' AND kb.team_id = :team_id""") 

        if user_id:
            # 公开知识库（只读）
            conditions.append("(kb.permission = 'public')")

        if kb_id:
            conditions.append("(kb.id = :kb_id)")

        return 'AND'.join(conditions) if conditions else "1=1"
            


    def _vector_search(self, db, query_embedding, filter_conditions, limit, threshold):
        """向量相似度搜索"""
        sql = text(f"""
            SELECT 
            dc.id,
            dc.document_id,
            dc.content,
            dc.chunk_index,
            d.file_name,
            d.title,
            kb.name as kb_name,
            kb.id as kb_id,
            1 - (dc.embedding <=> cast(:query_embedding as vector)) as similarity
            FROM kb_document_chunks dc
            JOIN kb_documents d ON dc.document_id = d.id
            JOIN kb_knowledge_bases kb ON d.knowledge_base_id = kb.id
            WHERE dc.embedding IS NOT NULL
                AND ({filter_conditions})
                AND 1 - (dc.embedding <=> cast(:query_embedding as vector)) >= :threshold
            ORDER BY dc.embedding <=> cast(:query_embedding as vector)
            LIMIT :limit
        """)

