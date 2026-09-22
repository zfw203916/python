# src/framework/ai/knowledge_simple/services/embedding_service.py
import os
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path
# 导入日志
import logging
import traceback
# 导入模型
from .....shared.llm import  get_embedding_client, EMBEDDING_MODEL
env_path = Path(__file__).parent.parent.parent.parent.parent / ".env"
load_dotenv(env_path)
from ...aicompanion_v2.logging_config import setup_logging
setup_logging()
logger = logging.getLogger(__name__)

class EmbeddingService:
    """向量化服务 - 使用SLM模型"""
    def __init__(self):
        # 使用硅流的 embedding 接口,deepseek没有向量的模型。
        self.client = get_embedding_client()
        self.model = EMBEDDING_MODEL
        self.enabled = self.client is not None
        # 是否启用向量化（如果没配置则使用简单文本搜索）
        if self.enabled:
            logger.info(f"✅ Embedding 服务已启用，模型: {self.model}")
        else:
            logger.info("⚠️ Embedding 未配置，将使用简单的文本搜索")

        # ← 加这两行：打印实例 id 和调用栈
        # logger.info(f"实例 id={id(self)}")
        # logger.info("调用栈:\n%s", "".join(traceback.format_stack()))

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