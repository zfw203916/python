import streamlit as st

st.set_page_config(page_title="测试", page_icon="🧪", layout="wide")

st.title("✅ Streamlit 运行正常！")
st.write("如果你能看到这个，说明 Streamlit 本身没问题。")

# 测试 session_state
if "test" not in st.session_state:
    st.session_state.test = 0

if st.button("点击测试"):
    st.session_state.test += 1
    st.write(f"点击次数：{st.session_state.test}")
