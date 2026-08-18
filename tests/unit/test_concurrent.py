"""Detect state leakage between tests.检测共享状态"""

from __future__ import annotations

from src.app.clients.school_client import SchoolClient
from src.framework.config import Settings


class TestStateLeakage:
    """Verify no global state is shared."""

    def test_client_token_isolation(self) -> None:
        """Test that token doesn't leak between instances."""
        settings = Settings(
            http={"base_url": "http://test.com", "timeout": 10, "retry_count": 3}
        )

        client1 = SchoolClient(settings=settings)
        client1.token = "token1"

        client2 = SchoolClient(settings=settings)

        # 关键断言：client2 不应该看到 client1 的 token
        assert client2.token is None
        assert client1.token == "token1"

        client1.close()
        client2.close()
