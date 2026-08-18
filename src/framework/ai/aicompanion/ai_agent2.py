from dotenv import load_dotenv
from openai import OpenAI
from datetime import datetime
import os
import json
import streamlit as st
import time
import requests
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

load_dotenv()

# ==========================================
# 第一部分：增强工具层（支持真实API + Fallback）
# ==========================================


class Tool:
    """工具基类"""

    def __init__(self, name: str, description: str, parameters: dict):
        self.name = name
        self.description = description
        self.parameters = parameters

    def execute(self, **kwargs) -> str:
        raise NotImplementedError

    def get_schema(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


class GetCurrentTimeTool(Tool):
    def __init__(self):
        super().__init__(
            name="get_current_time",
            description="获取当前日期时间，可用于回答需要时间基准的问题",
            parameters={"type": "object", "properties": {}, "required": []},
        )

    def execute(self, **kwargs) -> str:
        now = datetime.now()
        return f"当前时间：{now.strftime('%Y年%m月%d日 %H:%M:%S')}"


class SearchWeatherTool(Tool):
    """
    天气工具：优先调用真实API，失败时fallback到mock数据
    练手点：学会处理API Key、超时、降级策略
    """

    def __init__(self):
        super().__init__(
            name="search_weather",
            description="查询指定城市的实时天气，包含温度、天气状况、风力、空气质量",
            parameters={
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "城市名称，如北京、上海、杭州",
                    },
                    "date": {
                        "type": "string",
                        "description": "日期YYYY-MM-DD，不填则默认今天",
                    },
                },
                "required": ["city"],
            },
        )
        self.api_key = os.environ.get("WEATHER_API_KEY")  # 和风天气或其他
        self.mock_db = {
            "北京": {
                "天气": "晴朗",
                "温度": "25°C",
                "湿度": "45%",
                "风力": "3级",
                "空气质量": "良好",
            },
            "上海": {
                "天气": "多云",
                "温度": "28°C",
                "湿度": "60%",
                "风力": "2级",
                "空气质量": "良好",
            },
            "杭州": {
                "天气": "阴天",
                "温度": "26°C",
                "湿度": "65%",
                "风力": "3级",
                "空气质量": "良好",
            },
            "成都": {
                "天气": "小雨",
                "温度": "24°C",
                "湿度": "75%",
                "风力": "1级",
                "空气质量": "中等",
            },
        }

    def _call_real_api(self, city: str) -> Optional[str]:
        """真实API调用示例（这里用和风天气API结构演示）"""
        if not self.api_key:
            return None

        try:
            # 实际使用时替换为真实API endpoint
            # 这里展示标准HTTP调用结构
            url = f"https://devapi.qweather.com/v7/weather/now?location={city}&key={self.api_key}"
            resp = requests.get(url, timeout=5)
            data = resp.json()

            if data.get("code") == "200":
                now = data["now"]
                return (
                    f"{city}实时天气：{now['text']}，温度{now['temp']}°C，"
                    f"湿度{now['humidity']}%，风向{now['windDir']}"
                )
            return None
        except Exception:
            return None

    def execute(self, city: str, date: str = None, **kwargs) -> str:
        # 先尝试真实API
        real_result = self._call_real_api(city)
        if real_result:
            return real_result

        # Fallback到mock数据
        info = self.mock_db.get(city)
        if info:
            target_date = date or datetime.now().strftime("%Y-%m-%d")
            return (
                f"[模拟数据] {city}（{target_date}）天气：{info['天气']}，"
                f"温度{info['温度']}，湿度{info['湿度']}，{info['风力']}风，"
                f"空气质量{info['空气质量']}"
            )

        return f"未找到{city}的天气数据。支持的城市：{list(self.mock_db.keys())}"


