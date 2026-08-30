"""
批量注册用户脚本
从 test_users.csv 读取用户，调用注册接口批量注册
"""

import csv
import requests
import time
import os
import random
import string
from typing import List, Dict, Tuple

# ==================== 配置 ====================
API_BASE_URL = "http://localhost:5003"  # 修改为您的后端地址
REGISTER_ENDPOINT = "/api/register"     # 注册接口路径
LOGIN_ENDPOINT = "/api/login"           # 登录接口路径
CSV_FILE = "test_users.csv"             # CSV文件路径

# 请求超时时间（秒）
TIMEOUT = 10

# 重试配置
MAX_RETRIES = 3
RETRY_DELAY = 1

# 每批注册间隔（秒），避免压垮服务器
BATCH_DELAY = 0.1


# ==================== 工具函数 ====================
def generate_password(length: int = 8) -> str:
    """生成随机密码"""
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))


def generate_username(prefix: str = "test_user") -> str:
    """生成唯一用户名"""
    import time
    return f"{prefix}_{int(time.time())}_{random.randint(100, 999)}"


# ==================== 读取CSV ====================
def load_users_from_csv(file_path: str) -> List[Dict[str, str]]:
    """
    从CSV读取用户列表
    CSV格式: 每行 username,password 或 username (密码为空则自动生成)
    """
    users = []
    
    if not os.path.exists(file_path):
        print(f"❌ 文件不存在: {file_path}")
        # 如果文件不存在，创建示例文件
        create_sample_csv(file_path)
        return []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            # 检测是否有表头
            first_line = f.readline().strip()
            f.seek(0)
            
            has_header = 'username' in first_line.lower() and 'password' in first_line.lower()
            
            reader = csv.reader(f)
            if has_header:
                next(reader)  # 跳过表头
            
            for row in reader:
                if not row:
                    continue
                    
                username = row[0].strip()
                password = row[1].strip() if len(row) > 1 else ""
                
                # 如果密码为空，自动生成
                if not password:
                    password = generate_password()
                    print(f"⚠️ 用户 {username} 密码为空，自动生成: {password}")
                
                if username:
                    users.append({
                        "username": username,
                        "password": password
                    })
        
        print(f"✅ 从CSV加载了 {len(users)} 个用户")
        return users
        
    except Exception as e:
        print(f"❌ 读取CSV失败: {e}")
        return []


def create_sample_csv(file_path: str):
    """创建示例CSV文件"""
    sample_users = [
        {"username": "admin", "password": "admin123"},
        {"username": "test_user1", "password": "123456"},
        {"username": "test_user2", "password": "123456"},
        {"username": "test_user3", "password": "123456"},
        {"username": "test_user4", "password": "123456"},
        {"username": "test_user5", "password": "123456"},
    ]
    
    try:
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=["username", "password"])
            writer.writeheader()
            writer.writerows(sample_users)
        print(f"✅ 已创建示例CSV文件: {file_path}")
        print(f"   包含 {len(sample_users)} 个示例用户")
    except Exception as e:
        print(f"❌ 创建CSV失败: {e}")


