# Please install OpenAI SDK first: `pip3 install openai`
import os
from openai import OpenAI

client = OpenAI(
    api_key=os.environ.get("APP_DEEPSEEK_API_KEY"),
    # api_key = "sdfsfasfw4rwe",
    base_url="https://api.deepseek.com",
)
response = client.chat.completions.create(
    model="deepseek-v4-pro",
    messages=[
        {"role": "system", "content": "你是AI助手： 旺旺"},
        # {"role": "user", "content": "你好，请用最简短解释回复，什么是AI"}
        # {"role": "user", "content": "你叫什么名字，简短回复"}
        {
            "role": "user",
            "content": "46岁了该怎么办，还能做AI应用开发工程师吗？简短回复",
        },
        # 回答： 当然可以。年龄是经验，不是限制。
        # AI应用开发重在解决实际问题，您的阅历和工程思维正是优势。
        # 从主流框架（如LangChain、API调用）和Python学起，聚焦业务场景，完全能胜任。
    ],
    stream=False,
    reasoning_effort="high",
    extra_body={"thinking": {"type": "enabled"}},
)
print(response.choices[0].message.content)
