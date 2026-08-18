.PHONY: install test unit integration lint format mypy clean
# .PHONY: 声明伪目标，这些目标不对应实际的文件名
# 列出所有可用的命令目标，防止与同名文件冲突
# 伪目标总是被执行，即使存在同名文件

install:
	# 安装项目依赖
	uv sync --all-groups
	# uv: 现代化的Python包管理器
	# sync: 同步依赖到虚拟环境
	# --all-groups: 安装所有依赖组（包括dev依赖）
	# 相当于安装项目所有运行和开发依赖

test:
	# 运行所有测试
	uv run pytest tests/ -v --cov=src --cov-report=term-missing
	# uv run: 在项目的虚拟环境中运行命令
	# pytest: 测试框架
	# tests/: 测试目录
	# -v: 详细输出模式
	# --cov=src: 统计src目录的代码覆盖率
	# --cov-report=term-missing: 终端输出覆盖率报告，并显示未覆盖的行号

# 串行执行（调试时用）
test-serial:
	uv run pytest tests/ -v --cov=src --cov-report=term-missing

# 性能基准
benchmark:
	@echo "=== Serial ==="
	@time uv run pytest tests/ -q --tb=no
	@echo "\n=== Parallel (auto) ==="
	@time uv run pytest tests/ -q --tb=no -n auto

unit:
	# 运行单元测试
	uv run pytest tests/unit -v -m unit --cov=src --cov-report=term-missing
	# tests/unit: 单元测试目录
	# -m unit: 只运行标记为"unit"的测试（使用pytest的marker功能）
	# 其余参数同test目标

integration:
	# 运行集成测试
	uv run pytest tests/integration -v -m integration --cov=src --cov-report=term-missing
	# tests/integration: 集成测试目录
	# -m integration: 只运行标记为"integration"的测试
	# 其余参数同test目标

e23:
	# 运行特定测试（可能是个示例或临时测试）
	uv run pytests/e22 -v --cov=src --cov-report=term-missing
	# pytests/e22: 特定测试文件或目录（注意：这里可能是拼写错误，应该是tests/e22）
	# 其他参数同test目标
	# 注意：这个命令看起来像是临时添加的调试命令

lint:
	# 代码检查（Lint）
	uv run ruff check src tests
	# ruff check: 运行ruff的代码检查功能
	# src tests: 检查src和tests目录的所有Python文件
	# ruff: 快速的Python代码检查工具，替代pylint、flake8等
	
	uv run mypy src
	# mypy: 运行静态类型检查
	# src: 只检查src目录的类型注解

list:
	# 代码检查（更全面的版本）
	uv run ruff check src tests
	# 检查所有代码
	
	uv run mypy src tests
	# 检查src和tests两个目录的类型注解
	# 注意：这个目标名称"list"有点误导，实际上它做的是lint检查

format:
	# 代码格式化
	uv run ruff check --fix src tests
	# ruff check --fix: 自动修复可修复的代码问题
	# 比如：删除未使用的导入、修复格式等
	
	uv run ruff format src tests
	# ruff format: 使用ruff格式化代码（类似black）
	# 自动调整代码缩进、空格、换行等

mypy:
	# 单独运行类型检查
	uv run mypy src tests
	# 对src和tests目录进行静态类型检查
	# 检查类型注解的正确性和一致性

clean:
	# 清理临时文件和缓存
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	# find .: 从当前目录开始查找
	# -type d: 只查找目录
	# -name __pycache__: 查找名为__pycache__的目录
	# -exec rm -rf {} +: 删除找到的目录（递归强制删除）
	# 2>/dev/null: 重定向错误输出到null（忽略错误）
	# || true: 即使命令失败也继续执行
	
	find . -name "*.pyc" -delete 2>/dev/null || true
	# 查找并删除所有.pyc编译缓存文件
	# -delete: 删除找到的文件
	# 同样忽略错误
	
	rm -rf .pytest_cache reports/allure-results reports/allure-html
	# 删除pytest缓存目录和Allure报告目录
	# .pytest_cache: pytest缓存目录
	# reports/allure-results: Allure测试结果
	# reports/allure-html: Allure生成的HTML报告

allure:
	# 生成并打开Allure测试报告
	uv run pytest tests/ -v --alluredir=reports/allure-results
	# 运行所有测试并生成Allure数据文件
	# --alluredir=reports/allure-results: 指定Allure结果保存目录
	
	allure generate reports/allure-results -o reports/allure-html --clean
	# allure generate: 生成HTML报告
	# reports/allure-results: 输入目录（原始数据）
	# -o reports/allure-html: 输出目录（生成的报告）
	# --clean: 清理输出目录
	
	allure open reports/allure-html
	# 在浏览器中打开Allure报告
	# 自动启动本地服务器并打开浏览器

# 注释说明部分
# 我写的执行测试覆盖率生成.
# 作者添加的说明注释

# 打开 htmlcov/index.html 查看
# 说明如何查看覆盖率报告

# 红色行 = 未覆盖
# 绿色行 = 已覆盖
# 说明覆盖率报告的颜色含义

coverage:
	# 生成HTML格式的覆盖率报告
	uv run pytest --cov=src --cov-report=html
	# 运行测试并生成HTML覆盖率报告
	# --cov=src: 统计src目录覆盖率
	# --cov-report=html: 生成HTML格式报告（在htmlcov目录中）
	# 然后可以通过浏览器打开htmlcov/index.html查看