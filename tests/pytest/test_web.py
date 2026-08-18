import pytest


class Test:
    @pytest.mark.skip
    def test_hello(self):
        assert False

    def test_bad(self):
        a = 10
        b = "10"
        assert a == int(b)

    def test_correct(self):
        a = "a"
        b = "a"
        assert a == b

    def test_number(self):
        a = 1
        b = 1
        assert a == b

    @pytest.mark.xfail
    def test_xfail(self):
        print("想看打印后面就跟-s参数吧")
        pass


# 下面是数据驱动测试实例
# 下面是4组数据，所以是4个测试用例
@pytest.mark.parametrize(
    "a,b, expected", [(1, 1, 2), (-1, -1, -2), ("a", "b", "ab"), (["a"], [4], ["a", 4])]
)
# 下面是数据驱动测试实例
def test_add(a, b, expected):
    result = a + b
    assert result == expected, f"{a} + {b} 应该等于{expected},单等于{result}"
