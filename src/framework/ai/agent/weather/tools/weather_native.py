# src/framework/ai/agent/weather/tools/weather_native.py
"""
    原生天气工具
    只做一件事：根据城市名，返回天气信息。
"""
from typing import Dict,Optional
import httpx
from functools import lru_cache


@lru_cache(maxsize=10) # 缓存最近 10 个不同城市的查询结果。同样城市第二次调用时，不执行函数体，直接返回缓存。
def _fetch_weather(city: str) -> Optional[str]:
    """内部：调 wttr.in API(带缓存)"""
    try:
        headers = {"User-Agent":"curl/7.68.0"}
        url = f"https://wttr.in/{city}?format=%C+%t+%h+%w&lang=zh"
        response = httpx.get(url, headers=headers,timeout=10) 
        if response.status_code == 200:
            return response.text.strip()
        return None
    except Exception:
        return None

def get_weather(city: str) -> str:
    """
        查询指定城市的实时天气。
        当用户询问天气、温度、会不会下雨等问题时使用。
        Args:
            city:城市名称，如：北京、上海、广州
        Returns:
            天气信息字符串
    """
    result = _fetch_weather(city)
    if result:
        return f"📍 {city}的天气：{result}"
    return f"❌ 查询 {city} 天气失败，请稍后重试。"