# ==================== 注册用户 ====================
def register_user(username: str, password: str, base_url: str) -> Tuple[bool, str]:
    """
    注册单个用户
    返回: (是否成功, 消息)
    """
    url = f"{base_url}{REGISTER_ENDPOINT}"
    data = {
        "username": username,
        "password": password
    }
    
    try:
        response = requests.post(
            url,
            json=data,
            timeout=TIMEOUT,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code in [200, 201]:
            return True, "注册成功"
        elif response.status_code == 400:
            # 可能用户已存在
            try:
                resp_data = response.json()
                if "已存在" in str(resp_data) or "exists" in str(resp_data).lower():
                    return True, "用户已存在（跳过）"
            except:
                pass
            return False, f"注册失败 (HTTP {response.status_code}): {response.text}"
        else:
            return False, f"注册失败 (HTTP {response.status_code}): {response.text}"
            
    except requests.exceptions.ConnectionError:
        return False, f"连接失败，请检查服务是否运行: {base_url}"
    except requests.exceptions.Timeout:
        return False, "请求超时"
    except Exception as e:
        return False, f"未知错误: {e}"


def login_user(username: str, password: str, base_url: str) -> Tuple[bool, str]:
    """
    验证用户登录（可选）
    返回: (是否成功, 消息)
    """
    url = f"{base_url}{LOGIN_ENDPOINT}"
    data = {
        "username": username,
        "password": password
    }
    
    try:
        response = requests.post(
            url,
            json=data,
            timeout=TIMEOUT,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            return True, "登录成功"
        else:
            return False, f"登录失败 (HTTP {response.status_code})"
            
    except Exception as e:
        return False, f"登录验证失败: {e}"


# ==================== 批量注册 ====================
def batch_register(
    users: List[Dict[str, str]], 
    base_url: str,
    verify_login: bool = False
) -> Dict[str, int]:
    """
    批量注册用户
    """
    stats = {
        "total": len(users),
        "success": 0,
        "already_exists": 0,
        "failed": 0,
        "login_success": 0,
        "login_failed": 0,
    }
    
    failed_users = []
    
    print("\n" + "=" * 60)
    print(f"📝 开始批量注册 {len(users)} 个用户")
    print(f"   API地址: {base_url}")
    print(f"   注册接口: {REGISTER_ENDPOINT}")
    print("=" * 60 + "\n")
    
    for i, user in enumerate(users, 1):
        username = user["username"]
        password = user["password"]
        
        # 显示进度
        print(f"[{i}/{len(users)}] 注册用户: {username} ... ", end="")
        
        # 注册
        success, message = register_user(username, password, base_url)
        
        if success:
            if "已存在" in message:
                stats["already_exists"] += 1
                print(f"⏭️  {message}")
            else:
                stats["success"] += 1
                print(f"✅ {message}")
                
                # 验证登录
                if verify_login:
                    login_ok, login_msg = login_user(username, password, base_url)
                    if login_ok:
                        stats["login_success"] += 1
                        print(f"   🔐 登录验证: ✅ {login_msg}")
                    else:
                        stats["login_failed"] += 1
                        print(f"   🔐 登录验证: ❌ {login_msg}")
        else:
            stats["failed"] += 1
            print(f"❌ {message}")
            failed_users.append(f"{username}: {message}")
        
        # 批处理间隔，避免请求过快
        if i % 10 == 0:
            print(f"   ... 已处理 {i} 个用户，休息 {BATCH_DELAY * 2}s ...")
            time.sleep(BATCH_DELAY * 2)
        else:
            time.sleep(BATCH_DELAY)
    
    return stats, failed_users


# ==================== 生成CSV文件（批量生成测试用户） ====================
def generate_test_users_csv(
    file_path: str, 
    count: int = 100, 
    with_password: bool = True
):
    """
    生成指定数量的测试用户CSV文件
    """
    users = []
    for i in range(1, count + 1):
        username = f"test_user{i:04d}"
        password = generate_password() if with_password else ""
        users.append({"username": username, "password": password})
    
    try:
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=["username", "password"])
            writer.writeheader()
            writer.writerows(users)
        print(f"✅ 已生成测试用户CSV: {file_path}")
        print(f"   包含 {len(users)} 个用户")
        return True
    except Exception as e:
        print(f"❌ 生成CSV失败: {e}")
        return False


# ==================== 主函数 ====================
def main():
    """主函数"""
    import sys
    
    # 处理命令行参数
    if len(sys.argv) > 1:
        if sys.argv[1] == "--generate" or sys.argv[1] == "-g":
            count = int(sys.argv[2]) if len(sys.argv) > 2 else 100
            generate_test_users_csv(CSV_FILE, count)
            return
    
    # 检查配置文件
    print(f"📂 使用CSV文件: {CSV_FILE}")
    
    # 读取用户
    users = load_users_from_csv(CSV_FILE)
    if not users:
        print("\n❌ 没有找到任何用户")
        print("\n💡 提示:")
        print(f"   1. 确保 {CSV_FILE} 文件存在")
        print(f"   2. 每行格式: username,password")
        print(f"   3. 或运行: python batch_register.py --generate 100")
        return
    
    # 确认
    print(f"\n👥 将注册 {len(users)} 个用户到 {API_BASE_URL}")
    response = input("确认继续? (y/N): ")
    if response.lower() != 'y':
        print("❌ 已取消")
        return
    
    # 批量注册
    stats, failed_users = batch_register(users, API_BASE_URL, verify_login=False)
    
    # 打印统计
    print("\n" + "=" * 60)
    print("📊 注册结果统计")
    print("=" * 60)
    print(f"  总计用户数: {stats['total']}")
    print(f"  ✅ 新注册成功: {stats['success']}")
    print(f"  ⏭️  已存在（跳过）: {stats['already_exists']}")
    print(f"  ❌ 注册失败: {stats['failed']}")
    print("-" * 60)
    
    if stats['success'] > 0:
        print(f"  ✅ 有效用户数: {stats['success'] + stats['already_exists']}")
    
    if stats['failed'] > 0:
        print("\n❌ 失败用户列表:")
        for user in failed_users[:10]:
            print(f"   - {user}")
        if len(failed_users) > 10:
            print(f"   ... 还有 {len(failed_users) - 10} 个失败用户")
    
    print("=" * 60)


# ==================== 入口 ====================
if __name__ == "__main__":
    main()