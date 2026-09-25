# src/framework/ai/agent/weather/core/agent_native.py
"""
    原生 Agent 实现（不用 LangChain/LangGraph)
"""
import json
from typing import List, Dict, Callable
from openai import OpenAI

from ......shared.llm import get_chat_client, APP_DEEPSEEK_MODEL
from ..tools.weather_native import get_weather
from ..tools.date_native import get_current_date
from ..tools.student_native import get_student_info,update_student, delete_student # 介入学生管理系统。
import os
from ollama import Client

"""
    原生 Agent 实现（纯 OpenAI SDK、无 LangChain)

    核心原理：
    1. 定义工具（函数）
    2. 生成工具 JSON Schema
    3. 调用 LLM(带 tools)
    4. 解析 tool_calls
    5. 执行工具
    6. 回喂结果给 LLM
    7. 循环直到 LLM 不再调工具
"""

# 判断是否用本地模型
USE_LOCAL_INTENT = os.environ.get("USE_LOCAL_INTENT","false").lower() == "true"
LOCAL_MODEL = os.environ.get("LOCAL_MODEL","qwen3.5:4b")
local_client = Client() if USE_LOCAL_INTENT else None


# ========== 1. 工具注册表 ==========
# 工具名 → 函数
TOOLS_NATIVE: Dict[str, callable] = {
    "get_weather": get_weather,
    "get_current_date": get_current_date,
    "get_student_info": get_student_info,
    "update_student": update_student,   
    "delete_student": delete_student, 
}


# ========== 2. 工具 JSON Schema（给 LLM 看的） ==========
TOOLS_SCHEMA_NATIVE: List[Dict] = [{
    "type": "function",
    "function":{
        "name":"get_weather",
        "description":"查询指定城市的天气情况,温度,风向等细节", # 这是喂给AI的。
        "parameters":{ # 这是喂给AI的。喂给 AI 的是 tool_definitions 里的 description 和 parameters。
            "type": "object",
            "properties":{
                "city":{
                    "type": "string",
                    "description": "城市名称，如 '北京'、'上海'", 
                }
            },
            "required": ["city"],
        }
    }
},
{
    "type": "function",
    "function":{
        "name":"get_current_date",
        "description":"获取当前日期、时间和星期几。当用户问今天几号、现在几点、星期几时使用。", # 这是喂给AI的。
        "parameters":{ # 这是喂给AI的。喂给 AI 的是 tool_definitions 里的 description 和 parameters。
            "type": "object",
            "properties":{},
            "required": [],
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "get_student_info",
        "description": "查询学生信息。当用户询问学生的资料、年龄、学号时使用。可以按姓名或学号查询。",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "学生姓名（模糊匹配）"},
                "student_id": {"type": "string", "description": "学号（精确匹配）"},
            },
            "required": [],
        },
    },
},
    #更新学生
    {
        "type": "function",
        "function": {
            "name": "update_student",
            "description": "更新学生信息。当用户要求修改学生姓名或年龄时使用。必须提供 student_id 或 name 定位学生。",
            "parameters": {
                "type": "object",
                "properties": {
                    "student_id": {"type": "string", "description": "学号（用于定位）"},
                    "name": {"type": "string", "description": "原姓名（用于定位，student_id 为空时使用）"},
                    "new_name": {"type": "string", "description": "新姓名（可选）"},
                    "new_age": {"type": "integer", "description": "新年龄（可选）"},
                },
                "required": [],
            },
        },
    },
    # 删除学生
    {
        "type": "function",
        "function": {
            "name": "delete_student",
            "description": "删除学生。当用户要求删除某个学生时使用。必须提供 student_id 或 name。",
            "parameters": {
                "type": "object",
                "properties": {
                    "student_id": {"type": "string", "description": "学号"},
                    "name": {"type": "string", "description": "姓名"},
                },
                "required": [],
            },
        },
    },
]

