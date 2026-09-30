# my-test-framework/src/framework/ai/aicompanion_v2/routers/chat.py

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from ..models import MessageRequest
from ..services.chat_service import ChatService
import json
import uuid

router = APIRouter(prefix="/api/chat", tags=["chat"])
chat_service = ChatService()


@router.post("/stream")
async def chat_stream(
    request: MessageRequest,
    http_request: Request
):
    """流式聊天 - 统一走 AI 伴侣"""
    session_id = request.session_id or str(uuid.uuid4())
    user_role = http_request.session.get("role","viewer")
    user_name = http_request.session.get("username", "")
  
    try:
        generator = chat_service.chat(
            session_id, 
            request.content, 
            stream=True,
            nick_name=request.nick_name,
            nature=request.nature,
            user_role =  user_role,
            user_name = user_name, 
        )

        def stream_generator():
            try:
                for chunk in generator:
                    yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
            except Exception as e:
                error_data = {"type": "error", "message": str(e)}
                yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"

        return StreamingResponse(
            stream_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/non-stream")
async def chat_non_stream(request: MessageRequest):
    """非流式聊天 - 统一走 AI 伴侣"""
    session_id = request.session_id or str(uuid.uuid4())
    user_role = http_request.session.get("role","viewer")
    user_name = http_request.session.get("username", "")
    try:
        result = chat_service.chat(
            session_id, 
            request.content, 
            stream=False,
            nick_name=request.nick_name,
            nature=request.nature,
            user_role =  user_role,
            user_name = user_name,       
        )
        return {"session_id": result["session_id"], "response": result["response"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
