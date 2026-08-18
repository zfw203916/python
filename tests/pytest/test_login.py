import yaml
import pytest
import os
import requests as eq


def load_login_data():
    """从 YAML 加载测试数据"""
    file_dir = os.path.dirname(__file__)
    data_path = os.path.join(file_dir, "test_data", "login_data.yaml")
    with open(data_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def register_user(username, password):
    """注册函数"""
    url = "http://127.0.0.1:5003/api/register"
    try:
        response = eq.post(url, json={"username": username, "password": password})
        return response.json()
    except Exception as e:
        return {"success": False, "message": str(e)}


def login(username, password):
    # 登录函数
    url = "http://127.0.0.1:5003/api/login"
    try:
        response = eq.post(url, json={"username": username, "password": password})
        return response.json()
    except Exception as e:
        return {"success": False, "message": str(e)}


# 测试代码
class TestLogin:
    data = load_login_data()
    print(data)
    if not data:
        pytest.skip("测试数据加载失败，跳过所有测试", allow_module_level=True)

    @pytest.fixture(scope="class", autouse=True)
    def setup_and_cleanup(self):
        """准备和清理测试数据"""
        print("\n" + "=" * 50)
        print("开始测试前准备...")
        # 注册所有需要的用户
        """
        get() 是 Python 字典（dict） 的方法，用于安全地获取键对应的值。
        # 假设 result 是登录接口返回的数据
            result = {'success': True, 'message': '登录成功'}

            # 情况1：键存在
            success = result.get('success')  # → True
            message = result.get('message')  # → '登录成功'
        """
        try:
            reponse = eq.get("http://127.0.0.1:5003", timeout=3)
            if reponse.status_code != 200:
                pytest.skip("服务不可用，跳过测试")
        except:
            pytest.skip("无法连接到服务，跳过测试")

        all_user = self.data.get(
            "valid_users", []
        )  #  2. 取值，不存在返回空列表（最常见）
        for user in all_user:
            username = user["username"]
            password = user["password"]

            # 先尝试登录，如果成功说明用户已存在
            check = login(username, password)
            if check.get("success"):
                print(f"✅ 用户 '{username}' 已存在，跳过注册")
                continue

            # 不存在则注册
            result = register_user(username, password)
            print(f"这个是循环的结果数据:::: {result}")
            if result.get("success"):
                print(f"✅ 用户 '{username}' 注册成功")
            else:
                print(f"ℹ️  用户 '{username}':{result.get('message', '未知错误')}")
        print("=" * 50)

        yield  # 执行测试

        print("\n" + "=" * 50)
        print("测试完成")
        print("=" * 50)

    # 测试正常登录
    @pytest.mark.parametrize("test_case", data["valid_users"])
    def test_valid_login(self, test_case):
        # 从YAML取数据 → 调用login() → 验证结果
        result = login(test_case["username"], test_case["password"])
        # 注意：API返回的是 {'success': True, 'message': '登录成功'}
        # 所以需要用 result['message'] 比较
        print(f"\n📝 测试用例: {test_case['username']}")
        print(f"📊 返回结果: {result}")
        assert result["message"] == test_case["expected"]
        assert result.get("success") == True

    # 测试异常登录
    @pytest.mark.parametrize("test_case", data["invalid_users"])
    def test_invalid_login(self, test_case):
        result = login(test_case["username"], test_case["password"])
        print(
            f"\n📝 测试用例: username='{test_case['username']}', password='{test_case['password']}'"
        )
        print(f"📊 返回结果: {result}")
        assert result.get("message") == test_case["expected"]
        assert result.get("success") == False

    # 测试边界值
    @pytest.mark.parametrize("test_case", data["edge_cases"])
    def test_edge_cases(self, test_case):
        result = login(test_case["username"], test_case["password"])
        print(
            f"\n📝 测试边界值: username长度={len(test_case['username'])}, password长度={len(test_case['password'])}"
        )
        print(f"📊 返回结果: {result}")
        # 注意：边界值测试中，有些预期是"用户名长度不能超过50"，但API可能返回"用户名或密码错误"
        # 这是因为你的Flask应用可能没有做长度校验
        assert result["message"] == test_case["expected"]
