# 创建 HTTP 客户端
"""HTTP client wrapper with base configuration."""
from __future__ import annotations
import httpx
from src.logger import get_trace_id, log_request
from src.config import Settings
from tenacity import retry, stop_after_attempt, wait_exponential


class ApiClient:
    """Simple API client with base URL and timeout."""
    def __init__(self, settings: Settings) ->None:
        """Initialize the client with base URL and timeout."""
        """
            方式 A：使用 Client（推荐）
            client = httpx.Client(base_url="https://api.test.com")
            client.get("/users/1")  实际请求: https://api.test.com/users/1

            方式 B：直接请求（不推荐测试用）
            httpx.get("https://api.test.com/users/1")  # 完整 URL，每次新建连接
        """
        self.settings = settings
        self.client = httpx.Client(
            base_url = self.settings.http.base_url,
            timeout = self.settings.http.timeout,
            headers={
                "Content-Type": "application/json",
                "X-Trace-ID":get_trace_id(),
                "X-API-Key": settings.api_key
            }
        )


    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True    
    )


    def get_user(self, user_id: int) -> dict:
        """Fetch user by ID."""
        response = self.client.get(f"/users/{user_id}")
        response.raise_for_status()
        return response.json()
    
    def close(self) ->None:
        """Close HTTP connection."""
        self.client.close()