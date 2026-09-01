"""
学生管理系统 - 基础性能测试脚本
功能：模拟真实用户操作，包含登录、查询、添加、更新、删除等

学习要点：
1. HttpUser - 代表一个虚拟用户
2. @task - 定义用户操作，权重决定执行频率
3. between - 设置思考时间
4. catch_response - 捕获响应进行自定义验证
5. on_start/on_stop - 用户生命周期钩子
"""

from locust import HttpUser, task, between, TaskSet, events
import json
import random
from datetime import datetime
from faker import Faker
from utils import get_logger

# 获取日志器
logger = get_logger()


# ==================== 测试数据配置 ====================
class TestData:
    """测试数据管理类 - 所有测试数据集中管理"""

    # 预置测试账号（需要在系统中先注册）
    # 注意：这些账号必须在数据库中已存在
    TEST_USERS = [
        {"username": "test_user1", "password": "123456"},
        {"username": "test_user2", "password": "123456"},
        {"username": "test_user3", "password": "123456"},
        {"username": "test_user4", "password": "123456"},
        {"username": "test_user5", "password": "123456"},
        {"username": "admin", "password": "admin123"},
    ]

    # 搜索关键词 - 模拟用户真实搜索行为
    SEARCH_KEYWORDS = ["张", "李", "王", "刘", "陈", "杨", "黄", "周", "赵", "吴"]

    # 年龄范围
    AGES = list(range(18, 25))

    # 中文姓名库 - 用于生成测试数据
    SURNAMES = [
        "张",
        "李",
        "王",
        "刘",
        "陈",
        "杨",
        "黄",
        "周",
        "赵",
        "吴",
        "徐",
        "孙",
        "马",
        "朱",
        "胡",
    ]
    GIVEN_NAMES = [
        "伟",
        "芳",
        "秀英",
        "敏",
        "静",
        "丽",
        "强",
        "磊",
        "洋",
        "勇",
        "艳",
        "杰",
        "娜",
        "军",
        "涛",
    ]


