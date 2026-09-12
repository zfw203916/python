# src/framework/ai/aicompanion_v2/main.py

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

from .database import init_db
from .routers import sessions, chat

# ========== 导入知识库 ==========
from ..knowledge_simple.database import init_db as init_kb_db

# 从 routers 子模块中导入 router 对象
from ..knowledge_simple.routers.documents import router as documents_router
from ..knowledge_simple.routers.search import router as search_router

# ========== 导入 Agent（ ==========
from ..agent.weather.core.router import router as agent_router

# 导入日志
import logging
from .logging_config import setup_logging
setup_logging()
logger = logging.getLogger(__name__)


# 创建FastAPI应用
app = FastAPI(
    title="AI智能伴侣 + 知识库",
    description="AI伴侣聊天应用 + 知识库管理",
    version="2.0.1",
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========== ✏️ 修改：确保两个模块的数据库表都被创建 ==========
logger.info("🔄 正在初始化AI伴侣数据库...")
init_db()  # AI伴侣表
logger.info("🔄 正在初始化知识库数据库...")
init_kb_db()  # 知识库表（现在会创建向量索引）
logger.info("✅ 所有数据库初始化完成")

# ========== 注册AI伴侣路由 ==========
app.include_router(sessions)
app.include_router(chat)

# ========== 注册知识库路由 ==========
# ✅ 使用正确导入的 router 对象
app.include_router(documents_router)
app.include_router(search_router)

# ========== 工具集路由 ==========
app.include_router(agent_router)

# 静态文件服务
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# 知识库静态文件
kb_static_dir = Path(__file__).parent.parent / "knowledge_simple" / "static"
if kb_static_dir.exists():
    app.mount("/kb-static", StaticFiles(directory=str(kb_static_dir)), name="kb-static")


@app.get("/")
async def root():
    return {
        "message": "AI智能伴侣 + 知识库 API",
        "docs": "/docs",
        "ai_companion": "/static/index.html",
        "knowledge_base": "/kb-static/index.html",
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=["src", "."],
        reload_includes=[
            "*.py",
            "*.env",
            ".env",  # 有些系统把 .env 当作隐藏文件
        ],
    )
