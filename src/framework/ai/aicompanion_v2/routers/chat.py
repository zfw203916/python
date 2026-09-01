# my-test-framework/src/framework/ai/aicompanion_v2/routers/chat.py

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import json
import uuid

from ..models import MessageRequest
from ..services.chat_service import ChatService

router = APIRouter(prefix="/api/chat", tags=["chat"])
chat_service = ChatService()


@router.post("/stream")
async def chat_stream(request: MessageRequest):
    """流式聊天"""
    session_id = request.session_id or str(uuid.uuid4())

    try:
        generator = chat_service.chat(session_id, request.content, stream=True)

        def stream_generator():
            try:
                for chunk in generator:
                    yield f"data: {json.dumps(chunk,ensure_ascii=False)}\n\n"
            except Exception as e:
                error_data = {"type": "error", "message": str(e)}
                yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"

        return StreamingResponse(
            stream_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",  # 禁用Nginx缓冲
            },
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/non-stream")
async def chat_non_stream(request: MessageRequest):
    """非流式聊天"""
    session_id = request.session_id or str(uuid.uuid4())
    try:
        result = chat_service.chat(session_id, request.content, stream=False)
        return {"session_id": result["session_id"], "response": result["response"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
