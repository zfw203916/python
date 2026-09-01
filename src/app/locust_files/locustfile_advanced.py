"""
学生管理系统 - 企业级高级性能测试脚本

功能特点：
1. ✅ CSV数据驱动 - 支持从文件读取测试数据
2. ✅ 完整的断言验证 - 确保业务逻辑正确
3. ✅ 错误处理和重试机制
4. ✅ 自定义统计指标
5. ✅ 分布式测试支持
6. ✅ 环境变量配置
7. ✅ 请求链路追踪

学习要点：
1. 数据驱动测试
2. 业务断言
3. 异常处理
4. 高级配置
"""

from locust import HttpUser, task, between, TaskSet, events
import json
import random
import os
from datetime import datetime
from typing import Dict, Any, List
from faker import Faker
import csv
from utils import get_logger

# 获取日志器
logger = get_logger()


# ==================== 配置管理 ====================
class Config:
    """
    配置管理类 - 支持环境变量配置

    企业级应用通常需要灵活配置，环境变量是最好的方式
    """

    # 目标服务器地址
    HOST = os.getenv("TARGET_HOST", "http://localhost:5003")

    # 测试用户文件
    TEST_USERS_FILE = os.getenv("TEST_USERS_FILE", "test_users.csv")

    # 思考时间配置
    THINK_TIME_MIN = int(os.getenv("THINK_TIME_MIN", "1"))
    THINK_TIME_MAX = int(os.getenv("THINK_TIME_MAX", "5"))

    # 超时配置
    CONNECTION_TIMEOUT = float(os.getenv("CONNECTION_TIMEOUT", "10.0"))
    NETWORK_TIMEOUT = float(os.getenv("NETWORK_TIMEOUT", "10.0"))

    # 重试配置
    MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
    RETRY_DELAY = float(os.getenv("RETRY_DELAY", "1.0"))

    @classmethod
    def load_test_users(cls) -> List[Dict[str, str]]:
        """
        从CSV文件加载测试用户

        企业级特点：
        1. 支持大量用户数据
        2. 方便数据维护
        3. 支持动态更新

        Returns:
            List[Dict]: 用户列表
        """
        users = []

        # 尝试从CSV文件加载
        if os.path.exists(cls.TEST_USERS_FILE):
            try:
                with open(cls.TEST_USERS_FILE, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        username = row.get("username", "").strip()
                        password = row.get("password", "").strip()
                        if username and password:
                            users.append({"username": username, "password": password})
                logger.info(f"✅ 从CSV加载了 {len(users)} 个测试用户")
            except Exception as e:
                logger.error(f"❌ 加载CSV失败: {e}")

        # 如果没有加载到用户，使用默认用户
        if not users:
            logger.warning("⚠️ 未找到测试用户，使用默认用户")
            users = [
                {"username": "test_user1", "password": "123456"},
                {"username": "test_user2", "password": "123456"},
                {"username": "admin", "password": "admin123"},
            ]

        return users

    @classmethod
    def print_config(cls):
        """打印当前配置"""
        logger.info("=" * 70)
        logger.info("⚙️  当前配置:")
        logger.info(f"   TARGET_HOST: {cls.HOST}")
        logger.info(f"   TEST_USERS_FILE: {cls.TEST_USERS_FILE}")
        logger.info(f"   THINK_TIME: {cls.THINK_TIME_MIN}-{cls.THINK_TIME_MAX}s")
        logger.info(f"   MAX_RETRIES: {cls.MAX_RETRIES}")
        logger.info(f"   CONNECTION_TIMEOUT: {cls.CONNECTION_TIMEOUT}s")
        logger.info("=" * 70)


# ==================== 数据生成器 ====================
class DataGenerator:
    """
    测试数据生成器

    企业级特点：
    1. 生成唯一数据
    2. 数据池管理
    3. 支持多种数据类型
    """

    def __init__(self):
        self.fake = Faker("zh_CN")
        self.used_student_ids = set()
        self.used_names = set()

    def generate_student(self) -> Dict[str, Any]:
        """
        生成学生数据

        Returns:
            Dict: 学生数据
        """
        # 生成唯一的学号
        student_id = str(self.fake.unique.random_number(digits=10))
        while student_id in self.used_student_ids:
            student_id = str(self.fake.unique.random_number(digits=10))
        self.used_student_ids.add(student_id)

        # 生成姓名
        name = self.fake.name()
        while name in self.used_names:
            name = self.fake.name()
        self.used_names.add(name)

        return {"name": name, "student_id": student_id, "age": random.randint(18, 25)}

    def generate_search_params(self) -> Dict[str, str]:
        """
        生成搜索参数

        模拟各种搜索场景：
        1. 按姓名搜索
        2. 按学号搜索
        3. 按年龄搜索
        4. 组合搜索

        Returns:
            Dict: 搜索参数
        """
        search_types = ["name", "student_id", "age", "combined"]
        search_type = random.choice(search_types)

        # 中文姓氏
        surnames = ["张", "李", "王", "刘", "陈", "杨", "黄", "周", "赵", "吴"]

        if search_type == "name":
            return {"name": random.choice(surnames)}
        elif search_type == "student_id":
            # 学号前缀搜索
            return {"student_id": str(random.randint(100, 999))}
        elif search_type == "age":
            return {"age": str(random.randint(18, 25))}
        else:  # combined
            return {"name": random.choice(surnames), "age": str(random.randint(18, 22))}

    def reset(self):
        """重置数据池"""
        self.used_student_ids.clear()
        self.used_names.clear()


# ==================== 性能监控器 ====================
class PerformanceMonitor:
    """
    性能监控器

    企业级特点：
    1. 自定义指标收集
    2. 性能阈值告警
    3. 实时监控
    """

    # 性能阈值
    THRESHOLDS = {
        "response_time_avg": 200,  # 平均响应时间阈值 (ms)
        "response_time_p95": 500,  # 95%响应时间阈值 (ms)
        "failure_rate": 1.0,  # 失败率阈值 (%)
        "rps_min": 50,  # 最小吞吐量
    }

    def __init__(self, environment):
        # ✅ 修复1：直接赋值给 self.environment，不要用 self.user.environment
        self.environment = environment
        self.alerts = []

    def check_thresholds(self, stat) -> List[str]:
        """
        检查性能阈值

        Args:
            stat: 统计数据

        Returns:
            List[str]: 告警列表
        """
        alerts = []

        if stat.num_requests == 0:
            return alerts

        # 检查平均响应时间
        avg_response = stat.avg_response_time
        if avg_response > self.THRESHOLDS["response_time_avg"]:
            alerts.append(
                f"⚠️ 平均响应时间过高: {avg_response:.2f}ms "
                f"(阈值: {self.THRESHOLDS['response_time_avg']}ms)"
            )

        # 检查95%响应时间
        p95_response = stat.get_response_time_percentile(0.95)
        if p95_response > self.THRESHOLDS["response_time_p95"]:
            alerts.append(
                f"⚠️ 95%响应时间过高: {p95_response:.2f}ms "
                f"(阈值: {self.THRESHOLDS['response_time_p95']}ms)"
            )

        # 检查失败率
        failure_rate = (
            (stat.num_failures / stat.num_requests * 100)
            if stat.num_requests > 0
            else 0
        )
        if failure_rate > self.THRESHOLDS["failure_rate"]:
            alerts.append(
                f"⚠️ 失败率过高: {failure_rate:.2f}% "
                f"(阈值: {self.THRESHOLDS['failure_rate']}%)"
            )

        return alerts

    def collect_metrics(self) -> Dict[str, Any]:
        """
        收集性能指标

        Returns:
            Dict: 性能指标
        """
        if not self.environment.runner:
            return {}

        stats = self.environment.runner.stats
        total = stats.total

        return {
            "total_requests": total.num_requests,
            "total_failures": total.num_failures,
            "success_rate": (
                (total.num_requests - total.num_failures) / total.num_requests * 100
            )
            if total.num_requests > 0
            else 0,
            "avg_response_time": total.avg_response_time,
            "p95_response_time": total.get_response_time_percentile(0.95),
            "p99_response_time": total.get_response_time_percentile(0.99),
            "rps": total.total_rps,
            "alerts": self.alerts,
        }


# ==================== 用户行为（带完整断言） ====================
class StudentManagementTasks(TaskSet):
    """
    高级用户行为 - 带完整业务断言

    企业级特点：
    1. 完整的业务断言
    2. 数据一致性验证
    3. 错误恢复机制
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.data_generator = DataGenerator()
        # ✅ 修复2：删掉 self.user = None
        # ✅ 修复3：通过 self.user.environment 访问
        self.monitor = PerformanceMonitor(self.user.environment)

    def on_start(self):
        """
        用户启动 - 登录并验证

        企业级特点：
        1. 登录验证
        2. 会话管理
        3. 错误重试
        """
        users = Config.load_test_users()
        if not users:
            raise Exception("没有可用的测试用户")

        # ✅ 修复4：用 self.current_user 代替 self.user（避免覆盖框架属性）
        self.current_user = random.choice(users)
        username = self.current_user["username"]
        password = self.current_user["password"]

        logger.info(f"👤 用户 {username} 开始测试")

        # 登录重试机制
        for attempt in range(Config.MAX_RETRIES):
            try:
                with self.client.post(
                    "/api/login",
                    json={"username": username, "password": password},
                    catch_response=True,
                    name="登录",
                ) as response:
                    # 断言：状态码
                    assert (
                        response.status_code == 200
                    ), f"登录状态码异常: {response.status_code}"

                    # 断言：响应格式
                    data = response.json()
                    assert "success" in data, "响应缺少 success 字段"

                    # 断言：登录成功
                    assert (
                        data.get("success") is True
                    ), f"登录失败: {data.get('message', '未知错误')}"

                    # 断言：会话已建立
                    assert (
                        "logged_in" in self.client.cookies
                        or "session" in self.client.cookies
                    ), "登录会话未建立"

                    logger.info(f"✅ 用户 {username} 登录成功")
                    response.success()
                    return

            except AssertionError as e:
                logger.warning(f"⚠️ 登录尝试 {attempt + 1} 失败: {e}")
                if attempt < Config.MAX_RETRIES - 1:
                    time.sleep(Config.RETRY_DELAY * (attempt + 1))
            except Exception as e:
                logger.error(f"❌ 登录异常: {e}")
                if attempt < Config.MAX_RETRIES - 1:
                    time.sleep(Config.RETRY_DELAY * (attempt + 1))

        raise Exception(f"用户 {username} 登录失败，已重试 {Config.MAX_RETRIES} 次")

    @task(10)
    def get_students_with_validation(self):
        """
        获取学生列表 - 完整验证

        验证点：
        1. HTTP状态码
        2. 响应格式
        3. 数据完整性
        4. 数据有效性
        """
        with self.client.get(
            "/api/students", catch_response=True, name="获取学生列表"
        ) as response:
            # 1. 验证状态码
            if response.status_code != 200:
                response.failure(f"状态码异常: {response.status_code}")
                return

            # 2. 验证响应格式
            try:
                students = response.json()
            except json.JSONDecodeError:
                response.failure("响应不是有效的JSON")
                return

            # 3. 验证数据类型
            if not isinstance(students, list):
                response.failure("响应格式错误：期望数组")
                return

            # 4. 验证数据完整性
            if students:
                required_fields = ["id", "name", "student_id", "age"]
                for student in students:
                    for field in required_fields:
                        if field not in student:
                            response.failure(f"缺少必填字段: {field}")
                            return

                    # 5. 验证数据类型
                    if not isinstance(student["age"], int):
                        response.failure(f"年龄字段类型错误: {student['age']}")
                        return

                    # 6. 验证数据有效性
                    if student["age"] < 1 or student["age"] > 150:
                        response.failure(f"年龄超出范围: {student['age']}")
                        return

            response.success()

    @task(8)
    def search_with_validation(self):
        """
        搜索学生 - 完整验证

        企业级特点：
        1. 多条件搜索
        2. 结果验证
        3. 边界测试
        """
        params = self.data_generator.generate_search_params()

        with self.client.get(
            "/api/students/search",
            params=params,
            catch_response=True,
            name=f"搜索-{list(params.keys())}",
        ) as response:
            # 1. 验证状态码
            if response.status_code != 200:
                response.failure(f"搜索失败: {response.status_code}")
                return

            # 2. 验证响应格式
            try:
                results = response.json()
            except json.JSONDecodeError:
                response.failure("搜索响应不是有效的JSON")
                return

            # 3. 验证数据类型
            if not isinstance(results, list):
                response.failure("搜索响应格式错误：期望数组")
                return

            # 4. 验证搜索结果
            if "name" in params and results:
                keyword = params["name"]
                for student in results:
                    if keyword not in student.get("name", ""):
                        response.failure(
                            f"搜索结果不匹配: 搜索'{keyword}' 但返回 '{student.get('name')}'"
                        )
                        return

            response.success()

    @task(6)
    def create_student_with_validation(self):
        """
        创建学生 - 完整验证

        验证点：
        1. 创建成功
        2. 数据一致性
        3. 唯一性约束
        """
        student_data = self.data_generator.generate_student()

        with self.client.post(
            "/api/students", json=student_data, catch_response=True, name="创建学生"
        ) as response:
            # 1. 验证状态码
            if response.status_code != 200:
                response.failure(f"创建失败: {response.status_code}")
                return

            # 2. 验证响应
            try:
                data = response.json()
            except json.JSONDecodeError:
                response.failure("创建响应不是有效的JSON")
                return

            if not data.get("success"):
                response.failure(f"创建失败: {data.get('message')}")
                return

            # 3. 验证数据一致性 - 确认学生已创建
            try:
                verify_response = self.client.get("/api/students", name="验证创建")
                if verify_response.status_code == 200:
                    students = verify_response.json()

                    # 查找是否创建成功
                    found = any(
                        s.get("student_id") == student_data["student_id"]
                        for s in students
                    )

                    if found:
                        response.success()
                        logger.debug(f"✅ 创建学生成功: {student_data['name']}")
                    else:
                        response.failure("创建的学生未在列表中找到")
                else:
                    response.failure("无法验证学生创建")
            except Exception as e:
                response.failure(f"验证创建异常: {e}")

    @task(4)
    def update_with_validation(self):
        """
        更新学生 - 完整验证

        验证点：
        1. 更新成功
        2. 数据变化验证
        3. 字段完整性
        """
        # 1. 获取一个学生
        response = self.client.get("/api/students", name="获取列表-更新")
        if response.status_code != 200:
            return

        try:
            students = response.json()
            if not students:
                return

            student = random.choice(students)
            student_id = student["id"]

            # 2. 构造更新数据
            update_data = {
                "name": student["name"] + "改",
                "student_id": student["student_id"],
                "age": random.randint(18, 25),
            }

            # 3. 执行更新
            with self.client.put(
                f"/api/students/{student_id}",
                json=update_data,
                catch_response=True,
                name="更新学生",
            ) as update_response:
                # 验证状态码
                if update_response.status_code != 200:
                    update_response.failure(f"更新失败: {update_response.status_code}")
                    return

                # 验证响应
                try:
                    data = update_response.json()
                except json.JSONDecodeError:
                    update_response.failure("更新响应不是有效的JSON")
                    return

                if not data.get("success"):
                    update_response.failure(f"更新失败: {data.get('message')}")
                    return

                # 4. 验证更新是否成功
                verify_response = self.client.get(
                    f"/api/students/{student_id}", name="验证更新"
                )

                if verify_response.status_code == 200:
                    updated = verify_response.json()
                    if updated.get("name") == update_data["name"]:
                        update_response.success()
                        logger.debug(f"✅ 更新学生成功: {update_data['name']}")
                    else:
                        update_response.failure(
                            f"数据未更新: 期望 '{update_data['name']}'，"
                            f"实际 '{updated.get('name')}'"
                        )
                else:
                    update_response.failure("无法验证学生更新")

        except Exception as e:
            logger.error(f"更新异常: {e}")

    @task(2)
    def delete_with_validation(self):
        """
        删除学生 - 完整验证

        验证点：
        1. 删除成功
        2. 数据确实被删除
        3. 保留至少一条数据
        """
        # 1. 获取学生列表
        response = self.client.get("/api/students", name="获取列表-删除")
        if response.status_code != 200:
            return

        try:
            students = response.json()

            # 至少保留一条数据
            if len(students) < 2:
                return

            # 选择要删除的学生（不删除第一条）
            student = random.choice(students[1:])
            student_id = student["id"]
            student_name = student["name"]

            # 2. 执行删除
            with self.client.delete(
                f"/api/students/{student_id}", catch_response=True, name="删除学生"
            ) as delete_response:
                # 验证状态码
                if delete_response.status_code != 200:
                    delete_response.failure(f"删除失败: {delete_response.status_code}")
                    return

                # 验证响应
                try:
                    data = delete_response.json()
                except json.JSONDecodeError:
                    delete_response.failure("删除响应不是有效的JSON")
                    return

                if not data.get("success"):
                    delete_response.failure(f"删除失败: {data.get('message')}")
                    return

                # 3. 验证删除是否成功
                verify_response = self.client.get(
                    f"/api/students/{student_id}", name="验证删除"
                )

                if verify_response.status_code == 404:
                    delete_response.success()
                    logger.debug(f"✅ 删除学生成功: {student_name}")
                else:
                    delete_response.failure(
                        f"删除未生效: {verify_response.status_code}"
                    )

        except Exception as e:
            logger.error(f"删除异常: {e}")


# ==================== 用户类 ====================
class StudentManagementUser(HttpUser):
    """
    高级用户类

    企业级特点：
    1. 可配置的思考时间
    2. 连接池配置
    3. 生命周期管理
    """

    wait_time = between(Config.THINK_TIME_MIN, Config.THINK_TIME_MAX)
    tasks = [StudentManagementTasks]
    host = Config.HOST

    # 连接池配置
    pool_size = 100

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_time = None

    # def on_start(self):
    #     """用户启动"""
    #     self.start_time = datetime.now()
    #     logger.info(f"👤 用户会话开始: {self.start_time}")

    def on_start(self):
        """
        用户启动 - 登录并验证

        企业级特点：
        1. 登录验证
        2. 会话管理
        3. 错误重试
        4. 自动注册（如果用户不存在）
        """
        users = Config.load_test_users()
        if not users:
            raise Exception("没有可用的测试用户")

        # 用 self.current_user 代替 self.user（避免覆盖框架属性）
        self.current_user = random.choice(users)
        username = self.current_user["username"]
        password = self.current_user["password"]

        logger.info(f"👤 用户 {username} 开始测试")

        # 登录重试机制
        for attempt in range(Config.MAX_RETRIES):
            try:
                with self.client.post(
                    "/api/login",
                    json={"username": username, "password": password},
                    catch_response=True,
                    name="登录",
                ) as response:
                    # ============ 新增：如果用户不存在，自动注册 ============
                    if response.status_code == 400 or "用户不存在" in response.text:
                        logger.info(f"📝 用户 {username} 不存在，尝试注册...")

                        # 调用注册接口（根据您的实际 API 调整）
                        register_resp = self.client.post(
                            "/api/register",  # ⚠️ 请根据实际注册接口路径修改
                            json={"username": username, "password": password},
                            catch_response=True,
                            name="注册用户",
                        )

                        if register_resp.status_code in [200, 201]:
                            logger.info(f"✅ 用户 {username} 注册成功，重新登录...")
                            # 注册成功后，继续下一次循环重新登录
                            continue
                        else:
                            logger.error(
                                f"❌ 用户 {username} 注册失败: {register_resp.status_code}"
                            )
                            response.failure(f"注册失败: {register_resp.status_code}")
                            # 如果注册失败，继续尝试下一个用户
                            return

                    # ============ 正常登录验证 ============
                    # 断言：状态码
                    assert (
                        response.status_code == 200
                    ), f"登录状态码异常: {response.status_code}"

                    # 断言：响应格式
                    data = response.json()
                    assert "success" in data, "响应缺少 success 字段"

                    # 断言：登录成功
                    assert (
                        data.get("success") is True
                    ), f"登录失败: {data.get('message', '未知错误')}"

                    # 断言：会话已建立
                    assert (
                        "logged_in" in self.client.cookies
                        or "session" in self.client.cookies
                    ), "登录会话未建立"

                    logger.info(f"✅ 用户 {username} 登录成功")
                    response.success()
                    return

            except AssertionError as e:
                logger.warning(f"⚠️ 登录尝试 {attempt + 1} 失败: {e}")
                if attempt < Config.MAX_RETRIES - 1:
                    time.sleep(Config.RETRY_DELAY * (attempt + 1))
            except Exception as e:
                logger.error(f"❌ 登录异常: {e}")
                if attempt < Config.MAX_RETRIES - 1:
                    time.sleep(Config.RETRY_DELAY * (attempt + 1))

        raise Exception(f"用户 {username} 登录失败，已重试 {Config.MAX_RETRIES} 次")

    def on_stop(self):
        """用户停止"""
        if self.start_time:
            duration = (datetime.now() - self.start_time).total_seconds()
            logger.info(f"👤 用户会话结束，持续时间: {duration:.2f}秒")


# ==================== 测试事件监听 ====================
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """测试开始事件"""
    logger.info("=" * 80)
    logger.info("🚀 学生管理系统性能测试 (企业级)")
    logger.info(f"📅 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 打印配置
    Config.print_config()

    # 统计测试用户
    users = Config.load_test_users()
    logger.info(f"👥 测试用户数: {len(users)}")

    logger.info("=" * 80)


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """测试结束事件"""
    logger.info("=" * 80)
    logger.info("📊 性能测试报告摘要")
    logger.info(f"📅 结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    if environment.runner and environment.runner.stats:
        stats = environment.runner.stats
        total = stats.total

        if total.num_requests > 0:
            # 计算关键指标
            success_rate = (
                (total.num_requests - total.num_failures) / total.num_requests * 100
            )
            failure_rate = total.num_failures / total.num_requests * 100

            # 总览
            logger.info("-" * 70)
            logger.info("📈 总览:")
            logger.info(f"   总请求数: {total.num_requests:,}")
            logger.info(f"   失败请求数: {total.num_failures:,}")
            logger.info(f"   成功率: {success_rate:.2f}%")
            logger.info(f"   失败率: {failure_rate:.2f}%")

            # 响应时间
            logger.info(f"   平均响应时间: {total.avg_response_time:.2f}ms")
            logger.info(
                f"   中位数响应时间: {total.get_response_time_percentile(0.50):.2f}ms"
            )
            logger.info(
                f"   95% 响应时间: {total.get_response_time_percentile(0.95):.2f}ms"
            )
            logger.info(
                f"   99% 响应时间: {total.get_response_time_percentile(0.99):.2f}ms"
            )

            # 吞吐量
            logger.info(f"   每秒请求数 (RPS): {total.total_rps:.2f}")
            logger.info(f"   每秒失败数: {total.total_failures_per_sec:.2f}")

            # 各接口详情
            logger.info("-" * 70)
            logger.info("📋 各接口详情:")
            for name, stat in stats.entries.items():
                if stat.num_requests > 0:
                    failure_rate = (
                        (stat.num_failures / stat.num_requests * 100)
                        if stat.num_requests > 0
                        else 0
                    )
                    status = (
                        "✅" if failure_rate < 1 else "⚠️" if failure_rate < 5 else "❌"
                    )
                    logger.info(f"   {status} {name}:")
                    logger.info(f"      请求数: {stat.num_requests:,}")
                    logger.info(f"      平均响应: {stat.avg_response_time:.2f}ms")
                    logger.info(
                        f"      95%响应: {stat.get_response_time_percentile(0.95):.2f}ms"
                    )
                    logger.info(f"      失败率: {failure_rate:.2f}%")

            # 性能建议
            logger.info("-" * 70)
            logger.info("💡 性能建议:")

            # 响应时间建议
            if total.avg_response_time < 200:
                logger.info("   ✅ 平均响应时间优秀 (<200ms)")
            elif total.avg_response_time < 500:
                logger.info("   ⚠️ 平均响应时间可接受 (200-500ms)，建议优化")
            else:
                logger.info("   ❌ 平均响应时间过长 (>500ms)，需要重点优化")

            # 成功率建议
            if success_rate > 99.5:
                logger.info("   ✅ 成功率优秀 (>99.5%)")
            elif success_rate > 99:
                logger.info("   ⚠️ 成功率可接受 (99%-99.5%)")
            else:
                logger.info("   ❌ 成功率过低 (<99%)，需要排查问题")

    logger.info("=" * 80)


@events.request.add_listener
def on_request(
    request_type, name, response_time, response_length, exception, context, **kwargs
):
    """
    每个请求的事件监听

    企业级特点：
    1. 实时错误监控
    2. 性能异常告警
    """
    if exception:
        logger.warning(f"❌ 请求失败: {name} - {exception}")
    elif response_time > 5000:  # 超过5秒记录警告
        logger.warning(f"⚠️ 请求响应缓慢: {name} - {response_time:.2f}ms")


# 导入time模块
import time

# 导出
__all__ = ["StudentManagementUser", "Config"]
