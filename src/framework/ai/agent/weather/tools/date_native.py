# src/framework/ai/agent/weather/tools/date_native.py
"""
    原生日期工具
    只做一件事：返回当前日期/时间信息。
"""
from datetime import datetime
from typing import Optional

def get_current_date() -> str:
    """
        获取当前日期和时间信息。
        当用户询问今天几号、现在几点、星期几、今年是哪年等问题时使用。
        Args:
            无
        Returns:
            包含日期、时间、星期的字符串

        以上给开发人用得，而喂给 AI 的是 tool_definitions 里的 description 和 parameters。
    """
    now = datetime.now()
    # 中文星期映射
    weekday_map = {
        0: "星期一",
        1: "星期二",
        2: "星期三",
        3: "星期四",
        4: "星期五",
        5: "星期六",
        6: "星期日",
    }
    date_str = now.strftime("%Y年%m月%d日")
    time_str = now.strftime("%H:%M:%S")
    weekday_str = weekday_map[now.weekday()]

    # 函数必须返回 str（Agent 要求工具返回字符串）
    return (
        f"当日日期：{date_str}\n"
        f"当日时间：{time_str}\n"
        f"当日周几：{weekday_str}\n"
    )

