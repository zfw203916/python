from dotenv import load_dotenv
from openai import OpenAI
from datetime import datetime
import openai
import os
import json
import streamlit as st

# ========== 🆕 新增：导入 re 模块（用于计算器安全检查） ==========
import re
# ========== 🆕 新增结束 ==========

load_dotenv()


# 保存会话标识
def generate_session_name():
    return datetime.now().strftime("%Y%m%d%H%M%S%f")


# 保存会话信息函数
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
        # 将会话数据保存到本地文件或数据库中
        if not os.path.exists("sessions"):
            os.makedirs("sessions")

        # 将会话数据保存为JSON文件
        with open(
            f"sessions/{st.session_state.current_session}.json", "w", encoding="utf-8"
        ) as f:
            json.dump(session_data, f, ensure_ascii=False, indent=4)


# 加载会话信息函数
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
        if os.path.exists(f"sessions/{session_name}.json"):
            # 读取会话数据
            with open(f"sessions/{session_name}.json", "r", encoding="utf-8") as f:
                session_data = json.load(f)
                st.session_state.messages = session_data["messages"]
                st.session_state.nick_name = session_data["nick_name"]
                st.session_state.nature = session_data["nature"]
                st.session_state.current_session = session_name
    except Exception as e:
        st.error(f"加载会话失败: {str(e)}")


def delete_session_name(session_name):
    try:
        if os.path.exists(f"sessions/{session_name}.json"):
            os.remove(f"sessions/{session_name}.json")

            if st.session_state.current_session == session_name:
                st.session_state.messages = []
                st.session_state.current_session = generate_session_name()
    except Exception as e:
        st.error(f"删除会话失败: {str(e)}")


st.set_page_config(
    page_title="AI智能伴侣",
    page_icon="👽️",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={},
)

st.title("AI智能伴侣")

api_key = os.environ.get("APP_DEEPSEEK_API_KEY")
deepseek_url = os.environ.get("APP_DEEPSEEK_URL")
if api_key is None:
    st.error("APP_DEEPSEEK_API_KEY is not set")
    st.stop()
client = OpenAI(api_key=api_key, base_url=deepseek_url)

# 初始化 session_state（在一切使用之前）
if "messages" not in st.session_state:
    st.session_state.messages = []
if "nick_name" not in st.session_state:
    st.session_state.nick_name = "小甜甜"
if "nature" not in st.session_state:
    st.session_state.nature = "活泼开朗的台湾姑娘"
if "current_session" not in st.session_state:
    st.session_state.current_session = generate_session_name()
if "system_str" not in st.session_state:
    st.session_state.system_str = f"""
    你叫{st.session_state.nick_name}，现在是用户的真实伴侣，请完全代入伴侣角色。
    规则：
    1、每次只回1条消息.
    2、禁止任何场景或状态描述性文字.
    3、匹配用户的语言.
    4、回复简短，像微信聊天一样.
    5、有需要的话可以用🩷 💞等emoji表情.
    6、用符合伴侣性格的方式对话.
    7、回复的内容，要充分体现伴侣的性格特征.
    伴侣性格：
    - {st.session_state.nature}
    你必须严格遵守上述规则来回复用户。
"""


# ========== 🆕 新增：工具定义（让 AI 能调用外部功能） ==========
def get_current_time() -> str:
    """获取当前时间 - 工具函数"""
    now = datetime.now()
    return now.strftime("%Y年%m月%d日 %H:%M:%S")


def calculate(expression: str) -> str:
    """执行简单的数学计算 - 工具函数"""
    try:
        # 安全检查：只允许数字和基本运算符
        if not re.match(r"^[\d+\-*/().\s]+$", expression):
            return "❌ 表达式包含非法字符"
        result = eval(expression)
        return f"计算结果：{expression} = {result}"
    except Exception as e:
        return f"❌ 计算错误：{str(e)}"


# 工具的 JSON Schema（告诉 AI 有哪些工具可用、如何调用）
tools_schema = [
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "获取当前日期和时间，不需要参数",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "执行数学计算，支持加减乘除和括号",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "数学表达式，如 '2+3*4'",
                    }
                },
                "required": ["expression"],
            },
        },
    },
]

# 工具注册表（将工具名称映射到实际函数）
tools_registry = {"get_current_time": get_current_time, "calculate": calculate}
# ========== 🆕 新增：工具定义结束 ==========


# ========== 🆕 新增：工具调用处理函数 ==========
def handle_tool_calls(tool_calls):
    """处理工具调用并返回结果"""
    tool_results = []

    for tool_call in tool_calls:
        tool_name = tool_call.function.name
        tool_args = json.loads(tool_call.function.arguments)

        # 执行对应的工具函数
        if tool_name in tools_registry:
            tool_function = tools_registry[tool_name]
            try:
                if tool_args:
                    result = tool_function(**tool_args)
                else:
                    result = tool_function()
                tool_results.append({"tool_call_id": tool_call.id, "content": result})
            except Exception as e:
                tool_results.append(
                    {
                        "tool_call_id": tool_call.id,
                        "content": f"❌ 工具执行失败：{str(e)}",
                    }
                )
        else:
            tool_results.append(
                {"tool_call_id": tool_call.id, "content": f"❌ 未知工具：{tool_name}"}
            )

    return tool_results


