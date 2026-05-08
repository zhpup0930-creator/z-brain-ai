import streamlit as st
import google.generativeai as genai
import pandas as pd
from datetime import datetime
import os

# 1. 网页配置
st.set_page_config(page_title="我的 AI 知识收割机", layout="wide")

DB_FILE = "knowledge_base.csv"

# --- 侧边栏：配置与数据安全中心 ---
with st.sidebar:
    st.title("🧠 知识收割机")
    api_key = st.text_input("🔑 输入 Gemini API Key:", type="password")
    
    st.divider()
    st.subheader("💾 数据安全中心")
    
    # 恢复数据库功能
    uploaded_db = st.file_uploader("📂 1. 恢复数据库 (上传备份 CSV)", type="csv")
    if uploaded_db is not None:
        try:
            df_upload = pd.read_csv(uploaded_db)
            if "分类" in df_upload.columns:
                df_upload.to_csv(DB_FILE, index=False)
                st.success("✅ 数据库已成功恢复！")
            else:
                st.error("文件格式错误，请确保是简体中文版本的备份文件。")
        except:
            st.error("读取失败，请检查文件格式。")

    # 下载数据库功能
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'rb') as f:
            st.download_button("📥 2. 备份当前数据库", f, file_name=f"knowledge_backup_{datetime.now().strftime('%m%d')}.csv")

# --- 数据库初始化与防报错机制 ---
def init_db():
    # 如果文件不存在，或者文件存在但是旧的繁体版（没有'分类'这个词），就重新建一个
    needs_reset = False
    if not os.path.exists(DB_FILE):
        needs_reset = True
    else:
        try:
            temp_df = pd.read_csv(DB_FILE)
            if "分类" not in temp_df.columns:
                needs_reset = True
        except:
            needs_reset = True
            
    if needs_reset:
        df = pd.DataFrame(columns=["时间", "分类", "标题", "精华内容", "原始信息"])
        df.to_csv(DB_FILE, index=False)

init_db() # 运行初始化检查

def save_to_db(category, title, summary, original):
    df = pd.read_csv(DB_FILE)
    new_data = {
        "时间": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "分类": category,
        "标题": title,
        "精华内容": summary,
        "原始信息": original
    }
    df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
    df.to_csv(DB_FILE, index=False)

# --- AI 处理逻辑 ---
def process_content(text, key):
    genai.configure(api_key=key)
    available_models = [m.name.replace('models/', '') for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    best_model = "gemini-1.5-flash" if "gemini-1.5-flash" in available_models else available_models[0]
    model = genai.GenerativeModel(best_model)
    
    prompt = f"""
    你是一个知识架构专家。请分析以下内容：
    "{text}"
    
    任务：
    1. 从这四个标签中选一个最合适的：【💰 财富理财】、【🏋️ 运动科学】、【🧠 认知觉醒】、【📥 杂项收件箱】。
    2. 给这段知识起一个简短的标题。
    3. 提取核心干货（去掉废话，提炼成3点清晰的实操清单）。
    
    请严格按此格式使用简体中文返回，不要有其他废话：
    分类：[标签名称]
    标题：[标题名称]
    精华：[提纯后的内容]
    """
    return model.generate_content(prompt).text

# --- 主界面 ---
st.title("🚀 碎片知识自动收割系统")

if api_key:
    input_text = st.text_area("在此粘贴抖音文案或碎片信息：", height=150)
    
    if st.button("✨ 一键自动分类存储"):
        if input_text:
            with st.spinner("AI 正在解析并自动归类..."):
                try:
                    raw_res = process_content(input_text, api_key)
                    lines = raw_res.strip().split('\n')
                    cat, title, summary = "📥 杂项收件箱", "未命名", raw_res
                    
                    for line in lines:
                        if line.startswith("分类："): cat = line.replace("分类：", "").strip()
                        elif line.startswith("标题："): title = line.replace("标题：", "").strip()
                        elif line.startswith("精华："): summary = raw_res.split("精华：")[-1].strip()
                    
                    save_to_db(cat, title, summary, input_text)
                    st.success(f"已成功归类至：{cat}")
                except Exception as e:
                    st.error(f"处理失败，错误信息：{e}")
        else:
            st.warning("请先输入需要处理的内容。")

    st.divider()

    # 2. 展示区
    st.subheader("🗂️ 我的专属知识库")
    
    try:
        df_all = pd.read_csv(DB_FILE)
        if len(df_all) > 0:
            tabs = st.tabs(["💰 财富", "🏋️ 运动", "🧠 认知", "📥 全部数据"])
            
            with tabs[0]: st.table(df_all[df_all['分类'].str.contains("财富")][["时间", "标题", "精华内容"]])
            with tabs[1]: st.table(df_all[df_all['分类'].str.contains("运动")][["时间", "标题", "精华内容"]])
            with tabs[2]: st.table(df_all[df_all['分类'].str.contains("认知")][["时间", "标题", "精华内容"]])
            with tabs[3]: st.dataframe(df_all, use_container_width=True)
        else:
            st.info("知识库目前是空的。快去粘贴第一条知识吧！")
    except Exception as e:
         st.error(f"读取数据失败，请刷新网页重试。错误：{e}")
else:
    st.warning("👈 请在左侧输入 API Key 启动系统")
