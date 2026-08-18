# 这是学生成绩系统，跟之前那个学生管理studentmange->app.py的是另一个，不一样。
class Student:
    def __init__(
        self, def_name: str, def_chinese: float, def_math: float, def_english: float
    ):
        self.name = def_name
        self.chinese = round(def_chinese, 2)
        self.math = round(def_math, 2)
        self.english = round(def_english, 2)

    # 魔法函数
    def __str__(self):
        return f"姓名：{self.name}| 语文：{self.chinese:.2f}|数学：{self.math:.2f}|英语：{self.english:.2f}|总分：{self.chinese + self.math + self.english}"

    def _update_score(
        self,
        chinese: float | None = None,
        math: float | None = None,
        english: float | None = None,
    ):
        if chinese is not None:
            self.chinese = chinese
        if math is not None:
            self.math = math
        if english is not None:
            self.english = english


class EduManagement:
    system_version = "V1.0"
    system_name = "教务管理系统"

    def __init__(self):
        self.student_list = []

    def _find_student(self, name: str):
        """查找学生，返回学生对象或None"""
        for s in self.student_list:
            if s.name == name:
                return s
        return None

    def _validate_score(self, score: float, subject: str) -> bool:
        """验证单科成绩是否在0-100范围内"""
        if score is not None and not (0 <= score <= 100):
            print(f"{subject}成绩应在0-100之间")
            return False
        return True

    def _get_score_input(self, subject: str) -> float | None:
        """获取用户输入，返回float或None"""
        value = input(f"请修改学生{subject}的成绩，(回车为不修改):")
        return float(value) if value.strip() else None

    def _display_menu(self):
        print("#####################")
        print(f"当前是：{EduManagement.system_name}-{EduManagement.system_version}")
        print("#1、添加 2、修改 3、显示全部 4、退出")
        print("#####################")

    def _get_choice(self) -> int | None:
        """获取用户选择"""
        try:
            choice = int(input("输入序号："))
            return choice
        except ValueError:
            print("❌ 请输入有效的数字！")
            return None
        except Exception as e:
            print(f"其它错误:{e}")
            return None

    def _exit_system(self):
        print("👋 感谢使用教务管理系统，再见！")
        return True

    def _exit_test(self, name: str = "test----"):
        """
        测试用
        """
        print("测试立即执行函数")
        return name

    # 添加学生成绩
    def add_student(self):
        student_name = input("请输入学生姓名:")
        if self._find_student(student_name) is not None:
            print("❌ 学生名重复了")
            return

        student_chinese = float(input("请输入学生语文成绩:"))
        student_math = float(input("请输入学生数学成绩:"))
        student_english = float(input("请输入学生英语成绩:"))

        if (
            0 <= student_chinese <= 100
            and 0 <= student_math <= 100
            and 0 <= student_english <= 100
        ):
            stu = Student(student_name, student_chinese, student_math, student_english)
            self.student_list.append(stu)
            print("添加成功")
        else:
            print("输入分数应该在0-100")

    # 修改学生成绩
    def update_student(self):
        student_name = input("请输入学生姓名:")
        for s in self.student_list:
            if s.name == student_name:
                print(f"当前学生成绩：{s}")  # 这个魔术方法要好好理解一下。

                # 支持单项修改（直接回车不修改）
                student_chinese = self._get_score_input("语文")
                student_math = self._get_score_input("数学")
                student_english = self._get_score_input("英语")

                if not self._validate_score(student_chinese, "语文"):
                    return
                if not self._validate_score(student_math, "数学"):
                    return
                if not self._validate_score(student_english, "英语"):
                    return

                s._update_score(student_chinese, student_math, student_english)
                print("修改成功")
                return
        print("未找到，修改失败")

    # 删除学生成绩
    # 查询指定学生成绩
    # 展示全部
    def all_students(self):
        for s in self.student_list:
            print(s)

    # 运行系统的f方法
    def run(self):
        while True:
            self._display_menu()
            choice = self._get_choice()

            # 方法1：先处理错误情况
            if choice is None:
                print("❌ 输入错误，请重新选择！")
                continue

            # 使用字典映射代替 match-case（可选）
            """
            无参函数：4: self._exit_system 和 4: lambda: self._exit_system() 都行
            有参函数：必须用 lambda 或 functools.partial 包装，否则会立即执行

            简单记忆：Python 看到 () 就执行。
            """
            actions = {
                1: self.add_student,
                2: self.update_student,
                3: self.all_students,
                4: lambda: self._exit_system(),  # 用 lambda 包一层,整个 lambda 是个函数对象，没括号，不执行.或4: self._exit_system
                5: self._exit_test("test"),
            }

            if choice in actions:
                actions[choice]()  # 核心：字典把数字映射到函数，用 [key]() 动态调用。
                if choice == 4:
                    return


if __name__ == "__main__":
    test = EduManagement()
    test.run()

# 已上共有8个知识点：类首字母大写、__init__ 初始化函数、魔法函数、_name 受保护的函数、类型注解、每个函数只做一件事，符合单一职责原则、lambda匿名函数、字典硬射函数