# ========== 🆕 新增：工具调用处理函数结束 ==========

# 显示历史消息
for message in st.session_state.messages:
    st.chat_message(message["role"]).markdown(message["content"])

    # 会话标识
    if "current_session" not in st.session_state:
        st.session_state.current_session = generate_session_name()

# ========== 🔄 修改：侧边栏 - 新增"启用工具"选项 ==========
with st.sidebar:
    st.header("⚙️ AI伴侣设置")
    ai_name = st.text_input("AI名称", value="小甜甜")
    st.markdown("你可以在这里设置伴侣的性格和行为。")
    ai_personality = st.text_area(
        "伴侣性格描述", value="活泼开朗的台湾姑娘", height=100
    )
    ai_extra_rules = st.text_area(
        "伴侣行为规则",
        value="1、每次只回1条消息.\n2、禁止任何场景或状态描述性文字.\n3、匹配用户的语言.\n4、回复简短，像微信聊天一样.\n5、有需要的话可以用🩷 💞等emoji表情.\n6、用符合伴侣性格的方式对话.\n7、回复的内容，要充分体现伴侣的性格特征.\n",
        height=200,
    )

    # 🆕 新增：工具启用开关
    st.divider()
    st.subheader("🔧 工具设置")
    enable_tools = st.toggle(
        "启用工具调用", value=True, help="开启后，AI可以调用计算器、时间查询等工具"
    )
    # 🆕 新增结束

    if st.button("🔄 更新设定"):
        # 更新系统消息
        system_str = f"""
        你叫{ai_name}，现在是用户的真实伴侣，请完全代入伴侣角色。
        规则：
            {ai_extra_rules}
        伴侣性格：
            -{ai_personality}
        {ai_extra_rules}
        你必须严格遵守上述规则来回复用户。
        """
        st.session_state.system_str = system_str
        st.success("设置已更新!")
        st.rerun()

    # 新建会话
    if st.button("新建会话", icon="🔄", width=200):
        save_session()  # 保存当前会话
        if st.session_state.messages:
            st.session_state.messages = []
            st.session_state.current_session = generate_session_name()
            save_session()  # 保存新会话
            st.rerun()  # 刷新页面以显示新会话

    # 加载历史会话
    st.markdown("### 历史会话")
    session_list = load_session()
    for session_name in session_list:
        col1, col2 = st.columns([4, 1])
        with col1:
            # 三元运算符：主要按钮 type="primary"，次要按钮 type="secondary"
            if col1.button(
                session_name,
                width="stretch",
                icon="💾",
                key=f"load_{session_name}",
                type="primary"
                if session_name == st.session_state.current_session
                else "secondary",
            ):
                load_session_name(session_name)
                st.rerun()  # 刷新页面以显示加载的会话
        with col2:
            if col2.button(
                "", width="stretch", icon="❌️", key=f"delete_{session_name}"
            ):
                delete_session_name(session_name)
                st.rerun()  # 刷新页面以显示删除的会话
# ========== 🔄 修改结束 ==========

