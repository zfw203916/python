# src/framework/ai/knowledge_simple/services/document_service.py
import os
import uuid
import re
from typing import List, Tuple, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from ..database import KnowledgeDocument, KnowledgeChunk
from .embedding_service import EmbeddingService


class DocumentService:
    """文档处理服务"""
    
    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.chunk_size = 500  # 每块字符数
        self.chunk_overlap = 50  # 重叠字符数
        self.use_embedding = self.embedding_service.enabled
    
    def extract_text_from_file(self, file_path: str, file_type: str) -> str:
        """从文件中提取文本"""
        try:
            if file_type == 'txt':
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            
            elif file_type == 'pdf':
                try:
                    import pdfplumber
                    with pdfplumber.open(file_path) as pdf:
                        text = ''
                        for page in pdf.pages:
                            page_text = page.extract_text() or ''
                            text += page_text + '\n'
                    return text
                except ImportError:
                    return "⚠️ 请安装 pdfplumber: pip install pdfplumber"
                except Exception as e:
                    return f"PDF解析失败: {e}"
            
            elif file_type == 'docx':
                try:
                    from docx import Document
                    doc = Document(file_path)
                    text = '\n'.join([para.text for para in doc.paragraphs])
                    return text
                except ImportError:
                    return "⚠️ 请安装 python-docx: pip install python-docx"
                except Exception as e:
                    return f"DOCX解析失败: {e}"
            
            else:
                return f"不支持的文件类型: {file_type}"
                
        except Exception as e:
            return f"提取文本失败: {e}"
    
    def chunk_text(self, text: str) -> List[str]:
        """将文本分块"""
        if not text or not text.strip():
            return []
        
        # 清理文本
        text = text.strip()
        
        chunks = []
        start = 0
        text_length = len(text)
        
        while start < text_length:
            end = start + self.chunk_size
            if end < text_length:
                # 尝试在句号、问号等处分段
                for sep in ['。', '！', '？', '\n\n', '\n', '.', '!', '?']:
                    pos = text.rfind(sep, start, end)
                    if pos > start:
                        end = pos + len(sep)
                        break
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = end - self.chunk_overlap if end < text_length else end
        
        return chunks
    
    def save_document(
        self, 
        db: Session, 
        title: str, 
        filename: str, 
        file_type: str, 
        content: str
    ) -> KnowledgeDocument:
        """保存文档并生成向量"""
        # 1. 创建文档记录
        doc = KnowledgeDocument(
            title=title or filename,
            filename=filename,
            file_type=file_type,
            content=content[:10000]  # 只保存前10000字符，避免过大
        )
        db.add(doc)
        db.flush()
        
        # 2. 分块
        chunks = self.chunk_text(content)
        
        # 3. 为每块生成向量并保存
        for idx, chunk_text in enumerate(chunks):
            embedding = None
            if self.use_embedding:
                embedding = self.embedding_service.get_embedding(chunk_text)
            
            chunk = KnowledgeChunk(
                document_id=doc.id,
                chunk_index=idx,
                content=chunk_text,
                embedding=embedding
            )
            db.add(chunk)
        
        doc.chunk_count = len(chunks)
        db.commit()
        db.refresh(doc)
        
        print(f"✅ 文档已保存: {doc.title}, 共 {len(chunks)} 个分块")
        return doc
    
    def search_similar(
        self, 
        db: Session, 
        query: str, 
        top_k: int = 5,
        threshold: float = 0.3
    ) -> List[Tuple[KnowledgeChunk, float]]:
        """搜索相似文档块"""
        # 如果没有 embedding 或获取向量失败，使用文本搜索
        print(f"🔍 DocumentService.search_similar 被调用")
        print(f"   查询: {query[:50]}...")
        print(f"   top_k: {top_k}, threshold: {threshold}")
        # threshold 是浮点数
        if isinstance(threshold, tuple):
            threshold = threshold[0]
        threshold = float(threshold)
        query_embedding = None
        if self.use_embedding:
            query_embedding = self.embedding_service.get_embedding(query)
        
        if not query_embedding:
            # 降级到文本搜索
            return self._search_by_text(db, query, top_k)
        
        try:
            from sqlalchemy import text
            
            # 使用向量相似度搜索
            sql = text("""
                SELECT 
                    kc.id,
                    kc.document_id,
                    kc.chunk_index,
                    kc.content,
                    kc.embedding,
                    kc.created_at,
                    1 - (kc.embedding <=> cast(:query_embedding as vector)) as similarity
                FROM knowledge_chunks kc
                WHERE kc.embedding IS NOT NULL
                ORDER BY kc.embedding <=> cast(:query_embedding as vector)
                LIMIT :top_k
            """)
            
            result = db.execute(sql, {
                "query_embedding": query_embedding,
                "top_k": top_k * 2  # 多取一些，过滤低相似度
            })
            
            results = []
            for row in result:
                similarity = row[6]
                if similarity < threshold:
                    continue
                chunk = KnowledgeChunk(
                    id=row[0],
                    document_id=row[1],
                    chunk_index=row[2],
                    content=row[3],
                    embedding=row[4],
                    created_at=row[5]
                )
                results.append((chunk, similarity))
            
            # 按相似度排序
            results.sort(key=lambda x: x[1], reverse=True)
            return results[:top_k]
            
        except Exception as e:
            print(f"向量搜索失败，降级到文本搜索: {e}")
            return self._search_by_text(db, query, top_k)
    
    def _search_by_text(
        self, 
        db: Session, 
        query: str, 
        top_k: int = 5
    ) -> List[Tuple[KnowledgeChunk, float]]:
        """基于文本的搜索（降级方案）"""
        try:
            # 使用 PostgreSQL 全文搜索或 LIKE
            search_pattern = f"%{query}%"
            results = db.query(KnowledgeChunk).filter(
                KnowledgeChunk.content.ilike(search_pattern)
            ).limit(top_k).all()
            
            # 计算简单的相关性分数（关键词匹配度）
            query_words = set(query.lower().split())
            scored_results = []
            for chunk in results:
                chunk_words = set(chunk.content.lower().split())
                if chunk_words:
                    overlap = len(query_words & chunk_words) / len(query_words)
                    scored_results.append((chunk, overlap))
            
            scored_results.sort(key=lambda x: x[1], reverse=True)
            return scored_results
            
        except Exception as e:
            print(f"文本搜索失败: {e}")
            return []
    
    def get_document_by_id(self, db: Session, doc_id: str) -> Optional[KnowledgeDocument]:
        """根据ID获取文档"""
        try:
            return db.query(KnowledgeDocument).filter(
                KnowledgeDocument.id == uuid.UUID(doc_id)
            ).first()
        except ValueError:
            return None