# src/app/clients/studentmanage_v2/routers/students_ai.py
"""
    路由，接口。
"""
from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session
from typing import Annotated
from pydantic import BaseModel

from ..database import get_db
from ..services.ai_service import StudentAIService
router = APIRouter(prefix="/api/student/ai",tags=["student-ai"])
ai_service = StudentAIService()

class AIQueryRequest(BaseModel):
    query: str

def require_login(request: Request):
    """依赖：要求登录"""
    if not request.session.get("logged_in"):
        raise HTTPException(status_code=401, detail="未登录")
    return request.session.get("username")


@router.post("/query")
def ai_query(
    data: AIQueryRequest,
    username: Annotated[str, Depends(require_login)],
    db: Annotated[Session, Depends(get_db)],
):
    """AI 自然语言查询学生"""
    if not data.query or not data.query.strip():
        raise HTTPException(status_code=400, detail="查询内容不能为空")

    # 1. 解析意图（自然语言 → 结构化 dict）
    intent = ai_service.parse_intent(data.query.strip())
    print(f"🎯 意图解析: {intent}")

    if intent.get("action") == "unknown":
        return {"reply":"抱歉，我没理解你的意思，请换个说法。","intent":intent,"data":None}
    
    # 2. 执行意图,（dict → 数据库操作结果）
    result = ai_service.execute_intent(intent,db)
    result["action"] = intent["action"]

    # 3. 生成回复
    reply = ai_service.generate_reply(data.query,result)

    return{
        "reply": reply,
        "intent": intent,
        "data": result.get("data"),
        "success": result.get("success",False),
    }