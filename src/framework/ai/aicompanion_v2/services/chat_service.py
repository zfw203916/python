# src/framework/ai/aicompanion_v2/services/chat_service.py
import os
import sys
from openai import OpenAI
from datetime import datetime
from typing import List, Dict
import uuid
from ..database import SessionModel, SessionLocal
from .vector_service import VectorService
from dotenv import load_dotenv
from pathlib import Path
from sqlalchemy.orm import Session

# 🟢 导入 Agent
from ...agent.weather.core.agent import smart_agent


load_dotenv()
# 指定 .env 文件路径（项目根目录）
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)
RAG_TOP_K = int(os.environ.get("RAG_TOP_K", 5))
RAG_THRESHOLD = float(os.environ.get("RAG_THRESHOLD", 0.5))
# 添加知识库模块到路径
kb_path = Path(__file__).parent.parent.parent / "knowledge_simple"
sys.path.insert(0, str(kb_path))
# ============ 导入知识库服务 ============
from src.framework.ai.knowledge_simple.services.document_service import DocumentService
from src.framework.ai.knowledge_simple.database import KnowledgeChunk, KnowledgeDocument

# ================================================
class ChatService:
    def __init__(self):
        self.api_key = os.environ.get("APP_DEEPSEEK_API_KEY")
        self.base_url = os.environ.get("APP_DEEPSEEK_URL")
        self.model = os.environ.get("APP_DEEPSEEK_MODEL")
        self.vector_service = VectorService()

        # 初始化知识库服务，并配置是否启用
        self.kb_service = DocumentService()
        self.enable_rag = os.environ.get("ENABLE_RAG", "true").lower() == "true"

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
            【重要】当用户询问关于文档、书籍、故事等内容时，你必须基于【参考信息】中的内容来回答。
            如果【参考信息】中有相关内容，请直接引用并回答。
            如果【参考信息】中没有相关内容，请礼貌地告诉用户。

            你必须严格遵守上述规则来回复用户。
        """

    def _get_or_create_session(self, db: Session, session_id: str, nick_name: str = None, nature: str = None) -> SessionModel:
        """获取或创建会话"""
        session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
        if not session:
            print("📝 会话不存在，创建新会话")
            session_name = (
                datetime.now().strftime("%Y-%m-%d") + "-" + str(uuid.uuid4())[:4]
            )
            # 用前端传入的值，如果没有就用默认值
            session = SessionModel(
                id=session_id,
                session_name=session_name,
                nick_name=nick_name or "小甜甜",
                nature=nature or "活泼开朗的台湾姑娘",
                extra_rules="",
                system_str="",
                messages=[],
            )
            db.add(session)
            db.commit()
            db.refresh(session)
        else:
            updated = False
            if nick_name and session.nick_name != nick_name:
                session.nick_name = nick_name
                updated = True
            if nature and session.nature != nature:
                session.nature = nature
                updated = True
            if updated:
                session.system_str = self.get_system_prompt(
                    session.nick_name, session.nature, session.extra_rules or ""
                )
                db.commit()
                db.refresh(session)
        return session

    def chat(self, session_id: str, user_message: str, stream: bool = True, nick_name: str = None, nature: str = None):
        """处理聊天请求 - 集成 Agent 工具"""
        if not self.client:
            raise ValueError("OpenAI client not initialized")

        print(f"🔍 RAG 状态: enable_rag={self.enable_rag}")
        print(f"🔍 kb_service 状态: {self.kb_service}")

        db = SessionLocal()
        try:
            # ===== 1. 获取或创建会话 =====
            session = self._get_or_create_session(db, session_id, nick_name, nature)

            # ===== 2. 生成系统提示 =====
            system_str = self.get_system_prompt(
                session.nick_name,
                session.nature,
                session.extra_rules if hasattr(session, "extra_rules") else "",
            )

            # ===== 3. 🟢 让 Agent 判断是否需要工具 =====
            agent_result = None
            use_agent = smart_agent.should_use_tools(user_message)
            print(f"🤖 Agent 判断结果: use_agent={use_agent}")

            if use_agent:
                print(f"🔧 Agent 调用工具: {user_message}")
                agent_result = smart_agent.run(user_message)
                print(f"✅ Agent 返回: {agent_result[:50]}...")
                # 把工具结果注入 system_prompt
                system_str += f"\n\n【工具调用结果】\n{agent_result}\n请基于以上工具结果回答用户。"

            # ===== 4. 保存用户消息 =====
            messages = session.messages or []
            messages.append({"role": "user", "content": user_message})
            session.messages = messages

            # ===== 5. 保存用户消息向量 =====
            saved_message = self.vector_service.save_message_with_embedding(
                db, str(session_id), "user", user_message
            )
            current_message_id = str(saved_message.id) if saved_message else None

            # ===== 6. RAG 知识库检索 =====
            if self.vector_service.enable_rag:
                rag_parts = []
                try:
                    kb_results = self.kb_service.search_similar(
                        db,
                        user_message,
                        top_k=RAG_TOP_K,
                        threshold=RAG_THRESHOLD,
                    )
                    if kb_results:
                        print(f"📚 知识库检索到{len(kb_results)}条内容")
                        for chunk, similarity in kb_results:
                            doc_title = "未知文档"
                            try:
                                from ...knowledge_simple.database import (
                                    KnowledgeDocument,
                                )

                                doc = (
                                    db.query(KnowledgeDocument)
                                    .filter(KnowledgeDocument.id == chunk.document_id)
                                    .first()
                                )
                                if doc:
                                    doc_title = doc.title
                            except Exception:
                                pass
                            rag_parts.append(f"[📄 {doc_title}]: {chunk.content}")
                            print(
                                f"  相似度: {similarity:.3f} | {chunk.content[:30]}..."
                            )
                except Exception as e:
                    print(f"⚠️ 知识库检索失败: {e}")

                similar_messages = self.vector_service.search_similar_messages(
                    db,
                    user_message,
                    session_id=None,
                    exclude_id=current_message_id,
                    limit=self.vector_service.rag_top_k,
                    threshold=self.vector_service.rag_threshold,
                )

                if similar_messages:
                    print(f"🔍 第一条: {similar_messages[0]['content'][:50]}...")
                    for msg in similar_messages:
                        role = "用户" if msg["role"] == "user" else session.nick_name
                        rag_parts.append(f"[{role}]:{msg['content']}")
                    rag_context = "\n\n【参考历史对话】\n" + "\n".join(rag_parts)
                    system_str = system_str + rag_context
                    print(f"🔍 RAG召回{len(similar_messages)}条相似消息 ")
                    for msg in similar_messages:
                        print(
                            f"  相似度:{msg['similarity']:.3f} | {msg['content'][:30]}..."
                        )
                else:
                    print("⚠️ RAG 没有检索到相关内容")

                if rag_parts:
                    rag_context = (
                        "\n\n【参考信息 - 请基于以下内容回答】\n"
                        + "\n---\n".join(rag_parts)
                    )
                    system_str = system_str + rag_context
                    print(f"🔍 RAG共召回 {len(rag_parts)} 条参考信息")
                else:
                    print("⚠️ RAG 没有检索到任何相关内容")

            # ===== 7. 提交数据库 =====
            db.commit()
            db.refresh(session)

            # ===== 8. 准备 API 请求 =====
            api_messages = [{"role": "system", "content": system_str}, *messages]

            # ===== 9. 调用 LLM =====
            response = self.client.chat.completions.create(
                model=self.model,
                messages=api_messages,
                stream=stream,
            )

            session_id_str = str(session.id)
            nick_name = session.nick_name
            nature = session.nature
            extra_rules = session.extra_rules

            db.close()

            if stream:
                return self._handle_stream_response(
                    session_id_str, messages, response, nick_name, nature, extra_rules
                )
            else:
                return self._handle_non_stream_response(
                    session_id_str, messages, response, nick_name, nature, extra_rules
                )

        except Exception as e:
            db.rollback()
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
                    }

        messages.append({"role": "assistant", "content": full_response})

        db = SessionLocal()
        try:
            session = (
                db.query(SessionModel).filter(SessionModel.id == session_id).first()
            )
            if session:
                session.messages = messages
                if session.session_name.startswith("20") and len(messages) >= 2:
                    try:
                        summary_input = messages[:4]
                        summary_prompt = f"请根据以下对话，用不超过8个字总结核心主题，不要加标点，不要带引号：\n{summary_input}"
                        summary_resp = self.client.chat.completions.create(
                            model=self.model,
                            messages=[{"role": "user", "content": summary_prompt}],
                            max_tokens=20,
                            temperature=0.3,
                        )
                        new_title = summary_resp.choices[0].message.content.strip()
                        if new_title and len(new_title) <= 15:
                            session.session_name = new_title
                    except Exception as summary_error:
                        print(f"⚠️ 自动总结标题失败，保留原标题: {summary_error}")

                db.commit()
                db.refresh(session)

                self.vector_service.save_message_with_embedding(
                    db, session_id, "assistant", full_response
                )
        finally:
            db.close()

        yield {
            "type": "complete",
            "full_response": full_response,
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

        db = SessionLocal()
        try:
            session = (
                db.query(SessionModel).filter(SessionModel.id == session_id).first()
            )
            if session:
                session.messages = messages
                if session.session_name.startswith("20") and len(messages) >= 2:
                    try:
                        summary_input = messages[:4]
                        summary_prompt = f"请根据以下对话，用不超过8个字总结核心主题，不要加标点，不要带引号：\n{summary_input}"
                        summary_resp = self.client.chat.completions.create(
                            model=self.model,
                            messages=[{"role": "user", "content": summary_prompt}],
                            max_tokens=20,
                            temperature=0.3,
                        )
                        new_title = summary_resp.choices[0].message.content.strip()
                        if new_title and len(new_title) <= 15:
                            session.session_name = new_title
                    except Exception as summary_error:
                        print(f"⚠️ 自动总结标题失败，保留原标题: {summary_error}")
                db.commit()
                db.refresh(session)

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


    def get_stats(self):
        # 知识做调试用
        db = SessionLocal()
        doc_count = db.query(KnowledgeDocument).count()
        chunk_count = db.query(KnowledgeChunk).count()
        print(f"文档数量: {doc_count}")
        print(f"分块数量: {chunk_count}")