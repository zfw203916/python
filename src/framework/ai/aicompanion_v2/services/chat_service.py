import os
from openai import OpenAI
from datetime import datetime
from typing import List, Dict, Any, Optional
import uuid
import json
from ..database import SessionModel, SessionLocal
from ..models import SystemSettings
from .vector_service import VectorService

class ChatService:
    def __init__(self):
        self.api_key = os.environ.get("APP_DEEPSEEK_API_KEY")
        self.base_url = os.environ.get("APP_DEEPSEEK_URL")
        self.model = os.environ.get("APP_DEEPSEEK_MODEL", "deepseek-chat")
        self.vector_service = VectorService()
        if self.api_key:
            self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        else:
            self.client = None


    def get_system_prompt(self, nick_name: str, nature: str, extra_rules: str) -> str:
        """生成系统提示"""
        rules = extra_rules if extra_rules else """
            1、每次只回1条消息.
            2、禁止任何场景或状态描述性文字.
            3、匹配用户的语言.
            4、回复简短，像微信聊天一样.
            5、有需要的话可以用🩷 💞等emoji表情.
            6、用符合伴侣性格的方式对话.
            7、回复的内容，要充分体现伴侣的性格特征.
        """
        return f"""
            你叫{nick_name}，现在是用户的真实伴侣，请完全代入伴侣角色。
            规则：
            {rules}
            伴侣性格：
            - {nature}
            你必须严格遵守上述规则来回复用户。
        """
    
    def chat(self, session_id: str, user_message: str, stream: bool = True):
        """处理聊天请求"""
        if not self.client:
            raise ValueError("OpenAI client not initialized")

        # 获取会话信息
        db = SessionLocal()
        try:
            session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
            if not session:
                # 创建新会话
                session_name = datetime.now().strftime("%Y%m%d%H%M%S%f")
                session = SessionModel(
                    id=session_id,
                    session_name=session_name,
                    nick_name="小甜甜",
                    nature="活泼开朗的台湾姑娘",
                    extra_rules="",
                    system_str="",
                    messages=[]
                )
                db.add(session)
                db.commit()
                db.refresh(session)
            
            # 更新系统提示
            system_str = self.get_system_prompt(
                session.nick_name,
                session.nature,
                session.extra_rules if hasattr(session, 'extra_rules') else ""
            )
            session.system_str = system_str
            
            # 添加用户消息
            messages = session.messages or []
            messages.append({"role": "user", "content": user_message})
            
            # 保存用户消息到数据库
            session.messages = messages
            db.commit()
            db.refresh(session)
            
            # 保存消息向量（如果支持）
            self.vector_service.save_message_with_embedding(db, str(session.id), "user", user_message)
            
            # 准备API请求消息
            api_messages = [
                {"role": "system", "content": system_str},
                *messages
            ]
            
            # 调用API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=api_messages,
                stream=stream,
            )
            
            # 保存session_id用于后续处理
            session_id_str = str(session.id)
            nick_name = session.nick_name
            nature = session.nature
            extra_rules = session.extra_rules
            
            # 关闭数据库会话，因为流式响应可能会持续很长时间
            db.close()
            
            if stream:
                return self._handle_stream_response(session_id_str, messages, response, nick_name, nature, extra_rules)
            else:
                # 非流式响应，需要重新打开数据库会话
                return self._handle_non_stream_response(session_id_str, messages, response, nick_name, nature, extra_rules)
                
        except Exception as e:
            db.close()
            raise e

    def _handle_stream_response(self, session_id: str, messages: List[Dict], response, nick_name: str, nature: str, extra_rules: str):
        """处理流式响应"""
        full_response = ""
        thinking_content = ""
        
        for chunk in response:
            if chunk.choices and chunk.choices[0].delta is not None:
                delta = chunk.choices[0].delta
                
                if hasattr(delta, "reasoning_content") and delta.reasoning_content:
                    thinking_content += delta.reasoning_content
                
                if hasattr(delta, "content") and delta.content is not None:
                    full_response += delta.content
                    yield {
                        "type": "chunk",
                        "content": delta.content,
                        "full_response": full_response,
                        "thinking": thinking_content
                    }
        
        # 流结束后，保存完整的响应到数据库
        messages.append({"role": "assistant", "content": full_response})
        
        # 重新打开数据库会话保存数据
        db = SessionLocal()
        try:
            session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
            if session:
                session.messages = messages
                db.commit()
                db.refresh(session)
                
                # 保存助手消息向量
                self.vector_service.save_message_with_embedding(db, session_id, "assistant", full_response)
        finally:
            db.close()
        
        yield {
            "type": "complete",
            "full_response": full_response,
            "thinking": thinking_content,
            "session_id": session_id
        }

    def _handle_non_stream_response(self, session_id: str, messages: List[Dict], response, nick_name: str, nature: str, extra_rules: str):
        """处理非流式响应"""
        ai_response = response.choices[0].message.content
        messages.append({"role": "assistant", "content": ai_response})
        
        # 保存到数据库
        db = SessionLocal()
        try:
            session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
            if session:
                session.messages = messages
                db.commit()
                db.refresh(session)
                
                # 保存助手消息向量
                self.vector_service.save_message_with_embedding(db, session_id, "assistant", ai_response)
        finally:
            db.close()
        
        return {
            "response": ai_response,
            "session_id": session_id
        }

    def create_session(self, nick_name: str, nature: str, extra_rules: str = "") -> str:
        """创建新会话"""
        db = SessionLocal()
        try:
            session_name = datetime.now().strftime("%Y%m%d%H%M%S%f")
            session_id = uuid.uuid4()
            system_str = self.get_system_prompt(nick_name, nature, extra_rules)
            
            session = SessionModel(
                id=session_id,
                session_name=session_name,
                nick_name=nick_name,
                nature=nature,
                extra_rules=extra_rules,
                system_str=system_str,
                messages=[]
            )
            db.add(session)
            db.commit()
            db.refresh(session)
            return str(session.id)
        finally:
            db.close()
        