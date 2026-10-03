# src/framework/ai/knowledge_simple/services/embedding_service.py
import os
import httpx 
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

        self.use_local = os.environ.get("USE_LOCAL_EMBEDDING","false").lower() == "true"
        if self.use_local:
            # 使用本地 Ollama 配置
            self.api_key =  os.environ.get("LOCAL_EMBEDDING_API_KEY", "ollama")
            self.model = os.environ.get("LOCAL_EMBEDDING_MODEL")
            self.base_url = os.environ.get("LOCAL_EMBEDDING_URL") 
            # 临时加日志
            logger.info(f"LOCAL_EMBEDDING_URL = {self.base_url}")
            logger.info(f"🖥️ 使用本地 Embedding 模型: {self.model}")
            
            # ✅ 在这里检查 Ollama 是否可用
            try:
                # 从 base_url 去掉 /v1，得到 Ollama 原生地址
                ollama_host = self.base_url.replace("/v1", "")
                response = httpx.get(f"{ollama_host}/api/tags", timeout=5)
                if response.status_code == 200:
                    logger.info("✅ Ollama 可用，使用本地 SLM")
                else:
                    logger.warning(f"⚠️ Ollama 不可用，状态码: {response.status_code}")
            except Exception as e:
                logger.warning(f"⚠️ Ollama 不可用: {e}")
        else:
            # 3. 使用原有的云端配置
            self.api_key = os.environ.get("EMBEDDING_API_KEY")
            self.base_url = os.environ.get("EMBEDDING_URL")
            self.model = os.environ.get("EMBEDDING_MODEL", "BAAI/bge-large-zh-v1.5")
            logger.info(f"☁️ 使用云端 Embedding 模型: {self.model}")
        # 使用硅流的 embedding 接口,deepseek没有向量的模型。
        # 4. 统一初始化 OpenAI 客户端 (因为 Ollama 兼容 OpenAI 接口)
        self.enabled = bool(self.api_key)
        
        # 是否启用向量化（如果没配置则使用简单文本搜索）
        if self.enabled:
            self.client = OpenAI(
                api_key=self.api_key, 
                base_url=self.base_url
            )
            logger.info(f"✅ Embedding 服务已启用，模型: {self.model}")
        else:
            self.client = None
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