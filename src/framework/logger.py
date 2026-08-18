"""Structured logging with trace ID support."""

from __future__ import annotations
import uuid
from contextvars import ContextVar
from loguru import logger

# 每个请求的唯一追踪 ID
trace_id_var: ContextVar[str] = ContextVar("trace_id", default="")


def get_trace_id() -> str:
    """Get current trace ID or generate new one."""
    current: str = trace_id_var.get()

    if not current:
        new_id: str = str(uuid.uuid4())[:8]
        trace_id_var.set(new_id)
        return new_id

    return current


def log_request(
    method: str, url: str, status: str | None = None, error: str | None = None
) -> None:
    """Log HTTP request with trace ID."""
    trace_id = get_trace_id()
    log_data = {
        "trace_id": trace_id,
        "method": method,
        "url": url,
    }

    if status is not None:
        log_data["status"] = status
    if error is not None:
        log_data["error"] = error

    # 过滤掉值为 None 的项（如果有的话）
    extra = {k: v for k, v in log_data.items() if v is not None}

    if error is not None:
        logger.error(f"HTTP {method} {url} failed", **extra)
    else:
        logger.info(f"HTTP {method} {url} success", **extra)
