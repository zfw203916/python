# src/framework/ai/aicompanion_v2/logging_config.py
import logging, sys, os
from pathlib import Path
from dotenv import load_dotenv
# 日志目录
LOG_DIR = Path(__file__).parent.parent.parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

# 系统配置
env_path = Path(__file__).parent.parent.parent.parent.parent / ".env"
load_dotenv(env_path)
LOG_ENABLED = os.environ.get("LOG_ENABLED","false").lower() == "true"
LOG_LEVEL = os.environ.get("LOG_LEVEL","INFO")

def setup_logging(level: str = LOG_LEVEL):
    """配置全局日志"""
    #未启用日志则直接返回
    if not LOG_ENABLED:
        logging.disable(logging.CRITICAL)
        return
    # 日志格式
    fmt = "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d  | %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"

    # 控制台输出
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(fmt, datefmt))

    # 文件输出
    file_handler = logging.FileHandler(LOG_DIR / "app.log", encoding="utf-8")
    file_handler.setFormatter(logging.Formatter(fmt, datefmt))

    # 根 logger 配置
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        handlers=[console_handler, file_handler]
    )

    # 降低第三方库的日志级别（避免刷屏）
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)