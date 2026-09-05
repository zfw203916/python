# src/framework/ai/knowledge_simple/main.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

from .database import init_db
from .routers import documents, search



# 创建应用
app = FastAPI(
    title="知识库系统", 
    description="简单知识库管理，与AI智能伴侣共用数据库", 
    version="1.0.0"
)

# CORS
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
app.include_router(documents.router)
app.include_router(search.router)

# 静态文件
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/")
async def root():
    return {
        "service": "knowledge-simple",
        "status": "running",
        "docs": "/docs",
        "ui": "/static/index.html"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "knowledge-simple"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)