class WebSearchTool(Tool):
    """
    网页搜索工具：演示如何接入外部搜索API
    练手点：API封装、结果摘要、错误处理
    """

    def __init__(self):
        super().__init__(
            name="web_search",
            description="搜索互联网信息，获取实时新闻、数据、资料等。当内部知识不足以回答时使用。",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "搜索关键词"},
                    "num_results": {
                        "type": "integer",
                        "description": "返回结果数量，默认3条",
                    },
                },
                "required": ["query"],
            },
        )
        # 可替换为 Serper.dev / Bing API / Tavily 等
        self.search_api_key = os.environ.get("SEARCH_API_KEY")

    def _call_serper(self, query: str, num: int = 3) -> List[Dict]:
        """Serper.dev Google Search API 示例"""
        if not self.search_api_key:
            return []

        try:
            url = "https://google.serper.dev/search"
            headers = {
                "X-API-KEY": self.search_api_key,
                "Content-Type": "application/json",
            }
            payload = {"q": query, "num": num}

            resp = requests.post(url, headers=headers, json=payload, timeout=10)
            data = resp.json()

            results = []
            for item in data.get("organic", [])[:num]:
                results.append(
                    {
                        "title": item.get("title", ""),
                        "snippet": item.get("snippet", ""),
                        "link": item.get("link", ""),
                    }
                )
            return results
        except Exception as e:
            return [{"error": str(e)}]

    def execute(self, query: str, num_results: int = 3, **kwargs) -> str:
        results = self._call_serper(query, num_results)

        if not results:
            return (
                f"[搜索服务暂未配置] 无法搜索'{query}'。\n"
                f"提示：设置 SEARCH_API_KEY 环境变量可启用真实搜索。\n"
                f"模拟结果：关于'{query}'的最新信息需要接入搜索API获取。"
            )

        if "error" in results[0]:
            return f"搜索出错：{results[0]['error']}"

        lines = [f"🔍 搜索结果（{len(results)}条）："]
        for i, r in enumerate(results, 1):
            lines.append(f"{i}. {r['title']}\n   {r['snippet']}\n   {r['link']}")

        return "\n".join(lines)


class SearchAttractionsTool(Tool):
    def __init__(self):
        super().__init__(
            name="search_attractions",
            description="搜索城市景点，支持关键词筛选如'著名'、'免费'、'适合亲子'",
            parameters={
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "城市名称"},
                    "keyword": {"type": "string", "description": "筛选关键词"},
                },
                "required": ["city"],
            },
        )
        self.data = {
            "北京": {
                "著名景点": "故宫、天安门、颐和园、长城、天坛",
                "免费景点": "天安门广场、什刹海、南锣鼓巷、奥林匹克森林公园",
                "适合亲子": "北京动物园、中国科技馆、自然博物馆、环球影城",
            },
            "杭州": {
                "著名景点": "西湖、灵隐寺、雷峰塔、断桥、苏堤",
                "免费景点": "西湖景区、浙江省博物馆、河坊街",
                "适合亲子": "杭州动物园、宋城、极地海洋公园",
            },
        }

    def execute(self, city: str, keyword: str = "", **kwargs) -> str:
        info = self.data.get(city)
        if not info:
            return f"暂无{city}景点数据"

        if keyword:
            for k, v in info.items():
                if keyword in k or k in keyword:
                    return f"{city}【{k}】：{v}"
        return f"{city}著名景点：{info['著名景点']}"


class SearchFoodTool(Tool):
    def __init__(self):
        super().__init__(
            name="search_food",
            description="搜索城市美食，可指定位置如'西湖附近'、'故宫附近'",
            parameters={
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "城市名称"},
                    "location": {"type": "string", "description": "具体位置或区域"},
                },
                "required": ["city"],
            },
        )
        self.data = {
            "北京": {
                "推荐": "北京烤鸭、炸酱面、豆汁儿、涮羊肉",
                "故宫附近": "四季民福烤鸭店、故宫角楼餐厅",
                "南锣鼓巷": "文宇奶酪、炸灌肠、双皮奶",
            },
            "杭州": {
                "推荐": "西湖醋鱼、东坡肉、龙井虾仁、叫花鸡",
                "西湖附近": "楼外楼、知味观、外婆家",
            },
        }

    def execute(self, city: str, location: str = "", **kwargs) -> str:
        info = self.data.get(city)
        if not info:
            return f"暂无{city}美食数据"

        if location:
            for k, v in info.items():
                if location in k or k in location:
                    return f"{location}附近美食：{v}"
        return f"{city}特色美食：{info['推荐']}"


class CalculatorTool(Tool):
    def __init__(self):
        super().__init__(
            name="calculator",
            description="数学计算器，支持四则运算",
            parameters={
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "数学表达式，如 '150 * 3 + 80'",
                    }
                },
                "required": ["expression"],
            },
        )

    def execute(self, expression: str, **kwargs) -> str:
        allowed = set("0123456789+-*/.() ")
        if not all(c in allowed for c in expression):
            return "错误：表达式包含非法字符"
        try:
            result = eval(expression)
            return f"{expression} = {result}"
        except Exception as e:
            return f"计算错误：{str(e)}"


