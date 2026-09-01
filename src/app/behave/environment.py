# my-test-framework/src/app/behave/environment.py
import os
import sys
import shutil
import subprocess
import time
import requests

# 添加app.py所在路径到系统路径
APP_PATH = os.path.join(os.path.dirname(__file__), "..", "clients", "studentmange")
sys.path.insert(0, APP_PATH)

BASE_URL = "http://localhost:5003"
DB_PATH = os.path.join(APP_PATH, "student_management.db")


class TestContext:
    """测试上下文，用于在步骤之间共享数据"""

    def __init__(self):
        self.session = requests.Session()
        self.response = None
        self.students = []
        self.current_student = None
        self.logged_in = False


# def before_all(context):
#     """在所有测试开始前执行"""
#     context.test_context = TestContext()
#     context.app_process = None

#     # 备份原始数据库（如果存在）
#     original_db = os.path.join(APP_PATH, "student_management.db")
#     if os.path.exists(original_db):
#         backup_db = os.path.join(APP_PATH, "student_management.db.backup")
#         shutil.copy2(original_db, backup_db)
#         os.remove(original_db)

# 设置为 False 来禁用自动启动
AUTO_START_APP = False


def before_all(context):
    if AUTO_START_APP:
        start_app(context)  # 自动启动
    else:
        print("⚠️ 请手动启动 Flask 应用:")
        print("   cd src/app/clients/studentmanage/")
        print("   python app.py")
        print("   或 python -m flask --app app.py run --port=5003")
        print("等待应用启动...")
        wait_for_app()  # 仍然等待，但不启动


def before_scenario(context, scenario):
    """在每个场景开始前执行"""
    # 重置测试上下文
    context.test_context = TestContext()
    context.test_context.session = requests.Session()

    # 删除旧的数据库文件
    db_path = os.path.join(APP_PATH, "student_management.db")
    if os.path.exists(db_path):
        os.remove(db_path)

    # 启动Flask应用（如果需要）
    if not context.app_process:
        start_app(context)

    # 等待应用启动
    wait_for_app()


def start_app(context):
    """启动Flask应用"""
    app_script = os.path.join(APP_PATH, "app.py")
    context.app_process = subprocess.Popen(
        [sys.executable, app_script],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=APP_PATH,
        env={**os.environ, "PYTHONUNBUFFERED": "1"},
    )


def wait_for_app():
    """等待应用启动完成"""
    max_attempts = 30
    for i in range(max_attempts):
        try:
            response = requests.get(f"{BASE_URL}/", timeout=1)
            if response.status_code == 200:
                return True
        except requests.ConnectionError:
            pass
        time.sleep(0.5)
    raise Exception("Flask应用未能启动")


def after_scenario(context, scenario):
    """在每个场景结束后执行"""
    # 登出
    try:
        context.test_context.session.post(f"{BASE_URL}/api/logout")
    except:
        pass


def after_all(context):
    """在所有测试结束后执行"""
    # 停止Flask应用
    if context.app_process:
        context.app_process.terminate()
        context.app_process.wait(timeout=5)

    # 恢复原始数据库
    original_db = os.path.join(APP_PATH, "student_management.db")
    backup_db = os.path.join(APP_PATH, "student_management.db.backup")
    if os.path.exists(backup_db):
        if os.path.exists(original_db):
            os.remove(original_db)
        shutil.copy2(backup_db, original_db)
        os.remove(backup_db)
