# src/app/clients/studentmanage_v2/database.py
"""
    src/app/clients/studentmanage/
├── __init__.py
├── main.py              # FastAPI 应用
├── database.py          # 数据库连接
├── models.py            # Pydantic 模型
├── models_db.py         # SQLAlchemy 模型
├── routers/
│   ├── __init__.py
│   ├── auth.py          # 登录注册
│   └── students.py      # 学生管理
├── templates/
│   └── index.html       # 前端（复用）

前端：http://127.0.0.1:5004/

API 文档：http://127.0.0.1:5004/docs

"""
from ....shared.database import engine, SessionLocal, Base, get_db
# 导入日志
import logging
logger = logging.getLogger(__name__)


def init_db():
    """初始化表"""
    from .models_db import StudentUser, Student
    Base.metadata.create_all(bind=engine)
