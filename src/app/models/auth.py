# 模型就做4件事：写4中请求，LoginRequest,LoginResponse,StudentRequest,StudentResponse
from __future__ import annotations
from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str = Field(..., description="用户名", min_length=1)
    password: str = Field(..., description="密码", min_length=1)


class LoginResponse(BaseModel):
    message: str = Field()
    success: bool
    token: str | None = None


class StudentRequest(BaseModel):
    name: str = Field(..., description="学生姓名", min_length=1)
    age: int = Field(..., description="学生年龄", ge=0)
    gender: str = Field(..., description="学生性别", min_length=1)
    class_name: str = Field(description="学生班级", min_length=1, alias="class_name")


class StudentResponse(BaseModel):
    message: str
    success: bool
    student_id: int | None = None