# ==========================================
# 第二部分：用户记忆层（简单持久化）
# ==========================================


class UserMemory:
    """
    用户画像记忆：用JSON文件存储用户偏好
    练手点：RAG的简化版，后续可升级为向量数据库
    """

    def __init__(self, user_id: str = "default"):
        self.user_id = user_id
        self.file_path = f"memory/user_{user_id}.json"
        self.data = self._load()

    def _load(self) -> Dict:
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                pass
        return {"preferences": {}, "history": []}

    def save(self):
        os.makedirs("memory", exist_ok=True)
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    def get_preference(self, key: str, default=None):
        return self.data["preferences"].get(key, default)

    def set_preference(self, key: str, value: Any):
        self.data["preferences"][key] = value
        self.save()

    def add_history(self, record: Dict):
        self.data["history"].append({"time": datetime.now().isoformat(), **record})
        # 只保留最近50条
        self.data["history"] = self.data["history"][-50:]
        self.save()

    def get_context_prompt(self) -> str:
        """生成记忆上下文，注入到system prompt"""
        prefs = self.data["preferences"]
        if not prefs:
            return ""

        lines = ["\n【用户偏好记忆】"]
        for k, v in prefs.items():
            lines.append(f"- {k}: {v}")
        return "\n".join(lines)


# ==========================================
# 第三部分：真正的 ReAct Agent（增强版）
# ==========================================


@dataclass
class Step:
    step_num: int
    role: str  # thought, action, observation, reflection, final
    content: str
    tool_name: Optional[str] = None
    tool_params: Optional[dict] = None
    tool_result: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%H:%M:%S"))


