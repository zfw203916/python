# src/framework/ai/knowledge_simple/__init__.py
from .database import init_db, get_db, Base
from .main import app

__all__ = ['init_db', 'get_db', 'Base', 'app']