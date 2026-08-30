# my-test-framework/src/framework/ai/aicompanion_v2/models.py
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid
"""
MessageRequest	接收用户输入	API请求体（用户发消息）
MessageResponse	返回单条消息	获取某条消息的详情
SessionCreate	接收创建配置	创建新会话时的参数
SessionUpdate	接收更新配置	更新会话设置时的参数
SessionResponse	返回完整会话	获取会话详情
ChatResponse	返回AI回复	非流式聊天的响应
SystemSettings	表示系统配置	内部传递配置数据



"""
class MessageRequest(BaseModel):
    content: str
    session_id: Optional[str] = None 

class MessageResponse(BaseModel):
    role: str
    content: str
    timestamp: Optional[datetime] = None

class SessionCreate(BaseModel):
    nick_name: Optional[str] = "小甜甜"
    nature: Optional[str] = "活泼开朗的台湾姑娘"
    extra_rules: Optional[str] = ""

class SessionUpdate(BaseModel):
    nick_name: Optional[str] = None
    nature: Optional[str] = None
    extra_rules: Optional[str] = None

class SessionResponse(BaseModel):
    id: str
    session_name: str
    nick_name: str
    nature: str
    messages: List[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime

class ChatResponse(BaseModel):
    session_id: str
    message: str
    response: str
    thinking: Optional[str] = None

class SystemSettings(BaseModel):
    nick_name: str
    nature: str
    extra_rules: str
    system_str: str