prompt = st.chat_input("请输入您的问题：")
if prompt:
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # 打印调试信息
    print(
        [
            {"role": "system", "content": st.session_state.system_str},
            *st.session_state.messages,
        ]
    )

    # ========== 🔄 修改：主对话逻辑 - 支持工具调用 ==========
    try:
        # 构建消息列表
        messages = [
            {"role": "system", "content": st.session_state.system_str},
            *st.session_state.messages,
        ]

        # 准备 API 调用参数
        api_params = {
            "model": "deepseek-v4-pro",
            "messages": messages,
            "stream": True,
            "reasoning_effort": "high",
            "extra_body": {"thinking": {"type": "enabled"}},
        }

        # 🆕 新增：如果启用工具，添加 tools 参数
        if enable_tools:
            api_params["tools"] = tools_schema
            api_params["tool_choice"] = "auto"
        # 🆕 新增结束

        # 第一次 API 调用
        response = client.chat.completions.create(**api_params)

        # 🆕 新增：处理流式响应中的工具调用
        # 由于 DeepSeek 的流式响应中，工具调用信息在第一个 chunk 中
        # 我们需要收集所有 chunk 来判断是否有工具调用

        # 创建一个容器来存储流式响应的内容
        response_message = st.chat_message("assistant")
        thinking_placeholder = response_message.empty()
        message_placeholder = response_message.empty()
        full_response = ""
        thinking_content = ""

        # 存储工具调用信息
        tool_calls_info = []
        is_tool_call = False

        for chunk in response:
            if chunk.choices and chunk.choices[0].delta is not None:
                delta = chunk.choices[0].delta

                # 🆕 新增：检查是否有工具调用（在第一个 chunk 中）
                if hasattr(delta, "tool_calls") and delta.tool_calls:
                    is_tool_call = True
                    for tool_call in delta.tool_calls:
                        tool_calls_info.append(
                            {
                                "id": tool_call.id,
                                "function": {
                                    "name": tool_call.function.name
                                    if hasattr(tool_call.function, "name")
                                    else "",
                                    "arguments": tool_call.function.arguments
                                    if hasattr(tool_call.function, "arguments")
                                    else "{}",
                                },
                            }
                        )
                # 🆕 新增结束

                # 处理思考内容（如果有）
                if hasattr(delta, "reasoning_content") and delta.reasoning_content:
                    thinking_content += delta.reasoning_content
                    with thinking_placeholder.expander("💭 思考中", expanded=False):
                        st.markdown(thinking_content)

                # 处理实际回答内容（只有非 None 才拼接）
                if hasattr(delta, "content") and delta.content is not None:
                    full_response += delta.content
                    message_placeholder.markdown(full_response + "▌")

        # 🆕 新增：处理工具调用
        if enable_tools and is_tool_call and tool_calls_info:
            # 如果有工具调用，需要重新构建请求

            # 将 AI 的响应（包含工具调用）添加到消息历史
            # 注意：在流式模式下，我们需要模拟 assistant 消息
            # 但对于工具调用，我们使用非流式模式更简单

            # 切换到非流式模式重新请求
            # 但为了更好的用户体验，我们展示"正在调用工具..."状态
            with thinking_placeholder.expander("🔧 正在调用工具", expanded=False):
                st.write("📋 检测到需要调用工具...")

                # 构建工具调用消息
                tool_messages = messages.copy()

                # 这里我们重新用非流式模式调用，以便正确处理工具调用
                # 但由于 DeepSeek 流式和非流式的工具调用处理不同
                # 我们使用更可靠的方式：重新发送非流式请求

                # 如果有思考内容，保留它
                if thinking_content:
                    tool_messages.append(
                        {"role": "assistant", "content": thinking_content}
                    )

                # 重新调用（非流式，支持工具调用）
                tool_response = client.chat.completions.create(
                    model="deepseek-v4-pro",
                    messages=tool_messages,
                    tools=tools_schema,
                    tool_choice="auto",
                    stream=False,
                    reasoning_effort="high",
                    extra_body={"thinking": {"type": "enabled"}},
                )

                tool_response_message = tool_response.choices[0].message

                if tool_response_message.tool_calls:
                    # 执行工具调用
                    tool_results = handle_tool_calls(tool_response_message.tool_calls)

                    # 显示工具执行结果
                    for result in tool_results:
                        st.write(f"✅ 工具执行结果: {result['content']}")

                    # 构建包含工具结果的完整消息列表
                    final_messages = messages.copy()
                    final_messages.append(tool_response_message)

                    for result in tool_results:
                        final_messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": result["tool_call_id"],
                                "content": result["content"],
                            }
                        )

                    # 获取最终回答
                    final_response = client.chat.completions.create(
                        model="deepseek-v4-pro",
                        messages=final_messages,
                        stream=False,
                        reasoning_effort="high",
                        extra_body={"thinking": {"type": "enabled"}},
                    )

                    final_content = final_response.choices[0].message.content

                    # 显示最终回答
                    message_placeholder.markdown(final_content)
                    full_response = final_content

                    # 保存到会话历史
                    st.session_state.messages.append(
                        {"role": "assistant", "content": full_response}
                    )

                else:
                    # 如果没有工具调用，使用原有的回答
                    if tool_response_message.content:
                        message_placeholder.markdown(tool_response_message.content)
                        full_response = tool_response_message.content
                        st.session_state.messages.append(
                            {"role": "assistant", "content": full_response}
                        )

            # 保存会话
            save_session()

        else:
            # 🆕 新增结束：没有工具调用，使用原有逻辑
            # 最终显示（去掉光标）
            if full_response:
                message_placeholder.markdown(full_response)
                # 保存完整的回答到会话状态
                st.session_state.messages.append(
                    {"role": "assistant", "content": full_response}
                )
                save_session()  # 保存当前会话
            else:
                # 如果 full_response 为空，说明可能只有思考内容
                if thinking_content:
                    message_placeholder.markdown(thinking_content)
                    st.session_state.messages.append(
                        {"role": "assistant", "content": thinking_content}
                    )
                    save_session()
        # ========== 🔄 修改结束 ==========

    except openai.AuthenticationError:
        st.error("API Key无效，请检查环境变量APP_DEEPSEEK_API_KEY是否正确设置。")
    except openai.error.OpenAIError as e:
        st.error(f"💥 API服务异常: {str(e)}")
    except Exception as e:
        st.error(f"发生错误: {str(e)}")
        print(f"详情: {e}")
