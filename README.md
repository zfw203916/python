



# 确保没有残留环境变量
unset VIRTUAL_ENV 2>/dev/null || true
unset VIRTUAL_ENV 

# 3. 删除旧 .venv
rm -rf .venv uv.lock

# 安装所有依赖（自动创建 .venv）
uv sync --all-groups

# 验证 Python 路径
uv run python -c "import sys; print(sys.executable)"


验证确实在虚拟环境中:
uv run python -c "import sys; print(sys.executable); import pydantic; print(pydantic.__version__)"

如果你想进入虚拟环境 shell

#方式 1：uv 的 shell 模式
uv run bash
#方式 3：直接调用虚拟环境的 Python
.venv/bin/python -c "import sys; print(sys.executable)"

source .venv/bin/activate
which python
python -c "import sys; print(sys.executable)"



# 应该输出: .../my-test-framework/.venv/bin/python3
一个版本问题搞死我： requires-python = ">=3.13,<3.14"
# 运行测试
uv run pytest tests/ -v

## 退出 conda base，让 uv 自己管
conda deactivate