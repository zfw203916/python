# src/framework/ai/agent/weather/tools/student_native.py
"""
    学生查询工具（给 AI 伴侣用）
    只做一件事：根据关键词查学生，返回原始文本。
"""
from typing import Optional
from ......shared.database import SessionLocal
from ......app.clients.studentmanage_v2.models_db import Student

def get_student_info(name: str = "", student_id: str = "") -> str:
    """
        查询学生信息。

        当用户询问学生的资料、年龄、学号、成绩等信息时使用。

        Args:
            name: 学生姓名（模糊查询）
            student_id: 学号（精确查询）

        Returns:
            学生信息文本
    """
    if not name and not student_id:
        return "❌ 请提供学生姓名或学号。"

    db = SessionLocal()
    try:
        q = db.query(Student)
        if name:
            q = q.filter(Student.student_name.ilike(f"%{name}%"))
        if student_id:
            q = q.filter(Student.student_id == student_id)

        students = q.all()

        if not students:
            return f"❌ 没有找到符合条件的学生（姓名={name}, 学号={student_id}）"
        #拼装返回文本
        lines = [f"📋 找到 {len(students)} 名学生："]
        for s in students:
            lines.append(f"- 姓名：{s.student_name}，学号：{s.student_id}，年龄：{s.student_age}")
        return "\n".join(lines)
    except Exception as e:
        return f"❌ 查询失败: {e}"
    finally:
        db.close()


# 更新工具
def update_student(
    student_id: str = "",
    name: str = "",
    new_name: str = "",
    new_age: int = 0
) -> str:
    """
        更新学生信息。
        当用户要求修改学生的姓名或年龄时使用。
        必须提供 student_id 或 name 用于定位学生。

        Args:
            student_id: 学号（用于定位学生）
            name: 原姓名（用于定位学生，student_id 为空时使用）
            new_name: 新姓名（可选）
            new_age: 新年龄（可选）

        Returns:
            更新结果文本
    """
    if not student_id and not name:
        return "❌ 请提供学号或姓名用于定位学生。"

    if not new_name and not new_age:
        return "❌ 请提供要修改的内容（新姓名或新年龄）。"

    db = SessionLocal()
    try:
        q = db.query(Student)
        if student_id:
            q = q.filter(Student.student_id == student_id)
        if name:
            q = q.filter(Student.student_name == name) 
        student = q.first()
        if not student:
            return f"❌ 没有找到学生（学号={student_id}, 姓名={name})"
        # 记录旧值
        old_info = f"姓名={student.student_name}, 学号={student.student_id}, 年龄={student.student_age}"
        # 更新
        if new_name:
            student.student_name = new_name
        if new_age:
            student.student_age = new_age
        db.commit()
        new_info = f"姓名={student.student_name}, 学号={student.student_id}, 年龄={student.student_age}"
        return f"✅ 更新成功\n修改前：{old_info}\n修改后：{new_info}"
        
    except Exception as e:
        db.rollback()
        return f"❌ 更新失败: {e}"
    finally:
        db.close()


# 删除工具
def delete_student(
    student_id: str = "",
    name: str = "",
) -> str:
    """
        删除学生。
        当用户要求删除某个学生时使用。

        Args:
            student_id: 学号
            name: 姓名

        Returns:
            删除结果文本
    """
    if not student_id and not name:
            return "❌ 请提供学号或姓名用于定位学生。"

    db = SessionLocal()
    try:
        q = db.query(Student)
        if student_id:
            q = q.filter(Student.student_id == student_id)
        elif name:
            q = q.filter(Student.student_name == name)

        student = q.first()
        if not student:
            return f"❌ 没有找到学生（学号={student_id}, 姓名={name})"
        info = f"姓名={student.student_name}, 学号={student.student_id}, 年龄={student.student_age}"
        db.delete(student)
        db.commit()
        return f"✅ 已删除学生：{info}"
    except Exception as e:
        db.rollback()
        return f"❌ 删除失败: {e}"
    finally:
        db.close()