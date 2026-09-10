# src/framework/ai/knowledge_simple/__init__.py
from ..knowledge_simple.database import init_db, get_db, Base

__all__ = ['init_db', 'get_db', 'Base']