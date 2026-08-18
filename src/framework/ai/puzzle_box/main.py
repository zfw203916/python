# 汉字迷盒
from fastapi import FastAPI
from starlette.responses import FileResponse
import os, json
from fastapi.staticfiles import StaticFiles
from starlette.requests import Request
from starlette.responses import FileResponse, JSONResponse 
from datetime import datetime
from pydantic import BaseModel
from typing import Any
from dotenv import load_dotenv
from openai import OpenAI

import logging


app = FastAPI(title="汉字迷盒")
static_dir = os.path.join(os.path.dirname(__file__), "static")
session_dir = os.path.join(os.path.dirname(__file__),"session")
app.mount("/static", StaticFiles(directory=static_dir), name='static')
load_dotenv()
# logging.basicConfig(
#     format="%(asctime)s - (levelname)s - (filename)s:%(lineno)d - %(message)s"
# )
# logging.info("---------伴侣性格--------")

class ApiResponse(BaseModel):

    """
    API响应模型类
    用于统一规范API返回的数据结构
    包含状态码、消息和数据三个字段
    """
    code: int  # 状态码，用于标识请求处理状态，如200表示成功，400表示请求错误等
    message: str
    data: Any

class ChatRequest(BaseModel):
    session_id: str
    message: str

def generate_session_id():
    return datetime.now().strftime("%Y%m%d%H%M%S%f")

# 获取 session_id的文件名
def get_session_id(session_dir: str):
    return f"session/{session_dir}.json"

@app.get("/")
def root():
    # print(static_dir)
    return FileResponse(f"{static_dir}/index.html")


#新建会话
"""
# 不需要参数，直接发 POST
curl -X POST http://127.0.0.1:8001/api/session

# 查看详细请求过程
curl -v -X POST http://127.0.0.1:8001/api/session

# 查看响应头
curl -i -X POST http://127.0.0.1:8001/api/session

"""
@app.post("/api/session")
def create_session() -> ApiResponse:
   
    # 生成会话的标识（名字）
    session_id = generate_session_id()

    #组装会话信息，保存到文件
    session_data ={
        "current_session":session_id,
        "message":[]
    }
    
    os.makedirs(session_dir, exist_ok=True)
    file_path = os.path.join(session_dir, f"{session_id}.json")
    try:
        with open(file_path,"w", encoding='utf-8') as f:
            json.dump(session_data,f, ensure_ascii=False, indent=4)
    except Exception as e:
        return {"code":500,"message": f"保存文件失败:{str(e)}"}

    # 返回数据
    # return {"code":200,"message":"创建会话成功","data": session_id}
    return ApiResponse(code=200,message="创建会话成功",data=session_id)



@app.post("/api/chat")
def chat(request:ChatRequest, session_dir=session_dir) -> ApiResponse:
    # 与 AI交互
    print(f"与AI交互{request.session_id}....{request.message}")

    # 交互逻辑
    """
    1、先拿到配置，然后按配置去跟 API交互。
    2、该保存的保存，这次建议保存是redis+postgreSql
    3、后续扩展需求功能....然后为docker

    #1.加载json.文件中的会话数据
    #2.构建AI大模型交互的消息数据
    #3.调用AI大模型 DeepSeek
    #4.获取胸应的数据
    #5.跟新消息列表中的消息
    #6.保存会话信息到json.文件中
    #7.返回数据
    """
    if api_key is None:
        ...

    with open(session_dir,"r", encoding='utf-8') as f:
        session_data = json.load(f)
        messages=[
                {"role": "system", "content": st.session_state.system_str},
                # *st.session_state.messages
        ],
        print(session_data)
        #1.加载json.文件中的会话数据
    m   messages = [{"role":"system","count":SYSTEM_PROMPT}]
        logging.info(messages)
        for messages in session_data["message"]:
            messages.append(messages)
        messages = [{"role":"system","count":request.message}]

        #2.构建AI大模型交互的消息数据

        base_url = os.environ.get("APP_DEEPSEEK_URL")
        api_key = os.environ.get("APP_DEEPSEEK_API_KEY")
        client = OpenAI(
            api_key = api_key,
            base_url = base_url
        )
        

        #3.调用AI大模型 DeepSeek
        response= client.chat.completions.create(
            model="deepseek-v4-pro",
            messages=messages,
            stream=True,
            reasoning_effort="high",
            extra_body={"thinking": {"type": "enabled"}}
        )
        #4.获取胸应的数据

        ai_response = response.choices[0].message.content
    
        #5.跟新消息列表中的消息
        messages.append({"role":"assistant", "content":ai_response})
        #6.保存会话信息到json.文件中
        with open(f"{session_dir}.json","w", encoding="utf-8") as f:
            json.dump(session_data, f, ensure_ascii=False, indent=4)
        
        #7.返回数据


    return ApiResponse(code=200, message=request.message, data="AI过来的数据")

# 获取指定的会话信息
@app.get("/api/session/{session_id}")
def get_session(session_id: str) -> ApiResponse:
    session_file = get_session_file_name(session_id)
    with open(session_file,"r", encoding="utf-8"):
        session_data = json.load()

    return ApiResponse(code=200, message="获取会话信息成功", data=session_data)

# 与 AI交互逻辑

#删除指定信息
@app.delete("/app/session/{session_id}")
def delete_session(session_id: str) ->ApiResponse:
    session_file = get_session_file_name(session_id)
    os.remove(session_file)
    return ApiResponse(code=200, message="获取会话信息成功", data=None)


# 自动显示处理异常：
@app.exception_handler(Exception)
def handle_exception(request: Request, exc: Exception):
    logging.error(f"处理异常，请求路径{request.url},捕获到异常：{exec}")
    return JSONResponse(content={"code":200, "message":"服务器异常", "data":None})


if __name__ == "__main__" :
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
