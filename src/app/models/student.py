"""Student data model."""

from pydantic import BaseModel, Field


class Student(BaseModel):
    """Student data model."""

    name: str = Field(..., description="Student name", min_length=2, max_length=20)
    age: int = Field(..., description="Student age", ge=0, le=100)
    grade: int = Field(..., description="Student grade", gt=0, le=12)

    def test_get_function(a: int, b: int) -> None:
        """
        Test get function.这里是调用的函数说明显示
        :param a:整数，测试用
        :param b:整数，测试用:
        """
        print("test:")
        return a, b
