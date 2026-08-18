from dotenv import load_dotenv
from openai import OpenAI
from datetime import datetime, timedelta
import os
import json
import streamlit as st
from typing import List, Dict, Optional
from dataclasses import dataclass, field

load_dotenv()

# ==========================================
# 第一部分：工具层（Tool Layer）
# ==========================================


class Tool:
    """工具基类，所有真实工具都继承此结构"""

    def __init__(self, name: str, description: str, parameters: dict):
        self.name = name
        self.description = description
        self.parameters = parameters

    def execute(self, **kwargs) -> str:
        raise NotImplementedError

    def get_schema(self) -> dict:
        """返回 OpenAI 标准的 tool schema"""
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
            description="获取当前的日期和时间，可用于回答需要时间基准的问题",
            parameters={"type": "object", "properties": {}, "required": []},
        )

    def execute(self, **kwargs) -> str:
        now = datetime.now()
        return f"当前时间：{now.strftime('%Y年%m月%d日 %H:%M:%S')}，星期{now.weekday() + 1}"


class SearchWeatherTool(Tool):
    """天气工具（当前为模拟数据，但结构支持接入真实 API）"""

    def __init__(self):
        super().__init__(
            name="search_weather",
            description="查询指定城市未来几天的天气信息，包括温度、天气状况、风力等",
            parameters={
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "城市名称，如北京、上海"},
                    "date": {
                        "type": "string",
                        "description": "日期，格式YYYY-MM-DD，不填则默认明天",
                    },
                },
                "required": ["city"],
            },
        )
        self.weather_db = {
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
            "广州": {
                "天气": "阵雨",
                "温度": "32°C",
                "湿度": "80%",
                "风力": "1级",
                "空气质量": "中等",
            },
            "深圳": {
                "天气": "晴天",
                "温度": "30°C",
                "湿度": "70%",
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
            "西安": {
                "天气": "晴转多云",
                "温度": "27°C",
                "湿度": "50%",
                "风力": "2级",
                "空气质量": "良好",
            },
            "厦门": {
                "天气": "晴天",
                "温度": "29°C",
                "湿度": "65%",
                "风力": "3级",
                "空气质量": "良好",
            },
        }

    def execute(self, city: str, date: str = None, **kwargs) -> str:
        if not date:
            date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

        info = self.weather_db.get(city)
        if info:
            return (
                f"{city}（{date}）天气：{info['天气']}，温度{info['温度']}，"
                f"湿度{info['湿度']}，{info['风力']}风，空气质量{info['空气质量']}"
            )
        return f"未找到{city}的天气数据，目前支持的城市：{list(self.weather_db.keys())}"


class SearchAttractionsTool(Tool):
    def __init__(self):
        super().__init__(
            name="search_attractions",
            description="搜索城市的景点信息，可指定关键词如'著名'、'免费'、'适合晴天'等",
            parameters={
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "城市名称"},
                    "keyword": {
                        "type": "string",
                        "description": "筛选关键词，如著名景点、免费景点、适合晴天",
                    },
                },
                "required": ["city"],
            },
        )
        self.data = {
            "北京": {
                "著名景点": "故宫博物院、天安门广场、颐和园、八达岭长城、天坛公园",
                "适合晴天": "故宫、颐和园、天坛公园、北海公园、奥林匹克公园",
                "免费景点": "天安门广场、什刹海、南锣鼓巷、奥林匹克森林公园",
            },
            "上海": {
                "著名景点": "外滩、东方明珠、豫园、南京路步行街、上海迪士尼乐园",
                "适合晴天": "外滩、东方明珠、世纪公园、上海植物园",
                "免费景点": "外滩、南京路、田子坊、新天地",
            },
            "杭州": {
                "著名景点": "西湖、灵隐寺、雷峰塔、断桥、苏堤、河坊街",
                "适合晴天": "西湖、苏堤、白堤、灵隐寺、虎跑泉",
                "免费景点": "西湖大部分景点、浙江省博物馆",
            },
        }

    def execute(self, city: str, keyword: str = "", **kwargs) -> str:
        city_info = self.data.get(city)
        if not city_info:
            return f"未找到{city}的景点数据"

        if keyword:
            for k, v in city_info.items():
                if keyword in k or k in keyword:
                    return f"{city}【{k}】：{v}"
            return f"{city}景点信息：{city_info['著名景点']}"
        return f"{city}著名景点：{city_info['著名景点']}"


