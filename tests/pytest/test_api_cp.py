import pytest
import requests


@pytest.fixture()
def client():
    """基本的HTTP客户端"""
    session = requests.Session()
    session.headers.update(
        {"Content-Type": "application/json", "User-Agent": "pytest-test-client"}
    )
    yield session
    session.close()


@pytest.fixture(scope="session")
def authenticated_client():
    """已认证的客户端"""
    session = requests.Session()
    base_url = "http://127.0.0.1:5003"

    # 登录
    login_data = {"username": "zfw", "password": "zfw520"}

    try:
        response = session.post(f"{base_url}/login", json=login_data, timeout=5)

        if response.status_code == 200:
            data = response.json()
            if "token" in data:
                session.headers.update({"Authorization": f"Bearer {data['token']}"})
        else:
            pytest.skip(f"无法登录，状态码: {response.status_code}")

    except requests.exceptions.ConnectionError:
        pytest.skip("服务器未启动")
    except Exception as e:
        pytest.skip(f"登录失败: {e}")

    yield session
    session.close()


def test_login(client):
    """测试登录API"""
    url = "http://127.0.0.1:5003/login"

    test_cases = [
        {"username": "zfw", "password": "zfw520"},
        {"username": "admin", "password": "admin123"},
    ]

    for data in test_cases:
        resp = client.post(url, json=data, timeout=5)
        assert resp.status_code in [200, 201], f"登录失败: {resp.status_code}"

        # 验证响应格式
        response_data = resp.json()
        assert "message" in response_data or "token" in response_data

        print(f"用户 {data['username']} 登录成功")


def test_get_user_info(authenticated_client):
    """测试获取用户信息（需要认证）"""
    url = "http://127.0.0.1:5003/user/info"

    response = authenticated_client.get(url, timeout=5)
    assert response.status_code == 200

    user_data = response.json()
    assert "username" in user_data
    assert "email" in user_data


def test_invalid_login(client):
    """测试无效登录"""
    url = "http://127.0.0.1:5003/login"

    invalid_data = {"username": "wrong_user", "password": "wrong_password"}

    response = client.post(url, json=invalid_data, timeout=5)
    # 预期的错误状态码
    assert response.status_code in [401, 403, 400]
