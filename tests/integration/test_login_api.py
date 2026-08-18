"""Integration tests for login API."""

from __future__ import annotations

import allure
import httpx
import pytest
import respx
from httpx import Response

from src.app.clients.school_client import SchoolClient
from src.app.models.auth import LoginRequest
from src.framework.config import Settings


@pytest.fixture
def school_settings() -> Settings:
    """School API test settings."""
    return Settings(
        http={
            "base_url": "http://127.0.0.1:5003",
            "timeout": 10,
            "retry_count": 3,
        },
    )


@pytest.fixture
def school_client(school_settings: Settings) -> SchoolClient:
    """School client fixture."""
    client = SchoolClient(settings=school_settings)
    yield client
    client.close()


@allure.feature("学校管理系统")
@allure.story("用户登录")
class TestLoginAPI:
    """Login API integration tests."""

    @allure.title("登录成功返回 token")
    @respx.mock
    def test_login_success(self, school_client: SchoolClient) -> None:
        """Test successful login returns token."""
        with allure.step("Mock 登录成功响应"):
            route = respx.post("http://127.0.0.1:5003/api/login").mock(
                return_value=Response(
                    status_code=200,
                    json={
                        "message": "登录成功",
                        "success": True,
                        "token": "fake-jwt-token-123",
                    },
                )
            )

        with allure.step("发送登录请求"):
            result = school_client.login("admin", "123456")

        with allure.step("验证响应"):
            assert result.success is True
            assert result.message == "登录成功"
            assert result.token == "fake-jwt-token-123"
            assert school_client.token == "fake-jwt-token-123"
            assert route.called

    @allure.title("登录失败返回错误")
    @respx.mock
    def test_login_wrong_password(self, school_client: SchoolClient) -> None:
        """Test login with wrong password returns error."""
        with allure.step("Mock 登录失败响应"):
            respx.post("http://127.0.0.1:5003/api/login").mock(
                return_value=Response(
                    status_code=401,
                    json={
                        "message": "用户名或密码错误",
                        "success": False,
                    },
                )
            )

        with allure.step("验证抛出异常"):
            with pytest.raises(httpx.HTTPStatusError):
                school_client.login("admin", "wrong_password")

    @allure.title("登录请求参数验证")
    def test_login_request_validation(self) -> None:
        """Test login request parameter validation."""
        with allure.step("验证空用户名被拒绝"):
            with pytest.raises(ValueError):
                LoginRequest(username="", password="123456")
