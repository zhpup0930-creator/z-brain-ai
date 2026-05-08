import streamlit as st
import google.generativeai as genai
import pandas as pd
from datetime import datetime
import os
import streamlit.components.v1 as components

# 1. 网页配置
st.set_page_config(page_title="我的 AI 知识收割机", layout="wide")

# --- 注入防关闭代码 (JavaScript) ---
# 当你尝试关闭或刷新网页时，浏览器会弹出提示
components.html(
    """
    <script>
    window.parent.onbeforeunload = function() {
        return "数据尚未备份，确定离开吗？请确保已点击左侧【下载备份】按钮！";
    };
    </script>
    """,
    height=0,
)

DB_FILE = "knowledge_base.csv"

# --- 侧边栏：配置与数据安全中心 ---
with st.sidebar:
    st.title("🧠 知识收割机")
    api_key = st.text_input("🔑 输入 API Key:", type="password")
    
    st.divider()
    st.error("⚠️ **重要提醒**")
    st.write("本网页为云端临时环境，关闭前**必须**点击下方备份，否则今日数据会丢失！")
    
    # 下载数据库功能 (做成醒目的按钮)
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'rb') as f:
            st.download_button(
                label="🚨 点击下载备份 (存入 Google Drive)",
                data=f,
                file_name=f"knowledge_backup_{datetime.now().strftime('%m%d_%H%M')}.csv",
                mime="text/csv",
                help="关闭网页前点这个！"
            )

    st.divider()
    st.subheader("📂 恢复历史数据")
    uploaded_db = st.file_uploader("上传备份的 CSV 文件", type="csv")
    if uploaded_db is not None:
        try:
            df_upload = pd.read_csv(uploaded_db)
            if "分类" in df_upload.columns:
                df_upload.to_csv(DB_FILE, index=False)
                st.success("✅ 数据已恢复！")
            else:
                st.error("格式不匹配")
        except:
            st.error("恢复失败")

# --- 数据库初始化逻辑 ---
def init_db():
    needs_reset = False
    if not os.path.exists(DB_FILE):
        needs_reset = True
    else:
        try:
            temp_df = pd.read_csv(DB_FILE)
            if "分类" not in temp_df.columns: needs_reset = True
        except: needs_reset = True
    if needs_reset:
        pd.DataFrame(columns=["时间", "分类", "标题", "精华内容", "原始信息"]).to_csv(DB_FILE, index=False)

init_db()

def save_to_db(category, title, summary, original):
    df = pd.read_csv(DB_FILE)
    new_data = {"时间": datetime.now().strftime("%Y-%m-%d %H:%M"), "分类": category, "标题": title, "精华内容": summary, "原始信息": original}
    pd.concat([df, pd.DataFrame([new_data])], ignore_index=True).to_csv(DB_FILE, index=False)

# --- AI 处理逻辑 ---
def process_content(text, key):
    genai.configure(api_key=key)
    available_models = [m.name.replace('models/', '') for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    model = genai.GenerativeModel("gemini-1.5-flash" if "gemini-1.5-flash" in available_models else available_models[0])
    prompt = f"你是一个知识提纯专家。请分析：'{text}'。要求：1.从【💰 财富理财】、【🏋️ 运动科学】、【🧠 认知觉醒】、【📥 杂项收件箱】中选分类。2.起个简短标题。3.提炼3点实操干货。以简体中文返回：分类：\n标题：\n精华："
    return model.generate_content(prompt).text

# --- 主界面 ---
st.title("🚀 碎片知识自动收割系统")

if api_key:
    input_text = st.text_area("在此粘贴碎片信息：", height=150)
    
    if st.button("✨ 一键自动分类存储"):
        if input_text:
            with st.spinner("AI 正在解析..."):
                try:
                    raw_res = process_content(input_text, api_key)
                    lines = raw_res.strip().split('\n')
                    cat, title, summary = "📥 杂项收件箱", "未命名", raw_res
                    for line in lines:
                        if line.startswith("分类："): cat = line.replace("分类：", "").strip()
                        elif line.startswith("标题："): title = line.replace("标题：", "").strip()
                        elif line.startswith("精华："): summary = raw_res.split("精华：")[-1].strip()
                    
                    save_to_db(cat, title, summary, input_text)
                    st.success(f"已存入：{cat}")
                    # 【新增提醒】每次存完，弹出一个显眼的警告提醒备份
                    st.warning("💪 存储成功！但请记住：今日工作结束后，务必点击左侧【🚨 点击下载备份】！")
                except Exception as e:
                    st.error(f"处理失败：{e}")
    
    st.divider()
    df_all = pd.read_csv(DB_FILE)
    if len(df_all) > 0:
        tabs = st.tabs(["💰 财富", "🏋️ 运动", "🧠 认知", "📥 全部数据"])
        with tabs[0]: st.table(df_all[df_all['分类'].str.contains("财富")][["时间", "标题", "精华内容"]])
        with tabs[1]: st.table(df_all[df_all['分类'].str.contains("运动")][["时间", "标题", "精华内容"]])
        with tabs[2]: st.table(df_all[df_all['分类'].str.contains("认知")][["时间", "标题", "精华内容"]])
        with tabs[3]: st.dataframe(df_all, use_container_width=True)
else:
    st.warning("👈 请在左侧输入 API Key 启动系统")