class ReActAgent:
    """
    增强版 ReAct Agent：
    1. 支持并行工具调用（OpenAI一次可返回多个tool_calls）
    2. 自我反思机制（生成答案前检查完整性）
    3. 工具执行重试
    4. 用户记忆注入
    """

    def __init__(self, client: OpenAI, system_str: str, user_memory: UserMemory = None):
        self.client = client
        self.system_str = system_str
        self.max_iterations = 10
        self.user_memory = user_memory or UserMemory()

        # 工具注册
        self.tools: List[Tool] = [
            GetCurrentTimeTool(),
            SearchWeatherTool(),
            WebSearchTool(),
            SearchAttractionsTool(),
            SearchFoodTool(),
            CalculatorTool(),
        ]
        self.tool_map = {t.name: t for t in self.tools}

        self.steps: List[Step] = []
        self.iteration_count = 0

    def _get_tool_schemas(self) -> List[dict]:
        return [t.get_schema() for t in self.tools]

    def _execute_tool(self, tool_call, retry: int = 1) -> str:
        """执行工具，支持重试"""
        tool_name = tool_call.function.name
        tool = self.tool_map.get(tool_name)

        if not tool:
            return f"错误：未找到工具 '{tool_name}'"

        for attempt in range(retry + 1):
            try:
                params = json.loads(tool_call.function.arguments)
                return tool.execute(**params)
            except Exception as e:
                if attempt < retry:
                    time.sleep(0.5)
                    continue
                return f"工具执行异常（已重试{retry}次）：{str(e)}"

    def _add_step(self, role: str, content: str, **kwargs):
        self.iteration_count += 1
        step = Step(step_num=self.iteration_count, role=role, content=content, **kwargs)
        self.steps.append(step)
        return step

    def _build_system_prompt(self) -> str:
        """构建完整的system prompt，注入用户记忆"""
        memory_ctx = self.user_memory.get_context_prompt()
        return f"""{self.system_str}

【工作模式：ReAct Agent】
你具备调用工具的能力。请遵循以下流程：
1. 分析用户问题和当前已知信息
2. 如果信息不足，调用合适工具获取数据
3. 可以一次调用多个独立工具提高效率
4. 获得足够信息后，给出完整、自然的回答

【工具使用规范】
- 优先使用工具获取实时信息，不要编造数据
- 如果工具返回错误，如实告知用户
- 计算类问题必须使用 calculator 工具，不要心算

{memory_ctx}
"""

    def _self_reflect(self, messages: List[Dict], draft_answer: str) -> str:
        """
        自我反思：在给出最终答案前，检查是否完整、准确
        练手点：这是Agent自我纠错的核心机制
        """
        reflect_prompt = f"""请检查以下回答是否完整准确地解决了用户问题。

用户原始问题：{messages[1]['content'] if len(messages) > 1 else '未知'}

你的草稿回答：
{draft_answer}

请判断：
1. 是否回答了用户问题的所有部分？
2. 是否有编造未经验证的信息？
3. 是否有遗漏需要补充的内容？

如果回答完整准确，请直接输出"PASS"。
如果有问题，请输出改进后的完整回答。
"""

        try:
            resp = self.client.chat.completions.create(
                model="deepseek-v4-pro",
                messages=[
                    {"role": "system", "content": "你是严格的回答质量检查员。"},
                    {"role": "user", "content": reflect_prompt},
                ],
                stream=False,
                temperature=0.3,
            )
            result = resp.choices[0].message.content.strip()

            if result.upper() == "PASS" or result == "PASS":
                return draft_answer

            self._add_step(
                "reflection",
                f"自我反思发现问题，已优化回答。\n反思结果：{result[:200]}...",
            )
            return result
        except:
            return draft_answer

    def run(self, user_input: str) -> str:
        self.steps = []
        self.iteration_count = 0

        # 记录用户query到历史
        self.user_memory.add_history({"type": "query", "content": user_input})

        messages = [
            {"role": "system", "content": self._build_system_prompt()},
            {"role": "user", "content": user_input},
        ]

        final_answer = None

        for turn in range(self.max_iterations):
            response = self.client.chat.completions.create(
                model="deepseek-v4-pro",
                messages=messages,
                tools=self._get_tool_schemas(),
                tool_choice="auto",
                stream=False,
                reasoning_effort="high",
                extra_body={"thinking": {"type": "enabled"}},
            )

            message = response.choices[0].message

            # ===== 情况1：调用工具 =====
            if message.tool_calls:
                if message.content:
                    self._add_step("thought", message.content)

                # 添加assistant消息（含tool_calls）
                messages.append(
                    {
                        "role": "assistant",
                        "content": message.content or "",
                        "tool_calls": [
                            {
                                "id": tc.id,
                                "type": tc.type,
                                "function": {
                                    "name": tc.function.name,
                                    "arguments": tc.function.arguments,
                                },
                            }
                            for tc in message.tool_calls
                        ],
                    }
                )

                # 并行执行多个工具（如果LLM要求）
                for tc in message.tool_calls:
                    tool_name = tc.function.name
                    params = json.loads(tc.function.arguments)

                    self._add_step(
                        "action",
                        f"调用 {tool_name}",
                        tool_name=tool_name,
                        tool_params=params,
                    )

                    result = self._execute_tool(tc, retry=1)

                    self._add_step(
                        "observation", result, tool_name=tool_name, tool_result=result
                    )

                    messages.append(
                        {"role": "tool", "tool_call_id": tc.id, "content": str(result)}
                    )

            # ===== 情况2：直接回答 =====
            else:
                draft = message.content or "（无内容）"
                self._add_step("thought", f"准备生成最终答案（第{turn+1}轮）")

                # 自我反思
                final_answer = self._self_reflect(messages, draft)
                self._add_step("final", final_answer)

                # 提取用户偏好（简单规则：如果用户提到不喜欢/喜欢，记录）
                self._extract_preferences(user_input, final_answer)

                break

        if final_answer is None:
            final_answer = "⚠️ Agent 思考步数已达上限，任务未完成。"
            self._add_step("final", final_answer)

        return final_answer

    def _extract_preferences(self, query: str, answer: str):
        """简单规则提取用户偏好（生产环境应使用LLM提取）"""
        # 饮食偏好
        if "不吃辣" in query or "不吃辣" in answer:
            self.user_memory.set_preference("饮食禁忌", "不吃辣")
        if "素食" in query or "素食" in answer:
            self.user_memory.set_preference("饮食偏好", "素食")
        # 城市偏好
        cities = ["北京", "上海", "杭州", "成都", "西安", "广州", "深圳"]
        for city in cities:
            if city in query and ("去" in query or "玩" in query or "旅游" in query):
                self.user_memory.set_preference("常关注城市", city)


# ==========================================
# 第四部分：Streamlit UI
# ==========================================


