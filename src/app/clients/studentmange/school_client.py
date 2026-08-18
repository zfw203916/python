# 这个是客户端，做请求用,就是请求登录和增加学生。
from __future__ import annotations
from src.app.models.auth import (
    LoginRequest,
    LoginResponse,
    StudentRequest,
    StudentResponse,
)
from src.framework.config import Settings
import httpx
from src.framework.logger import get_trace_id, log_request


class SchoolClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.client = httpx.Client(
            base_url=settings.http.base_url,
            timeout=self.settings.http.timeout,
            headers={
                "Content-Typ": "application/json",
                "X-Trace-ID": get_trace_id(),
            },
        )

    def _get_headers(self) -> dict[str, str]:
        """构建通用请求头"""
        headers: dict[str, str] = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def login(self, username: str, password: str) -> LoginResponse:
        """登录并返回响应"""
        # 显式构造请求
        request = LoginRequest(username=username, password=password)
        response = self.client.post("/auth/login", json=request.model_dump())

        # 发送请求
        response.raise_for_status()

        # 解析响应
        result = LoginResponse(**response.json())
        if result.success and result.token:
            self.token = result.token

        log_request("POST", "/auth/login", status=response.status_code)
        return result

    def add_student(self, username: str, age: int, class_name: str) -> StudentResponse:
        """添加学生"""
        headers = self._get_headers()
        request = StudentRequest(name=username, age=age, **{"class": class_name})
        response = self.client.post(
            "/api/students", json=request.model_dump(by_alias=True), headers=headers
        )
        response.raise_for_status()

        student = StudentResponse(**response.json())
        if not student.sussess:
            raise ValueError(f"添加学生失败:{student.message}")
        log_request("POST", "/api/students", status=response.status_code)
        return student

    def close(self) -> None:
        """关闭"""
        self.client.close()
