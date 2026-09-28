# src/app/clients/studentmanage_v2/routers/students_ai.py
"""
    路由，接口。让 AI介入。只有增加了路由，才能暴露接口才能变成 API接口调用。
"""

from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session
from typing import Annotated
from pydantic import BaseModel

from ..database import get_db
from ..services.ai_service import StudentAIService
from .auth import require_login

router = APIRouter(prefix="/api/student/ai", tags=["student-ai"])
ai_service = StudentAIService()


class AIQueryRequest(BaseModel):
    query: str


# def require_login(request: Request):
#     """依赖：要求登录"""
#     if not request.session.get("logged_in"):
#         raise HTTPException(status_code=401, detail="未登录")
#     return request.session.get("username")


@router.post("/query")  #没有这个就不能请求。
def ai_query(
    data: AIQueryRequest,
    username: Annotated[str, Depends(require_login)],
    request:Request, # 拿 session
    db: Annotated[Session, Depends(get_db)],
):
    """AI 自然语言查询学生"""
    if not data.query or not data.query.strip():
        raise HTTPException(status_code=400, detail="查询内容不能为空")

    # 从 session 拿 role
    user_role  = request.session.get("role", "viewer")
    # 1. 解析意图（自然语言 → 结构化 dict）
    intent = ai_service.parse_intent(data.query.strip())
    print(f"🎯 意图解析: {intent}, 用户角色: {user_role}")

    if intent.get("action") == "unknown":
        return {
            "reply": "抱歉，我没理解你的意思，请换个说法。",
            "intent": intent,
            "data": None,
        }

    # 2. 执行意图,（dict → 数据库操作结果）,把 role 传给 execute_intent
    result = ai_service.execute_intent(intent, db, user_role = user_role)
    result["action"] = intent["action"]
    
    # 3. 生成回复
    reply = ai_service.generate_reply(data.query, result)

    return {
        "reply": reply,
        "intent": intent,
        "data": result.get("data"),
        "success": result.get("success", False),
    }
