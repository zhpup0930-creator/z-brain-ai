import streamlit as st
import google.generativeai as genai
import pandas as pd
from datetime import datetime
import os

# 1. 网页配置
st.set_page_config(page_title="我的 AI 知识收割机", layout="wide")

# --- 側邊欄配置 ---
with st.sidebar:
    st.title("🧠 知識收割機")
    api_key = st.text_input("輸入 Gemini API Key:", type="password")
    st.info("模式：自動識別 + 提純 + 存儲")

# --- 數據庫初始化 (CSV) ---
DB_FILE = "knowledge_base.csv"
if not os.path.exists(DB_FILE):
    df = pd.DataFrame(columns=["時間", "分類", "標題", "精華內容", "原始信息"])
    df.to_csv(DB_FILE, index=False)

def save_to_db(category, title, summary, original):
    df = pd.read_csv(DB_FILE)
    new_data = {
        "時間": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "分類": category,
        "標題": title,
        "精華內容": summary,
        "原始信息": original
    }
    df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
    df.to_csv(DB_FILE, index=False)

# --- AI 處理邏輯 (加入了防 404 報錯機制) ---
def process_content(text, key):
    genai.configure(api_key=key)
    
    # 自動尋找可用模型，解決 NotFound 報錯
    available_models = [m.name.replace('models/', '') for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    best_model = "gemini-1.5-flash" if "gemini-1.5-flash" in available_models else available_models[0]
    model = genai.GenerativeModel(best_model)
    
    prompt = f"""
    你是一個知識架構專家。請分析以下內容：
    "{text}"
    
    任務：
    1. 從這四個標籤中選一個最合適的：【💰 財富理財】、【🏋️ 運動科學】、【🧠 認知覺醒】、【📥 雜項收件箱】。
    2. 給這段知識起一個簡短的標題。
    3. 提取核心乾貨（去掉廢話，3點清單）。
    
    請嚴格按此格式返回，不要有其他廢話：
    分類：[標籤名稱]
    標題：[標題名稱]
    精華：[提純後的內容]
    """
    response = model.generate_content(prompt)
    return response.text

# --- 主界面 ---
st.title("🚀 碎片知識自動收割系統")

if api_key:
    # 1. 投餵區
    input_text = st.text_area("在此粘貼抖音文案或碎片信息：", height=200)
    
    if st.button("✨ 一鍵自動分類存儲"):
        if input_text:
            with st.spinner("AI 正在解析並自動歸類..."):
                try:
                    raw_res = process_content(input_text, api_key)
                    
                    # 解析 AI 返回的內容 (增強容錯處理)
                    lines = raw_res.strip().split('\n')
                    cat = "📥 雜項收件箱"
                    title = "未命名知識"
                    summary = raw_res
                    
                    for line in lines:
                        if line.startswith("分類："): cat = line.replace("分類：", "").strip()
                        elif line.startswith("標題："): title = line.replace("標題：", "").strip()
                        elif line.startswith("精華："): summary = raw_res.split("精華：")[-1].strip()
                    
                    # 存入 CSV
                    save_to_db(cat, title, summary, input_text)
                    st.success(f"已成功自動歸類至：{cat}")
                    st.balloons()
                except Exception as e:
                    st.error(f"處理失敗，錯誤信息：{e}")
        else:
            st.warning("請先輸入內容")

    st.divider()

    # 2. 展示區 (四個大面板)
    st.subheader("🗂️ 我的知識庫")
    df_all = pd.read_csv(DB_FILE)
    
    tabs = st.tabs(["💰 財富", "🏋️ 運動", "🧠 認知", "📥 全部"])
    
    with tabs[0]:
        st.table(df_all[df_all['分類'].str.contains("財富")][["時間", "標題", "精華內容"]])
    with tabs[1]:
        st.table(df_all[df_all['分類'].str.contains("運動")][["時間", "標題", "精華內容"]])
    with tabs[2]:
        st.table(df_all[df_all['分類'].str.contains("認知")][["時間", "標題", "精華內容"]])
    with tabs[3]:
        st.dataframe(df_all, use_container_width=True)
else:
    st.warning("👈 請在左側輸入 API Key 啟動系統
