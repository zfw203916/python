# src/framework/ai/aicompanion_v2/main.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware #中间件
from pathlib import Path
import logging
from logging import os
from dotenv import load_dotenv

from .database import init_db
from .routers import sessions, chat

# ========== 导入知识库 ==========
from ..knowledge_simple.database import init_db as init_kb_db

# 从 routers 子模块中导入 router 对象
from ..knowledge_simple.routers.documents import router as documents_router
from ..knowledge_simple.routers.search import router as search_router

# ========== 导入 Agent（ ==========
from ..agent.weather.core.router import router as agent_router

# ========= 导入学生管理系统 =========
from ....app.clients.studentmanage_v2.routers import auth as student_auth
from ....app.clients.studentmanage_v2.routers import students as student_students
from ....app.clients.studentmanage_v2.database import init_db as init_student_db


# 导入日志
from .logging_config import setup_logging
setup_logging()
logger = logging.getLogger(__name__)

# 读取.env 配置
env_path = Path(__file__).parent.parent.parent.parent.parent / ".env"
load_dotenv(env_path)
add_middleware_secret_key = os.environ.get("add_middleware_secret_key")
if not add_middleware_secret_key:
    raise RuntimeError("必须设置 SECRET_KEY 环境变量")
logger.info(f"这个是cookie配置值:{add_middleware_secret_key}")

# 创建FastAPI应用
app = FastAPI(
    title="AI智能系统",
    description="AI伴侣聊天应用 + 知识库管理 + 学生管理系统 + AI agent",
    version="2.0.2",
)



# Session 中间件（学生管理系统需要），
# add_middleware 做加密解密处理。加密/解密 Session Cookie 。
app.add_middleware(
    SessionMiddleware,
    secret_key=add_middleware_secret_key,
    session_cookie="student_session" # ← 学生管理的 cookie 名,用不同的 session cookie 名.防止跟 AI的session冲突。
)

# ========== 中间件,CORS配置 ==========
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========== ✏️ 修改：确保两个模块的数据库表都被创建 ==========
init_db()  # AI伴侣表
init_kb_db()  # 知识库表（现在会创建向量索引）
init_student_db() # 学生管理表

# ========== 注册AI伴侣路由 ==========
app.include_router(sessions)
app.include_router(chat)

# ========== 注册知识库路由 ==========
# 使用正确导入的 router 对象
app.include_router(documents_router)
app.include_router(search_router)

# ========== 工具集路由 ==========
app.include_router(agent_router)

# ========== 学生管理路由 ==========
app.include_router(student_auth.router)
app.include_router(student_students.router)


# ========== 静态文件服务 ==========
# AI智能伴侣静态文件
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# 知识库静态文件
kb_static_dir = Path(__file__).parent.parent / "knowledge_simple" / "static"
if kb_static_dir.exists():
    app.mount("/kb-static", StaticFiles(directory=str(kb_static_dir)), name="kb-static")

# 学生管理前端
student_templates_dir = Path(__file__).parent.parent.parent.parent / "app" / "clients" / "studentmanage_v2" / "templates"
if student_templates_dir.exists():
    app.mount("/student-static",StaticFiles(directory=str(student_templates_dir)), name="student-static")


@app.get("/")
async def root():
    return {
        "message": "AI智能伴侣 + 知识库 API",
        "docs": "/docs",
        "ai_companion": "/static/index.html",
        "knowledge_base": "/kb-static/index.html",
        "student_manage" : "/student",
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


# 学生管理主页
from fastapi.responses import HTMLResponse
@app.get("/student", response_class=HTMLResponse)
async def student_index():
    """学生管理主页"""
    html_file = student_templates_dir / "index.html"
    if not html_file.exists():
        return HTMLResponse(content="<h1>学生管理页面不存在</h1>", status_code=404)
    return HTMLResponse(html_file.read_text(encoding="utf-8"))

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
