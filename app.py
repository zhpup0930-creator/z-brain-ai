import streamlit as st
import google.generativeai as genai
import pandas as pd
from datetime import datetime
import os
import streamlit.components.v1 as components

# 1. 网页配置
st.set_page_config(page_title="我的 AI 知识收割机", layout="wide")

components.html(
    """<script>window.parent.onbeforeunload = function() { return "数据尚未备份，确定离开吗？"; };</script>""",
    height=0,
)

DB_FILE = "knowledge_base.csv"

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

with st.sidebar:
    st.title("🧠 知识收割机")
    api_key = st.text_input("🔑 输入 API Key:", type="password")
    
    st.divider()
    st.error("⚠️ **今日备份提醒**")
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "rb") as file:
                st.download_button(label="🚨 点击下载备份 (存入 G盘)", data=file, file_name=f"我的知识库备份_{datetime.now().strftime('%m%d_%H%M')}.csv", mime="text/csv")
        except: pass

    st.divider()
    st.subheader("📂 恢复历史数据")
    uploaded_db = st.file_uploader("上传备份的 CSV", type="csv")
    if uploaded_db is not None:
        try:
            df_upload = pd.read_csv(uploaded_db)
            if "分类" in df_upload.columns:
                df_upload.to_csv(DB_FILE, index=False)
                st.success("✅ 数据已恢复！")
                st.rerun()
        except: st.error("恢复失败")

def save_to_db(category, title, summary, original):
    df = pd.read_csv(DB_FILE)
    new_data = {"时间": datetime.now().strftime("%Y-%m-%d %H:%M"), "分类": category, "标题": title, "精华内容": summary, "原始信息": original}
    pd.concat([df, pd.DataFrame([new_data])], ignore_index=True).to_csv(DB_FILE, index=False)

# --- 终极核心逻辑：直接锁定 2.0-flash-lite 高额度轻量模型 ---
def process_content(text, key):
    genai.configure(api_key=key)
    
    # 根据你截图的真实名单，直接绑定这个最高效的模型
    model = genai.GenerativeModel("gemini-2.0-flash-lite")
    
    prompt = f"""
    你是一个知识架构专家。请对以下内容进行深度提纯：
    "{text}"
    
    任务：
    1. 分类：选一个：【💰 财富理财】、【📈 商业思维】、【🏋️ 运动健身】、【🥗 饮食营养】、【🎭 心理人性】、【💬 社交情商】、【🚀 自我成长】、【📥 杂项收件箱】。
    2. 标题：简短本质。
    3. 精华：有几点干货写几点，直接启发思考。
    
    格式使用简体中文：\n分类：\n标题：\n精华：
    """
    return model.generate_content(prompt).text

# --- 主界面 ---
st.title("🚀 碎片知识全自动收割系统")

if api_key:
    input_text = st.text_area("在此粘贴抖音文案：", height=150)
    
    if st.button("✨ 一键自动分类存储"):
        if input_text:
            with st.spinner("AI 正在光速解析..."):
                try:
                    raw_res = process_content(input_text, api_key)
                    lines = raw_res.strip().split('\n')
                    cat, title, summary = "📥 杂项收件箱", "未命名", raw_res
                    for line in lines:
                        if "分类：" in line: cat = line.split("：")[-1].strip()
                        elif "标题：" in line: title = line.split("：")[-1].strip()
                        elif "精华：" in line: summary = raw_res.split("精华：")[-1].strip()
                    
                    save_to_db(cat, title, summary, input_text)
                    st.success(f"✅ 已存入：{cat}")
                    st.rerun()
                except Exception as e:
                    # 如果这都能错，只会是网络问题或者真的一天点了几千次
                    st.error(f"🚨 运行失败：{e}")
        else:
            st.warning("请先输入内容")
    
    st.divider()
    try:
        df_all = pd.read_csv(DB_FILE)
        if len(df_all) > 0:
            tabs = st.tabs(["💰 财富", "📈 商业", "🏋️ 健身", "🥗 营养", "🎭 人性", "💬 社交", "🚀 成长", "📥 全部"])
            cats_list = ["财富", "商业", "健身", "营养", "人性", "社交", "成长"]
            for i in range(7):
                with tabs[i]:
                    filtered_df = df_all[df_all['分类'].str.contains(cats_list[i], na=False)]
                    st.table(filtered_df[["时间", "标题", "精华内容"]])
            with tabs[7]: st.dataframe(df_all, use_container_width=True)
    except: pass
else:
    st.warning("👈 请在左侧输入 API Key 启动系统")