def generate_session_name():
    return datetime.now().strftime("%Y%m%d%H%M%S%f")


def save_session():
    if (
        hasattr(st.session_state, "current_session")
        and st.session_state.current_session
    ):
        session_data = {
            "nick_name": st.session_state.nick_name,
            "messages": st.session_state.messages,
            "nature": st.session_state.nature,
            "current_session": st.session_state.current_session,
        }
        os.makedirs("sessions", exist_ok=True)
        with open(
            f"sessions/{st.session_state.current_session}.json", "w", encoding="utf-8"
        ) as f:
            json.dump(session_data, f, ensure_ascii=False, indent=4)


def load_session():
    session_list = []
    if os.path.exists("sessions"):
        for filename in os.listdir("sessions"):
            if filename.endswith(".json"):
                session_list.append(filename[:-5])
        session_list.sort(reverse=True)
    return session_list


def load_session_name(session_name):
    try:
        path = f"sessions/{session_name}.json"
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                session_data = json.load(f)
                st.session_state.messages = session_data["messages"]
                st.session_state.nick_name = session_data["nick_name"]
                st.session_state.nature = session_data["nature"]
                st.session_state.current_session = session_name
    except Exception as e:
        st.error(f"加载失败: {str(e)}")


def delete_session_name(session_name):
    try:
        path = f"sessions/{session_name}.json"
        if os.path.exists(path):
            os.remove(path)
            if st.session_state.current_session == session_name:
                st.session_state.messages = []
                st.session_state.current_session = generate_session_name()
    except Exception as e:
        st.error(f"删除失败: {str(e)}")


