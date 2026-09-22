# src/framework/ai/agent/weather/core/agent.py
import os
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain.agents import create_agent
from dotenv import load_dotenv
from pathlib import Path
from ......shared.llm import get_langchain_llm

env_path = Path(__file__).parent.parent.parent.parent.parent / ".env"
load_dotenv(env_path)

from ..tools.weather import  get_weather

class SmartAgent:
    def __init__(self):
        self.llm = self._init_llm()
        self.tools = [get_weather]
        self.agent = None

    def _init_llm(self):
        return get_langchain_llm()

    def _create_agent(self):
        """创建 Agent"""
        system_prompt = """
            你是一个智能助手，可以根据用户的问题自主决定调用哪些工具。

            可用工具：
                1. get_weather - 查询天气
                2. calculate - 数学计算

            规则：
                - 根据用户问题自主选择是否需要调用工具
                - 如果不需要工具，直接回答
                - 如果需要工具，调用并组织答案
                - 始终用中文回复
        """
        self.agent = create_agent(
            self.llm,
            self.tools,
            system_prompt=system_prompt
        )
        return self.agent

    def run(self, message:str, chat_history: str = None) -> str:
        """运行 Agent"""
        if not self.agent:
            self._create_agent()
        messages = []
        if chat_history:
            for msg in chat_history:
                if msg.get("role") == "user":
                    messages.append(HumanMessage(content=msg.get("content","")))
                else:
                    messages.append(SystemMessage(content=msg.get("content","")))
        messages.append(HumanMessage(content=message))
        result = self.agent.invoke({"messages": messages})
        msgs = result.get("messages", [])
        if msgs:
            return msgs[-1].content
        return "无响应"
    
    def should_use_tools(self, message: str) -> bool:
        """让 LLM 判断是否需要调用工具"""

        prompt = f"""判断用户是否需要调用工具来处理问题。
            可用工具：
            1. get_weather - 查询天气
            2. calculate - 数学计算

            用户问题：{message}

            如果用户需要查询天气或计算，回答 "true"，否则回答 "false"。
            只回答 true 或 false，不要有其他内容。
        """

        try:
            response = self.llm.invoke(prompt)
            result = response.content.strip().lower()
            print(f"🤖 LLM 判断结果: {result} (原始: {response.content})") 
            return result == "true"
        except Exception as e:
            print(f"⚠️ 判断失败，默认使用 Agent: {e}")
            return True
    async def stream(self, message: str):
        """流式运行 Agent"""
        if not self.agent:
             self._create_agent()
        async for chunk in self.agent.astream({"messages":[HumanMessage(content=message)]}
        ):
            if "messages" in chunk:
                for msg in chunk["messages"]:
                    if hasattr(msg, "content") and msg.content:
                        yield {"output": msg.content}


smart_agent = SmartAgent()
# smart_agent._create_agent()