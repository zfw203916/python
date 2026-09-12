# my-test-framework/src/framework/ai/aicompanion_v2/routers/sessions.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import Text
from typing import List
import uuid, json
from ..database import SessionModel, get_db
from ..models import SessionCreate, SessionUpdate, SessionResponse
from ..services.chat_service import ChatService
from typing import Annotated

router = APIRouter(prefix="/api/sessions", tags=["sessions"])
chat_service = ChatService()


@router.get("/", response_model=List[SessionResponse])
async def get_sessions(db: Annotated[Session, Depends(get_db)]):
    """获取所有会话"""

    sessions = db.query(SessionModel).order_by(
        SessionModel.is_pinned.desc(),
        SessionModel.updated_at.desc()
        ).all()
    return [
        {
            "id": str(s.id),
            "session_name": s.session_name,
            "nick_name": s.nick_name,
            "nature": s.nature,
            "messages": s.messages or [],
            "extra_rules": s.extra_rules,
            "created_at": s.created_at,
            "updated_at": s.updated_at,
            "is_pinned": s.is_pinned
        }
        for s in sessions
    ]

  
@router.get("/search")
async def search_sessions(q: str, db: Annotated[Session, Depends(get_db)]):
    """搜索会话（按标题或消息内容模糊搜索）"""
    if not q or not q.strip():
        return []
  
    unicode_q = json.dumps(q.strip(), ensure_ascii=True)[1:-1]
    search_term = f"%{unicode_q}%"
    # 1. 按 session_name 搜索
    sessions_by_name =  db.query(SessionModel).filter(SessionModel.session_name.ilike(f"%{q.strip()}%")).all() 
    # 2. 按 messages 里的内容搜索
    sessions_by_msg = db.query(SessionModel).filter(SessionModel.messages.cast(Text).ilike(search_term)).all()
    # 合并结果并去重
    seen_ids = set()
    results = []
    for s in sessions_by_name + sessions_by_msg:
        if s.id not in seen_ids:
            seen_ids.add(s.id)
            results.append({
                "id": str(s.id),
                "session_name": s.session_name,
                "nick_name": s.nick_name,
                "nature": s.nature,
                "messages" : s.messages or [],
                "extra_rules": s.extra_rules,
                "created_at": s.created_at,
                "updated_at": s.updated_at,
                "is_pinned": s.is_pinned
                })
    # 按更新时间排序      
    results.sort(key=lambda x: x["updated_at"],reverse=True)
    print(f"🚨 搜索完成，最终返回 {len(results)} 个会话")
    return results

@router.post("/{session_id}/pin")
async def pin_session(session_id: str,db: Annotated[Session, Depends(get_db)]):
    """# 置顶接口"""
    session = db.query(SessionModel).filter(SessionModel.id == uuid.UUID(session_id)).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    session.is_pinned = True
    db.commit()
    db.refresh(session)
    return {"message":"会话已置顶", "is_pinned": True}

@router.post("/{session_id}/unpin")
async def unpin_session(session_id: str,db: Annotated[Session, Depends(get_db)]):
    """#取消置顶"""
    session = db.query(SessionModel).filter(SessionModel.id == uuid.UUID(session_id)).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    session.is_pinned = False
    db.commit()
    db.refresh(session)
    return {"message":"已取消置顶", "is_pinned": False}

  
    

@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str, db: Annotated[Session, Depends(get_db)]):
    """获取特定会话"""
    session = (
        db.query(SessionModel).filter(SessionModel.id == uuid.UUID(session_id)).first()
    )
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return {
        "id": str(session.id),
        "session_name": session.session_name,
        "nick_name": session.nick_name,
        "nature": session.nature,
        "extra_rules": session.extra_rules,
        "messages": session.messages or [],
        "created_at": session.created_at,
        "updated_at": session.updated_at,
        "is_pinned": session.is_pinned
    }


@router.post("/", response_model=dict)
async def create_session(session_create: SessionCreate):
    """创建新会话"""
    session_id = chat_service.create_session(
        session_create.nick_name, session_create.nature, session_create.extra_rules
    )
    return {"session_id": session_id}


@router.put("/{session_id}", response_model=dict)
async def update_session(
    session_id: str, session_update: SessionUpdate, db: Annotated[ Session,Depends(get_db)]):
    """更新会话设置"""
    session = (
        db.query(SessionModel).filter(SessionModel.id == uuid.UUID(session_id)).first()
    )
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
        session.nick_name, session.nature, session.extra_rules
    )
    session.system_str = system_str
    db.commit()
    db.refresh(session)
    return {"message": "Session updated successfully"}


@router.delete("/{session_id}")
async def delete_session(session_id: str, db: Annotated[Session, Depends(get_db)]):
    """删除会话"""
    session = (
        db.query(SessionModel).filter(SessionModel.id == uuid.UUID(session_id)).first()
    )

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    db.delete(session)
    db.commit()
    return {"message": "Session delete successfully"}
