# src/app/clients/studentmanage_v2/main.py

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from starlette.middleware.sessions import SessionMiddleware
from pathlib import Path

from .database import init_db
from .routers import auth, students

BASE_DIR = Path(__file__).parent
app = FastAPI(
    title="学生管理系统",
    description="FastAPI + PostgreSQL 学生管理",
    version="2.0.0",
)
# Session 中间件（替代 Flask session）
app.add_middleware(
    SessionMiddleware,
    secret_key="653-254-338",
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
app.include_router(auth.router)
app.include_router(students.router)
# 静态文件服务
# static_dir = BASE_DIR / "static"
# if student_static_dir.exists():
#     app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

@app.get("/",response_class=HTMLResponse)
async def index():
    """主页"""
    html_file = BASE_DIR / "templates" / "index.html"
    return HTMLResponse(content=html_file.read_text(encoding="utf-8"))

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "student-manage"}

if __name__=="__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=5004,
        reload=True,
    )