class SearchFoodTool(Tool):
    def __init__(self):
        super().__init__(
            name="search_food",
            description="搜索城市的美食推荐，可指定具体位置如'故宫附近'、'西湖附近'",
            parameters={
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "城市名称"},
                    "location": {
                        "type": "string",
                        "description": "具体位置或区域，如故宫附近、西湖附近",
                    },
                },
                "required": ["city"],
            },
        )
        self.data = {
            "北京": {
                "推荐": "北京烤鸭、炸酱面、豆汁儿、焦圈、驴打滚、豌豆黄、涮羊肉",
                "故宫附近": "四季民福烤鸭店、故宫角楼餐厅、老北京炸酱面馆",
                "天安门附近": "全聚德烤鸭店、王府井小吃街、东来顺涮肉",
                "南锣鼓巷": "老北京小吃、文宇奶酪、炸灌肠",
            },
            "上海": {
                "推荐": "小笼包、生煎包、蟹粉汤包、排骨年糕、本帮菜",
                "外滩附近": "外滩三号、和平饭店、外滩源、老正兴",
            },
            "杭州": {
                "推荐": "西湖醋鱼、东坡肉、龙井虾仁、叫花鸡、小笼包",
                "西湖附近": "楼外楼、山外山、知味观、外婆家",
            },
        }

    def execute(self, city: str, location: str = "", **kwargs) -> str:
        city_info = self.data.get(city)
        if not city_info:
            return f"未找到{city}的美食数据"

        if location:
            for k, v in city_info.items():
                if location in k or k in location:
                    return f"{location}附近美食：{v}"
            return f"{city}特色美食：{city_info['推荐']}"
        return f"{city}特色美食：{city_info['推荐']}"


class CalculatorTool(Tool):
    """新增：计算工具，演示 Agent 如何使用工具进行推理"""

    def __init__(self):
        super().__init__(
            name="calculator",
            description="进行数学计算，支持加减乘除和简单表达式",
            parameters={
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "数学表达式，如 '25 * 4 + 10'",
                    }
                },
                "required": ["expression"],
            },
        )

    def execute(self, expression: str, **kwargs) -> str:
        try:
            # 安全计算：只允许数字和运算符
            allowed = set("0123456789+-*/.() ")
            if not all(c in allowed for c in expression):
                return "错误：表达式包含非法字符"
            result = eval(expression)
            return f"{expression} = {result}"
        except Exception as e:
            return f"计算错误：{str(e)}"


# ==========================================
# 第二部分：Agent 核心（ReAct 循环）
# ==========================================


@dataclass
class Step:
    """单步执行记录"""

    step_num: int
    role: str  # 'thought', 'action', 'observation', 'final'
    content: str
    tool_name: Optional[str] = None
    tool_params: Optional[dict] = None
    tool_result: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%H:%M:%S"))


class ReActAgent:
    """
    真正的 ReAct Agent：
    1. 不预先规划固定子任务，而是每轮让 LLM 自主决定下一步
    2. 使用标准 OpenAI Tool Calling API
    3. 维护完整的对话历史（包含工具返回结果）
    4. 支持观察-思考-行动的循环
    """

    def __init__(self, client: OpenAI, system_str: str):
        self.client = client
        self.system_str = system_str
        self.max_iterations = 10

        # 注册所有工具
        self.tools: List[Tool] = [
            GetCurrentTimeTool(),
            SearchWeatherTool(),
            SearchAttractionsTool(),
            SearchFoodTool(),
            CalculatorTool(),
        ]
        self.tool_map: Dict[str, Tool] = {t.name: t for t in self.tools}

        # 执行历史
        self.steps: List[Step] = []
        self.iteration_count = 0

    def _get_tool_schemas(self) -> List[dict]:
        return [t.get_schema() for t in self.tools]

    def _execute_tool(self, tool_call) -> str:
        """执行单个工具调用"""
        tool_name = tool_call.function.name
        tool = self.tool_map.get(tool_name)

        if not tool:
            return f"错误：未找到工具 '{tool_name}'"

        try:
            params = json.loads(tool_call.function.arguments)
            result = tool.execute(**params)
            return result
        except Exception as e:
            return f"工具执行异常：{str(e)}"

    def _add_step(self, role: str, content: str, **kwargs):
        self.iteration_count += 1
        step = Step(step_num=self.iteration_count, role=role, content=content, **kwargs)
        self.steps.append(step)
        return step

    def run(self, user_input: str) -> str:
        """
        ReAct 主循环：
        每一轮 LLM 看到完整的上下文（包括之前的工具结果），自主决定：
        - 调用工具获取更多信息（Action）
        - 直接给出最终答案（Final Answer）
        """
        self.steps = []
        self.iteration_count = 0

        # 系统提示中加入 ReAct 指导
        react_system = (
            self.system_str
            + """
        
【重要：你的工作模式】
你是一个具备工具调用能力的智能 Agent。请遵循 ReAct（Reasoning + Acting）模式：
1. 观察当前信息（Observation）
2. 思考下一步（Thought）
3. 决定行动：调用工具获取信息，或直接回答用户
4. 如果信息不足，优先调用工具而非猜测

注意：每次回复请保持你的伴侣角色性格，温柔可爱。
"""
        )

        messages = [
            {"role": "system", "content": react_system},
            {"role": "user", "content": user_input},
        ]

        # ReAct 循环
        for turn in range(self.max_iterations):
            # ---- 调用 LLM ----
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

            # ---- 情况1：LLM 要求调用工具（Action）----
            if message.tool_calls:
                # 记录 LLM 的思考（如果有 content）
                if message.content:
                    self._add_step("thought", message.content)

                # 必须先添加 assistant 的 tool_calls 消息到历史
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

                # 逐个执行工具
                for tc in message.tool_calls:
                    tool_name = tc.function.name
                    params = json.loads(tc.function.arguments)

                    # 记录 Action
                    self._add_step(
                        "action",
                        f"调用工具：{tool_name}",
                        tool_name=tool_name,
                        tool_params=params,
                    )

                    # 执行
                    result = self._execute_tool(tc)

                    # 记录 Observation
                    self._add_step(
                        "observation", result, tool_name=tool_name, tool_result=result
                    )

                    # 添加 tool 返回消息到对话历史
                    messages.append(
                        {"role": "tool", "tool_call_id": tc.id, "content": str(result)}
                    )

                # 继续下一轮，让 LLM 基于新观察决定下一步

            # ---- 情况2：LLM 直接给出最终答案 ----
            else:
                final_answer = message.content or "（无回复内容）"
                self._add_step("final", final_answer)

                # 可选：让 LLM 自我反思（Self-reflection）
                # 这里简化处理，直接返回
                return final_answer

        # 如果循环耗尽仍未结束，给出提示
        return "⚠️ Agent 思考步数已达上限，但任务似乎尚未完成。请尝试简化问题。"


