# src/app/clients/studentmanage_v2/models.py
from pydantic import BaseModel, Field

"""
    验证请求/响应数据
    是把注册登录和登出的都写在这里？应该是所有请求部分。确切的说是： 请求模型（Request）  包含了更新学生等等。
"""
class RegisterRequest(BaseModel):
    """注册"""
    username: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=1)


class LoginRequest(BaseModel):
    """登录请求"""
    username: str
    password: str

class LoginResponse(BaseModel):
    """登录回调"""
    success: bool
    message: str
class SuccessResponse(BaseModel):
    """成功回调"""
    success: bool
    message: str

class StudentCreate(BaseModel):
    """ 创建学生"""
    name: str = Field(..., min_length=1, max_length=50)
    student_id: str = Field(..., min_length=1, max_length=50)
    age: int = Field(...,ge=1, le=150)


class StudentUpdate(BaseModel):
    """ 更新学生"""
    name: str = Field(..., min_length=1, max_length=50)
    student_id: str = Field(..., min_length=1, max_length=50)
    age: int = Field(...,ge=1, le=150)


class StudentResponse(BaseModel):
    """学生列表"""
    id: int
    name: str
    student_id: str
    age: int
    class Config:   # ← 内部类，配置 StudentResponse 的行为
        from_attributes = True

# class StudentResponse(BaseModel):
#     """学生列表"""
#     id: int
#     student_name: str
#     student_id: str
#     student_age: int
#     class Config:   # ← 内部类，配置 StudentResponse 的行为
#         from_attributes = True