# ==================== 用户行为定义 ====================
class StudentManagementTasks(TaskSet):
    """
    学生管理系统用户行为集

    学习要点：
    1. TaskSet 可以组织一组相关的用户操作
    2. 每个 @task 方法代表一种用户操作
    3. @task(权重) 控制执行频率
    4. on_start 在每个用户开始测试时执行（类似 setup）
    """

    def on_start(self):
        """
        用户启动时执行 - 登录系统

        每个虚拟用户启动时都会执行此方法
        """
        # 随机选择一个测试用户
        user = random.choice(TestData.TEST_USERS)
        self.username = user["username"]
        self.password = user["password"]

        # 执行登录
        with self.client.post(
            "/api/login",
            json={"username": self.username, "password": self.password},
            catch_response=True,
            name="登录",
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    logger.info(f"✅ 用户 {self.username} 登录成功")
                    response.success()
                else:
                    error_msg = data.get("message", "未知错误")
                    logger.warning(f"❌ 用户 {self.username} 登录失败: {error_msg}")
                    response.failure(f"登录失败: {error_msg}")
            else:
                logger.warning(
                    f"❌ 用户 {self.username} 登录请求失败: {response.status_code}"
                )
                response.failure(f"登录请求失败: {response.status_code}")

    @task(10)
    def view_student_list(self):
        """
        查看学生列表 - 高频操作 (权重10)

        这是系统最常用的功能，应该分配较高的权重
        """
        with self.client.get(
            "/api/students", catch_response=True, name="获取学生列表"
        ) as response:
            if response.status_code == 200:
                try:
                    students = response.json()
                    if isinstance(students, list):
                        # 记录返回数据量，用于性能分析
                        count = len(students)
                        logger.debug(f"获取到 {count} 名学生")
                        response.success()
                    else:
                        response.failure("返回数据格式错误：期望数组")
                except json.JSONDecodeError:
                    response.failure("返回数据不是有效的JSON")
            else:
                response.failure(f"状态码异常: {response.status_code}")

    @task(8)
    def search_students_by_name(self):
        """
        按姓名搜索 - 高频操作 (权重8)

        模拟用户通过姓名搜索学生的场景
        """
        keyword = random.choice(TestData.SEARCH_KEYWORDS)
        params = {"name": keyword}

        with self.client.get(
            "/api/students/search",
            params=params,
            catch_response=True,
            name="搜索-按姓名",
        ) as response:
            if response.status_code == 200:
                try:
                    students = response.json()
                    if isinstance(students, list):
                        logger.debug(f"搜索 '{keyword}' 找到 {len(students)} 条结果")
                        response.success()
                    else:
                        response.failure("搜索返回数据格式错误")
                except json.JSONDecodeError:
                    response.failure("搜索返回数据不是有效的JSON")
            else:
                response.failure(f"搜索失败: {response.status_code}")

    @task(6)
    def search_by_student_id(self):
        """
        按学号搜索 - 中频操作 (权重6)

        先获取一个学号，然后用学号进行精确搜索
        """
        # 先获取学生列表，从中选一个学号
        response = self.client.get("/api/students", name="获取列表-用于搜索")
        if response.status_code != 200:
            return

        try:
            students = response.json()
            if not students:
                return

            # 随机选择一个学生
            student = random.choice(students)
            student_id = student.get("student_id", "")

            if not student_id:
                return

            params = {"student_id": student_id}

            with self.client.get(
                "/api/students/search",
                params=params,
                catch_response=True,
                name="搜索-按学号",
            ) as search_response:
                if search_response.status_code == 200:
                    search_response.success()
                else:
                    search_response.failure(
                        f"学号搜索失败: {search_response.status_code}"
                    )
        except Exception as e:
            logger.error(f"学号搜索异常: {e}")

    @task(5)
    def search_by_age(self):
        """
        按年龄搜索 - 中频操作 (权重5)
        """
        age = random.choice(TestData.AGES)
        params = {"age": str(age)}

        with self.client.get(
            "/api/students/search",
            params=params,
            catch_response=True,
            name="搜索-按年龄",
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"年龄搜索失败: {response.status_code}")

    @task(4)
    def view_student_detail(self):
        """
        查看学生详情 - 中频操作 (权重4)

        模拟用户点击查看某个学生的详细信息
        """
        # 先获取学生列表
        response = self.client.get("/api/students", name="获取列表-查看详情")
        if response.status_code != 200:
            return

        try:
            students = response.json()
            if not students:
                return

            # 随机选择一个学生
            student = random.choice(students)
            student_id = student.get("id")

            if not student_id:
                return

            with self.client.get(
                f"/api/students/{student_id}", catch_response=True, name="获取学生详情"
            ) as detail_response:
                if detail_response.status_code == 200:
                    detail_response.success()
                elif detail_response.status_code == 404:
                    detail_response.failure("学生不存在")
                else:
                    detail_response.failure(
                        f"查看详情失败: {detail_response.status_code}"
                    )
        except Exception as e:
            logger.error(f"查看详情异常: {e}")

    @task(3)
    def add_student(self):
        """
        添加学生 - 中低频操作 (权重3)

        模拟管理员添加新学生
        """
        # 使用 Faker 生成测试数据
        new_student = {
            "name": fake.name(),
            "student_id": str(fake.unique.random_number(digits=10)),
            "age": random.randint(18, 25),
        }

        with self.client.post(
            "/api/students", json=new_student, catch_response=True, name="添加学生"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    logger.debug(f"添加学生成功: {new_student['name']}")
                    response.success()
                else:
                    response.failure(f"添加失败: {data.get('message')}")
            elif response.status_code == 400:
                # 学号重复等业务错误
                data = response.json()
                response.failure(f"添加失败(业务错误): {data.get('message')}")
            else:
                response.failure(f"添加请求失败: {response.status_code}")

    @task(2)
    def update_student(self):
        """
        更新学生信息 - 低频操作 (权重2)

        模拟管理员修改学生信息
        """
        # 获取学生列表
        response = self.client.get("/api/students", name="获取列表-用于更新")
        if response.status_code != 200:
            return

        try:
            students = response.json()
            if not students:
                return

            # 随机选择一个学生
            student = random.choice(students)
            student_id = student.get("id")

            if not student_id:
                return

            # 构造更新数据
            update_data = {
                "name": student.get("name", "") + "改",
                "student_id": student.get("student_id", ""),
                "age": random.randint(18, 25),
            }

            with self.client.put(
                f"/api/students/{student_id}",
                json=update_data,
                catch_response=True,
                name="更新学生",
            ) as update_response:
                if update_response.status_code == 200:
                    data = update_response.json()
                    if data.get("success"):
                        update_response.success()
                    else:
                        update_response.failure(f"更新失败: {data.get('message')}")
                else:
                    update_response.failure(
                        f"更新请求失败: {update_response.status_code}"
                    )
        except Exception as e:
            logger.error(f"更新异常: {e}")

    @task(1)
    def delete_student(self):
        """
        删除学生 - 最低频操作 (权重1)

        模拟管理员删除学生，注意保留至少一条数据
        """
        # 获取学生列表
        response = self.client.get("/api/students", name="获取列表-用于删除")
        if response.status_code != 200:
            return

        try:
            students = response.json()
            # 至少保留一条数据，所以如果少于2条就不删除
            if len(students) < 2:
                return

            # 选择要删除的学生（不删除第一条）
            student = random.choice(students[1:])
            student_id = student.get("id")

            if not student_id:
                return

            with self.client.delete(
                f"/api/students/{student_id}", catch_response=True, name="删除学生"
            ) as delete_response:
                if delete_response.status_code == 200:
                    data = delete_response.json()
                    if data.get("success"):
                        logger.debug(f"删除学生成功: {student.get('name')}")
                        delete_response.success()
                    else:
                        delete_response.failure(f"删除失败: {data.get('message')}")
                else:
                    delete_response.failure(
                        f"删除请求失败: {delete_response.status_code}"
                    )
        except Exception as e:
            logger.error(f"删除异常: {e}")

    @task(1)
    def combined_search(self):
        """
        组合搜索 - 最低频操作 (权重1)

        模拟用户使用多个条件进行组合搜索
        """
        params = {
            "name": random.choice(TestData.SEARCH_KEYWORDS),
            "age": str(random.choice(TestData.AGES)),
        }

        with self.client.get(
            "/api/students/search",
            params=params,
            catch_response=True,
            name="搜索-组合条件",
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"组合搜索失败: {response.status_code}")


# ==================== 用户类 ====================
class StudentManagementUser(HttpUser):
    """
    学生管理系统的虚拟用户

    学习要点：
    1. wait_time - 定义用户操作之间的等待时间（思考时间）
    2. tasks - 指定用户执行的任务集
    3. host - 目标服务器地址
    """

    # 思考时间：每个任务执行后等待 1-5 秒
    # 模拟真实用户的思考时间
    wait_time = between(1, 5)

    # 指定任务集
    tasks = [StudentManagementTasks]

    # 连接超时配置
    connection_timeout = 10.0
    network_timeout = 10.0

    def on_start(self):
        """用户启动时的钩子"""
        logger.info("👤 虚拟用户启动")

    def on_stop(self):
        """用户停止时的钩子"""
        logger.info("👤 虚拟用户停止")


# ==================== 测试事件监听 ====================
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """
    测试开始事件监听

    在测试开始前执行，用于：
    1. 打印测试信息
    2. 准备测试数据
    3. 预热系统
    """
    logger.info("=" * 70)
    logger.info("🚀 学生管理系统性能测试开始")
    logger.info(f"📅 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"👥 测试用户数: {len(TestData.TEST_USERS)}")
    logger.info(f"🔍 搜索关键词: {TestData.SEARCH_KEYWORDS}")
    logger.info("=" * 70)

    # 检查测试数据是否有效
    if not TestData.TEST_USERS:
        logger.warning("⚠️ 没有配置测试用户，请检查 TestData.TEST_USERS")

    # 系统预热（可选）
    logger.info("🔥 系统预热中...")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """
    测试结束事件监听

    在测试结束后执行，用于：
    1. 打印测试结果摘要
    2. 生成测试报告
    3. 清理资源
    """
    logger.info("=" * 70)
    logger.info("📊 学生管理系统性能测试结束")
    logger.info(f"📅 结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 获取统计数据
    if environment.runner and environment.runner.stats:
        stats = environment.runner.stats
        total = stats.total

        # 计算关键指标
        total_requests = total.num_requests
        total_failures = total.num_failures
        success_rate = (
            ((total_requests - total_failures) / total_requests * 100)
            if total_requests > 0
            else 0
        )

        # 打印测试结果
        logger.info("-" * 70)
        logger.info("📈 测试结果摘要:")
        logger.info(f"   总请求数: {total_requests:,}")
        logger.info(f"   失败请求数: {total_failures:,}")
        logger.info(f"   成功率: {success_rate:.2f}%")
        logger.info(f"   平均响应时间: {total.avg_response_time:.2f}ms")
        logger.info(
            f"   95% 响应时间: {total.get_response_time_percentile(0.95):.2f}ms"
        )
        logger.info(
            f"   99% 响应时间: {total.get_response_time_percentile(0.99):.2f}ms"
        )
        logger.info(f"   吞吐量 (RPS): {total.total_rps:.2f}")
        logger.info("-" * 70)

        # 各接口详情
        if stats.entries:
            logger.info("📋 各接口详情:")
            for name, stat in stats.entries.items():
                if stat.num_requests > 0:
                    failure_rate = (
                        (stat.num_failures / stat.num_requests * 100)
                        if stat.num_requests > 0
                        else 0
                    )
                    logger.info(f"   {name}:")
                    logger.info(f"      请求数: {stat.num_requests:,}")
                    logger.info(f"      失败率: {failure_rate:.2f}%")
                    logger.info(f"      平均响应: {stat.avg_response_time:.2f}ms")
                    logger.info(
                        f"      95%响应: {stat.get_response_time_percentile(0.95):.2f}ms"
                    )

        # 生成报告
        try:
            from utils import generate_report

            report_data = {
                "total": {
                    "num_requests": total.num_requests,
                    "num_failures": total.num_failures,
                    "success_rate": success_rate,
                    "avg_response_time": total.avg_response_time,
                    "p95_response_time": total.get_response_time_percentile(0.95),
                    "p99_response_time": total.get_response_time_percentile(0.99),
                    "rps": total.total_rps,
                    "failure_rate": total_failures / total_requests * 100
                    if total_requests > 0
                    else 0,
                },
                "entries": {
                    name: {
                        "num_requests": stat.num_requests,
                        "num_failures": stat.num_failures,
                        "avg_response_time": stat.avg_response_time,
                        "p95_response_time": stat.get_response_time_percentile(0.95),
                    }
                    for name, stat in stats.entries.items()
                    if stat.num_requests > 0
                },
            }
            report_file = generate_report(report_data)
            logger.info(f"📄 报告已生成: {report_file}")
        except Exception as e:
            logger.error(f"生成报告失败: {e}")

    logger.info("=" * 70)


@events.quitting.add_listener
def on_quitting(environment, **kwargs):
    """退出时清理"""
    logger.info("👋 正在退出性能测试...")


# 初始化 Faker
fake = Faker("zh_CN")

# 导出配置供其他模块使用
__all__ = ["StudentManagementUser", "TestData"]
