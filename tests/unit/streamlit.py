import streamlit as st


st.set_page_config(
    page_title="Ex-stream-ly Cool App",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": "https://www.extremelycoolapp.com/help",
        "Report a bug": "https://www.extremelycoolapp.com/bug",
        "About": "# This is a header. This is an *extremely* cool app!",
    },
)

st.title("一级标题")
st.text("这是一段文字")
st.markdown("这是一段文字")
st.write(
    "如果都能正常工作,就说明安装完全没问题了。小提示： 如果你在 zsh 中想避免打错字,可以输入前几个字母后按 Tab 键自动补全："
)
st.code("print('Hello, World!')")
st.latex(r"\int_a^b f(x) dx")

# confusion_matrix = pd.DataFrame(
#     {
#         "Predicted Cat" :[1,2],
#         "Predicted Dog" :[6,7],
#     },
#     index=["Actual Cat", "Actual Dog"]
# )
student_data = {
    "姓名": ["王林", "李慕婉", "贝罗", "莫厉海", "石萧"],
    "学号": ["20260001", "20260002", "20260003", "20260004", "20260005"],
    "语文": ["98", "90", "59", "29", "80"],
    "数学": ["88", "78", "65", "70", "39"],
    "英语": ["99", "89", "87", "59", "62"],
    "总分": ["285", "257", "211", "158", "181"],
}
st.table(student_data)

title = st.text_input("请输入标题")
st.write(f"您输入的是：{title}")
