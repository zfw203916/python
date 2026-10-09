# src/framework/ai/knowledge_simple/services/qdrant_service.py
"""
    Qdrant 向量数据库服务封装

    职责：
    - 管理 collection 生命周期（创建、删除、检查）
    - 写入/删除/搜索向量
    - 封装 payload 结构
"""
import os
import uuid
from typing import List, Dict, Optional, Tuple
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
    PayloadSchemaType,
)
import logging
logger = logging.getLogger(__name__)

# ========== 配置 ==========
QDRANT_URL = os.environ.get("QDRANT_URL","http://qdrant:6333")
QDRANT_API_KEY = os.environ.get("QDRANT_API_KEY")
COLLECTION = "knowledge_chunks"
VECTOR_SIZE = 1024 # 和 EmbeddingService 输出维度一致
DISTANCE = Distance.COSINE # 余弦相似度

class QdrantService:
    """Qdrant 向量库封装"""
    _client: Optional[QdrantClient] = None
    def __init__(self):
        # 1. 先确保类属性有 client（单例）
        if QdrantService._client is None:
            QdrantService._client = QdrantClient(url=QDRANT_URL, timeout=30,api_key=QDRANT_API_KEY)
            logger.info(f"✅ Qdrant 客户端初始化: {QDRANT_URL}")
        # 2. 再赋值给实例属性
        self.client = QdrantService._client
        # 3. 最后才调用 _ensure_collection（此时 self.client 已有值）
        self._ensure_collection()

    def _ensure_collection(self):
        """没有就建，有就跳过"""
        existing = [c.name for c in self.client.get_collections().collections]
        if COLLECTION in existing:
            return 
        self.client.create_collection(
            collection_name = COLLECTION,
            vectors_config = VectorParams(size=VECTOR_SIZE,distance=Distance.COSINE),
        )
        self.client.create_payload_index(
            collection_name = COLLECTION,
            field_name = "document_id",
            field_schema = PayloadSchemaType.KEYWORD
        )
        logging.info(f"✅ 创建 Qdrant collection:{COLLECTION}")

    def upsert_chunks(self, points: List[dict]) -> int:
        """批量写向量。points: [{chunk_id, vector, payload}]"""
        if not points:
            return 0
        structs = [
            PointStruct(
                id = p["chunk_id"],
                vector = p["vector"],
                payload = p["payload"],
            ) for p in points  if p.get("vector")
        ]
        if not structs:
            return 0
        self.client.upsert(collection_name=COLLECTION, points=structs, wait=True)
        return len(structs)

    def search(
        self,
        query_vector: List[float],
        top_k: int = 5,
        threshold: float = 0.5,
        document_id: Optional[str] = None,  
    ) -> list[Dict]:
        """向量搜索，返回 [{chunk_id, score, document_id, content, ...}]"""
        query_filter = None
        if document_id:
           query_filter = Filter(
               must=[FieldCondition(key="document_id", match=MatchValue(value=document_id))]
           ) 
        hits = self.client.search(
            collection_name = COLLECTION,
            query_vector = query_vector,
            limit = top_k * 2,
            query_filter = query_filter,
            with_payload = True,
        )
        results = []
        for h in hits:
            if h.score < threshold:
                continue
            results.append({
                "chunk_id": str(h.id),
                "score": float(h.score),
                "document_id": h.payload.get("document_id"),
                "document_title": h.payload.get("document_title", ""),
                "content": h.payload.get("content", ""),
            })
        return results[:top_k]

    def delete_by_document(self, document_id: str):
        """删某文档所有向量"""
        self.client.delete(
            collection_name = COLLECTION,
            points_selector = Filter(must=[FieldCondition(key="document_id", match=MatchValue(value=document_id))]),
            wait = True,
        )

    def get_stats(self) -> Dict:
        info = self.client.get_collection(COLLECTION)
        return {"points": info.points_count, "status": str(info.status)}

    