st.set_page_config(
    page_title="AI伴侣 - 工业级ReAct Agent",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("🧠 AI智能伴侣 - 工业级 ReAct Agent")

api_key = os.environ.get("APP_DEEPSEEK_API_KEY")
deepseek_url = os.environ.get("APP_DEEPSEEK_URL")

if not api_key:
    st.error("❌ 请设置环境变量 APP_DEEPSEEK_API_KEY")
    st.stop()

client = OpenAI(api_key=api_key, base_url=deepseek_url)

# 初始化
if "messages" not in st.session_state:
    st.session_state.messages = []
if "nick_name" not in st.session_state:
    st.session_state.nick_name = "小甜甜"
if "nature" not in st.session_state:
    st.session_state.nature = "活泼开朗的台湾姑娘，说话温柔可爱，擅长旅行规划"
if "current_session" not in st.session_state:
    st.session_state.current_session = generate_session_name()
if "system_str" not in st.session_state:
    st.session_state.system_str = f"""你叫{st.session_state.nick_name}，是用户的真实伴侣。
规则：
1. 回复自然亲切，体现温柔可爱的性格
2. 口语化表达，像微信聊天
3. 适当使用emoji💞🩷
4. 信息准确、有帮助
5. 回复完整有条理

性格：{st.session_state.nature}"""
if "agent_mode" not in st.session_state:
    st.session_state.agent_mode = True
if "show_debug" not in st.session_state:
    st.session_state.show_debug = True
if "user_memory" not in st.session_state:
    st.session_state.user_memory = UserMemory()

# 显示历史
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 侧边栏
with st.sidebar:
    st.header("⚙️ 设置")

    ai_name = st.text_input("AI名称", value=st.session_state.nick_name)
    ai_personality = st.text_area("性格描述", value=st.session_state.nature, height=80)

    st.divider()

    st.subheader("🧠 Agent 配置")
    agent_mode = st.toggle("启用 ReAct Agent", value=st.session_state.agent_mode)
    show_debug = st.toggle("显示思考过程", value=st.session_state.show_debug)

    if agent_mode != st.session_state.agent_mode:
        st.session_state.agent_mode = agent_mode
        st.rerun()
    if show_debug != st.session_state.show_debug:
        st.session_state.show_debug = show_debug
        st.rerun()

    if agent_mode:
        st.info("""
        🔧 **当前能力**：
        - 动态工具决策（非预规划）
        - 并行工具调用
        - 自我反思纠错
        - 用户偏好记忆
        - 真实API + Mock降级
        """)

    # 显示用户记忆
    with st.expander("💾 用户记忆"):
        mem = st.session_state.user_memory.data.get("preferences", {})
        if mem:
            for k, v in mem.items():
                st.write(f"**{k}**: {v}")
        else:
            st.caption("暂无记忆，Agent会在对话中自动学习")

        if st.button("🗑️ 清除记忆"):
            st.session_state.user_memory.data["preferences"] = {}
            st.session_state.user_memory.save()
            st.rerun()

    st.divider()

    if st.button("🔄 更新设定", use_container_width=True):
        st.session_state.system_str = f"""你叫{ai_name}，是用户的真实伴侣。
规则：
1. 回复自然亲切，体现温柔可爱的性格
2. 口语化表达，像微信聊天
3. 适当使用emoji💞🩷
4. 信息准确、有帮助
5. 回复完整有条理

性格：{ai_personality}"""
        st.session_state.nick_name = ai_name
        st.session_state.nature = ai_personality
        st.success("✅ 已更新!")
        st.rerun()

    if st.button("🆕 新建会话", use_container_width=True):
        save_session()
        st.session_state.messages = []
        st.session_state.current_session = generate_session_name()
        save_session()
        st.rerun()

    st.markdown("### 📚 历史会话")
    for sname in load_session()[:15]:
        c1, c2 = st.columns([4, 1])
        with c1:
            if st.button(sname[:16], key=f"load_{sname}", use_container_width=True):
                load_session_name(sname)
                st.rerun()
        with c2:
            if st.button("❌", key=f"del_{sname}"):
                delete_session_name(sname)
                st.rerun()

# 主对话
prompt = st.chat_input("试试：明天去杭州玩，我不吃辣，帮我规划一下...")

if prompt:
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        try:
            if st.session_state.agent_mode:
                status = st.empty()
                status.info("🧠 Agent 正在 ReAct 循环...")

                agent = ReActAgent(
                    client, st.session_state.system_str, st.session_state.user_memory
                )
                answer = agent.run(prompt)

                # 展示思考链
                if st.session_state.show_debug and agent.steps:
                    with st.expander("🔍 Agent 完整执行链路", expanded=False):
                        for step in agent.steps:
                            if step.role == "thought":
                                st.markdown(f"**💭 思考** `{step.timestamp}`")
                                st.info(step.content or "（模型直接调用工具）")
                            elif step.role == "action":
                                st.markdown(f"**🔧 行动** `{step.timestamp}`")
                                st.code(
                                    f"{step.tool_name}({json.dumps(step.tool_params, ensure_ascii=False)})",
                                    language="python",
                                )
                            elif step.role == "observation":
                                st.markdown(f"**👁️ 观察** `{step.timestamp}`")
                                st.success(
                                    step.content[:300]
                                    + ("..." if len(step.content) > 300 else "")
                                )
                            elif step.role == "reflection":
                                st.markdown(f"**🔍 反思** `{step.timestamp}`")
                                st.warning(step.content)
                            elif step.role == "final":
                                st.markdown(f"**✅ 终答** `{step.timestamp}`")
                                st.markdown(step.content)
                            st.divider()

                        st.caption(
                            f"总步数: {len(agent.steps)} | "
                            f"工具调用: {len([s for s in agent.steps if s.role=='action'])}"
                        )

                st.markdown(answer)
                st.session_state.messages.append(
                    {"role": "assistant", "content": answer}
                )

                action_count = len([s for s in agent.steps if s.role == "action"])
                status.success(
                    f"✅ 完成！{action_count} 次工具调用，{len(agent.steps)} 个思考步骤"
                )

                # 如果记忆有更新，提示一下
                if st.session_state.user_memory.data.get("preferences"):
                    st.caption("💡 Agent 已记住你的偏好，可在侧边栏查看")

            else:
                # 普通模式
                msgs = [
                    {"role": "system", "content": st.session_state.system_str},
                    *st.session_state.messages,
                ]
                resp = client.chat.completions.create(
                    model="deepseek-v4-pro",
                    messages=msgs,
                    stream=True,
                    reasoning_effort="high",
                    extra_body={"thinking": {"type": "enabled"}},
                )

                full = ""
                ph = st.empty()
                for chunk in resp:
                    if chunk.choices and chunk.choices[0].delta.content:
                        full += chunk.choices[0].delta.content
                        ph.markdown(full + "▌")
                ph.markdown(full)
                st.session_state.messages.append({"role": "assistant", "content": full})

            save_session()

        except Exception as e:
            st.error(f"💥 错误: {str(e)}")
            import traceback

            st.code(traceback.format_exc())
