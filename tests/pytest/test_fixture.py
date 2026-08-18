import pytest
import datetime


@pytest.fixture(scope="module")
def jiaju_fixture():
    print("\n=== 开始模块测试 ===")
    print("前置时间：", datetime.datetime.now())
    yield
    print("后置时间：", datetime.datetime.now())
    print("=== 结束模块测试 ===")


def test_case_1(jiaju_fixture):
    print("执行测试用例1")
    assert 1 + 1 == 2


def test_case_2(jiaju_fixture):
    print("执行测试用例1")
    assert 1 + 1 == 2


class User:
    def __init__(self, name, age):
        self.name = name
        self.age = age
        self._saved = False

    def save(self):
        """模拟保存到数据库"""
        self._saved = True
        print(f"✅ 用户 {self.name} 已保存")

    def delete(self):
        """模拟从数据库删除"""
        self._saved = False
        print(f"🗑️ 用户 {self.name} 已删除")

    def __repr__(self):
        return f"User(name='{self.name},age='{self.age}')"


@pytest.fixture
def test_user():
    user = User(name="张三", age=25)
    user.save()
    yield user  # 把用户对象传给测试
    user.delete()  # 测试结束后自动清理


def test_user_profile(test_user):
    assert test_user.name == "张三"


def test_user_login(test_user):
    assert test_user.age == 25
