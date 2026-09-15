# src/app/clients/studentmanage_v2/models_db.py
from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from .database import Base

"""
ORM 操作 (models_db.py)              
│    ├── Student 类 → students 表          
│    ├── db.add(student)                   
│    └── db.commit()                       
│    → 生成 SQL:                           
│       INSERT INTO students (...) VALUES 
映射数据库表，生成 SQL
"""
class StudentUser(Base):
    """学生管理系统的登录用户表"""
    __tablename__ = "student_users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    st_username = Column(String(50), unique=True, nullable=False)
    st_password = Column(String(255), nullable=False)  # 生产环境要加密
    created_at = Column(DateTime, default=datetime.now)

class Student(Base):
    """学生信息表"""
    __tablename__ = "students"
    id = Column(Integer, primary_key=True, autoincrement=True)
    student_name = Column(String(50), nullable=False)
    student_id = Column(String(50), unique=True, nullable=False)
    student_age = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)