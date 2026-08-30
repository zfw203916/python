# my-test-framework/src/framework/ai/aicompanion_v2/routers/sessions.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import uuid
from datetime import datetime

from ..database import SessionModel, get_db
from ..models import SessionCreate, SessionUpdate, SessionResponse
from ..services.chat_service import ChatService
from typing import Annotated

router = APIRouter(prefix="/api/sessions", tags=["sessions"])
chat_service = ChatService()

@router.get("/", response_model=List[SessionResponse])
#async def get_sessions(db: Session = Depends(get_db)):
async def get_sessions(db: Annotated[Session, Depends(get_db)]):
    """获取所有会话"""
    sessions = db.query(SessionModel).order_by(SessionModel.updated_at.desc()).all()
    return [
        {
            "id": str(s.id),
            "session_name": s.session_name,
            "nick_name": s.nick_name,
            "nature": s.nature,
            "messages": s.messages or [],
            "created_at": s.created_at,
            "updated_at": s.updated_at
        } 
        for s in sessions
    ]

@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(session_id:str,db: Session = Depends(get_db)):
    """获取特定会话"""
    session = db.query(SessionModel).filter(SessionModel.id==uuid.UUID(session_id)).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return {
        "id": str(session.id),
            "session_name": session.session_name,
            "nick_name": session.nick_name,
            "nature": session.nature,
            "messages": session.messages or [],
            "created_at": session.created_at,
            "updated_at": session.updated_at
        }

@router.post("/", response_model=dict)
async def create_session(session_create: SessionCreate):
    """创建新会话"""
    print(f"=== DEBUG:收到创建会话请求 ===")
    print(f"请求数据: {session_create}")
    session_id = chat_service.create_session(
        session_create.nick_name,
        session_create.nature,
        session_create.extra_rules
    )
    print(f"返回的 session_id: {session_id}")
    return {"session_id":session_id}


@router.put("/{session_id}", response_model=dict)
async def update_session(session_id:str,session_update: SessionUpdate, db: Session = Depends(get_db)):
    """更新会话设置"""
    session = db.query(SessionModel).filter(SessionModel.id==uuid.UUID(session_id)).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session_update.nick_name is not None:
        session.nick_name = session_update.nick_name
    if session_update.nature is not None:
        session.nature = session_update.nature
    if session_update.extra_rules is not None:
        session.extra_rules = session_update.extra_rules

    # 更新系统提示
    system_str = chat_service.get_system_prompt(
        session.nick_name, 
        session.nature,
        getattr(session, 'extra_rules', '')
    )
    session.system_str = system_str
    print(f"看一下这个数据：{session.system_str}")
    db.commit()
    return {"message": "Session updated successfully"}


@router.delete("/{session_id}")
async def delete_session(session_id:str, db: Session = Depends(get_db)):
    """删除会话"""
    session = db.query(SessionModel).filter(SessionModel.id==uuid.UUID(session_id)).first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    db.delete(session)
    db.commit()
    return {"message": "Session delete successfully"}