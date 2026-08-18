# test_app_cp.py
import unittest
import json
import os
import tempfile
from app_cp import app, get_db, init_database


class AppTestCase(unittest.TestCase):
    """测试Flask应用"""

    def setUp(self):
        """每个测试前的准备工作"""
        # 创建临时数据库文件
        self.db_fd, self.db_path = tempfile.mkstemp()
        # 覆盖全局数据库路径
        import python_web.src.app.app_cp as app_cp

        app_cp.DB_PATH = self.db_path

        # 设置测试模式
        app.config["TESTING"] = True
        app.config["SECRET_KEY"] = "test_secret_key"
        self.client = app.test_client()

        # 初始化数据库
        init_database()

        # 创建一个测试用户并登录
        self._create_test_user()
        self._login_test_user()

    def tearDown(self):
        """每个测试后的清理工作"""
        os.close(self.db_fd)
        os.unlink(self.db_path)

    def _create_test_user(self):
        """创建测试用户"""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO login_table (st_username, st_password) VALUES (?, ?)",
            ("testuser", "testpass123"),
        )
        conn.commit()
        conn.close()

    def _login_test_user(self):
        """登录测试用户"""
        response = self.client.post(
            "/api/login", json={"username": "testuser", "password": "testpass123"}
        )
        return response

    def _add_test_student(self, name="张三", student_id="S001", age=20):
        """添加测试学生"""
        response = self.client.post(
            "/api/students", json={"name": name, "student_id": student_id, "age": age}
        )
        return response

    # ============ 用户认证测试 ============

    def test_register_success(self):
        """测试注册成功"""
        response = self.client.post(
            "/api/register", json={"username": "newuser", "password": "newpass123"}
        )
        data = json.loads(response.data)
        self.assertTrue(data["success"])
        self.assertEqual(data["message"], "注册成功")

    def test_register_existing_user(self):
        """测试注册已存在的用户"""
        response = self.client.post(
            "/api/register", json={"username": "testuser", "password": "testpass123"}
        )
        data = json.loads(response.data)
        self.assertFalse(data["success"])
        self.assertEqual(data["message"], "用户名已存在")

    def test_register_empty_username(self):
        """测试注册空用户名"""
        response = self.client.post(
            "/api/register", json={"username": "", "password": "testpass123"}
        )
        data = json.loads(response.data)
        self.assertFalse(data["success"])
        self.assertEqual(data["message"], "用户名或密码不能为空")

    def test_login_success(self):
        """测试登录成功"""
        response = self.client.post(
            "/api/login", json={"username": "testuser", "password": "testpass123"}
        )
        data = json.loads(response.data)
        self.assertTrue(data["success"])
        self.assertEqual(data["message"], "登录成功")

    def test_login_wrong_password(self):
        """测试密码错误"""
        response = self.client.post(
            "/api/login", json={"username": "testuser", "password": "wrongpassword"}
        )
        data = json.loads(response.data)
        self.assertFalse(data["success"])
        self.assertEqual(data["message"], "用户名或密码错误")

    def test_login_empty_credentials(self):
        """测试空凭证登录"""
        response = self.client.post("/api/login", json={"username": "", "password": ""})
        data = json.loads(response.data)
        self.assertFalse(data["success"])
        self.assertEqual(data["message"], "用户名或密码不能为空")

    def test_logout(self):
        """测试登出"""
        response = self.client.post("/api/logout")
        data = json.loads(response.data)
        self.assertEqual(data["message"], "登出成功")

    # ============ 学生管理测试 ============

    def test_get_students_unauthorized(self):
        """测试未登录获取学生列表"""
        # 先登出
        self.client.post("/api/logout")
        response = self.client.get("/api/students")
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.data)
        self.assertEqual(data["error"], "未登录")

    def test_add_student_success(self):
        """测试添加学生成功"""
        response = self._add_test_student()
        data = json.loads(response.data)
        self.assertTrue(data["success"])
        self.assertEqual(data["message"], "学生添加成功")

    def test_add_student_duplicate_id(self):
        """测试添加重复学号的学生"""
        self._add_test_student(student_id="S001")
        response = self.client.post(
            "/api/students", json={"name": "李四", "student_id": "S001", "age": 22}
        )
        data = json.loads(response.data)
        self.assertFalse(data["success"])
        self.assertEqual(data["message"], "学号已存在")

    def test_add_student_unauthorized(self):
        """测试未登录添加学生"""
        self.client.post("/api/logout")
        response = self.client.post(
            "/api/students", json={"name": "张三", "student_id": "S001", "age": 20}
        )
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.data)
        self.assertEqual(data["error"], "未登录")

    def test_get_students(self):
        """测试获取学生列表"""
        # 先添加几个学生
        self._add_test_student("张三", "S001", 20)
        self._add_test_student("李四", "S002", 22)

        response = self.client.get("/api/students")
        data = json.loads(response.data)
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["name"], "李四")  # 按创建时间降序

    def test_get_student_by_id(self):
        """测试根据ID获取学生"""
        # 添加学生
        self._add_test_student()
        # 获取学生列表
        response = self.client.get("/api/students")
        students = json.loads(response.data)
        student_id = students[0]["id"]

        # 获取单个学生
        response = self.client.get(f"/api/students/{student_id}")
        data = json.loads(response.data)
        self.assertEqual(data["name"], "张三")
        self.assertEqual(data["student_id"], "S001")
        self.assertEqual(data["age"], 20)

    def test_get_student_not_found(self):
        """测试获取不存在的学生"""
        response = self.client.get("/api/students/9999")
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertEqual(data["error"], "学生不存在")

    def test_update_student_success(self):
        """测试更新学生信息"""
        # 添加学生
        self._add_test_student()
        response = self.client.get("/api/students")
        students = json.loads(response.data)
        student_id = students[0]["id"]

        # 更新学生
        response = self.client.put(
            f"/api/students/{student_id}",
            json={"name": "王五", "student_id": "S003", "age": 25},
        )
        data = json.loads(response.data)
        self.assertTrue(data["success"])
        self.assertEqual(data["message"], "学生信息更新成功")

        # 验证更新
        response = self.client.get(f"/api/students/{student_id}")
        data = json.loads(response.data)
        self.assertEqual(data["name"], "王五")
        self.assertEqual(data["student_id"], "S003")
        self.assertEqual(data["age"], 25)

    def test_update_student_invalid_age(self):
        """测试更新学生时年龄无效"""
        self._add_test_student()
        response = self.client.get("/api/students")
        students = json.loads(response.data)
        student_id = students[0]["id"]

        response = self.client.put(
            f"/api/students/{student_id}",
            json={"name": "王五", "student_id": "S003", "age": -1},
        )
        data = json.loads(response.data)
        self.assertFalse(data["success"])
        self.assertEqual(data["message"], "年龄必须是1-150之间的数字")

    def test_delete_student_success(self):
        """测试删除学生"""
        # 添加学生
        self._add_test_student()
        response = self.client.get("/api/students")
        students = json.loads(response.data)
        student_id = students[0]["id"]

        # 删除学生
        response = self.client.delete(f"/api/students/{student_id}")
        data = json.loads(response.data)
        self.assertTrue(data["success"])
        self.assertEqual(data["message"], "学生删除成功")

        # 验证已删除
        response = self.client.get("/api/students")
        students = json.loads(response.data)
        self.assertEqual(len(students), 0)

    def test_delete_student_unauthorized(self):
        """测试未登录删除学生"""
        self._add_test_student()
        response = self.client.get("/api/students")
        students = json.loads(response.data)
        student_id = students[0]["id"]

        self.client.post("/api/logout")
        response = self.client.delete(f"/api/students/{student_id}")
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.data)
        self.assertEqual(data["error"], "未登录")

    # ============ 搜索功能测试 ============

    def test_search_students_by_name(self):
        """测试按姓名搜索"""
        self._add_test_student("张三", "S001", 20)
        self._add_test_student("李四", "S002", 22)
        self._add_test_student("张伟", "S003", 21)

        response = self.client.get("/api/students/search?name=张")
        data = json.loads(response.data)
        self.assertEqual(len(data), 2)
        self.assertTrue(all("张" in s["name"] for s in data))

    def test_search_students_by_student_id(self):
        """测试按学号搜索"""
        self._add_test_student("张三", "S001", 20)
        self._add_test_student("李四", "S002", 22)

        response = self.client.get("/api/students/search?student_id=001")
        data = json.loads(response.data)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["student_id"], "S001")

    def test_search_students_by_age(self):
        """测试按年龄搜索"""
        self._add_test_student("张三", "S001", 20)
        self._add_test_student("李四", "S002", 22)
        self._add_test_student("王五", "S003", 20)

        response = self.client.get("/api/students/search?age=20")
        data = json.loads(response.data)
        self.assertEqual(len(data), 2)
        self.assertTrue(all(s["age"] == 20 for s in data))

    def test_search_students_multiple_conditions(self):
        """测试多条件搜索"""
        self._add_test_student("张三", "S001", 20)
        self._add_test_student("张伟", "S002", 22)

        response = self.client.get("/api/students/search?name=张&age=20")
        data = json.loads(response.data)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["name"], "张三")

    def test_search_students_no_results(self):
        """测试搜索无结果"""
        self._add_test_student("张三", "S001", 20)

        response = self.client.get("/api/students/search?name=李")
        data = json.loads(response.data)
        self.assertEqual(len(data), 0)

    def test_search_students_unauthorized(self):
        """测试未登录搜索"""
        self.client.post("/api/logout")
        response = self.client.get("/api/students/search?name=张")
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.data)
        self.assertEqual(data["error"], "未登录")

    # ============ 页面访问测试 ============

    def test_index_page_unauthorized(self):
        """测试未登录访问主页"""
        self.client.post("/api/logout")
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        # self.assertIn(b'学生管理系统', response.data)
        self.assertIn("学生管理系统".encode(), response.data)
        # self.assertIn(b'登录', response.data)
        self.assertIn("登录".encode(), response.data)

    def test_index_page_authorized(self):
        """测试已登录访问主页"""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("学生信息管理系统".encode(), response.data)
        self.assertIn("添加学生".encode(), response.data)

    # ============ 会话测试 ============

    def test_session_persistence(self):
        """测试会话持久性"""
        # 登录
        self.client.post(
            "/api/login", json={"username": "testuser", "password": "testpass123"}
        )

        # 访问需要登录的接口
        response = self.client.get("/api/students")
        self.assertEqual(response.status_code, 200)

        # 登出
        self.client.post("/api/logout")

        # 再次访问
        response = self.client.get("/api/students")
        self.assertEqual(response.status_code, 401)


if __name__ == "__main__":
    unittest.main()
