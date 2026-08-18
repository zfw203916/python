"""API tests with mocked HTTP responses."""

from __future__ import annotations
import pytest
import respx
import httpx
from httpx import Response
from src.client import ApiClient
from src.config import Settings
import allure


@pytest.fixture
def settings() -> Settings:
    """test setting"""
    return Settings(
        http={"base_url": "https://api.test.com", "timeout": 30, "retry_count": 3},
        api_key="test-key",
    )


@pytest.fixture
def api_client(settings: Settings) -> ApiClient:
    """Create API client for testing."""
    client = ApiClient(
        settings=settings
    )  # ✅ 传实例 settings，不是类 Settings,之前写错了。 ApiClient(settings=Settings)
    yield client
    client.close()


@allure.feature("用户管理")
@allure.story("获取用户信息")
@respx.mock
def test_get_user_success(api_client: ApiClient) -> None:
    """Test fetching a user returns correct data."""
    # Arrange: mock the API response
    with allure.step("Mock API 响应"):
        route = respx.get("https://api.test.com/users/1").mock(
            return_value=Response(
                status_code=200,
                json={"id": 1, "username": "john_doe", "email": "john@test.com"},
            )
        )
    # Act: call the client
    with allure.step("调用客户端"):
        user = api_client.get_user(1)
        assert user["id"] == 1
        assert user["username"] == "john_doe"
        assert user["email"] == "john@test.com"
        assert route.called  # verify the mock was actually hit


@allure.feature("用户管理")
@allure.story("处理错误场景")
@respx.mock
def test_get_user_not_found(api_client: ApiClient) -> None:
    """Test 404 response raises exception."""
    with allure.step("Mock 404 响应"):
        # Arrange: mock 404 response
        respx.get("https://api.test.com/users/999").mock(
            return_value=Response(status_code=404, text="Not Found")
        )

    with allure.step("验证异常"):
        # Act & Assert: should raise HTTPStatusError
        with pytest.raises(httpx.HTTPStatusError):
            api_client.get_user(999)
