import streamlit as st
import pandas as pd
import datetime
import os
import json
import requests
import plotly.express as px

EXCEL_FILE = "IQC.xlsx"

# Apps Script Web App 專屬網址
APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxhm_5oR08CgCMveu_BVN1mT2g_L_CUg9wFXFIAFCwBT4AovMOaeZS1GoJD1tXQpQ6B/exec"

st.set_page_config(page_title="IQC 品保進料檢驗系統", page_icon="🛡️", layout="wide")

# 優先從 Google 試算表實時讀取資料 (快取時間設定 3 秒以確保數據即時性)
@st.cache_data(ttl=3)
def load_sheet(sheet_name):
    try:
        payload = {"action": "get_data", "sheet_name": sheet_name}
        res = requests.get(APPS_SCRIPT_URL, params={"data": json.dumps(payload)}, timeout=10)
        res_json = res.json()
        if res_json.get("status") == "success":
            raw_data = res_json.get("data", [])
            if len(raw_data) > 1:
                headers = raw_data[0]
                rows = raw_data[1:]
                df = pd.DataFrame(rows, columns=headers)
                return df
            elif len(raw_data) == 1:
                return pd.DataFrame(columns=raw_data[0])
    except Exception:
        pass

    # 備援：若 API 連線失敗時，讀取本地 IQC.xlsx
    if os.path.exists(EXCEL_FILE):
        try:
            xls = pd.ExcelFile(EXCEL_FILE)
            if sheet_name in xls.sheet_names:
                return pd.read_excel(EXCEL_FILE, sheet_name=sheet_name)
        except Exception as e:
            st.error(f"讀取 {sheet_name} 分頁失敗: {e}")
    return pd.DataFrame()

# 主標題
st.title("🛡️ IQC 品保數位化進料檢驗系統")

# 左側功能選單
menu = st.sidebar.radio("系統功能選單", [
    "📝 1. 新增進料檢驗", 
    "➕ 2. 新增料件主檔",
    "🔍 3. 歷史紀錄查詢", 
    "📊 4. 品質分析看板"
])

# 載入實時料件主檔
df_items = load_sheet("料件主檔")

# 1. 新增進料檢驗
if menu == "📝 1. 新增進料檢驗":
    st.subheader("📋 填寫檢驗單")
    col1, col2 = st.columns(2)
    
    with col1:
        date_input = st.date_input("檢驗日期", datetime.date.today())
        part_list = df_items["料號"].astype(str).tolist() if not df_items.empty and "料號" in df_items.columns else []
        selected_part = st.selectbox("選擇料號", part_list if part_list else ["無主檔資料"])
        
        if not df_items.empty and "料號" in df_items.columns:
            item_info = df_items[df_items["料號"].astype(str) == selected_part]
            if not item_info.empty:
                part_name = str(item_info.iloc[0].get("
