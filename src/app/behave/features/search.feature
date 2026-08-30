# my-test-framework/src/app/behave/features/search.feature
Feature: 学生搜索功能
  作为已登录的用户
  我想要搜索学生
  以便快速找到特定学生

  Background:
    Given 系统已启动
    And 数据库已初始化
    And 存在用户 "testuser" 密码 "testpass123"
    And 我已登录
    And 存在以下学生:
      | 姓名 | 学号 | 年龄 |
      | 张三 | S001 | 20   |
      | 张四 | S002 | 21   |
      | 李四 | S003 | 22   |
      | 王五 | S004 | 20   |

  Scenario: 按姓名搜索学生
    When 我搜索姓名为 "张三" 的学生
    Then 应该找到 "1" 条记录
    And 结果中应该包含 "张三"
    And 结果中不应该包含 "李四"

  Scenario: 按学号搜索学生
    When 我搜索学号为 "S003" 的学生
    Then 应该找到 "1" 条记录
    And 结果中应该包含 "李四"

  Scenario: 按年龄搜索学生
    When 我搜索年龄为 "20" 的学生
    Then 应该找到 "2" 条记录
    And 结果中应该包含 "张三"
    And 结果中应该包含 "王五"

  Scenario: 组合条件搜索
    When 我按条件搜索:
      | 姓名 | 学号 | 年龄 |
      | 张   |      | 20   |
    Then 应该找到 "1" 条记录
    And 结果中应该包含 "张三"

  Scenario: 搜索不存在的学生
    When 我搜索姓名为 "不存在" 的学生
    Then 应该找到 "0" 条记录
    And 应该显示 "未找到匹配的学生"