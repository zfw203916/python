# test_ollama_tool.py
"""
    测试模型是否支持 function calling 工具调用。
"""
from ollama import Client

client = Client()

# 1. 定义工具（和你的 date_native.py 结构一致）
tools = [{
    "type": "function",
    "function": {
        "name": "get_current_date",
        "description": "获取当前日期和时间",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    }
}]

# 2. 发送测试请求
response = client.chat(
    # model="qwen3.5:4b",  # 换成你实际下载的模型名
    model="qwen2.5:3b",
    messages=[{"role": "user", "content": "今天几号？"}],
    tools=tools
)

# 3. 打印结果
print("完整响应：")
print(response)
print("\n消息内容：")
print(response.message)
print("\n工具调用：")
print(response.message.tool_calls)