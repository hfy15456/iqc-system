import streamlit as st
import pandas as pd
import datetime
import os
import requests
import plotly.express as px

EXCEL_FILE = "IQC.xlsx"

https://script.google.com/macros/s/AKfycbz-cLEOSo5ph4_SA9CN-o34ejiIemoLFEExyMb6xaeE61ukNgcekEhnyjrlKkZTaOfZ/exec
APPS_SCRIPT_URL = "https://script.google.com/macros/s/你的API專屬ID/exec"

st.set_page_config(page_title="IQC 品保進料檢驗系統", page_icon="🛡️", layout="wide")

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

st.title("🛡️ IQC 品保數位化進料檢驗系統")

menu = st.sidebar.radio("系統功能選單", [
    "📝 1. 新增進料檢驗", 
    "➕ 2. 新增料件主檔",
    "🔍 3. 歷史紀錄查詢", 
    "📊 4. 品質分析看板"
])

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
    
    inspector = st.text_input("檢驗人員簽名", value="Eddie")
    notes = st.text_area("不良原因 / 備註敘述", value="")

    if st.button("💾 儲存送出檢驗紀錄", type="primary"):
        payload = {
            "action": "add_inspection",
            "date": str(date_input),
            "part_name": part_name,
            "part_no": selected_part,
            "supplier": supplier,
            "category": category,
            "link_text": f"👉 前往{category}表",
            "total_qty": total_qty,
            "inspect_qty": inspect_qty,
            "defect_qty": defect_qty,
            "status": status,
            "yield_rate": yield_rate,
            "inspector": inspector,
            "notes": notes
        }
        
        try:
            res = requests.post(APPS_SCRIPT_URL, json=payload, timeout=10)
            if res.status_code == 200 and res.json().get("status") == "success":
                st.success(f"已成功同步寫入 Google 試算表！料號：【{selected_part}】")
                st.cache_data.clear()
            else:
                st.error(f"寫入失敗：{res.text}")
        except Exception as e:
            st.error(f"連線異常：{e}")

# 2. 新增料件主檔
elif menu == "➕ 2. 新增料件主檔":
    st.subheader("➕ 建立新料件主檔資料")
    new_part_no = st.text_input("新料號 (Part Number)", "")
    new_part_name = st.text_input("品名規格 (Description)", "")
    new_supplier = st.selectbox("供應商", ["定晨", "Patrick", "晨樺", "全葳", "其他"])
    new_category = st.selectbox("料件屬性", ["PCBA", "PCB", "二手來料", "料件維修", "治具", "一般料件"])
    
    if st.button("💾 新增至料件主檔", type="primary"):
        if new_part_no and new_part_name:
            payload = {
                "action": "add_item",
                "part_no": new_part_no,
                "part_name": new_part_name,
                "supplier": new_supplier,
                "category": new_category
            }
            try:
                res = requests.post(APPS_SCRIPT_URL, json=payload, timeout=10)
                if res.status_code == 200 and res.json().get("status") == "success":
                    st.success(f"料號【{new_part_no}】已成功新增至雲端主檔！")
                    st.cache_data.clear()
                else:
                    st.error(f"新增失敗：{res.text}")
            except Exception as e:
                st.error(f"連線異常：{e}")
        else:
            st.warning("請填寫完整的料號與品名！")

# 3. 歷史紀錄查詢
elif menu == "🔍 3. 歷史紀錄查詢":
    st.subheader("🔍 歷史進料檢驗資料庫與種類明細")
    search_keyword = st.text_input("🔎 跨表搜尋 (輸入料號 / 供應商 / 品名 / 檢驗人員)", "")

    tabs = st.tabs([
        "📋 檢驗紀錄 (總表)", "🟢 PCB 檢驗", "🔵 PCBA 檢驗", 
        "🟠 二手來料檢驗", "🟣 料件維修檢驗", "🟡 治具量測", "⚪ 一般料件檢驗"
    ])
    
    sheet_mapping = [
        ("檢驗紀錄", tabs[0]), ("PCB檢驗", tabs[1]), ("PCBA檢驗", tabs[2]),
        ("二手來料檢驗", tabs[3]), ("料件維修檢驗", tabs[4]), ("治具量測", tabs[5]), ("一般料件檢驗", tabs[6])
    ]
    
    for sheet_name, tab in sheet_mapping:
        with tab:
            df = load_sheet(sheet_name)
            if not df.empty:
                if search_keyword:
                    df_filtered = df[df.astype(str).apply(lambda x: x.str.contains(search_keyword, case=False)).any(axis=1)]
                    st.dataframe(df_filtered, use_container_width=True)
                else:
                    st.dataframe(df, use_container_width=True)
            else:
                st.info(f"【{sheet_name}】目前無紀錄或分頁為空。")

# 4. 品質分析看板
elif menu == "📊 4. 品質分析看板":
    st.subheader("📊 供應商與品質分析儀表板")
    df_records = load_sheet("檢驗紀錄")
    if not df_records.empty and "供應商" in df_records.columns:
        col_chart1, col_chart2 = st.columns(2)
        with col_chart1:
            fig1 = px.histogram(df_records, x="供應商", color="Pass/Fail", barmode="group", title="各供應商進料批次 Pass/Fail 統計")
            st.plotly_chart(fig1, use_container_width=True)
        with col_chart2:
            if "料件屬性" in df_records.columns:
                fig2 = px.pie(df_records, names="料件屬性", title="檢驗料件屬性佔比")
                st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("尚無足夠數據繪製品質分析圖表。")
