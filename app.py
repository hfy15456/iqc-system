import streamlit as st
import requests
import pandas as pd
from datetime import date

GAS_API_URL = "https://script.google.com/macros/s/AKfycbzeQ7G0xJ-c9D0ExQ_dmo4OqugJ9XauRKy8M6s2-Dti_ZCvzq9XhXzG2sweI3gJdybAmw/exec"

st.set_page_config(page_title="IQC 進料品質管理系統", layout="wide")

st.title("IQC 進料品質管理系統")
st.caption("連動雲端試算表：ItemMaster (主檔) 與 InspectionLogs (檢驗紀錄)")

def get_api_data(action):
    try:
        res = requests.get(f"{GAS_API_URL}?action={action}", timeout=30)
        if res.status_code == 200:
            data = res.json()
            if data.get("status") == "success":
                return data.get("data", [])
            else:
                st.error(f"後端錯誤: {data.get('message')}")
        else:
            st.error(f"HTTP 請求失敗: {res.status_code}")
    except Exception as e:
        st.error(f"API 連線異常: {e}")
    return []

def post_api_data(action, payload):
    try:
        res = requests.post(GAS_API_URL, json={"action": action, "data": payload}, timeout=30)
        if res.status_code == 200:
            return res.json()
        return {"status": "error", "message": f"HTTP {res.status_code}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

tab1, tab2, tab3, tab4 = st.tabs(["1. 新增料件主檔", "2. 新增進料檢驗", "3. 歷史紀錄查詢", "4. 品質分析看板"])

# 預設常見供應商選單
COMMON_SUPPLIERS = ["全葳", "辰樺", "Patrick", "滔寶", "手動輸入其他..."]

# ==========================================
# 頁面 1：新增料件主檔 (ItemMaster)
# ==========================================
with tab1:
    st.subheader("新增料件主檔 (ItemMaster)")
    with st.form("form_item_master", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            part_no = st.text_input("料號 *", placeholder="例：8705161-03-S")
            part_name = st.text_input("品名 *", placeholder="例：APEX PA")
        with col2:
            supplier_select = st.selectbox("供應商選單 *", COMMON_SUPPLIERS, index=0)
            custom_supplier = st.text_input("請輸入自訂供應商名稱", placeholder="選取『手動輸入其他...』時填寫")
            aql = st.selectbox("AQL 允收水準", ["0.65", "0.4", "1.0"], index=0)
            
        submitted_master = st.form_submit_button("儲存至 ItemMaster", use_container_width=True)
        if submitted_master:
            final_supplier = custom_supplier.strip() if supplier_select == "手動輸入其他..." else supplier_select
            
            if not part_no or not part_name or not final_supplier:
                st.warning("請完整填寫料號、品名與供應商！")
            else:
                with st.spinner("存檔中..."):
                    res = post_api_data("addItemMaster", {
                        "partNo": part_no.strip(),
                        "partName": part_name.strip(),
                        "supplier": final_supplier,
                        "aql": aql
                    })
                    if res.get("status") == "success":
                        st.success("✅ " + res.get("message"))
                    else:
                        st.error("❌ " + res.get("message"))

# ==========================================
# 頁面 2：新增進料檢驗 (按料號搜尋連動帶入)
# ==========================================
with tab2:
    st.subheader("新增進料檢驗單")
    
    # 彙整料件資料庫
    master_items = get_api_data("getItemMaster")
    history_items = get_api_data("getHistory")
    
    parts_db = {}
    
    for item in master_items:
        p_no = item.get("partNo", "").strip()
        if p_no:
            parts_db[p_no] = {
                "partNo": p_no,
                "partName": item.get("partName", ""),
                "supplier": item.get("supplier", "")
            }
            
    for item in history_items:
        p_no = item.get("partNo", "").strip()
        if p_no and p_no not in parts_db:
            parts_db[p_no] = {
                "partNo": p_no,
                "partName": item.get("partNameSpec", ""),
                "supplier": item.get("supplier", "")
            }

    st.markdown("##### 🔍 1. 搜尋料號 (輸入關鍵字過濾並自動帶入品名與供應商)")
    search_list = [""] + sorted(list(parts_db.keys()))
    
    selected_part_no = st.selectbox(
        "點擊輸入關鍵字搜尋料號：",
        options=search_list,
        index=0,
        format_func=lambda x: f"{x} ({parts_db[x]['partName']})" if x in parts_db else "-- 請輸入或選擇料號 --"
    )
    
    if selected_part_no in parts_db:
        info = parts_db[selected_part_no]
        init_part_no = info.get("partNo", "")
        init_part_name = info.get("partName", "")
        init_supplier = info.get("supplier", "")
    else:
        init_part_no = selected_part_no
        init_part_name = ""
        init_supplier = ""

    st.markdown("---")
    
    with st.form("form_add_inspection", clear_on_submit=True):
        st.markdown("##### 📌 2. 料件細項資訊 (根據選取料號自動填入)")
        col_a1, col_a2 = st.columns(2)
        with col_a1:
            part_no_input = st.text_input("料號 (C欄) *", value=init_part_no, placeholder="例：8705161-03-S")
            part_name_input = st.text_input("品名 (B欄) *", value=init_part_name, placeholder="例：APEX PA")
        with col_a2:
            supplier_input = st.text_input("供應商 (D欄) *", value=init_supplier, placeholder="例：Patrick / 全葳")
            item_attr = st.selectbox("料件屬性 (E欄)", ["二手來料", "PCB", "料件維修", "一般料件"], index=0)
            
        st.markdown("---")
        st.markdown("##### 📌 3. 填寫檢驗數據與結果")
        col_b1, col_b2 = st.columns(2)
        with col_b1:
            inspect_date = st.date_input("檢驗日期 (A欄) *", value=date.today())
            total_qty = st.number_input("數量 / 進貨數 (F欄) *", min_value=1, value=10, step=1)
            
        with col_b2:
            sample_qty = st.number_input("檢驗數量 (G欄) *", min_value=1, value=10, step=1)
            defect_qty = st.number_input("異常數量 (H欄) *", min_value=0, value=0, step=1)
            result = st.selectbox("Pass/Fail 判定 (I欄) *", ["Pass", "Fail"], index=0)

        defect_reason = st.text_area("不良原因描述 (K欄)", placeholder="若有異常請詳細描述不良現象...")

        submitted_insp = st.form_submit_button("寫入 InspectionLogs 試算表", use_container_width=True)
        if submitted_insp:
            if not part_no_input or not part_name_input:
                st.warning("請填寫料號與品名！")
            else:
                with st.spinner("資料寫入中..."):
                    res = post_api_data("addInspection", {
                        "inspectDate": str(inspect_date),
                        "partNo": part_no_input.strip(),
                        "partName": part_name_input.strip(),
                        "supplier": supplier_input.strip(),
                        "itemAttr": item_attr,
                        "totalQty": total_qty,
                        "sampleQty": sample_qty,
                        "defectQty": defect_qty,
                        "result": result,
                        "defectReason": defect_reason.strip()
                    })
                    if res.get("status") == "success":
                        st.success("✅ " + res.get("message"))
                    else:
                        st.error("❌ " + res.get("message"))

# ==========================================
# 頁面 3：歷史紀錄查詢 (完全對齊 InspectionLogs 11 欄位)
# ==========================================
with tab3:
    st.subheader("歷史檢驗紀錄查詢 (InspectionLogs)")
    search_kw = st.text_input("關鍵字搜尋 (料號 / 品名規格 / 供應商 / 不良描述)", "")
    
    history_data = get_api_data("getHistory")
    if history_data:
        df = pd.DataFrame(history_data)
        
        col_map = {
            "inspectDate": "檢驗日期",
            "partNameSpec": "品名規格",
            "partNo": "料號",
            "supplier": "供應商",
            "itemAttr": "料件屬性",
            "totalQty": "數量",
            "sampleQty": "檢驗數量",
            "defectQty": "異常數量",
            "result": "Pass/Fail",
            "yieldRate": "良率",
            "defectReason": "不良原因描述"
        }
        df = df.rename(columns=col_map)
        
        ordered_cols = ["檢驗日期", "品名規格", "料號", "供應商", "料件屬性", "數量", "檢驗數量", "異常數量", "Pass/Fail", "良率", "不良原因描述"]
        df = df[[c for c in ordered_cols if c in df.columns]]
        
        if search_kw:
            kw = search_kw.lower()
            mask = df["料號"].astype(str).str.lower().str.contains(kw) | \
                   df["品名規格"].astype(str).str.lower().str.contains(kw) | \
                   df["供應商"].astype(str).str.lower().str.contains(kw) | \
                   df["不良原因描述"].astype(str).str.lower().str.contains(kw)
            df = df[mask]
            
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("尚無 InspectionLogs 檢驗紀錄或載入中...")

# ==========================================
# 頁面 4：品質分析看板
# ==========================================
with tab4:
    st.subheader("品質分析看板")
    stats = get_api_data("getDashboardStats")
    if stats:
        c1, c2, c3 = st.columns(3)
        c1.metric("總檢驗筆數", stats.get("total", 0))
        c2.metric("批次合格率", f"{stats.get('passRate', 0)}%")
        c3.metric("不合格筆數 (Fail)", stats.get("failCount", 0))
        
        st.markdown("---")
        st.subheader("近期不合格警示列表 (Fail)")
        fails = stats.get("recentFails", [])
        if fails:
            fail_df = pd.DataFrame(fails).rename(columns={
                "inspectDate": "檢驗日期",
                "partNameSpec": "品名規格",
                "partNo": "料號",
                "supplier": "供應商",
                "defectQty": "異常數量",
                "result": "Pass/Fail",
                "defectReason": "不良原因描述"
            })
            st.dataframe(fail_df, use_container_width=True, hide_index=True)
        else:
            st.success("目前無不合格 (Fail) 紀錄。")