# ========== 3. 原生 Agent ==========
class NativeWeatherAgent:
    """原生天气 Agent"""
    def __init__(self):
        self.client = get_chat_client()
        self.model = APP_DEEPSEEK_MODEL
        self.tools = TOOLS_NATIVE
        self.tool_schemas = TOOLS_SCHEMA_NATIVE 
        self.system_prompt = """
            你是一个智能助手，可以调用工具来回答用户的问题。
            可用工具：
                - get_weather：查询指定城市的天气情况、温度、风向
                - get_current_date：获取当前日期、时间和星期几
                - get_student_info：查询学生信息（姓名、学号、年龄）
                - update_student：更新学生信息（改姓名、改年龄）
                - delete_student：删除学生

            调用规则：
            1. 用户问天气 → 用 get_weather
            2. 用户问日期、时间、星期 → 用 get_current_date
            3. 用户问学生资料/年龄/学号 → 用 get_student_info
            4. 用户要改学生信息（"把张三的年龄改成12"）→ 用 update_student
            5. 用户要删除学生（"删除李四"）→ 用 delete_student
            6. 其他问题 → 直接回答

            【重要】删除操作很危险，如果用户明确说"删除"才调用 delete_student。
            回复要简洁、准确，用中文回答。
        """
    def _execute_tool(self,name: str, args: Dict) -> str:
        """执行工具"""
        # 先检查工具名是否在注册表里，防止 LLM 幻觉出不存在的工具。
        if name not in self.tools:
            return f"未知工具: {name}"

        try:
            func  =  self.tools[name]
            results = func(**args)
            return results
        except Exception as e:
            return f"工具执行失败: {e}"

    def run(self, user_message: str, max_iterations: int = 5) -> str:
        """
            运行 Agent
            
            Args:
                user_message: 用户消息
                max_iterations: 最大循环次数（防止死循环）
            
            Returns:
                AI 最终回复
        """
        # 初始化消息历史
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_message},
        ]
        # 循环调用
        for iteration in range(max_iterations):
            print(f"🔄 第 {iteration+1}轮")

            # 调用 LLM
            """
                self.client          # OpenAI 客户端实例
                .chat            # 聊天相关 API 的入口
                .completions     # 聊天补全（chat completion）模块
                .create(...)     # 创建一次请求
            """
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=self.tool_schemas,
                tool_choice="auto",
            )
            message = response.choices[0].message
            # 检查是否有工具调用
            if not message.tool_calls:
                print("✅ 完成，返回答案") 
                return message.content
            # 有工具调用
            print(f"🔧 LLM 请求调用 {len(message.tool_calls)}个工具")
            messages.append(message)
            # 执行每个工具
            for tool_call in message.tool_calls:
                name = tool_call.function.name
                args_raw =  tool_call.function.arguments or "{}"
                args =  json.loads(args_raw) if args_raw.strip() else {}
                # print(f"args的参数：：：：{args}")
                print(f"   调用: {name}({args})")
                # 执行
                result = self._execute_tool(name, args)
                print(f"   结果: {result}")
            
                # 回喂结果
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result,
                })
        
        return "抱歉，处理超时，请重试。"

    def should_use_tools(self, message: str) -> bool:
        """
            判断是否需要工具
            
            简单实现：包含天气，日期等相关关键词 → 用 Agent
        """
        # 原来的关键词匹配
        keywords = [
            # 天气类
            "天气", "下雨", "晴天", "阴天", "温度", "冷", "热",
            # 日期类
            "今天", "明天", "昨天", "现在", "几点", "几号", "日期",
            "星期", "周几", "礼拜", "今年", "哪年", "时间",
            # 学生类
            "学生", "学号", "姓名", "资料", "年龄", "查一下",
            # 操作类
            "改成", "修改", "更新", "改为",
            "删除", "移除", "删掉",
        ]
        return any(kw in message for kw in keywords)

