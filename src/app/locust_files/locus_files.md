my-test-framework/
├── src/
│   └── app/
│       ├── clients/
│       │   └── studentmange/
│       │       └── app.py              # 被测应用
│       └── locust_files/
│           ├── locustfile.py           # 主测试脚本
│           ├── locustfile_advanced.py  # 高级测试脚本
│           ├── run_scenario.py         # 场景执行器
│           ├── scenarios.yaml          # 场景配置
│           ├── test_users.csv          # 测试用户数据
│           ├── monitor.py              # 实时监控
│           └── utils.py                # 工具函数
├── reports/                            # 测试报告目录
├── logs/                               # 日志目录
└── requirements.txt                    # 依赖管理


3. 运行性能测试
# 交互式模式（推荐）
cd ../locust_files
python run_scenario.py

# 直接执行场景
python run_scenario.py smoke      # 冒烟测试
python run_scenario.py load       # 负载测试
python run_scenario.py stress     # 压力测试
python run_scenario.py spike      # 尖刺测试

# 使用高级脚本
python run_scenario.py load --advanced

# 调试模式
python run_scenario.py smoke --debug

# 列出所有场景
python run_scenario.py list



4. 实时监控
# 在另一个终端运行监控
python monitor.py

# 指定刷新间隔
python monitor.py --interval 5

# 导出数据
python monitor.py --export data.json



5. 查看报告
测试完成后，报告会生成在 reports/ 目录下，直接在浏览器打开 HTML 文件即可。



📚 学习要点总结
1. Locust 核心概念
HttpUser: 虚拟用户

@task: 定义用户操作，权重控制频率

wait_time: 思考时间

catch_response: 自定义响应验证

on_start/on_stop: 生命周期钩子

2. 企业级实践
数据驱动: 使用 CSV 管理测试数据

配置管理: 环境变量 + YAML 配置

日志系统: 结构化日志

报告生成: 自动生成 HTML 报告

监控告警: 实时监控 + 阈值告警

3. 测试策略
冒烟测试: 快速验证

负载测试: 正常负载

压力测试: 系统极限

尖刺测试: 突发流量

耐力测试: 长时间运行

4. 最佳实践
合理的思考时间

完整的业务断言

错误处理和重试

数据清理和隔离

结果分析和报告

🎯 下一步建议
理解代码: 逐行阅读，理解每个部分的作用

修改配置: 调整场景参数，观察效果

添加场景: 在 scenarios.yaml 中添加自定义场景

扩展功能: 添加新的 @task 方法

集成 CI/CD: 将测试集成到 Jenkins/GitLab CI

有任何问题，随时问我！🚀

