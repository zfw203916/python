# src/framework/ai/agent/weather/tools/weather.py
import httpx
from langchain.tools import tool


@tool
def get_weather(city: str) -> str:
    """
    查询指定城市的实时天气。
    当用户询问天气、温度、会不会下雨等问题时使用。

    Args:
        city: 城市名称，如：北京、上海、广州
    """
    try:
        url = f"https://wttr.in/{city}?format=%C+%t&lang=zh"
        response = httpx.get(url, timeout=10)
        if response.status_code == 200:
            return f"📍 {city} 的天气：{response.text.strip()}"
        return f"查询 {city} 天气失败"
    except Exception as e:
        return f"天气服务异常：{str(e)}"
