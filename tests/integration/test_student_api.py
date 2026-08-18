"""Integration tests for student API."""

from __future__ import annotations


import allure
import pytest
import respx
from httpx import Response

from src.app.clients.school_client import SchoolClient
from src.framework.config import Settings


@pytest.fixture
def school_settings() -> Settings:
    """School API test settings."""
    return Settings(
        http={
            "base_url": "http://127.0.0.1:5004",
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
@allure.story("学生管理")
class TestStudentAPI:
    """Student API integration tests."""

    @allure.title("添加学生成功")
    @respx.mock
    def test_add_student_success(self, school_client: SchoolClient) -> None:
        """Test adding student after login."""
        with allure.step("先登录获取 token"):
            respx.post("http://127.0.0.1:5004/api/login").mock(
                return_value=Response(
                    status_code=200,
                    json={
                        "message": "登录成功",
                        "success": True,
                        "token": "test-token",
                    },
                )
            )
            school_client.login("zfw", "zfw")

        with allure.step("Mock 添加学生成功"):
            route = respx.post("http://127.0.0.1:5004/api/students").mock(
                return_value=Response(
                    status_code=200,
                    json={
                        "message": "学生添加成功",
                        "success": True,
                    },
                )
            )

        with allure.step("添加学生"):
            result = school_client.add_student("张三", 18, "三年级二班")

        with allure.step("验证响应"):
            assert result["success"] is True
            assert result["message"] == "学生添加成功"
            assert route.called

    @allure.title("未登录添加学生失败")
    @respx.mock
    def test_add_student_without_login(self, school_client: SchoolClient) -> None:
        """Test adding student without token fails."""
        with allure.step("Mock 未授权响应"):
            respx.post("http://127.0.0.1:5004/api/students").mock(
                return_value=Response(
                    status_code=401,
                    json={
                        "message": "请先登录",
                        "success": False,
                    },
                )
            )

        with allure.step("验证未登录被拒绝"):
            with pytest.raises(Exception):
                school_client.add_student("张三", 18, "三年级二班")
