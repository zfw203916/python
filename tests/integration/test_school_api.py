from __future__ import annotations
import allure
import httpx
import pytest
import respx
from httpx import Response

from src.app.models.auth import LoginRequest
from src.app.clients.school_client import SchoolClient
from src.framework.config import Settings


@pytest.fixture
def school_settings() -> Settings:
    seetings = Settings(
        http={
            "base_url": "http://127.0.0.1:5004",
            "timeout": 10,
            "retry_count": 3,
        },
    )
    return seetings


@pytest.fixture
def school_client(school_settings: Settings) -> SchoolClient:
    client = SchoolClient(settings=school_settings)
    yield client
    client.close()


@allure.feature("认证系统")
@allure.story("用户登录")
class TestSchoolAPI:
    """
    测试学校API的测试类，包含多个与登录相关的测试用例。
    该类用于验证学校API的登录功能是否正常工作。
    """

    @allure.title("登录成功返回 token")
    @respx.mock
    def test_login_success(self, school_client: SchoolClient) -> None:
        """
        测试成功登录的场景
        验证当提供正确的用户名和密码时，API是否能正确处理登录请求并返回成功响应
        """
        with allure.step("Mock 登录成功响应"):
            route = respx.post(
                "http://127.0.0.1:5004/auth/login",
            ).mock(
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
            result = school_client.login("zfw", "zfw")
            assert result.success is True
            assert result.message == "登录成功"
            assert result.token == "fake-jwt-token-123"
            assert school_client.token == "fake-jwt-token-123"
            assert route.called

    @allure.title("登录失败返回错误")
    @respx.mock
    def test_login_wrong_password(self, school_client: SchoolClient) -> None:
        """
        测试密码错误的场景
        验证当提供错误的密码时，API是否能正确处理并返回适当的错误信息
        """
        # 测试用例：使用错误密码尝试登录
        # 预期结果：返回认证失败状态码
        # 预期结果：返回错误提示信息
        with allure.step("Mock 登录失败响应"):
            route = respx.post(
                "http://127.0.0.1:5004/auth/login",
            ).mock(
                return_value=Response(
                    status_code=401,
                    json={
                        "message": "认证失败",
                        "success": False,
                    },
                )
            )
            with allure.step("验证抛出异常"):
                with pytest.raises(httpx.HTTPStatusError):
                    school_client.login("zfw", "zfw123")

    def test_login_request_validation(self):
        """
        测试登录请求验证的场景
        验证API是否能正确处理格式不正确的登录请求，并返回适当的错误提示
        """
        # 测试用例：发送格式不正确的登录请求
        # 预期结果：返回请求无效状态码
        # 预期结果：返回请求格式错误的具体信息
        with allure.step("验证空用户名被拒绝"):
            """Test login request parameter validation."""
            with pytest.raises(ValueError):
                LoginRequest(username="", password="password")
