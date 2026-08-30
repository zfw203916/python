from flask import Flask, render_template_string, request, session, jsonify
import sqlite3
import os
import sys


app = Flask(__name__)
app.secret_key = "653-254-338"

# SQLite 数据库文件路径
DB_PATH = "student_management.db"

# HTML 模板
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>学生管理系统</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Microsoft YaHei', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        
        /* 登录页面样式 */
        .login-container {
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            padding: 20px;
        }
        
        .login-box {
            background: white;
            border-radius: 10px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            padding: 40px;
            width: 100%;
            max-width: 400px;
        }
        
        .login-title {
            text-align: center;
            color: #333;
            margin-bottom: 30px;
            font-size: 28px;
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        .form-group label {
            display: block;
            margin-bottom: 5px;
            color: #555;
            font-weight: 500;
        }
        
        .form-group input {
            width: 100%;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 14px;
            transition: border-color 0.3s;
        }
        
        .form-group input:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .btn {
            padding: 10px 20px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
            transition: all 0.3s;
        }
        
        .btn-primary {
            background: #667eea;
            color: white;
            width: 100%;
        }
        
        .btn-primary:hover {
            background: #5a67d8;
        }
        
        .btn-success {
            background: #28a745;
            color: white;
        }
        
        .btn-success:hover {
            background: #218838;
        }
        
        .btn-warning {
            background: #ffc107;
            color: #333;
        }
        
        .btn-warning:hover {
            background: #e0a800;
        }
        
        .btn-danger {
            background: #dc3545;
            color: white;
        }
        
        .btn-danger:hover {
            background: #c82333;
        }
        
        .btn-info {
            background: #17a2b8;
            color: white;
        }
        
        .btn-info:hover {
            background: #138496;
        }
        
        .btn-sm {
            padding: 5px 10px;
            font-size: 12px;
        }
        
        /* 主页面样式 */
        .main-container {
            min-height: 100vh;
        }
        
        .navbar {
            background: white;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            padding: 15px 30px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .navbar h2 {
            color: #333;
        }
        
        .user-info {
            display: flex;
            align-items: center;
            gap: 15px;
        }
        
        .content {
            padding: 30px;
        }
        
        .toolbar {
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 10px;
        }
        
        .search-form {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }
        
        .search-form input {
            padding: 8px 12px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 14px;
        }
        
        .table-container {
            background: white;
            border-radius: 8px;
            overflow-x: auto;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
        }
        
        th, td {
            padding: 12px;
            text-align: center;
            border-bottom: 1px solid #eee;
        }
        
        th {
            background: #f8f9fa;
            color: #555;
            font-weight: 600;
        }
        
        tr:hover {
            background: #f8f9fa;
        }
        
        .action-buttons {
            display: flex;
            gap: 5px;
            justify-content: center;
        }
        
        /* 模态框样式 */
        .modal {
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.5);
            justify-content: center;
            align-items: center;
        }
        
        .modal-content {
            background: white;
            border-radius: 10px;
            padding: 30px;
            width: 90%;
            max-width: 500px;
            max-height: 80vh;
            overflow-y: auto;
        }
        
        .modal-header {
            margin-bottom: 20px;
        }
        
        .modal-header h3 {
            color: #333;
        }
        
        .modal-buttons {
            display: flex;
            gap: 10px;
            justify-content: flex-end;
            margin-top: 20px;
        }
        
        .close {
            float: right;
            cursor: pointer;
            font-size: 24px;
        }
        
        .message {
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 15px 20px;
            border-radius: 5px;
            color: white;
            z-index: 1100;
            animation: slideIn 0.3s ease;
        }
        
        .message-success {
            background: #28a745;
        }
        
        .message-error {
            background: #dc3545;
        }
        
        .message-warning {
            background: #ffc107;
            color: #333;
        }
        
        @keyframes slideIn {
            from {
                transform: translateX(100%);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }
        
        .stats {
            color: #666;
            font-size: 14px;
        }
        
        @media (max-width: 768px) {
            .toolbar {
                flex-direction: column;
            }
            
            .search-form {
                width: 100%;
            }
            
            .search-form input {
                flex: 1;
            }
        }
    </style>
</head>
<body>
    {% if not session.logged_in %}
    <!-- 登录页面 -->
    <div class="login-container">
        <div class="login-box">
            <h2 class="login-title">学生管理系统</h2>
            <form id="loginForm">
                <div class="form-group">
                    <label>用户名</label>
                    <input type="text" id="username" required>
                </div>
                <div class="form-group">
                    <label>密码</label>
                    <input type="password" id="password" required>
                </div>
                <div style="display: flex; gap: 10px;">
                    <button type="button" class="btn btn-primary" onclick="register()">注册</button>
                    <button type="button" class="btn btn-primary" onclick="login()" style="background: #28a745;">登录</button>
                </div>
            </form>
        </div>
    </div>
    {% else %}
    <!-- 主页面 -->
    <div class="main-container">
        <div class="navbar">
            <h2>📚 学生信息管理系统</h2>
            <div class="user-info">
                <span>欢迎, {{ session.username }}</span>
                <button class="btn btn-danger btn-sm" onclick="logout()">退出登录</button>
            </div>
        </div>
        
        <div class="content">
            <div class="toolbar">
                <div class="search-form">
                    <input type="text" id="searchName" placeholder="姓名">
                    <input type="text" id="searchId" placeholder="学号">
                    <input type="text" id="searchAge" placeholder="年龄">
                    <button class="btn btn-primary" onclick="searchStudents()">🔍 查询</button>
                    <button class="btn btn-warning" onclick="resetSearch()">🔄 重置</button>
                </div>
                <div>
                    <button class="btn btn-success" onclick="showAddModal()">➕ 添加学生</button>
                    <button class="btn btn-info" onclick="loadStudents()">🔄 刷新</button>
                </div>
            </div>
            
            <div class="table-container">
                <table id="studentTable">
                    <thead>
                        <tr>
                            <th>姓名</th>
                            <th>学号</th>
                            <th>年龄</th>
                            <th>操作</th>
                        </tr>
                    </thead>
                    <tbody id="studentTableBody">
                        <tr>
                            <td colspan="4" style="text-align: center;">加载中...</td>
                        </tr>
                    </tbody>
                </table>
            </div>
            <div class="stats" id="stats" style="margin-top: 10px;"></div>
        </div>
    </div>
    
    <!-- 添加/编辑模态框 -->
    <div id="studentModal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <span class="close" onclick="closeModal()">&times;</span>
                <h3 id="modalTitle">添加学生</h3>
            </div>
            <form id="studentForm">
                <input type="hidden" id="studentId">
                <div class="form-group">
                    <label>姓名</label>
                    <input type="text" id="studentName" required>
                </div>
                <div class="form-group">
                    <label>学号</label>
                    <input type="text" id="studentNumber" required>
                </div>
                <div class="form-group">
                    <label>年龄</label>
                    <input type="number" id="studentAge" required>
                </div>
                <div class="modal-buttons">
                    <button type="button" class="btn btn-warning" onclick="closeModal()">取消</button>
                    <button type="button" class="btn btn-success" onclick="saveStudent()">保存</button>
                </div>
            </form>
        </div>
    </div>
    {% endif %}
    
    <script>
        function showMessage(msg, type) {
            const messageDiv = document.createElement('div');
            messageDiv.className = `message message-${type}`;
            messageDiv.innerHTML = msg;
            document.body.appendChild(messageDiv);
            setTimeout(() => {
                messageDiv.remove();
            }, 3000);
        }
        
        async function login() {
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            
            if (!username || !password) {
                showMessage('请输入用户名和密码', 'warning');
                return;
            }
            
            const response = await fetch('/api/login', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({username, password})
            });
            
            const data = await response.json();
            if (data.success) {
                showMessage('登录成功', 'success');
                setTimeout(() => location.reload(), 500);
            } else {
                showMessage(data.message, 'error');
            }
        }
        
        async function register() {
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            
            if (!username || !password) {
                showMessage('请输入用户名和密码', 'warning');
                return;
            }
            
            const response = await fetch('/api/register', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({username, password})
            });
            
            const data = await response.json();
            if (data.success) {
                showMessage('注册成功', 'success');
                
            } else {
                showMessage(data.message, 'error');
            }
        }
        
        function logout() {
            fetch('/api/logout', {method: 'POST'})
                .then(() => location.reload());
        }
        
        async function loadStudents() {
            const response = await fetch('/api/students');
            const students = await response.json();
            
            const tbody = document.getElementById('studentTableBody');
            if (students.length === 0) {
                tbody.innerHTML = '<tr><td colspan="4" style="text-align: center;">暂无数据</td></tr>';
                document.getElementById('stats').innerHTML = '共 0 条记录';
                return;
            }
            
            tbody.innerHTML = students.map(s => `
                <tr>
                    <td>${escapeHtml(s.name)}</td>
                    <td>${escapeHtml(s.student_id)}</td>
                    <td>${s.age}</td>
                    <td class="action-buttons">
                        <button class="btn btn-warning btn-sm" onclick="editStudent(${s.id})">编辑</button>
                        <button class="btn btn-danger btn-sm" onclick="deleteStudent(${s.id})">删除</button>
                    </td>
                </tr>
            `).join('');
            
            document.getElementById('stats').innerHTML = `共 ${students.length} 条记录`;
        }
        
        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
        
        async function searchStudents() {
            const name = document.getElementById('searchName').value;
            const student_id = document.getElementById('searchId').value;
            const age = document.getElementById('searchAge').value;
            
            const params = new URLSearchParams();
            if (name) params.append('name', name);
            if (student_id) params.append('student_id', student_id);
            if (age) params.append('age', age);
            
            const response = await fetch(`/api/students/search?${params}`);
            const students = await response.json();
            
            const tbody = document.getElementById('studentTableBody');
            if (students.length === 0) {
                tbody.innerHTML = '<tr><td colspan="4" style="text-align: center;">未找到匹配的学生</td></tr>';
                document.getElementById('stats').innerHTML = '共 0 条记录';
                return;
            }
            
            tbody.innerHTML = students.map(s => `
                <tr>
                    <td>${escapeHtml(s.name)}</td>
                    <td>${escapeHtml(s.student_id)}</td>
                    <td>${s.age}</td>
                    <td class="action-buttons">
                        <button class="btn btn-warning btn-sm" onclick="editStudent(${s.id})">编辑</button>
                        <button class="btn btn-danger btn-sm" onclick="deleteStudent(${s.id})">删除</button>
                    </td>
                </tr>
            `).join('');
            
            document.getElementById('stats').innerHTML = `共 ${students.length} 条记录`;
        }
        
        function resetSearch() {
            document.getElementById('searchName').value = '';
            document.getElementById('searchId').value = '';
            document.getElementById('searchAge').value = '';
            loadStudents();
        }
        
        function showAddModal() {
            document.getElementById('modalTitle').innerText = '添加学生';
            document.getElementById('studentId').value = '';
            document.getElementById('studentName').value = '';
            document.getElementById('studentNumber').value = '';
            document.getElementById('studentAge').value = '';
            document.getElementById('studentModal').style.display = 'flex';
        }
        
        function editStudent(id) {
            fetch(`/api/students/${id}`)
                .then(res => res.json())
                .then(student => {
                    document.getElementById('modalTitle').innerText = '编辑学生';
                    document.getElementById('studentId').value = student.id;
                    document.getElementById('studentName').value = student.name;
                    document.getElementById('studentNumber').value = student.student_id;
                    document.getElementById('studentAge').value = student.age;
                    document.getElementById('studentModal').style.display = 'flex';
                });
        }
        
        async function saveStudent() {
            const id = document.getElementById('studentId').value;
            const name = document.getElementById('studentName').value;
            const student_id = document.getElementById('studentNumber').value;
            const age = document.getElementById('studentAge').value;
            
            if (!name || !student_id || !age) {
                showMessage('请填写所有字段', 'warning');
                return;
            }
            
            const url = id ? `/api/students/${id}` : '/api/students';
            const method = id ? 'PUT' : 'POST';
            
            const response = await fetch(url, {
                method: method,
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({name, student_id, age: parseInt(age)})
            });
            
            const data = await response.json();
            if (data.success) {
                showMessage(data.message, 'success');
                closeModal();
                loadStudents();
            } else {
                showMessage(data.message, 'error');
            }
        }
        
        async function deleteStudent(id) {
            if (confirm('确定要删除这名学生吗？')) {
                const response = await fetch(`/api/students/${id}`, {
                    method: 'DELETE'
                });
                const data = await response.json();
                if (data.success) {
                    showMessage('删除成功', 'success');
                    loadStudents();
                } else {
                    showMessage('删除失败', 'error');
                }
            }
        }
        
        function closeModal() {
            document.getElementById('studentModal').style.display = 'none';
        }
        
        // 点击模态框外部关闭
        window.onclick = function(event) {
            const modal = document.getElementById('studentModal');
            if (event.target === modal) {
                closeModal();
            }
        }
        
        // 页面加载时加载学生数据
        {% if session.logged_in %}
        loadStudents();
        {% endif %}
    </script>
</body>
</html>
"""


def init_database():
    """初始化数据库和表"""
    try:
        # 创建数据库连接
        conn = sqlite3.connect(DB_PATH)
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
        # 只在非测试模式下输出信息
        if not sys.argv[0].endswith("pytest") and "unittest" not in sys.modules:
            print("SQLite数据库初始化完成")
            print(f"数据库位置: {os.path.abspath(DB_PATH)}")
    except Exception as e:
        return jsonify({"status": "error", "message": f"数据库初始化错误: {e}"})


def get_db():
    """获取数据库连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# 初始化数据库
init_database()


@app.route("/")
def index():
    """主页"""
    return render_template_string(HTML_TEMPLATE)


@app.route("/api/register", methods=["POST"])
def api_register():
    """注册API"""
    data = request.get_json()
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()

    if not username or not password:
        return jsonify({"success": False, "message": "用户名或密码不能为空"})

    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO login_table (st_username, st_password) VALUES (?, ?)",
            (username, password),
        )
        conn.commit()
        return jsonify({"success": True, "message": "注册成功"})
    except sqlite3.IntegrityError:
        return jsonify({"success": False, "message": "用户名已存在"})
    except Exception as e:
        return jsonify({"success": False, "message": f"注册失败:{str(e)}"})
    finally:
        conn.close()


@app.route("/api/login", methods=["POST"])
def api_login():
    """登录API"""
    data = request.get_json()
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()


    if not username and not password:
        return jsonify({"success": False, "message": "请输入用户名和密码"})
    if not username:
        return jsonify({"success": False, "message": "请输入用户名"})
    if not password:
        return jsonify({"success": False, "message": "请输入密码"})

    # 在数据库中查找用户
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM login_table WHERE st_username = ?", (username,))
        user = cursor.fetchone()
        if not user:
            # ✅ 用户不存在
            return jsonify({"success": False, "message": "用户不存在"})

        # 2. 用户存在,检查密码
        cursor.execute(
            "SELECT * FROM login_table WHERE st_username = ? AND st_password = ?",
            (username, password),
        )
        user_with_password = cursor.fetchone()
        if user_with_password:
            # 登录成功，设置用户会话
            session["logged_in"] = True
            session["username"] = username
            return jsonify({"success": True, "message": "登录成功"})
        else:
            # ✅ 密码错误
            return jsonify({"success": False, "message": "用户名或密码错误"})
    except Exception as e:
        return jsonify({"success": False, "message": f"登录失败:{str(e)}"})
    finally:
        conn.close()


@app.route("/api/logout", methods=["POST"])
def logout():
    """登出接口"""
    # 清除用户会话
    session.clear()
    return jsonify({"message": "登出成功"})


