# src/framework/ai/agent/weather/core/router.py
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
import json
import uuid

from .agent import smart_agent

router = APIRouter(prefix="/api/agent", tags=["agent"])


class AgentRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class AgentResponse(BaseModel):
    response: str
    session_id: Optional[str] = None


@router.post("/chat", response_model=AgentResponse)
async def chat(request: AgentRequest):
    """同步聊天 - Agent 自主决定调用工具"""
    if not request.message or not request.message.strip():
        raise HTTPException(status_code=400, detail="消息不能为空")

    try:
        response = smart_agent.run(request.message)
        return AgentResponse(
            response=response, session_id=request.session_id or str(uuid.uuid4())
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat/stream")
async def chat_stream(request: AgentRequest):
    """流式聊天 - Agent 自主决定调用工具"""
    if not request.message or not request.message.strip():
        raise HTTPException(status_code=400, detail="消息不能为空")

    session_id = request.session_id or str(uuid.uuid4())

    async def generate():
        full_response = ""
        try:
            async for chunk in smart_agent.stream(request.message):
                # 处理不同类型的 chunk
                if "output" in chunk:
                    full_response += chunk["output"]
                    yield f"data: {json.dumps({'type': 'chunk', 'content': chunk['output'], 'full': full_response}, ensure_ascii=False)}\n\n"
                elif "steps" in chunk:
                    # 工具调用步骤
                    yield f"data: {json.dumps({'type': 'step', 'content': str(chunk)}, ensure_ascii=False)}\n\n"

            yield f"data: {json.dumps({'type': 'complete', 'full_response': full_response, 'session_id': session_id}, ensure_ascii=False)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/tools")
async def list_tools():
    """列出所有可用工具"""
    from ..tools.weather import get_weather
    from ..tools.calculator import calculate
    from ..tools.knowledge import search_knowledge

    return {
        "tools": [
            {"name": get_weather.name, "description": get_weather.description},
            {"name": calculate.name, "description": calculate.description},
            {
                "name": search_knowledge.name,
                "description": search_knowledge.description,
            },
        ]
    }
