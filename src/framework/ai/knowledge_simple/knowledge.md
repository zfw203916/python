my-test-framework/
├── pyproject.toml                    # uv 依赖管理
├── .env                             # 环境变量
├── src/
│   └── framework/
│       └── ai/
│           ├── aicompanion_v2/      # 原有AI智能伴侣（保持不变）
│           │   ├── database.py
│           │   ├── models.py
│           │   ├── main.py
│           │   ├── routers/
│           │   │   ├── sessions.py
│           │   │   ├── chat.py
│           │   │   └── knowledge.py  # 🟢 新增：知识库路由
│           │   └── services/
│           │       ├── chat_service.py  # 🟡 修改：集成知识库
│           │       ├── vector_service.py
│           │       ├── knowledge_service.py  # 🟢 新增
│           │       └── document_parser.py  # 🟢 新增
│           └── knowledge-base/       # 🟢 新增：独立知识库系统
│               ├── __init__.py
│               ├── main.py           # 🟢 新增：知识库独立服务
│               ├── database.py       # 🟢 新增
│               ├── models.py         # 🟢 新增
│               ├── routers/
│               │   ├── __init__.py
│               │   ├── documents.py  # 🟢 新增：文档管理
│               │   ├── search.py     # 🟢 新增：搜索接口
│               │   └── admin.py      # 🟢 新增：管理接口
│               ├── services/
│               │   ├── __init__.py
│               │   ├── document_parser.py  # 🟢 新增
│               │   ├── embedding_service.py  # 🟢 新增
│               │   ├── search_service.py  # 🟢 新增
│               │   └── index_service.py  # 🟢 新增
│               ├── core/
│               │   ├── __init__.py
│               │   ├── config.py     # 🟢 新增
│               │   ├── security.py   # 🟢 新增：认证权限
│               │   └── audit.py      # 🟢 新增：审计日志
│               ├── models/
│               │   ├── __init__.py
│               │   ├── document.py   # 🟢 新增
│               │   ├── chunk.py      # 🟢 新增
│               │   ├── knowledge_base.py  # 🟢 新增
│               │   ├── user.py       # 🟢 新增
│               │   └── audit_log.py  # 🟢 新增
│               └── static/
│                   └── index.html    # 🟢 新增：知识库管理界面


# uv add "passlib[bcrypt]"


简化版本：

my-test-framework/
├── src/
│   └── framework/
│       └── ai/
│           ├── aicompanion_v2/      # 原有AI智能伴侣（保持不变）
│           └── knowledge_simple/    # 简单知识库
│               ├── __init__.py
│               ├── database.py      # 知识库数据库
│               ├── models.py        # 数据模型
│               ├── main.py          # FastAPI 入口
│               ├── routers/
│               │   ├── __init__.py
│               │   ├── documents.py # 文档上传/管理
│               │   └── search.py    # 知识库检索
│               ├── services/
│               │   ├── __init__.py
│               │   ├── embedding_service.py  # 向量化服务
│               │   └── document_service.py   # 文档处理服务
│               └── static/
│                   └── index.html   # 知识库管理界面

# 跑通这个
uv run python -m src.framework.ai.knowledge_simple.main

# 或者用 uvicorn
知识库：
uv run uvicorn src.framework.ai.knowledge_simple.main:app --host 0.0.0.0 --port 8001 --reload

AI智能伴侣：
uv run uvicorn src.framework.ai.aicompanion_v2.main:app --host 0.0.0.0 --port 8000 --reload

# 数据表，程序中已自动创建：
-- 知识库文档表
CREATE TABLE knowledge_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(200) NOT NULL,
    filename VARCHAR(255) NOT NULL,
    file_type VARCHAR(20) NOT NULL,  -- txt, pdf, docx
    content TEXT NOT NULL,
    chunk_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 知识库分块表（向量存储）
CREATE TABLE knowledge_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES knowledge_documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    embedding VECTOR(1024),
    created_at TIMESTAMP DEFAULT NOW()
);

-- 向量索引（可选，提高搜索速度）
CREATE INDEX idx_knowledge_chunks_embedding ON knowledge_chunks 
    USING ivfflat (embedding vector_cosine_ops) WITH (lists=100);



# 访问地址
完整的地址列表
根据你的 main.py 中的静态文件挂载配置：

服务	访问地址
AI智能伴侣	http://localhost:8000/static/index.html
知识库	http://localhost:8000/kb-static/index.html
API 文档	http://localhost:8000/docs
ReDoc 文档	http://localhost:8000/redoc
OpenAPI JSON	http://localhost:8000/openapi.json
根路径	http://localhost:8000/ (会显示API信息)



七、后续可扩展功能
多轮对话优化 - 更好的上下文管理

知识库版本管理 - 文档更新追踪

用户认证系统 - 多用户隔离

对话导出 - 导出为 Markdown/PDF

批量文档上传 - 支持文件夹上传

知识库统计 - 文档数、检索次数等



# 知识库的执行流程图：

