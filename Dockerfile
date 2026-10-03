FROM python:3.11-slim

# ========== 系统依赖 ==========
RUN apt-get update && apt-get install -y \
    gcc libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

# ========== 安装 uv ==========
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:${PATH}"

# ========== 工作目录 ==========
WORKDIR /app

# ========== 关键：告诉 uv 装到系统 Python ==========
ENV UV_PROJECT_ENVIRONMENT=/usr/local

# ========== 复制依赖文件 ==========
COPY pyproject.toml uv.lock ./

# ========== 装依赖到系统 ==========
RUN uv sync --frozen --no-dev

# ========== 验证 ==========
RUN python -c "import fastapi, sqlalchemy, pgvector; print('✓ Dependencies installed')"

# ========== 复制源码 ==========
COPY src/ ./src/

# ========== 日志目录 ==========
RUN mkdir -p /app/logs && chmod 755 /app/logs

# ========== 环境变量 ==========
ENV PYTHONUNBUFFERED=1
ENV APP_ENV=production

# ========== 启动 ==========
CMD ["sh", "-c", "uvicorn src.framework.ai.aicompanion_v2.main:app --host 0.0.0.0 --port 8000"]