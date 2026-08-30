# my-test-framework/src/app/behave/features/login.feature
Feature: 用户登录功能
  作为学生管理系统的用户
  我想要登录系统
  以便管理学生信息

  Background:
    Given 系统已启动
    And 数据库已初始化
    And 存在用户 "testuser" 密码 "testpass123"

  Scenario: 使用正确的用户名和密码登录
    When 我使用用户名 "testuser" 和密码 "testpass123" 登录
    Then 登录应该成功
    And 我应该看到欢迎消息 "欢迎, testuser"

  Scenario: 使用错误的密码登录
    When 我使用用户名 "testuser" 和密码 "wrongpassword" 登录
    Then 登录应该失败
    And 我应该看到错误消息 "用户名或密码错误"

  Scenario: 使用不存在的用户登录
    When 我使用用户名 "nonexistent" 和密码 "anypass" 登录
    Then 登录应该失败
    And 我应该看到错误消息 "用户不存在"

  Scenario: 用户名为空登录
    When 我使用用户名 "" 和密码 "testpass123" 登录
    Then 登录应该失败
    And 我应该看到错误消息 "请输入用户名"

  Scenario: 密码为空登录
    When 我使用用户名 "testuser" 和密码 "" 登录
    Then 登录应该失败
    And 我应该看到错误消息 "请输入密码"