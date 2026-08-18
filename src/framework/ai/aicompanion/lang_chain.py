import os
from dotenv import load_dotenv
from langchain_deepseek import ChatDeepSeek
from importlib.metadata import version

# 检查版本（如果你需要）
print("LangChain version:", version("langchain"))
# print("langchain version:", langchain.__version__)
load_dotenv()
models = ChatDeepSeek(
    api_key=os.environ.get("APP_DEEPSEEK_API_KEY"),
    base_url=os.environ.get("APP_DEEPSEEK_URL"),
    model="deepseek-v4-pro",
    temprature=0.7,
)

print(models.invoke("你是谁，简短回答"))  # 测试连接是否成功
