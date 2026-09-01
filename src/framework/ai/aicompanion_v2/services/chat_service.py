import os
from openai import OpenAI
from datetime import datetime
from typing import List, Dict
import uuid
from ..database import SessionModel, SessionLocal
from .vector_service import VectorService
from dotenv import load_dotenv
from pathlib import Path


# 指定 .env 文件路径（项目根目录）
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)


class ChatService:
    def __init__(self):
        self.api_key = os.environ.get("APP_DEEPSEEK_API_KEY")
        self.base_url = os.environ.get("APP_DEEPSEEK_URL")
        self.model = os.environ.get("APP_DEEPSEEK_MODEL")
        self.vector_service = VectorService()
        if self.api_key:
            self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        else:
            self.client = None

    def get_system_prompt(self, nick_name: str, nature: str, extra_rules: str) -> str:
        """生成系统提示"""
        rules = (
            extra_rules
            if extra_rules
            else """
                1、每次只回1条消息.
                2、禁止任何场景或状态描述性文字.
                3、匹配用户的语言.
                4、回复简短，像微信聊天一样.
                5、有需要的话可以用🩷 💞等emoji表情.
                6、用符合伴侣性格的方式对话.
                7、回复的内容，要充分体现伴侣的性格特征.
            """
        )
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
            # ===== 1. 获取或创建会话 =====
            session = (
                db.query(SessionModel).filter(SessionModel.id == session_id).first()
            )
            if not session:
                # 创建新会话
                session_name = (
                    datetime.now().strftime("%Y-%m-%d") + "-" + str(uuid.uuid4())[:4]
                )
                session = SessionModel(
                    id=session_id,
                    session_name=session_name,
                    nick_name="小甜甜",
                    nature="活泼开朗的台湾姑娘",
                    extra_rules="",
                    system_str="",
                    messages=[],
                )
                db.add(session)
                db.commit()
                db.refresh(session)

            # 保存消息向量（如果支持），这个新增功能。貌似deepseek不支持这个字段，只有openAI支持。
            # 在 chat 方法中，准备 API 请求消息之前添加
            # === 新增：RAG检索增强 ===
            # 检索相似历史消息（当前会话 + 全局）

            # ===== 2. 生成系统提示 =====
            system_str = self.get_system_prompt(
                session.nick_name,
                session.nature,
                session.extra_rules if hasattr(session, "extra_rules") else "",
            )
            session.system_str = system_str

            # ===== 3. 添加用户消息 =====
            messages = session.messages or []
            messages.append({"role": "user", "content": user_message})

            # 保存用户消息到数据库
            session.messages = messages
            db.commit()
            db.refresh(session)

            # ===== 4. 保存用户消息向量=====
            saved_message = self.vector_service.save_message_with_embedding(
                db, str(session_id), "user", user_message
            )
            current_message_id = str(saved_message.id) if saved_message else None

            # ===== 5. RAG检索增强 =====
            rag_context = ""
            if self.vector_service.enable_rag:
                # 检索相似历史消息
                similar_messages = self.vector_service.search_similar_messages(
                    db,
                    user_message,
                    # session_id=str(session_id),
                    session_id=None,  # ← 关键修复：None = 跨会话检索
                    exclude_id=current_message_id,
                    limit=self.vector_service.rag_top_k,
                    threshold=self.vector_service.rag_threshold,
                )
                if similar_messages:
                    # 构建RAG上下文
                    rag_parts = []
                    for msg in similar_messages:
                        role = "用户" if msg["role"] == "user" else session.nick_name
                        rag_parts.append(f"[{role}]:{msg['content']}")
                    rag_context = "\n\n【参考历史对话】\n" + "\n".join(rag_parts)
                    # 注入到系统提示中
                    system_str = system_str + rag_context
                    # 🟢 调试日志
                    print(f"🔍 RAG召回{len(similar_messages)}条相似消息 ")
                    for msg in similar_messages:
                        print(
                            f"  相似度:{msg['similarity']:.3f} | {msg['content'][:30]}..."
                        )

            # ===== 6. 准备API请求 =====
            api_messages = [{"role": "system", "content": system_str}, *messages]

            # ===== 7. 调用LLM =====
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
                return self._handle_stream_response(
                    session_id_str, messages, response, nick_name, nature, extra_rules
                )
            else:
                # 非流式响应，需要重新打开数据库会话
                return self._handle_non_stream_response(
                    session_id_str, messages, response, nick_name, nature, extra_rules
                )

        except Exception as e:
            db.close()
            raise e

    def _handle_stream_response(
        self,
        session_id: str,
        messages: List[Dict],
        response,
        nick_name: str,
        nature: str,
        extra_rules: str,
    ):
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
                        # "thinking": thinking_content,
                    }

        # 流结束后，保存完整的响应到数据库
        messages.append({"role": "assistant", "content": full_response})

        # 重新打开数据库会话保存数据
        db = SessionLocal()
        try:
            session = (
                db.query(SessionModel).filter(SessionModel.id == session_id).first()
            )
            if session:
                session.messages = messages
                # ==================== 🆕 新增：AI自动总结标题 ====================
                # 缺点：会额外消耗一次 API 调用。
                if session.session_name.startswith("20") and len(messages) >= 2:
                    # 提取最近的消息用于总结（比如前2条）
                    try:
                        summary_input = messages[:4]
                        summary_prompt = f"请根据以下对话，用不超过8个字总结核心主题，不要加标点，不要带引号：\n{summary_input}"
                        # 调用大模型总结LLM
                        summary_resp = self.client.chat.completions.create(
                            model=self.model,
                            messages=[{"role": "user", "content": summary_prompt}],
                            max_tokens=20,
                            temperature=0.3,
                        )
                        new_title = summary_resp.choices[0].message.content.strip()

                        # 如果总结成功且非空，更新标题
                        if new_title and len(new_title) <= 15:
                            session.session_name = new_title
                    except Exception as summary_error:
                        # 总结失败不要紧，保持原标题（日期），不报错
                        print(f"⚠️ 自动总结标题失败，保留原标题: {summary_error}")

                db.commit()
                db.refresh(session)

                # 保存助手消息向量
                self.vector_service.save_message_with_embedding(
                    db, session_id, "assistant", full_response
                )
        finally:
            db.close()

        yield {
            "type": "complete",
            "full_response": full_response,
            # "thinking": thinking_content,
            "session_id": session_id,
        }

    def _handle_non_stream_response(
        self,
        session_id: str,
        messages: List[Dict],
        response,
        nick_name: str,
        nature: str,
        extra_rules: str,
    ):
        """处理非流式响应"""
        ai_response = response.choices[0].message.content
        messages.append({"role": "assistant", "content": ai_response})

        # 保存到数据库
        db = SessionLocal()
        try:
            session = (
                db.query(SessionModel).filter(SessionModel.id == session_id).first()
            )
            if session:
                session.messages = messages
                # ==================== 🆕 新增：AI自动总结标题 ====================
                # 缺点：会额外消耗一次 API 调用。
                if session.session_name.startswith("20") and len(messages) >= 2:
                    # 提取最近的消息用于总结（比如前2条）
                    try:
                        summary_input = messages[:4]
                        summary_prompt = f"请根据以下对话，用不超过8个字总结核心主题，不要加标点，不要带引号：\n{summary_input}"
                        # 调用大模型总结LLM
                        summary_resp = self.client.chat.completions.create(
                            model=self.model,
                            messages=[{"role": "user", "content": summary_prompt}],
                            max_tokens=20,
                            temperature=0.3,
                        )
                        new_title = summary_resp.choices[0].message.content.strip()

                        # 如果总结成功且非空，更新标题
                        if new_title and len(new_title) <= 15:
                            session.session_name = new_title
                    except Exception as summary_error:
                        # 总结失败不要紧，保持原标题（日期），不报错
                        print(f"⚠️ 自动总结标题失败，保留原标题: {summary_error}")
                db.commit()
                db.refresh(session)

                # 保存助手消息向量
                self.vector_service.save_message_with_embedding(
                    db, session_id, "assistant", ai_response
                )
        finally:
            db.close()

        return {"response": ai_response, "session_id": session_id}

    def create_session(self, nick_name: str, nature: str, extra_rules: str = "") -> str:
        """创建新会话"""
        db = SessionLocal()
        try:
            session_name = (
                datetime.now().strftime("%Y-%m-%d") + "-" + str(uuid.uuid4())[:4]
            )
            session_id = uuid.uuid4()
            system_str = self.get_system_prompt(nick_name, nature, extra_rules)

            session = SessionModel(
                id=session_id,
                session_name=session_name,
                nick_name=nick_name,
                nature=nature,
                extra_rules=extra_rules,
                system_str=system_str,
                messages=[],
            )
            db.add(session)
            db.commit()
            db.refresh(session)
            return str(session.id)
        finally:
            db.close()
