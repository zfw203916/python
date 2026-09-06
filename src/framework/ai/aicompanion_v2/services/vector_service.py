# my-test-framework/src/framework/ai/aicompanion_v2/services/vector_service.py
import os
from openai import OpenAI
from sqlalchemy.orm import Session
from sqlalchemy import text
from ..database import MessageModel
from dotenv import load_dotenv
from pathlib import Path


# 指定 .env 文件路径（项目根目录）
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)


class VectorService:
    load_dotenv()  # 加载.env文件

    def __init__(self):
        self.embedding_api_key = os.environ.get("EMBEDDING_API_KEY")
        self.embedding_url = os.environ.get("EMBEDDING_URL")
        # Embedding模型配置
        self.embedding_model = os.environ.get("EMBEDDING_MODEL")

        # 独立的Embedding客户端
        if self.embedding_api_key:
            self.embedding_client = OpenAI(
                api_key=self.embedding_api_key, base_url=self.embedding_url
            )
        else:
            self.embedding_client = None

        # RAG配置
        self.enable_rag = os.environ.get("ENABLE_RAG", "true").lower() == "true"
        self.rag_top_k = int(os.environ.get("RAG_TOP_K", "5"))
        self.rag_threshold = float(os.environ.get("RAG_THRESHOLD", "0.5"))

    def get_embedding(self, text: str) -> list:
        """获取文本的向量表示"""
        if not self.embedding_client:
            return None
        try:
            # DeepSeek可能不支持embeddings，返回None
            # 如果使用OpenAI，可以启用下面的代码
            response = self.embedding_client.embeddings.create(
                model=self.embedding_model, input=text
            )
            return response.data[0].embedding
            # return None
        except Exception as e:
            print(f"Error getting embedding: {e}")
            return None

    def save_message_with_embedding(
        self, db: Session, session_id: str, role: str, content: str
    ):
        """搜索相似消息，增加相似度阈值过滤"""

        """保存消息并生成向量"""
        try:
            embedding = self.get_embedding(content)
            message = MessageModel(
                session_id=session_id, role=role, content=content, embedding=embedding
            )
            db.add(message)
            db.commit()
            return message
        except Exception as e:
            print(f"Error saving message with embedding:{e}")
            return None

    def search_similar_messages(
        self,
        db: Session,
        query: str,
        session_id: str = None,
        exclude_id: str = None,
        limit: int = 5,
        threshold: float = 0.5,
    ) -> list:
        """搜索相似消息"""
        """
            🟢 新增：搜索相似消息（带阈值过滤）
            用于RAG检索增强
        """
        query_embedding = self.get_embedding(query)
        if not query_embedding:
            return []
        try:
            # 构建向量搜索查询
            query_sql = text("""
                SELECT id, session_id, role, content, 
                        1 - (embedding <=> cast(:query_embedding as vector)) as similarity
                FROM ai_messages
                WHERE (:session_id IS NULL OR session_id = :session_id)
                    AND embedding IS NOT NULL
                    AND (:exclude_id IS NOT NULL OR id != cast(:exclude_id as uuid))
                ORDER BY embedding <=> cast(:query_embedding as vector)
                LIMIT :limit 
            """)

            result_value = db.execute(
                query_sql,
                {
                    "query_embedding": query_embedding,
                    "session_id": session_id,
                    "exclude_id": exclude_id,
                    "limit": limit,
                },
            )
            # 先转成字典列表
            results = [
                {
                    "id": row[0],
                    "session_id": row[1],
                    "role": row[2],
                    "content": row[3],
                    "similarity": row[4],
                }
                for row in result_value.fetchall()
            ]
            return [r for r in results if r["similarity"] >= threshold]
        except Exception as e:
            print(f"Error searching similar messages: {e}")
            return []