# ==========================================
# 第三部分：Streamlit UI（保留原结构，增强展示）
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
        if not os.path.exists("sessions"):
            os.makedirs("sessions")
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
        st.error(f"加载会话失败: {str(e)}")


def delete_session_name(session_name):
    try:
        path = f"sessions/{session_name}.json"
        if os.path.exists(path):
            os.remove(path)
            if st.session_state.current_session == session_name:
                st.session_state.messages = []
                st.session_state.current_session = generate_session_name()
    except Exception as e:
        st.error(f"删除会话失败: {str(e)}")


# ---- 页面配置 ----
st.set_page_config(
    page_title="AI智能伴侣 - 真正的ReAct Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("🤖 AI智能伴侣 - 真正的 ReAct Agent")

api_key = os.environ.get("APP_DEEPSEEK_API_KEY")
deepseek_url = os.environ.get("APP_DEEPSEEK_URL")

if api_key is None:
    st.error("❌ 环境变量 APP_DEEPSEEK_API_KEY 未设置")
    st.stop()

client = OpenAI(api_key=api_key, base_url=deepseek_url)

# ---- 初始化状态 ----
if "messages" not in st.session_state:
    st.session_state.messages = []
if "nick_name" not in st.session_state:
    st.session_state.nick_name = "小甜甜"
if "nature" not in st.session_state:
    st.session_state.nature = (
        "活泼开朗的台湾姑娘，说话温柔可爱，是个贴心的旅行规划小助手"
    )
if "current_session" not in st.session_state:
    st.session_state.current_session = generate_session_name()
if "system_str" not in st.session_state:
    st.session_state.system_str = f"""你叫{st.session_state.nick_name}，现在是用户的真实伴侣。
规则：
1. 每次回复要自然、亲切，体现温柔可爱的性格
2. 用口语化的方式表达，像微信聊天一样
3. 适当使用emoji表情💞🩷
4. 信息要准确、有帮助
5. 回复要完整、有条理

伴侣性格：{st.session_state.nature}"""
if "agent_mode" not in st.session_state:
    st.session_state.agent_mode = True
if "show_debug" not in st.session_state:
    st.session_state.show_debug = True

# ---- 显示历史消息 ----
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ---- 侧边栏 ----
with st.sidebar:
    st.header("⚙️ 设置")

    ai_name = st.text_input("AI名称", value=st.session_state.nick_name)
    ai_personality = st.text_area("性格描述", value=st.session_state.nature, height=80)

    st.divider()

    st.subheader("🧠 Agent 模式")
    agent_mode = st.toggle("启用 ReAct Agent", value=st.session_state.agent_mode)
    show_debug = st.toggle("显示 Agent 思考过程", value=st.session_state.show_debug)

    if agent_mode != st.session_state.agent_mode:
        st.session_state.agent_mode = agent_mode
        st.rerun()

    if show_debug != st.session_state.show_debug:
        st.session_state.show_debug = show_debug
        st.rerun()

    if agent_mode:
        st.info("""
        🔄 **ReAct Agent 工作流**：
        1. **Observation**：观察当前已知信息
        2. **Thought**：LLM 自主思考下一步
        3. **Action**：自动调用工具获取数据
        4. **循环**：重复直到信息充足
        5. **Final Answer**：生成最终回复
        
        💡 与旧版区别：不再预先固定子任务，每轮动态决策
        """)

    st.divider()

    if st.button("🔄 更新设定", use_container_width=True):
        system_str = f"""你叫{ai_name}，现在是用户的真实伴侣。
规则：
1. 每次回复要自然、亲切，体现温柔可爱的性格
2. 用口语化的方式表达，像微信聊天一样
3. 适当使用emoji表情💞🩷
4. 信息要准确、有帮助
5. 回复要完整、有条理

伴侣性格：{ai_personality}"""
        st.session_state.system_str = system_str
        st.session_state.nick_name = ai_name
        st.session_state.nature = ai_personality
        st.success("✅ 设置已更新!")
        st.rerun()

    if st.button("🆕 新建会话", use_container_width=True):
        save_session()
        st.session_state.messages = []
        st.session_state.current_session = generate_session_name()
        save_session()
        st.rerun()

    st.markdown("### 📚 历史会话")
    session_list = load_session()
    for session_name in session_list[:20]:  # 只显示最近20个
        col1, col2 = st.columns([4, 1])
        with col1:
            display_name = session_name[:16] if len(session_name) > 16 else session_name
            if st.button(
                display_name, key=f"load_{session_name}", use_container_width=True
            ):
                load_session_name(session_name)
                st.rerun()
        with col2:
            if st.button("❌", key=f"delete_{session_name}"):
                delete_session_name(session_name)
                st.rerun()

# ---- 主对话区 ----
prompt = st.chat_input("输入您的问题，例如：帮我规划一下明天去杭州的行程...")

if prompt:
    # 显示用户消息
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        try:
            if st.session_state.agent_mode:
                # ====== ReAct Agent 模式 ======
                status = st.empty()
                status.info("🧠 Agent 正在 ReAct 循环中思考与行动...")

                # 运行 Agent
                agent = ReActAgent(client, st.session_state.system_str)
                final_answer = agent.run(prompt)

                # 展示思考过程（可折叠）
                if st.session_state.show_debug and agent.steps:
                    with st.expander(
                        "🔍 查看 Agent 完整思考与执行过程", expanded=False
                    ):
                        st.markdown("---")

                        for step in agent.steps:
                            if step.role == "thought":
                                st.markdown(f"**🤔 思考 ({step.timestamp})**")
                                st.info(step.content or "（模型直接输出工具调用）")

                            elif step.role == "action":
                                st.markdown(f"**🔧 行动 ({step.timestamp})**")
                                params_str = json.dumps(
                                    step.tool_params, ensure_ascii=False, indent=2
                                )
                                st.code(
                                    f"工具: {step.tool_name}\n参数: {params_str}",
                                    language="json",
                                )

                            elif step.role == "observation":
                                st.markdown(f"**👁️ 观察 ({step.timestamp})**")
                                st.success(step.content)

                            elif step.role == "final":
                                st.markdown(f"**✅ 最终答案 ({step.timestamp})**")
                                st.markdown(step.content)

                            st.markdown("---")

                        st.caption(f"总计执行步数: {len(agent.steps)}")

                # 展示最终答案
                st.markdown(final_answer)
                st.session_state.messages.append(
                    {"role": "assistant", "content": final_answer}
                )

                # 更新状态
                action_count = len([s for s in agent.steps if s.role == "action"])
                status.success(
                    f"✅ 任务完成！共进行 {action_count} 次工具调用，{len(agent.steps)} 个思考步骤"
                )

            else:
                # ====== 普通模式（直接对话）======
                messages = [
                    {"role": "system", "content": st.session_state.system_str},
                    *st.session_state.messages,
                ]

                response = client.chat.completions.create(
                    model="deepseek-v4-pro",
                    messages=messages,
                    stream=True,
                    reasoning_effort="high",
                    extra_body={"thinking": {"type": "enabled"}},
                )

                full_response = ""
                placeholder = st.empty()

                for chunk in response:
                    if chunk.choices and chunk.choices[0].delta is not None:
                        delta = chunk.choices[0].delta
                        if hasattr(delta, "content") and delta.content:
                            full_response += delta.content
                            placeholder.markdown(full_response + "▌")

                placeholder.markdown(full_response)
                st.session_state.messages.append(
                    {"role": "assistant", "content": full_response}
                )

            save_session()

        except Exception as e:
            st.error(f"💥 发生错误: {str(e)}")
            import traceback

            st.code(traceback.format_exc())
