"""Debug test to see actual request URL."""
import respx
import re
from httpx import Response
from src.client import ApiClient
from src.config import Settings

@respx.mock
def test_debug_request() -> None:
    """Test to see actual request URL."""
    """Debug: see what URL is actually requested."""
    # 捕获所有 GET 请求
    route = respx.get(url=re.compile(r".*")).mock(
        return_value=Response(status_code=200, json={"debug": True})
    )
    settings = Settings(
        http={
            "base_url": "https://api.test.com",
            "timeout": 10,
            "retry_count": 3,
        },
        api_key="debug-key",
    )
    client = ApiClient(settings=settings)
    try:
        result = client.get_user(1)
        print(f"结果1:{result}")
        print(f"结果2：Route called:{route.called}")
        if route.called:
            print(f"结果3：Request URL: {route.calls[0].request.url}")
    finally:
        client.close()
        

