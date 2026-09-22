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


# ========== 1. 工具注册表 ==========
# 工具名 → 函数
TOOLS_NATIVE: Dict[str, callable] = {
    "get_weather": get_weather,
    "get_current_date": get_current_date
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
}
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

            请根据用户的意图，选择合适的工具。
            如果用户问的是天气，用 get_weather。
            如果用户问的是日期、时间、星期，用 get_current_date。
            如果都不相关，就直接回答，不要调用工具。
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
            print(f"results::::::::::::------{results}")
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
        keywords = [
            # 天气类
            "天气", "下雨", "晴天", "阴天", "温度", "冷", "热",
            # 日期类
            "今天", "明天", "昨天", "现在", "几点", "几号", "日期",
            "星期", "周几", "礼拜", "今年", "哪年", "时间",
        ]
        return any(kw in message for kw in keywords)

# ========== 4. 全局实例 ==============
native_weather_agent = NativeWeatherAgent()