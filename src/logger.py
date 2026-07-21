"""Structured logging with trace ID support."""
from __future__ import annotations
import uuid
from contextvars import ContextVar
from loguru import logger

# 每个请求的唯一追踪 ID
trace_id_var : ContextVar[str] = ContextVar("trace_id", default="")

def get_trace_id() -> str:
    """Get current trace ID or generate new one."""
    current = trace_id_var.get()

    if not current:
        current = str(uuid.uuid4())[:8]
        trace_id_var.set(current)

    return current

def log_request(method: str, url: str, status: int | None = None ,error: str | None = None) -> None:
    """Log HTTP request with trace ID."""
    trace_id = get_trace_id()
    log_data ={
        "trace_id": trace_id,
        "method": method,
        "url": url,
    }

    if status is not None:
        log_data["status"] = status
    if error is not None:
        log_data["error"] = error
        logger.error(f"HTTP {method} {url} failed", **log_data)
    else:
         logger.info(f"HTTP {method} {url} success", **log_data)
