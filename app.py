import streamlit as st
import google.generativeai as genai
import pandas as pd
from datetime import datetime
import os

# 1. 网页配置
st.set_page_config(page_title="我的 AI 知识收割机", layout="wide")

DB_FILE = "knowledge_base.csv"

# --- 側邊欄：配置與數據安全中心 ---
with st.sidebar:
    st.title("🧠 知識收割機")
    api_key = st.text_input("🔑 輸入 Gemini API Key:", type="password")
    
    st.divider()
    st.subheader("💾 數據安全中心 (防丟失)")
    
    # 恢復數據庫功能
    uploaded_db = st.file_uploader("📂 1. 恢復數據庫 (上傳備份的 CSV)", type="csv")
    if uploaded_db is not None:
        try:
            df_upload = pd.read_csv(uploaded_db)
            df_upload.to_csv(DB_FILE, index=False)
            st.success("✅ 數據庫已成功恢復！")
        except:
            st.error("文件格式錯誤")

    # 下載數據庫功能
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'rb') as f:
            st.download_button("📥 2. 備份當前數據庫 (存入 Google Drive)", f, file_name=f"knowledge_backup_{datetime.now().strftime('%m%d')}.csv")
            
    st.caption("提示：為防止雲端重啟導致數據丟失，請在關閉網頁前點擊【備份】。下次使用時【上傳】恢復即可。")

# --- 數據庫初始化 ---
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

# --- AI 處理邏輯 ---
def process_content(text, key):
    genai.configure(api_key=key)
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
    return model.generate_content(prompt).text

# --- 主界面 ---
st.title("🚀 碎片知識自動收割系統")

if api_key:
    # 1. 投餵區
    input_text = st.text_area("在此粘貼抖音文案或碎片信息：", height=150)
    
    if st.button("✨ 一鍵自動分類存儲"):
        if input_text:
            with st.spinner("AI 正在解析並自動歸類..."):
                try:
                    raw_res = process_content(input_text, api_key)
                    lines = raw_res.strip().split('\n')
                    cat, title, summary = "📥 雜項收件箱", "未命名", raw_res
                    
                    for line in lines:
                        if line.startswith("分類："): cat = line.replace("分類：", "").strip()
                        elif line.startswith("標題："): title = line.replace("標題：", "").strip()
                        elif line.startswith("精華："): summary = raw_res.split("精華：")[-1].strip()
                    
                    save_to_db(cat, title, summary, input_text)
                    st.success(f"已成功歸類至：{cat}")
                except Exception as e:
                    st.error(f"處理失敗：{e}")
        else:
            st.warning("請先輸入內容")

    st.divider()

    # 2. 展示區
    st.subheader("🗂️ 我的專屬知識庫")
    df_all = pd.read_csv(DB_FILE)
    
    if len(df_all) > 0:
        tabs = st.tabs(["💰 財富", "🏋️ 運動", "🧠 認知", "📥 全部數據"])
        
        with tabs[0]: st.table(df_all[df_all['分類'].str.contains("財富")][["時間", "標題", "精華內容"]])
        with tabs[1]: st.table(df_all[df_all['分類'].str.contains("運動")][["時間", "標題", "精華內容"]])
        with tabs[2]: st.table(df_all[df_all['分類'].str.contains("認知")][["時間", "標題", "精華內容"]])
        with tabs[3]: st.dataframe(df_all, use_container_width=True)
    else:
        st.info("知識庫目前是空的。快去粘貼第一條知識吧！或者從左側上傳備份恢復。")
else:
    st.warning("👈 請在左側輸入 API Key 啟動系統")
