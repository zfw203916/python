# my-test-framework/src/framework/ai/aicompanion_v2/main.py

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os
from pathlib import Path

from .database import init_db
from .routers import sessions, chat


# 创建FastAPI应用
app = FastAPI(
    title="AI智能伴侣",
    description="AI伴侣聊天应用",
    version="1.0.0"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化数据库
init_db()

# 注册路由
app.include_router(sessions)
app.include_router(chat)

# 静态文件服务（用于前端）
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static",StaticFiles(directory=str(static_dir)), name="static")

@app.get("/")
async def root():
    """根路径重定向到静态页面"""
    return {"message": "AI智能伴侣API", "docs": "/docs"}
 

@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )