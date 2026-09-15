# my-test-framework/src/app/clients/studentmange_v1/app.py
from flask import Flask, render_template, request, session, jsonify
import sqlite3
import os
import sys

# 获取当前文件所在目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "templates"),
    static_folder=os.path.join(BASE_DIR, "static"),
)
app.secret_key = "653-254-338"

# SQLite 数据库文件路径（放在当前目录下）
DB_PATH = os.path.join(BASE_DIR, "student_management.db")


def init_database():
    """初始化数据库和表"""
    try:
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
        if not sys.argv[0].endswith("pytest") and "unittest" not in sys.modules:
            print("SQLite数据库初始化完成")
            print(f"数据库位置: {DB_PATH}")
    except Exception as e:
        print(f"数据库初始化错误: {e}")


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
    return render_template("index.html")


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

    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM login_table WHERE st_username = ?", (username,))
        user = cursor.fetchone()
        if not user:
            return jsonify({"success": False, "message": "用户不存在"})

        cursor.execute(
            "SELECT * FROM login_table WHERE st_username = ? AND st_password = ?",
            (username, password),
        )
        user_with_password = cursor.fetchone()
        if user_with_password:
            session["logged_in"] = True
            session["username"] = username
            return jsonify({"success": True, "message": "登录成功"})
        else:
            return jsonify({"success": False, "message": "用户名或密码错误"})
    except Exception as e:
        return jsonify({"success": False, "message": f"登录失败:{str(e)}"})
    finally:
        conn.close()


@app.route("/api/logout", methods=["POST"])
def logout():
    """登出接口"""
    session.clear()
    return jsonify({"message": "登出成功"})


@app.route("/api/session", methods=["GET"])
def api_session():
    """获取当前会话状态"""
    return jsonify({
        "logged_in": session.get("logged_in", False),
        "username": session.get("username", "")
    })


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
            conditions.append("student_id LIKE ?")
            params.append(f"%{student_id}%")

        if age and age.isdigit():
            conditions.append("student_age = ?")
            params.append(int(age))

        if conditions:
            sql = f"SELECT * FROM info_table WHERE {' AND '.join(conditions)} ORDER BY created_at DESC"
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

    if not isinstance(age, int) or age <= 0 or age > 150:
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