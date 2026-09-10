# src/framework/ai/knowledge_simple/services/embedding_service.py
import os
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).parent.parent.parent.parent.parent / ".env"
load_dotenv(env_path)

class EmbeddingService:
    """向量化服务 - 使用SLM模型"""
    def __init__(self):
        # 使用 DeepSeek 或 OpenAI 的 embedding 接口,deepseek没有向量的模型。
        self.api_key = os.environ.get("EMBEDDING_API_KEY") or os.environ.get("APP_DEEPSEEK_API_KEY")
        self.base_url = os.environ.get("EMBEDDING_URL") or os.environ.get("APP_DEEPSEEK_URL")
        self.model = os.environ.get("EMBEDDING_MODEL", "text-embedding-3-small")

        # 是否启用向量化（如果没配置则使用简单文本搜索）
        self.enabled  = bool(self.api_key)

        if self.enabled:
            self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
            print(f"✅ Embedding 服务已启用，模型: {self.model}")
        else:
            self.client = None
            print("⚠️ Embedding 未配置，将使用简单的文本搜索")



    def get_embedding(self, text: str) -> str:
        """获取文本向量"""
        if not self.enabled  or not self.client:
            return None
        try:
            # 截断过长的文本
            if len(text) > 8000:
                text = text[:8000]
            response = self.client.embeddings.create(
                model=self.model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
             print(f"❌ 获取向量失败: {e}")
             return None

    def get_embedding_safe(self, text: str) -> list:
        """安全获取向量，失败时返回 None"""
        try:
            return self.get_embedding(text)
        except Exception as e:
            print(f"错误：{e}")
            return None