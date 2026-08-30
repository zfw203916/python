V1.0.1 AI智能伴侣。第一版本：用了streamlit
streamlit run src/framework/ai/aicompanion/ai_companion.py

V1.0.2 第二版将改造为FastAPI
目录结构：
my-test-framework/src/framework/ai/aicompanion/
├── __init__.py
├── ai_companion.py (原文件，保留作为参考)
├── main.py (FastAPI主应用)
├── models.py (数据模型)
├── database.py (数据库操作)
├── routers/
│   ├── __init__.py
│   ├── sessions.py (会话管理API)
│   └── chat.py (聊天API)
├── services/
│   ├── __init__.py
│   ├── vector_service.py (向量服务),用于存储和搜索的。
│   └── chat_service.py (聊天服务)
└── static/
    ├── index.html
    ├── style.css
    └── script.js






# 启用命令：
#1. 初始化项目
cd my-test-framework
uv init
uv add fastapi uvicorn openai pydantic python-dotenv sse-starlette

#2. 启动后端
uv run uvicorn src.framework.ai.aicompanion.main:app --host 0.0.0.0 --port 8000 --reload

#或者使用脚本
uv run start-backend

#3. 前端直接用浏览器打开
open frontend/index.html
#或使用Live Server插件

# 方案一：用Docker（最推荐）,这里通过docker安装了向量数据库的插件
像运行一个“数据库APP”一样，不需要在电脑里装一堆东西，几步就能搞定，最省心。

先安装 Docker Desktop（一个运行容器的软件）。

打开终端 (Terminal)，执行以下命令，就能自动下载并运行带 pgvector 扩展的 PostgreSQL：

bash
docker run -d \
  --name ai_companion_db \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_DB=ai_companion \
  -p 5432:5432 \
  pgvector/pgvector:pg15
之后在 DBeaver 里用 localhost、端口 5432、用户名 postgres、密码 postgres 去连接就行。

✅ 得到的优势
前后端分离 → 前端可以独立部署CDN，后端可以水平扩展

企业级基础 → 后续可加鉴权、监控、日志

uv管理 → 依赖锁死，环境统一

渐进式扩展 → 加RAG、加插件、加多模型都在backend里

🚀 后续扩展方向
鉴权：JWT + 用户登录

RAG：在core.py中集成向量检索

监控：加Prometheus指标

日志：结构化日志 + ELK

容器化：Dockerfile + docker-compose

#  需要在根目录下执行。
uv run python -m uvicorn src.framework.ai.aicompanion.main:app --host 0.0.0.0 --port 8000 --reload

# 设置环境变量 (.env)
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/ai_companion



# FastAPi 自动文档：
http://127.0.0.1:8000/docs
http://127.0.0.1:8000/redoc
http://127.0.0.1:8000/openapi.json
        

V1.0.3
上下文管理、插件系统 （试试调用系统工具，创建文件，关机）、


v1.0.4 
Token统计、请求日志、异常处理、Retry（重试机制）、成本统计


v1.0.5
RAG = 检索增强生成

