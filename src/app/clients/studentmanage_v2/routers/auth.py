# src/app/clients/studentmanage_v2/routers/auth.py
from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models_db import StudentUser 
from ..models import RegisterRequest, LoginRequest, LoginResponse
from typing import Annotated
from ..security import  hash_password, verify_password #  加密密码

router = APIRouter(prefix="/api/student/auth", tags=["student-auth"])

# 通用的角色检查依赖
def require_login(request: Request):
    """要求登录"""
    if not request.session.get("logged_in"):
        raise HTTPException(status_code=401, detail="未登录")
    return request.session.get("username")

# 角色检查工厂
def require_role(*allowed_roles: str):
    """
        用法：
            @router.delete("/xx")
            def delete(..., role: Annotated[str, Depends(require_role("admin"))]):
                ...
    """
    def checker(request: Request):
        if not request.session.get("logged_in"):
            raise HTTPException(status_code=401, detail="未登录")
        role = request.session.get("role", "viewer")
        if role not in allowed_roles:
            raise HTTPException(status_code=403, detail=f"权限不足，需要角色：{allowed_roles}") 
        return role
    return checker  # ← 返回函数本身，不执行



@router.post("/register",response_model=LoginResponse)
def register(data: RegisterRequest, db: Annotated[Session, Depends(get_db)]):
    """注册"""
    username = data.username.strip()
    password = data.password.strip()
    if not username or not password:
        return LoginResponse(success= False, message= "用户名或密码不能为空")
    # 检查用户是否已存在
    existing = db.query(StudentUser).filter(StudentUser.st_username == username).first()
    if existing:
        return LoginResponse(success=False, message="用户已存在")
    # 加密密码
    hashed = hash_password(password)

    # 新注册用户默认 viewer，第一个用户给 admin
    use_account = db.query(StudentUser).count()
    role = "admin" if use_account == 0 else "viewer"

    # 创建用户
    user = StudentUser(
        st_username = username, 
        st_password = hashed,
        role = role,
    )
    db.add(user)
    db.commit()
    return LoginResponse(success=True, message=f"注册成功（角色：{role}）")

@router.post("/login", response_model=LoginResponse)
def login(data: LoginRequest, request: Request, db: Annotated[Session, Depends(get_db)]):
    """登录"""
    username = data.username.strip()
    password = data.password.strip()
    if not username or not password:
        return LoginResponse(success= False, message= "用户名或密码不能为空")
    if not username:
        return LoginResponse(success= False, message= "请输入用户名")
    if not password:
        return LoginResponse(success= False, message= "请输入密码")
    
    user = db.query(StudentUser).filter(StudentUser.st_username == username).first()
    if not user or not verify_password(password, user.st_password):
        return LoginResponse(success=False, message="用户名或密码不正确")

    # 用 Session 保存登录状态
    request.session["logged_in"] = True
    request.session["username"] = username
    request.session["role"] = user.role
    return LoginResponse(success=True, message="登录成功")

@router.post("/logout")
def lougout(request: Request):  # 定义一个异步函数lougout
    """登出"""   # 使用多行字符串作为函数文档字符串，说明函数功能为"登出"
    request.session.clear()
    return {"message": "登出成功"}

@router.get("/session")
def get_session(request: Request):
    """
        获取当前会话状态。

        /session 的作用：
        判断用户是否登录
        获取当前用户名
        决定显示哪个页面
    """
    return {
        "logged_in": request.session.get("logged_in", False),
        "username": request.session.get("username", ""),
        "role": request.session.get("role", "viewer"), # session.get(key, default) ，default是"session 里没有 role 时的兜底默认值"。 admin , teacher, viewer
    }