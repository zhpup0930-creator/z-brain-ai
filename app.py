import streamlit as st
import google.generativeai as genai
import pandas as pd
from datetime import datetime
import os
import streamlit.components.v1 as components

# 1. 网页配置
st.set_page_config(page_title="我的 AI 知识收割机", layout="wide")

# --- 注入防关闭代码 ---
components.html(
    """
    <script>
    window.parent.onbeforeunload = function() {
        return "数据尚未备份，确定离开吗？";
    };
    </script>
    """,
    height=0,
)

DB_FILE = "knowledge_base.csv"

# --- 数据库初始化逻辑 ---
def init_db():
    if not os.path.exists(DB_FILE):
        pd.DataFrame(columns=["时间", "分类", "标题", "精华内容", "原始信息"]).to_csv(DB_FILE, index=False)
    else:
        try:
            df = pd.read_csv(DB_FILE)
            if "分类" not in df.columns:
                pd.DataFrame(columns=["时间", "分类", "标题", "精华内容", "原始信息"]).to_csv(DB_FILE, index=False)
        except:
             pd.DataFrame(columns=["时间", "分类", "标题", "精华内容", "原始信息"]).to_csv(DB_FILE, index=False)

init_db()

# --- 侧边栏配置 ---
with st.sidebar:
    st.title("🧠 知识收割机")
    api_key = st.text_input("🔑 输入 API Key:", type="password")
    
    st.divider()
    st.error("⚠️ **今日备份提醒**")
    
    # 【修复重点】：实时读取文件内容，确保下载按钮永远有效
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "rb") as file:
                btn = st.download_button(
                    label="🚨 点击下载备份 (存入 Google Drive)",
                    data=file,
                    file_name=f"我的知识库备份_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv"
                )
        except Exception as e:
            st.error(f"准备下载文件时出错: {e}")

    st.divider()
    st.subheader("📂 恢复数据")
    uploaded_db = st.file_uploader("上传备份的 CSV", type="csv")
    if uploaded_db is not None:
        try:
            df_upload = pd.read_
