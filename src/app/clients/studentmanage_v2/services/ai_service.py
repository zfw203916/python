# src/app/clients/studentmanage_v2/services/ai_service.py
"""
    学生管理 AI 服务
    - 意图解析（本地 SLM）
    - SQL 执行（复用 ORM）
    - 回复生成（本地 SLM 或模板）


    # 2. 查询
curl -b cookies.txt -X POST http://127.0.0.1:8000/api/student/ai/query \
  -H "Content-Type: application/json" \
  -d '{"query":"查一下张三"}'

"""

import os
import json
from typing import Dict
from sqlalchemy.orm import Session
from ollama import Client
from ..models_db import Student
from .....shared.llm import get_chat_client, APP_DEEPSEEK_MODEL

# ========== 配置 ==========
USE_LOCAL_SLM = os.environ.get("USE_LOCAL_SLM", "true").lower() == "true"
LOCAL_MODEL = os.environ.get("LOCAL_MODEL", "qwen3.5:4b")
local_client = Client() if USE_LOCAL_SLM else None
class StudentAIService:
    """学生管理 AI 服务"""

    def __init__(self):
        self.client = local_client 
        self.model = LOCAL_MODEL
        # 加：DeepSeek 兜底客户端
        self.fallback_client = get_chat_client()
        self.fallback_model = APP_DEEPSEEK_MODEL
        self.local_available = self._check_local()

    def _check_local(self) -> bool:
        """检查本地 SLM 是否真的可用"""
        if not self.client:
            return False
        try: 
            self.client.list()
            print("✅ Ollama 可用，使用本地 SLM")
            return True
        except Exception as e:
            print(f"⚠️ Ollama 不可用: {e}")
            return False


    # ========== 1. 意图解析 ==========
    def parse_intent(self,user_input: str) ->Dict:
        """
            把自然语言解析成结构化意图
            返回：{"action": "search|stats|update|delete|unknown", ...}
        """

        prompt = f"""你是学生管理系统的意图解析器。
            用户说：{user_input}

            请提取意图和参数，返回 JSON 格式，只返回 JSON，不要任何其他文字。

            支持的意图：
            - search：查询学生（参数：name, student_id, age）
            - stats：统计（参数：无 或 class_name）
            - update：更新学生（参数：student_id 必须，name, age 可选）
            - delete：删除学生（参数：student_id 或 name）
            - unknown：无法识别

            示例1：输入"查一下张三" → {{"action":"search","name":"张三"}}
            示例2：输入"三年级有多少人" → {{"action":"stats"}}
            示例3：输入"把学号1001的年龄改成12" → {{"action":"update","student_id":"1001","age":12}}
            示例4：输入"删除李四" → {{"action":"delete","name":"李四"}}

            现在请解析：{user_input}
        """
        try:
            #本地 SLM 和 DeepSeek 两条调用链分开
            if self.local_available:
                response = self.client.chat(
                    model = self.model,
                    messages = [{"role":"user","content":prompt}],
                    format= "json"
                )
                content = response.message.content.strip()
            else:
                response = self.fallback_client.chat.completions.create(
                    model=self.fallback_model,
                    messages=[{"role": "user", "content": prompt}],
                    response_format={"type": "json_object"},  # DeepSeek 的 JSON 模式
                )
                content = response.choices[0].message.content.strip()
            return json.loads(content)
        
        except Exception as e:
            print(f"❌ 意图解析失败: {e}")    
            # 本地失败时，兜底重试一次 DeepSeek
            if self.local_available:
                try:
                    print("⚠️ 本地 SLM 异常，降级重试 DeepSeek")
                    response = self.fallback_client.chat.completions.create(
                        model=self.fallback_model,
                        messages=[{"role": "user", "content": prompt}],
                        response_format={"type": "json_object"},
                    )
                    content = response.choices[0].message.content.strip()
                except Exception as e2:
                    print(f"❌ DeepSeek 兜底也失败: {e2}")
            return {"action": "unknown"}

    # ========== 2. 执行意图 ==========
    def execute_intent(self,intent: Dict, db: Session) -> Dict:
        """
            根据意图执行数据库操作
            返回：{"success": bool, "data": [...], "message": str}
        """
        action = intent.get("action","unknown")
        try:
            if action == "search":
                return self._do_search(intent, db)
            elif action == "stats":
                return self._do_stats(intent,db)
            elif action == "update":
                return self._do_update(intent,db)
            elif action == "delete":
                return self._do_delete(intent,db)
            else:
                return {"success": False, "message": "无法理解你的意思"}
        except Exception as e:
            return {"success": False, "message": f"执行失败: {e}"}


    def _do_search(self,intent: Dict, db: Session) -> Dict:
        q = db.query(Student)
        if intent.get("name"):
            q = q.filter(Student.student_name.ilike(f"%{intent['name']}%"))
        if intent.get("student_id"):
            q = q.filter(Student.student_id.ilike(f"%{intent['student_id']}"))
        if intent.get("age"):
            q = q.filter(Student.student_age == intent["age"])

        students = q.all()
        data = [
            {"id":s.id,
             "name":s.student_name,
             "student_id":s.student_id,
             "age":s.student_age
            } 
            for s in students
        ]
        return {"success": True, "data":data, "count": len(data)}


    def _do_stats(self, intent: Dict, db: Session) -> Dict:
        total = db.query(Student).count()
        return {"success": True, "data":{"total":total}}

    def _do_update(self, intent: Dict, db: Session) -> Dict:
        student_id = intent.get("student_id")
        if not student_id:
            return {"success": False, "message": "更新需要提供学号"}
        student = db.query(Student).filter(Student.student_id == student_id).first()
        if not student:
            return {"success": False, "message": f"学号 {student_id} 不存在"}
        if intent.get("name"):
            student.student_name = intent["name"]
        if intent.get("age"):
            student.student_age = intent["age"]
        db.commit()
        return {"success": True, "message": f"学号 {student_id} 已更新"}
    
    def _do_delete(self, intent: Dict, db: Session) -> Dict:
        q = db.query(Student)
        if intent.get("student_id"):
            q = q.filter(Student.student_id == intent["student_id"])

        elif intent.get("name"):
            q = q.filter(Student.student_name == intent["name"])
        else:
            return {"success": False, "message": "删除需要提供学号或姓名"}

        student = q.first()
        if not student:
            return {"success": False, "message": "学生不存在"}
        db.delete(student)
        db.commit()
        return {"success": True, "message": f"已删除学生 {student.student_name}"}


    # ========== 3. 生成回复 ==========
    def generate_reply(self, user_input: str, result: Dict) -> str:
        """
            根据执行结果生成自然语言回复
            数据量小 → SLM 生成；数据量大 → 模板
        """
        if not result.get("success"):
            return result.get("message","操作失败")

        action = result.get("action", "")
        data = result.get("data")

        # stats 用模板，不走 SLM
        if action == "stats":
            total = data.get("total", 0) if isinstance(data, dict) else 0
            return f"当前系统共有 {total} 名学生。"
        
        # 数据量大 → 用模板
        if isinstance(data, list) and len(data) > 5 :
            return f"共找到 {len(data)} 条记录，请查看下方列表。"
        
        # 数据量小 → 让 SLM 组织语言
        prompt = f"""用户问：{user_input}
            系统查询结果：{json.dumps(result, ensure_ascii=False)}

            请用简洁自然的中文回复用户，直接说结果，不要解释过程，不要重复用户的问题。
        """
        try:
            # 本地 SLM 和 DeepSeek 两条调用链分开
            if self.local_available:
                # —— 本地 SLM ——
                response = self.client.chat(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],        
                )
                return response.message.content.strip()
            else:
                # —— DeepSeek 兜底 ——
                print("⚠️ 本地 SLM 未启用，生成回复降级到 DeepSeek")
                response = self.fallback_client.chat.completions.create(
                    model=self.fallback_model,
                    messages=[{"role": "user", "content": prompt}],
                )
                return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"❌ 生成回复失败: {e}")
            # 本地失败时兜底重试

            if self.local_available:
                try:
                    print("⚠️ 生成回复异常，降级重试 DeepSeek")
                    response = self.fallback_client.chat.completions.create(
                        model=self.fallback_model,
                        messages=[{"role": "user", "content": prompt}],
                    )
                    return response.choices[0].message.content.strip()
                except Exception as e2:
                    print(f"❌ DeepSeek 兜底也失败: {e2}")
            return f"操作完成：{json.dumps(result, ensure_ascii=False)}"