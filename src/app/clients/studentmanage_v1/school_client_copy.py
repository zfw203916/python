"""School system API client."""

from __future__ import annotations

from typing import Any

import httpx

from src.app.models.auth import LoginRequest, LoginResponse, StudentRequest
from src.framework.config import Settings
from src.framework.logger import get_trace_id, log_request


class SchoolClient:
    """Client for school management system."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.client = httpx.Client(
            base_url=settings.http.base_url,
            timeout=settings.http.timeout,
            headers={
                "Content-Type": "application/json",
                "X-Trace-ID": get_trace_id(),
            },
        )
        self.token: str | None = None

    def login(self, username: str, password: str) -> LoginResponse:
        """Login and store token."""
        request = LoginRequest(username=username, password=password)

        response = self.client.post(
            "/api/login",
            json=request.model_dump(),
        )
        response.raise_for_status()

        data = response.json()
        result = LoginResponse(**data)

        if result.success and result.token:
            self.token = result.token

        log_request("POST", "/api/login", status=response.status_code)
        return result

    def add_student(self, name: str, age: int, class_name: str) -> dict[str, Any]:
        """Add a student."""
        # request = StudentRequest(name=name, age=age, class_name=class_name)
        # 使用 **{"class": class_name} 来传递别名参数
        request = StudentRequest(
            name=name, age=age, **{"class": class_name}
        )  # 处理了这个可以了。

        headers: dict[str, str] = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        response = self.client.post(
            "/api/students",
            json=request.model_dump(by_alias=True),
            headers=headers,
        )
        response.raise_for_status()

        log_request("POST", "/api/students", status=response.status_code)
        return response.json()

    def close(self) -> None:
        """Close connection."""
        self.client.close()
