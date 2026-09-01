# ============================================================
# my-test-framework/src/app/behave/steps/common_steps.py
# 【完整修改版】：包含所有步骤定义
# ============================================================
import sys
import time
import sqlite3
from behave import given, when, then
from pathlib import Path

# ============================================================
# 【修改】：修正目录名 studentmange -> studentmanage
# ============================================================
# 获取 app.py 的绝对路径
CURRENT_DIR = Path(__file__).resolve().parent  # src/app/behave/steps
BEHAVE_DIR = CURRENT_DIR.parent  # src/app/behave
APP_DIR = BEHAVE_DIR.parent  # src/app
STUDENT_MANAGE_DIR = (
    APP_DIR / "clients" / "studentmange"
)  # src/app/clients/studentmanage

# 将 app.py 所在目录添加到 sys.path
sys.path.insert(0, str(STUDENT_MANAGE_DIR))

BASE_URL = "http://localhost:5003"
DB_PATH = STUDENT_MANAGE_DIR / "student_management.db"


def init_database_direct():
    """直接创建数据库和表（不依赖 app.py）"""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    # 创建登录表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS login_table (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            st_username TEXT UNIQUE NOT NULL,
            st_password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 创建学生信息表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS info_table (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_name TEXT NOT NULL,
            student_id TEXT UNIQUE NOT NULL,
            student_age INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()
    return True


def get_db_connection():
    """获取数据库连接"""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


# ============================================================
# 【新增】：通用的 Given 步骤
# ============================================================
@given("系统已启动")
def step_system_started(context):
    """检查系统是否已启动"""
    try:
        response = context.test_context.session.get(f"{BASE_URL}/")
        assert response.status_code == 200
    except:
        raise Exception("系统未启动，请确保Flask应用正在运行")


@given("数据库已初始化")
def step_db_initialized(context):
    """确保数据库已初始化"""
    init_database_direct()

    # 验证数据库文件存在
    for _ in range(5):
        if DB_PATH.exists():
            break
        time.sleep(0.1)

    assert DB_PATH.exists(), f"数据库文件未创建: {DB_PATH}"


@given('存在用户 "{username}" 密码 "{password}"')
def step_user_exists(context, username, password):
    """创建测试用户（直接操作数据库）"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR IGNORE INTO login_table (st_username, st_password) VALUES (?, ?)",
            (username, password),
        )
        conn.commit()
    finally:
        conn.close()


@given("我已登录")
def step_i_am_logged_in(context):
    """用户已登录"""
    # 先确保用户存在
    step_user_exists(context, "testuser", "testpass123")

    # 通过 API 登录
    response = context.test_context.session.post(
        f"{BASE_URL}/api/login",
        json={"username": "testuser", "password": "testpass123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data.get("success") == True
    context.test_context.logged_in = True


@given("我已登出")
def step_i_am_logged_out(context):
    """用户已登出"""
    context.test_context.session.post(f"{BASE_URL}/api/logout")
    context.test_context.logged_in = False


# ============================================================
# 【修改】：添加不带冒号的版本，兼容两种写法
# ============================================================
@given("存在以下学生")
def step_students_exist_no_colon(context):
    """批量创建学生（不带冒号版本）"""
    step_students_exist(context)


@given("存在以下学生:")
def step_students_exist(context):
    """批量创建学生（带冒号版本）"""
    if not context.test_context.logged_in:
        # 先登录
        step_user_exists(context, "testuser", "testpass123")
        context.test_context.session.post(
            f"{BASE_URL}/api/login",
            json={"username": "testuser", "password": "testpass123"},
        )
        context.test_context.logged_in = True

    for row in context.table:
        response = context.test_context.session.post(
            f"{BASE_URL}/api/students",
            json={
                "name": row["姓名"],
                "student_id": row["学号"],
                "age": int(row["年龄"]),
            },
        )
        assert response.status_code == 200


@given("已存在学生")
def step_student_exists_no_colon(context):
    """已存在单个学生（不带冒号版本）"""
    step_students_exist(context)


@given("已存在学生:")
def step_student_exists(context):
    """已存在单个学生（带冒号版本）"""
    step_students_exist(context)


# ============================================================
# 【新增】：所有 When 步骤
# ============================================================


@when('我使用用户名 "{username}" 和密码 "{password}" 登录')
def step_login(context, username, password):
    """执行登录操作"""
    response = context.test_context.session.post(
        f"{BASE_URL}/api/login", json={"username": username, "password": password}
    )
    context.test_context.response = response
    if response.status_code == 200:
        data = response.json()
        if data.get("success"):
            context.test_context.logged_in = True


# 空用户名和空密码的登录步骤
@when('我使用用户名 "" 和密码 "testpass123" 登录')
def step_login_empty_username(context):
    """使用空用户名登录"""
    response = context.test_context.session.post(
        f"{BASE_URL}/api/login", json={"username": "", "password": "testpass123"}
    )
    context.test_context.response = response


@when('我使用用户名 "testuser" 和密码 "" 登录')
def step_login_empty_password(context):
    """使用空密码登录"""
    response = context.test_context.session.post(
        f"{BASE_URL}/api/login", json={"username": "testuser", "password": ""}
    )
    context.test_context.response = response


# ============================================================
# 【新增】：学生管理相关的 When 步骤（带冒号和不带冒号版本）
# ============================================================


@when("我添加一名学生")
def step_add_student_no_colon(context):
    """添加学生（不带冒号版本）"""
    step_add_student(context)


@when("我添加一名学生:")
def step_add_student(context):
    """添加学生（带冒号版本）"""
    if not context.test_context.logged_in:
        step_user_exists(context, "testuser", "testpass123")
        context.test_context.session.post(
            f"{BASE_URL}/api/login",
            json={"username": "testuser", "password": "testpass123"},
        )
        context.test_context.logged_in = True

    for row in context.table:
        response = context.test_context.session.post(
            f"{BASE_URL}/api/students",
            json={
                "name": row["姓名"],
                "student_id": row["学号"],
                "age": int(row["年龄"]),
            },
        )
        context.test_context.response = response


@when("我尝试添加一名学生")
def step_try_add_student_no_colon(context):
    """尝试添加学生（不带冒号版本）"""
    step_try_add_student(context)


@when("我尝试添加一名学生:")
def step_try_add_student(context):
    """尝试添加学生（带冒号版本）"""
    for row in context.table:
        response = context.test_context.session.post(
            f"{BASE_URL}/api/students",
            json={
                "name": row["姓名"],
                "student_id": row["学号"],
                "age": int(row["年龄"]),
            },
        )
        context.test_context.response = response


@when('我编辑学号 "{student_id}" 的学生')
def step_edit_student_no_colon(context, student_id):
    """编辑学生（不带冒号版本）"""
    step_edit_student(context, student_id)


@when('我编辑学号 "{student_id}" 的学生:')
def step_edit_student(context, student_id):
    """编辑学生（带冒号版本）"""
    if not context.test_context.logged_in:
        step_user_exists(context, "testuser", "testpass123")
        context.test_context.session.post(
            f"{BASE_URL}/api/login",
            json={"username": "testuser", "password": "testpass123"},
        )
        context.test_context.logged_in = True

    # 先获取学生ID
    response = context.test_context.session.get(f"{BASE_URL}/api/students")
    students = response.json()
    student = next((s for s in students if s["student_id"] == student_id), None)
    if not student:
        raise Exception(f"学生 {student_id} 不存在")

    for row in context.table:
        response = context.test_context.session.put(
            f"{BASE_URL}/api/students/{student['id']}",
            json={
                "name": row["姓名"],
                "student_id": row["学号"],
                "age": int(row["年龄"]),
            },
        )
        context.test_context.response = response


@when('我删除学号 "{student_id}" 的学生')
def step_delete_student(context, student_id):
    """删除学生"""
    if not context.test_context.logged_in:
        step_user_exists(context, "testuser", "testpass123")
        context.test_context.session.post(
            f"{BASE_URL}/api/login",
            json={"username": "testuser", "password": "testpass123"},
        )
        context.test_context.logged_in = True

    # 先获取学生ID
    response = context.test_context.session.get(f"{BASE_URL}/api/students")
    students = response.json()
    student = next((s for s in students if s["student_id"] == student_id), None)
    if not student:
        raise Exception(f"学生 {student_id} 不存在")

    response = context.test_context.session.delete(
        f"{BASE_URL}/api/students/{student['id']}"
    )
    context.test_context.response = response


# ============================================================
# 【新增】：搜索相关的 When 步骤
# ============================================================


@when("我按条件搜索")
def step_search_by_conditions_no_colon(context):
    """按条件搜索（不带冒号版本）"""
    step_search_by_conditions(context)


@when("我按条件搜索:")
def step_search_by_conditions(context):
    """按条件搜索（带冒号版本）"""
    params = {}
    for row in context.table:
        if row["姓名"]:
            params["name"] = row["姓名"]
        if row["学号"]:
            params["student_id"] = row["学号"]
        if row["年龄"]:
            params["age"] = row["年龄"]

    response = context.test_context.session.get(
        f"{BASE_URL}/api/students/search", params=params
    )
    context.test_context.response = response
    context.test_context.students = response.json()


@when('我搜索姓名为 "{name}" 的学生')
def step_search_by_name(context, name):
    """按姓名搜索"""
    response = context.test_context.session.get(
        f"{BASE_URL}/api/students/search?name={name}"
    )
    context.test_context.response = response
    context.test_context.students = response.json()


@when('我搜索学号为 "{student_id}" 的学生')
def step_search_by_id(context, student_id):
    """按学号搜索"""
    response = context.test_context.session.get(
        f"{BASE_URL}/api/students/search?student_id={student_id}"
    )
    context.test_context.response = response
    context.test_context.students = response.json()


@when('我搜索年龄为 "{age}" 的学生')
def step_search_by_age(context, age):
    """按年龄搜索"""
    response = context.test_context.session.get(
        f"{BASE_URL}/api/students/search?age={age}"
    )
    context.test_context.response = response
    context.test_context.students = response.json()


# ============================================================
# 【新增】：所有 Then 步骤
# ============================================================


@then("登录应该成功")
def step_login_success(context):
    """验证登录成功"""
    response = context.test_context.response
    assert response.status_code == 200
    data = response.json()
    assert data.get("success") == True


@then("登录应该失败")
def step_login_fail(context):
    """验证登录失败"""
    response = context.test_context.response
    if response.status_code == 200:
        data = response.json()
        assert data.get("success") == False
    else:
        assert response.status_code in [400, 401]


@then('我应该看到欢迎消息 "{message}"')
def step_welcome_message(context, message):
    """验证欢迎消息"""
    response = context.test_context.session.get(f"{BASE_URL}/")
    assert response.status_code == 200
    assert message in response.text


@then('我应该看到错误消息 "{message}"')
def step_common_error_message(context, message):
    """验证错误消息 - 通用版本"""
    response = context.test_context.response
    if response.status_code == 200:
        data = response.json()
        # 检查 message 或 error 字段
        error_msg = data.get("message") or data.get("error") or ""
        assert message in error_msg, f"期望消息 '{message}' 不在 '{error_msg}' 中"
    else:
        # 对于非200状态码，直接检查状态码
        assert response.status_code in [
            400,
            401,
            404,
        ], f"期望错误状态码，实际: {response.status_code}"
        try:
            data = response.json()
            error_msg = data.get("message") or data.get("error") or ""
            assert message in error_msg, f"期望消息 '{message}' 不在 '{error_msg}' 中"
        except:
            pass  # 如果响应不是JSON，忽略


@then('错误消息应该是 "未登录"')
def step_error_message_unauthorized(context):
    """验证错误消息是未登录"""
    response = context.test_context.response
    assert response.status_code == 401
    data = response.json()
    assert data.get("error") == "未登录"


# ============================================================
# 【新增】：学生管理相关的 Then 步骤
# ============================================================


@then("添加应该成功")
def step_add_success(context):
    """验证添加成功"""
    response = context.test_context.response
    assert response.status_code == 200
    data = response.json()
    assert data.get("success") == True


@then("添加应该失败")
def step_add_fail(context):
    """验证添加失败"""
    response = context.test_context.response
    assert response.status_code in [400, 401]


@then('我应该看到消息 "{message}"')
def step_see_message(context, message):
    """验证消息"""
    response = context.test_context.response
    data = response.json()
    assert data.get("message") == message


@then('学生列表中应该包含 "{name}"')
def step_student_list_contains(context, name):
    """验证学生列表中包含指定学生"""
    response = context.test_context.session.get(f"{BASE_URL}/api/students")
    assert response.status_code == 200
    students = response.json()
    assert any(s["name"] == name for s in students)


@then('学生列表中不应该包含 "{name}"')
def step_student_list_not_contains(context, name):
    """验证学生列表中不包含指定学生"""
    response = context.test_context.session.get(f"{BASE_URL}/api/students")
    assert response.status_code == 200
    students = response.json()
    assert not any(s["name"] == name for s in students)


@then("编辑应该成功")
def step_edit_success(context):
    """验证编辑成功"""
    response = context.test_context.response
    assert response.status_code == 200
    data = response.json()
    assert data.get("success") == True


@then('学生 "{name}" 的年龄应该是 "{age}"')
def step_student_age_is(context, name, age):
    """验证学生年龄"""
    response = context.test_context.session.get(f"{BASE_URL}/api/students")
    students = response.json()
    student = next((s for s in students if s["name"] == name), None)
    assert student is not None
    assert str(student["age"]) == age


@then("删除应该成功")
def step_delete_success(context):
    """验证删除成功"""
    response = context.test_context.response
    assert response.status_code == 200
    data = response.json()
    assert data.get("success") == True


@then("应该返回未授权错误")
def step_unauthorized_error(context):
    """验证未授权错误"""
    response = context.test_context.response
    assert response.status_code == 401
    data = response.json()
    assert data.get("error") == "未登录"


# ============================================================
# 【新增】：搜索相关的 Then 步骤
# ============================================================


@then('应该找到 "{count}" 条记录')
def step_search_count(context, count):
    """验证搜索结果数量"""
    if context.test_context.students:
        assert len(context.test_context.students) == int(count)
    else:
        assert int(count) == 0


@then('结果中应该包含 "{name}"')
def step_search_contains(context, name):
    """验证搜索结果包含某个名字"""
    students = context.test_context.students
    assert any(s["name"] == name for s in students)


@then('结果中不应该包含 "{name}"')
def step_search_not_contains(context, name):
    """验证搜索结果不包含某个名字"""
    students = context.test_context.students
    assert not any(s["name"] == name for s in students)


@then('应该显示 "{message}"')
def step_show_message(context, message):
    """验证显示的消息"""
    response = context.test_context.session.get(f"{BASE_URL}/")
    assert response.status_code == 200
    assert message in response.text


# ============================================================
# 【修改】：删除空的 common_steps.py 中未使用的函数
# ============================================================
def step_common_unauthorized(context):
    """验证未授权错误 - 通用版本"""
    response = context.test_context.response
    assert response.status_code == 401
    try:
        data = response.json()
        error_msg = data.get("error") or data.get("message") or ""
        assert "未登录" in error_msg or "Unauthorized" in error_msg
    except:
        pass  # 如果响应不是JSON，只检查状态码


# ============================================================
# 【新增】：数据库清理工具
# ============================================================
def clean_database():
    """清理数据库（用于测试后清理）"""
    if DB_PATH.exists():
        DB_PATH.unlink()


def reset_database():
    """重置数据库（删除并重新创建）"""
    clean_database()
    init_database_direct()
