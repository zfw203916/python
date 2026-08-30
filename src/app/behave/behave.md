my-test-framework/src/app/
├── clients/
│   └── studentmanage/
│       └── app.py                          # Flask 学生管理系统
├── behave/                                 # BDD 测试目录
│   ├── features/
│   │   ├── login.feature                   # 登录功能测试
│   │   ├── search.feature                  # 搜索功能测试
│   │   └── student_management.feature      # 学生管理测试
│   ├── steps/
│   │   └── common_steps.py                 # 所有步骤定义（统一管理）
│   └── environment.py                      # 测试环境配置