# src/app/clients/studentmanage_v2/routers/students.py
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Annotated

from ..database import get_db
from ..models_db import Student
from ..models import StudentCreate, StudentUpdate, StudentResponse, SuccessResponse

router = APIRouter(prefix="/api/student/students",tags=["student-students"])

def require_login(request: Request):
    """依赖：要求登录"""
    if not request.session.get("logged_in"):
        raise HTTPException(status_code=401, detail="未登录")
    return request.session.get("username")


"""
    核心：装饰器 = 把普通函数变成 API 接口。
    路由装饰器，作用是：把函数注册到 FastAPI 的路由表，并指定"HTTP 方法 + 路径
"""
@router.get(
    "", 
    response_model=List[StudentResponse],
    responses={
        200: {"description": "获取成功"},
        401: {"description": "未登录"},
    },
)
def get_students(
    username: Annotated[str, Depends(require_login)],
    db: Annotated[Session, Depends(get_db)]
):
    """获取所有学生"""      
    students = db.query(Student).order_by(Student.created_at.desc()).all()
    # return students
    return [
        StudentResponse(
            id = s.id,
            name = s.student_name,
            student_id = s.student_id,
            age = s.student_age
        )
        for s in students
    ]


"""核心：装饰器 = 把普通函数变成 API 接口。"""
@router.get(
    "/search",
    response_model=List[StudentResponse],
    responses={
        200:{"description": "搜索成功"},
        401:{"description": "未登录"}
    }
)
def search_students(
    username: Annotated[str, Depends(require_login)], 
    db: Annotated[Session, Depends(get_db)],
    name: Annotated[Optional[str], Query()] = None, 
    student_id: Annotated[Optional[str], Query()] = None,
    age: Annotated[Optional[int],Query()] = None,
):
    """搜索学生"""
    query = db.query(Student)
    if name:
        query = query.filter(Student.student_name.ilike(f"%{name}%"))
    if student_id:
        query = query.filter(Student.student_id.ilike(f"%{student_id}%"))
    if age:
        query = query.filter(Student.student_age == age)
    students = query.order_by(Student.created_at.desc()).all()
    return [
        StudentResponse(
            id = s.id,
            name = s.student_name,
            student_id = s.student_id,
            age = s.student_age
        )
        for s in students
    ]


@router.get(
    "/{db_id}", 
    response_model=StudentResponse, 
    responses={
        200:{"description": "获取成功"},
        401: {"description": "未登录"},
        404:{"description": "学生不存在"}
    }
)
def get_student(
    db_id:int,
    username: Annotated[str, Depends(require_login)],
    db: Annotated[Session, Depends(get_db)]
):
    """获取单个学生"""
    student = db.query(Student).filter(Student.id == db_id).first()
    if not student:
        raise HTTPException(status_code=404, detail='学生不存在')
    return StudentResponse(
            id = student.id,
            name = student.student_name,
            student_id = student.student_id,
            age = student.student_age
        ) 
    


@router.post(
    "", 
    response_model=dict,
    responses={
        200: {"description": "添加成功"},
        400: {"description": "学号已存在"},
        401: {"description": "未登录"},
        422: {"description": "参数验证失败"},
    },
)
def add_student(data: StudentCreate, username: Annotated[str, Depends(require_login)], db: Annotated[Session, Depends(get_db)]):
    """添加学生"""
    # 检查学号是否已存在
    existing = db.query(Student).filter(Student.student_id == data.student_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="学号已经存在")
    students = Student(
        student_name = data.name,
        student_id = data.student_id,
        student_age = data.age
    )
    db.add(students)
    db.commit()
    db.refresh(students)
    return {"success": True, "message": "学生添加成功"}

# @router.put("/{db_id}", response_model=dict) # 因为返回的是字典,return {"success": True, "message": "学生更新成功"}
@router.put(
    "/{db_id}", 
    response_model=SuccessResponse,
    responses={
        200: {"description": "更新成功"},
        400: {"description": "学号已被其他学生占用"},
        401: {"description": "未登录"},
        404: {"description": "学生不存在"},   # 改 400 → 404
        422: {"description": "参数验证失败"},
    },
)
def update_student(
    db_id: int,
    data:StudentUpdate, 
    username: Annotated[str, Depends(require_login)], 
    db: Annotated[Session, Depends(get_db)]
):
    """更新学生"""
    student = db.query(Student).filter(Student.id == db_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="学生不存在")

    # 检查学号是否被其他学生占用
    conflict = db.query(Student).filter(Student.id != db_id, Student.student_id == data.student_id).first()
    if conflict:
        raise HTTPException(status_code=400, detail="学号已被其他学生占用")

    # 更新学生（实例，不是类:如这个是错误的Student.student_name = data.name）
    student.student_name = data.name
    student.student_id = data.student_id
    student.student_age = data.age
    db.commit()
    db.refresh(student)
    return {"success": True, "message": "学生更新成功"}


@router.delete(
    "/{db_id}", 
    response_model=SuccessResponse,
    responses={
        200: {"description": "删除成功"},
        401: {"description": "未登录"},
        404: {"description": "学生不存在"},   # 改 400 → 404
    },
)
def delete_student(db_id: int, username: Annotated[str, Depends(require_login)], db: Annotated[Session, Depends(get_db)]):
    """删除学生"""
    student = db.query(Student).filter(Student.id == db_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="学生不存在")
    db.delete(student)
    db.commit()
    return {"success": True, "message": "学生删除成功"}