@app.route("/api/students", methods=["GET"])
def api_get_students():
    """获取所有学生"""
    if not session.get("logged_in"):
        return jsonify({"error": "未登录"}), 401

    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM info_table ORDER BY created_at DESC")
        students = cursor.fetchall()
        return jsonify(
            [
                {
                    "id": s["id"],
                    "name": s["student_name"],
                    "student_id": s["student_id"],
                    "age": s["student_age"],
                }
                for s in students
            ]
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


@app.route("/api/students/search", methods=["GET"])
def api_search_students():
    """搜索学生"""
    if not session.get("logged_in"):
        return jsonify({"error": "未登录"}), 401

    name = request.args.get("name", "").strip()
    student_id = request.args.get("student_id", "").strip()
    age = request.args.get("age", "").strip()
    conn = get_db()

    try:
        cursor = conn.cursor()
        conditions = []
        params = []
        if name:
            conditions.append("student_name LIKE ?")
            params.append(f"%{name}%")

        if student_id:
            conditions.append("student_id  LIKE ?")
            params.append(f"%{student_id}%")

        if age and age.isdigit():
            conditions.append("student_age = ?")
            params.append(int(age))

        if conditions:
            sql = f"SELECT * FROM info_table WHERE {' AND '.join(conditions)}  ORDER BY created_at DESC"
            cursor.execute(sql, params)

        else:
            cursor.execute("SELECT * FROM info_table ORDER BY created_at DESC")

        students = cursor.fetchall()

        return jsonify(
            [
                {
                    "id": s["id"],
                    "name": s["student_name"],
                    "student_id": s["student_id"],
                    "age": s["student_age"],
                }
                for s in students
            ]
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


@app.route("/api/students/<int:student_id>", methods=["GET"])
def api_get_student(student_id):
    """获取单个学生"""
    if not session.get("logged_in"):
        return jsonify({"error": "未登录"}), 401
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM info_table WHERE id = ?", (student_id,))
        student = cursor.fetchone()
        if student:
            return jsonify(
                {
                    "id": student["id"],
                    "name": student["student_name"],
                    "student_id": student["student_id"],
                    "age": student["student_age"],
                }
            )
        else:
            return jsonify({"error": "学生不存在"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


@app.route("/api/students", methods=["POST"])
def api_add_student():
    """添加学生"""
    if not session.get("logged_in"):
        return jsonify({"error": "未登录"}), 401
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO info_table (student_name, student_id, student_age) VALUES (?, ?, ?)",
            (request.json["name"], request.json["student_id"], request.json["age"]),
        )
        conn.commit()
        return jsonify({"success": True, "message": "学生添加成功"}), 200
    except sqlite3.IntegrityError:
        return jsonify({"success": False, "message": "学号已存在"}), 400
    except Exception as e:
        return jsonify({"success": False, "message": f"添加失败: {str(e)}"})
    finally:
        conn.close()


@app.route("/api/students/<int:student_id>", methods=["PUT"])
def api_update_student(student_id):
    """更新学生"""
    if not session.get("logged_in"):
        return jsonify({"error": "未登录"}), 401

    data = request.get_json()
    name = data.get("name", "").strip()
    student_id_new = data.get("student_id", "").strip()
    age = data.get("age")

    if not name or not student_id_new or not age:
        return jsonify({"success": False, "message": "参数不完整"}), 400

    if not isinstance(age, int) or age < 0 or age <= 0 or age > 150:
        return jsonify({"success": False, "message": "年龄必须是1-150之间的数字"})

    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE info_table SET student_name = ?, student_id = ?, student_age = ? WHERE id = ?",
            (name, student_id_new, age, student_id),
        )
        conn.commit()
        return jsonify({"success": True, "message": "学生信息更新成功"}), 200
    except Exception as e:
        return jsonify({"success": False, "message": f"更新失败: {str(e)}"}), 400
    finally:
        conn.close()


@app.route("/api/students/<int:student_id>", methods=["DELETE"])
def api_delete_student(student_id):
    """删除学生"""
    if not session.get("logged_in"):
        return jsonify({"error": "未登录"}), 401

    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM info_table WHERE id = ?", (student_id,))
        conn.commit()
        return jsonify({"success": True, "message": "学生删除成功"}), 200
    except Exception as e:
        return jsonify({"success": False, "message": f"删除失败: {str(e)}"}), 400
    finally:
        conn.close()


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5003)
