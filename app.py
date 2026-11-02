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
                part_name = str(item_info.iloc[0].get("名稱", ""))
                supplier = str(item_info.iloc[0].get("供應商", ""))
                category = str(item_info.iloc[0].get("料件屬性", "一般料件"))
            else:
                part_name, supplier, category = "", "", "一般料件"
        else:
            part_name, supplier, category = "", "", "一般料件"
            
        st.text_input("品名規格 (自動帶出)", value=part_name, disabled=True)
        st.text_input("供應商 (自動帶出)", value=supplier, disabled=True)
        st.text_input("料件屬性 (自動帶出)", value=category, disabled=True)

    with col2:
        total_qty = st.number_input("進貨總數量", min_value=1, value=10)
        inspect_qty = st.number_input("抽檢數量", min_value=1, value=total_qty)
        defect_qty = st.number_input("異常數量", min_value=0, value=0)
        
        yield_rate = (inspect_qty - defect_qty) / inspect_qty if inspect_qty > 0 else 1.0
        st.metric("當前批次良率", f"{yield_rate * 100:.1f}%")
        
        auto_status = "Pass" if defect_qty == 0 else "Fail"
        status = st.selectbox("總判定", ["Pass", "Fail"], index=0 if auto_status == "Pass" else 1)

    st.markdown("---")
    st.subheader(f"⚙️ 特殊類別項目檢驗：【{category}】")
    
    if category == "二手來料":
        st.info("💡 提醒：請核對 SOP 標準進行電測（如 Diode 0.65-0.7V / 電阻 9.9-10.1Ω）")
        e_col1, e_col2 = st.columns(2)
        with e_col1:
            st.selectbox("外觀/結構檢驗", ["OK", "NG"])
            st.selectbox("電測/功能檢驗", ["OK", "NG", "N/A"])
        with e_col2:
            st.text_input("關鍵量測數據紀錄 (例如: D1=0.67V)", value="")
            st.text_input("檢驗手冊/SOP 連結", value=f"D:\\IQC_SOP\\{selected_part}.pdf")
            
    elif category == "PCB":
        p_col1, p_col2 = st.columns(2)
        with p_col1:
            st.selectbox("外觀與線路檢驗", ["OK", "NG"])
        with p_col2:
            st.selectbox("板材與翹曲度", ["OK", "NG"])
            
    elif category == "PCBA":
        pcba_col1, pcba_col2 = st.columns(2)
        with pcba_col1:
            st.selectbox("刮傷/汙點/斷線", ["OK", "NG"])
            st.selectbox("偏位/彎曲/翹曲", ["OK", "NG"])
        with pcba_col2:
            st.selectbox("焊點/元件位置", ["OK", "NG"])
            st.selectbox("送電測試", ["OK", "NG", "N/A"])

    elif category == "料件維修":
        m_col1, m_col2 = st.columns(2)
        with m_col1:
            st.selectbox("保壓測試", ["OK", "NG", "N/A"])
        with m_col2:
            st.selectbox("水迴路測試", ["OK", "NG", "N/A"])

    elif category == "治具":
        j_col1, j_col2 = st.columns(2)
        with j_col1:
            st.selectbox("是否符合製圖", ["OK", "NG"])
        with j_col2:
            st.selectbox("是否能安裝", ["OK", "NG"])
            
    inspector = st.text_input("檢驗人員簽名", value="Eddie")
    notes = st
