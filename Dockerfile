FROM python:3.11-slim

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 安装 uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh && \
    echo 'export PATH="/root/.local/bin:$PATH"' >> /root/.bashrc
ENV PATH="/root/.local/bin:${PATH}"

# 复制依赖文件
COPY pyproject.toml uv.lock ./

# [修改] 使用 uv sync 安装依赖到系统 Python，而不是虚拟环境
RUN uv sync --frozen --no-dev --system

# [修改] 验证安装
RUN python -c "import yaml; print('✓ PyYAML installed successfully')"

# 设置工作目录
WORKDIR /app

# 复制应用代码和配置
COPY app/ .
COPY config.yaml ./

# 创建日志目录
RUN mkdir -p /app/logs && chmod 755 /app/logs

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV APP_ENV=production

CMD ["python", "main.py"]