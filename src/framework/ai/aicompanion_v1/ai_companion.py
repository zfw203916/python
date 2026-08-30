# streamlit run src/framework/ai/aicompanion/ai_companion.py

from dotenv import load_dotenv
from openai import OpenAI
from datetime import datetime
import openai
import os
import json
import streamlit as st

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

    # with open(f"sessions/{filename}", "r", encoding="utf-8") as f:
    #     session_data = json.load(f)
    #     session_list.append(session_data)


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
deepseek_model = os.environ.get("APP_DEEPSEEK_MODEL")
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

# 显示历史消息
for message in st.session_state.messages:
    st.chat_message(message["role"]).markdown(message["content"])

    # 会话标识
    if "current_session" not in st.session_state:
        st.session_state.current_session = generate_session_name()

# ========== 侧边栏 ==========
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
    #
    try:
        response = client.chat.completions.create(
            model= deepseek_model,
            messages=[
                {"role": "system", "content": st.session_state.system_str},
                *st.session_state.messages,
            ],
            stream=True,
            # reasoning_effort="high",
            # extra_body={"thinking": {"type": "enabled"}}
        )

        # 非流式输出处理。
        # ai_response=response.choices[0].message.content
        # st.chat_message("assistant").markdown(ai_response)
        # st.session_state.messages.append({"role": "assistant", "content": ai_response})

        # 流式输出处理。
        response_message = st.chat_message("assistant")  # 创建一个新的聊天消息组件
        thinking_placeholder = (
            response_message.empty()
        )  # 创建一个空的占位符组件，用于显示思考内容
        message_placeholder = (
            response_message.empty()
        )  # 创建一个空的占位符组件，用于显示思考内容
        full_response = ""
        thinking_content = ""
        for chunk in response:
            if chunk.choices and chunk.choices[0].delta is not None:
                delta = chunk.choices[0].delta

                # 处理思考内容（如果有）
                if hasattr(delta, "reasoning_content") and delta.reasoning_content:
                    # 可选：显示思考过程
                    thinking_content += delta.reasoning_content
                    with thinking_placeholder.expander("💭 思考中", expanded=False):
                        st.markdown(thinking_content)

                # 处理实际回答内容（只有非 None 才拼接）
                if hasattr(delta, "content") and delta.content is not None:
                    full_response += delta.content
                    # 使用markdown显示，支持更好的格式化
                    message_placeholder.markdown(full_response + "▌")
        # 最终显示（去掉光标）
        message_placeholder.markdown(full_response)
        # 保存完整的回答到会话状态
        st.session_state.messages.append(
            {"role": "assistant", "content": full_response}
        )
        save_session()  # 保存当前会话

    except openai.AuthenticationError:
        st.error("API Key无效，请检查环境变量APP_DEEPSEEK_API_KEY是否正确设置。")
    # except openai.error.OpenAIError as e:
    except openai.APIError as e:
        st.error(f"💥 API服务异常: {str(e)}")
    except Exception as e:
        st.error(f"发生错误: {str(e)}")
        print(f"详情: {e}")
