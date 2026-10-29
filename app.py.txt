import streamlit as st
import pandas as pd
import datetime
import os
import plotly.express as px

EXCEL_FILE = "IQC.xlsx"

# 頁面基本配置
st.set_page_config(page_title="IQC 品保進料檢驗系統", page_icon="🛡️", layout="wide")

# 讀取 Excel 分頁的防錯函數
@st.cache_data(ttl=2)
def load_sheet(sheet_name):
    if os.path.exists(EXCEL_FILE):
        try:
            xls = pd.ExcelFile(EXCEL_FILE)
            if sheet_name in xls.sheet_names:
                return pd.read_excel(EXCEL_FILE, sheet_name=sheet_name)
        except Exception as e:
            st.error(f"讀取 {sheet_name} 分頁失敗: {e}")
    return pd.DataFrame()

# 標題欄
st.title("🛡️ IQC 品保數位化進料檢驗系統")

# 左側功能選單
menu = st.sidebar.radio("系統功能選單", ["📝 1. 新增進料檢驗", "🔍 2. 歷史紀錄查詢", "📊 3. 品質分析看板"])

# 載入料件主檔
df_items = load_sheet("料件主檔")

if menu == "📝 1. 新增進料檢驗":
    st.subheader("📋 填寫檢驗單")
    
    col1, col2 = st.columns(2)
    
    with col1:
        date_input = st.date_input("檢驗日期", datetime.date.today())
        
        # 取得主檔料號清單
        part_list = df_items["料號"].astype(str).tolist() if not df_items.empty and "料號" in df_items.columns else []
        selected_part = st.selectbox("選擇料號", part_list if part_list else ["無主檔資料"])
        
        # 自動對應主檔資料
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
        
        # 計算良率
        yield_rate = (inspect_qty - defect_qty) / inspect_qty if inspect_qty > 0 else 1.0
        st.metric("當前批次良率", f"{yield_rate * 100:.1f}%")
        
        auto_status = "Pass" if defect_qty == 0 else "Fail"
        status = st.selectbox("總判定", ["Pass", "Fail"], index=0 if auto_status == "Pass" else 1)

    st.markdown("---")
    st.subheader(f"⚙️ 特殊類別項目檢驗：【{category}】")
    
    # 根據屬性呈現對應檢驗項目
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
    notes = st.text_area("不良原因 / 備註敘述", value="")

    if st.button("💾 儲存送出檢驗紀錄", type="primary"):
        st.success(f"已成功錄入料號【{selected_part}】之檢驗紀錄！")

elif menu == "🔍 2. 歷史紀錄查詢":
    st.subheader("🔍 歷史進料檢驗資料庫")
    df_records = load_sheet("檢驗紀錄")
    
    if not df_records.empty:
        search_keyword = st.text_input("🔎 搜尋料號 / 供應商 / 品名", "")
        if search_keyword:
            df_filtered = df_records[df_records.astype(str).apply(lambda x: x.str.contains(search_keyword, case=False)).any(axis=1)]
            st.dataframe(df_filtered, use_container_state=True)
        else:
            st.dataframe(df_records, use_container_state=True)
    else:
        st.info("目前尚無歷史檢驗紀錄。")

elif menu == "📊 3. 品質分析看板":
    st.subheader("📊 供應商與品質分析儀表板")
    df_records = load_sheet("檢驗紀錄")
    
    if not df_records.empty and "供應商" in df_records.columns:
        col_chart1, col_chart2 = st.columns(2)
        
        with col_chart1:
            fig1 = px.histogram(df_records, x="供應商", color="Pass/Fail", barmode="group", title="各供應商進料批次 Pass/Fail 統計")
            st.plotly_chart(fig1, use_container_state=True)
            
        with col_chart2:
            if "料件屬性" in df_records.columns:
                fig2 = px.pie(df_records, names="料件屬性", title="檢驗料件屬性佔比")
                st.plotly_chart(fig2, use_container_state=True)
    else:
        st.info("尚無足夠數據繪製品質分析圖表。")