# ========== 5. 本地 SLM Agent（方案 A：本地跑工具） ==========
class LocalSLMAgent:
    """
        用本地 SLM（Ollama）跑工具调用
        - 判断意图
        - 调用工具
        - 返回工具执行结果文本（不做美化）
    """
    def __init__(self):
        self.client = local_client         # 本机 11434
        self.model = LOCAL_MODEL
        self.tools = TOOLS_NATIVE
        self.tool_schemas = TOOLS_SCHEMA_NATIVE
        self.system_prompt = """
            你是一个智能助手，可以调用工具来回答用户的问题。
            可用工具：
                - get_weather：查询指定城市的天气情况、温度、风向
                - get_current_date：获取当前日期、时间和星期几
                - get_student_info：查询学生信息（姓名、学号、年龄）
                - update_student：更新学生信息（改姓名、改年龄）
                - delete_student：删除学生

            调用规则：
            1. 用户问天气 → 用 get_weather
            2. 用户问日期、时间、星期 → 用 get_current_date
            3. 用户问学生资料/年龄/学号 → 用 get_student_info
            4. 用户要改学生信息（"把张三的年龄改成12"）→ 用 update_student
            5. 用户要删除学生（"删除李四"）→ 用 delete_student
            6. 其他问题 → 直接回答

            【重要】删除操作很危险，如果用户明确说"删除"才调用 delete_student。
            回复要简洁、准确，用中文回答。
        """
    def _execute_tool(self, name: str, args: Dict) -> str:
        """执行工具"""
        if name not in self.tools:
            return f"未知工具: {name}"
        try:
            func = self.tools[name]
            return func(**args)
        except Exception as e:
            return f"工具执行失败: {e}"
        
    def run(self, user_message: str, max_iterations: int = 3) -> str:
        """
            运行 Agent
            
            Args:
                user_message: 用户消息
                max_iterations: 最大循环次数（防止死循环）
            
            Returns:
                AI 最终回复
        """
        # 初始化消息历史
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_message},
        ]
        # 循环调用
        for iteration in range(max_iterations):
            print(f"🟢 [本地SLM] 第 {iteration+1} 轮")

            # 调用 LLM
            """
                self.client          # OpenAI 客户端实例
                .chat            # 聊天相关 API 的入口
                .completions     # 聊天补全（chat completion）模块
                .create(...)     # 创建一次请求
            """
            try:

                response = self.client.chat(
                    model=self.model,
                    messages=messages,
                    tools=self.tool_schemas,
                )
            except Exception as e:
                print(f"❌ [本地SLM] 调用失败: {e}")
                return ""      # ← 返回空 → 上层降级
            message = response.message
            tool_calls = getattr(message, "tool_calls", None)
            # 没有工具调用 → 直接返回文本
            if not tool_calls:
                print("✅ [本地SLM] 完成，直接返回")
                return message.content or ""
            # 有工具调用
            print(f"🔧 [本地SLM] 请求调用 {len(tool_calls)} 个工具")

            # ★ Ollama 格式：tool_calls 没有 id 字段，回喂时不带 tool_call_id
            messages.append({
                "role": "assistant",
                "content": message.content or "",
                "tool_calls":[
                    {
                        "function":{
                            "name":tc.function.name,
                            "arguments":(
                                json.loads(tc.function.arguments)
                                if isinstance(tc.function.arguments, str) 
                                else  tc.function.arguments
                            ),
                        }
                    } for tc in tool_calls
                ],
            })

            # 执行每个工具
            for tc in tool_calls:
                name = tc.function.name
                args_raw =  tc.function.arguments or "{}"
                try:
                    args =  json.loads(args_raw) if isinstance(args_raw, str) else args_raw
                except json.JSONDecodeError:
                    args = {}

                print(f"   调用: {name}({args})")
                # ★ Ollama 的 arguments 可能已是 dict，不是字符串
                result = self._execute_tool(name, args)
                print(f"   结果: {result}")
            
                # 回喂结果
                messages.append({
                    "role": "tool",
                    "content": result,
                })
        
        return "抱歉，处理超时，请重试。"


    def should_use_tools(self, message: str) -> bool:
        """
            判断是否需要工具
            
            简单实现：包含天气，日期等相关关键词 → 用 Agent
        """
        # 如果启用了本地模型，且客户端可用。
        if  USE_LOCAL_INTENT and local_client:
            prompt = f"""判断这句话是否需要调用工具。只回答“天气”、“日期”、"查询学生"、"更新学生"、"删除学生"或"否"。用户: {message}回答:"""
            resp = local_client.chat(
                model=LOCAL_MODEL,
                messages=[{"role":"user","content":prompt}]
            )
            # 用小模型判断意图
            result = resp.message.content.strip()
            # return result in ["天气", "日期", "学生","查询学生", "更新学生", "删除学生"] 
            return result != "否" # 只要不是"否"，就进 Agent，具体调哪个工具交给 run()。
        else:
            # 原来的关键词匹配
            keywords = [
                # 天气类
                "天气", "下雨", "晴天", "阴天", "温度", "冷", "热",
                # 日期类
                "今天", "明天", "昨天", "现在", "几点", "几号", "日期",
                "星期", "周几", "礼拜", "今年", "哪年", "时间",
                # 学生类
                "学生", "学号", "姓名", "资料", "年龄", "查一下",
                # 操作类
                "改成", "修改", "更新", "改为",
                "删除", "移除", "删掉",
            ]
            return any(kw in message for kw in keywords)
# ========== 4. 全局实例 ==============
native_weather_agent = NativeWeatherAgent()
local_slm_agent = LocalSLMAgent() if USE_LOCAL_INTENT else None