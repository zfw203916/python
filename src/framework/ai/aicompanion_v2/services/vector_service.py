# my-test-framework/src/framework/ai/aicompanion_v2/services/vector_service.py
import os
from openai import OpenAI
from sqlalchemy.orm import Session
from sqlalchemy import text
from ..database import MessageModel
from ..models import MessageResponse
import numpy as np

class VectorService:
    def __init__(self):
        self.api_key = os.environ.get("APP_DEEPSEEK_API_KEY")
        self.base_url = os.environ.get("APP_DEEPSEEK_URL")
        if self.api_key:
            self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        else:
            self.client = None

    def get_embedding(self, text: str) -> list:
        """获取文本的向量表示"""
        if not self.client:
            return None
        try:
            # DeepSeek可能不支持embeddings，返回None
            # 如果使用OpenAI，可以启用下面的代码
            # response = self.client.embeddings.create(
            #     model="text-embedding-3-small",
            #     input=text
            # )
            # return response.data[0].embedding
            return None
        except Exception as e:
            print(f"Error getting embedding: {e}")
            return None

    def save_message_with_embedding(self, db: Session, session_id: str, role: str, content:str):
        """保存消息并生成向量"""
        try:
            embedding = self.get_embedding(content)
            message = MessageModel(
                session_id = session_id,
                role = role,
                content = content,
                embedding = embedding

            )
            db.add(message)
            db.commit()
            return message
        except Exception as e:
            print(f"Error saving message with embedding:{e}")
            return None

    def search_similar_messages(self,db: Session, query: str, session_id: str = None, limit: int = 5):
        """搜索相似消息"""
        query_embedding = self.get_embedding(query)
        if not query_embedding:
            return []
        try:
            # 构建向量搜索查询
            query_sql = text("""
                SELECT id, session_id, role, content, 
                        1 - (embedding <=> :query_embedding::vector) as similarity
                FROM ai_messages
                WHERE (:session_id IS NULL OR session_id = :session_id)
                ORDER BY embedding <=> :query_embedding::vector
                LIMIT : limit 
            """)
            result = db.execute(query_sql,{
                "query_embedding": query_embedding,
                "session_id": session_id,
                "limit": limit
            })

            return [{
                "id" :row[0],
                "session_id" : row[1],
                "role": row[2],
                "content": row[3],
                "similarity": row[4]
            }for row in result.fetchall()] 
        except Exception as e:
            print(f"Error searching similar messages: {e}")
            return []