# my-test-framework/src/app/behave/features/student_management.feature
Feature: 学生信息管理
  作为已登录的用户
  我想要管理学生信息
  以便维护学生数据

  Background:
    Given 系统已启动
    And 数据库已初始化
    And 存在用户 "testuser" 密码 "testpass123"
    And 我已登录

  Scenario: 添加一名新学生
    When 我添加一名学生:
      | 姓名 | 学号 | 年龄 |
      | 张三 | S001 | 20   |
    Then 添加应该成功
    And 我应该看到消息 "学生添加成功"
    And 学生列表中应该包含 "张三"

  Scenario: 添加学号重复的学生
    Given 已存在学生:
      | 姓名 | 学号 | 年龄 |
      | 李四 | S002 | 21   |
    When 我添加一名学生:
      | 姓名 | 学号 | 年龄 |
      | 李五 | S002 | 22   |
    Then 添加应该失败
    And 我应该看到错误消息 "学号已存在"

  Scenario: 编辑学生信息
    Given 已存在学生:
      | 姓名 | 学号 | 年龄 |
      | 王六 | S003 | 19   |
    When 我编辑学号 "S003" 的学生:
      | 姓名 | 学号 | 年龄 |
      | 王六 | S003 | 21   |
    Then 编辑应该成功
    And 学生 "王六" 的年龄应该是 "21"

  Scenario: 删除学生
    Given 已存在学生:
      | 姓名 | 学号 | 年龄 |
      | 赵七 | S004 | 20   |
    When 我删除学号 "S004" 的学生
    Then 删除应该成功
    And 学生列表中不应该包含 "赵七"

  Scenario: 未登录时尝试添加学生
    Given 我已登出
    When 我尝试添加一名学生:
      | 姓名 | 学号 | 年龄 |
      | 钱八 | S005 | 20   |
    Then 应该返回未授权错误
    And 错误消息应该是 "未登录"