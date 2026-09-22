# src/shared/llm.py
"""
    共享 LLM 客户端

    统一管理：
    - DeepSeek 聊天客户端(OpenAI 兼容）
    - Embedding 客户端
    - LangChain 聊天客户端

    所有模块复用，避免重复初始化。
"""
import os
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

# ========== 加载 .env ==========
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)

# ========== 配置 ==========
APP_DEEPSEEK_API_KEY = os.environ.get("APP_DEEPSEEK_API_KEY")
APP_DEEPSEEK_URL = os.environ.get("APP_DEEPSEEK_URL")
APP_DEEPSEEK_MODEL = os.environ.get("APP_DEEPSEEK_MODEL")

EMBEDDING_API_KEY = os.environ.get("EMBEDDING_API_KEY")
EMBEDDING_URL = os.environ.get("EMBEDDING_URL")
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "text-embedding-3-small")

# ========== 全局单例客户端 ==========
_chat_client = None  # 真正私有用双下划线。
_embedding_client = None

def get_chat_client():
    """获取聊天客户端（全局单例）"""
    global _chat_client  # ← 声明"我要修改全局变量"
    if _chat_client is None:
        if not APP_DEEPSEEK_API_KEY:
            raise ValueError("APP_DEEPSEEK_API_KEY 未配置")
        _chat_client = OpenAI(
            api_key = APP_DEEPSEEK_API_KEY,
            base_url = APP_DEEPSEEK_URL
        )
    return _chat_client

def get_embedding_client():
    """获取 Embedding 客户端（全局单例）"""
    global _embedding_client  # ← 声明"我要修改全局变量"
    if _embedding_client is None:
        if not EMBEDDING_API_KEY:
            return None         
        _embedding_client = OpenAI(
            api_key = EMBEDDING_API_KEY,
            base_url = EMBEDDING_URL
        )
    return _embedding_client

def get_langchain_llm():
    """获取 LangChain 聊天模型（延迟导入）"""
    from langchain_openai import ChatOpenAI # 延迟导入	用到时才加载
    if not APP_DEEPSEEK_API_KEY:
        raise ValueError("APP_DEEPSEEK_API_KEY 未配置")
    return  ChatOpenAI(
        model=APP_DEEPSEEK_MODEL,
        api_key=APP_DEEPSEEK_API_KEY,
        base_url=APP_DEEPSEEK_URL,
        temperature=0.7,
        streaming=True,
    )