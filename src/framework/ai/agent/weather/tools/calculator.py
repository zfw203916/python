# src/framework/ai/agent/weather/tools/calculator.py
from langchain.tools import tool
import ast
import operator

@tool
def calculate(expression: str) -> str:
    """
    计算数学表达式。
    当用户需要计算数字、公式、算术时使用。
    
    Args:
        expression: 数学表达式，如 "2 + 3 * 4" 或 "(10 + 5) / 3"
    """
    # 只允许安全的数学运算
    allowed_operators = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
    }
    
    def safe_eval(node):
        if isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.BinOp):
            left = safe_eval(node.left)
            right = safe_eval(node.right)
            op = allowed_operators.get(type(node.op))
            if op:
                return op(left, right)
        elif isinstance(node, ast.UnaryOp):
            operand = safe_eval(node.operand)
            op = allowed_operators.get(type(node.op))
            if op:
                return op(operand)
        raise ValueError("不支持的表达式")
    
    try:
        tree = ast.parse(expression, mode='eval')
        result = safe_eval(tree.body)
        return f"计算结果：{expression} = {result}"
    except Exception as e:
        return f"计算错误：{str(e)}"