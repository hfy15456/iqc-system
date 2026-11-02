import streamlit as st
import requests
import pandas as pd
from datetime import date

# Google Apps Script API 網址
GAS_API_URL = "https://script.google.com/macros/s/AKfycbzeQ7G0xJ-c9D0ExQ_dmo4OqugJ9XauRKy8M6s2-Dti_ZCvzq9XhXzG2sweI3gJdybAmw/exec"

# 頁面基本設定
st.set_page_config(page_title="IQC 進料品質管理系統", layout="wide")

st.title("IQC 進料品質管理系統")
st.caption("Google Sheets 後端連動 × Python Streamlit 管理介面")

# 通用 API 請求函式
def get_api_data(action):
    try:
        res = requests.get(f"{GAS_API_URL}?action={action}", timeout=10)
        if res.status_code == 200:
            data = res.json()
            if data.get("status") == "success":
                return data.get("data", [])
            else:
                st.error(f"後端回應錯誤: {data.get('message')}")
        else:
            st.error(f"HTTP 請求失敗 (狀態碼: {res.status_code})")
    except Exception as e:
        st.error(f"API 連線失敗: {e}")
    return []

def post_api_data(action, payload_data):
    try:
        res = requests.post(GAS_API_URL, json={"action": action, "data": payload_data}, timeout=10)
        if res.status_code == 200:
            return res.json()
        else:
            return {"status": "error", "message": f"HTTP 狀態碼: {res.status_code}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# 建立分頁
tab1, tab2, tab3, tab4 = st.tabs(["1. 新增料件主檔", "2. 新增進料檢驗", "3. 歷史紀錄查詢", "4. 品質分析看板"])

# ==========================================
# 頁面 1：新增料件主檔
# ==========================================
with tab1:
    st.subheader("新增料件主檔")
    with st.form("form_item_master", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            part_no = st.text_input("料號 *", placeholder="例：PCBA-2026-001")
            part_name = st.text_input("品名 *", placeholder="例：控制主板")
            spec = st.text_input("規格描述", placeholder="例：Rev B / RoHS")
        with col2:
            supplier = st.text_input("供應商", placeholder="例：台積電 / 鴻海")
            aql = st.selectbox("AQL 允收水準", ["0.65", "0.4", "1.0"], index=0)
        
        submitted = st.form_submit_button("儲存料件主檔", use_container_width=True)
        if submitted:
            if not part_no or not part_name:
                st.warning("請完整填寫料號與品名！")
            else:
                with st.spinner("存檔中..."):
                    res = post_api_data("addItemMaster", {
                        "partNo": part_no.strip(),
                        "partName": part_name.strip(),
                        "spec": spec.strip(),
                        "supplier": supplier.strip(),
                        "aql": aql
                    })
                    if res.get("status") == "success":
                        st.success(res.get("message"))
                    else:
                        st.error(f"新增失敗: {res.get('message')}")

# ==========================================
# 頁面 2：新增進料檢驗
# ==========================================
with tab2:
    st.subheader("新增進料檢驗單")
    
    # 載入料件主檔供選單使用
    items = get_api_data("getItemMaster")
    item_dict = {item["partNo"]: item["partName"] for item in items} if items else {}
    
    with st.form("form_inspection", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            part_options = [""] + list(item_dict.keys())
            selected_part_no = st.selectbox(
                "選擇料號 *", 
                options=part_options, 
                format_func=lambda x: f"{x} ({item_dict[x]})" if x in item_dict else "請選擇料號"
            )
            part_name_display = item_dict.get(selected_part_no, "")
            st.text_input("自動填入品名", value=part_name_display, disabled=True)
            
            inspect_date = st.date_input("檢驗日期 *", value=date.today())
            inspector = st.text_input("檢驗人員 *", placeholder="請輸入姓名/工號")
            
        with col2:
            batch_size = st.number_input("進貨數量 *", min_value=1, value=100, step=1)
            sample_size = st.number_input("抽驗數量 *", min_value=1, value=10, step=1)
            defect_count = st.number_input("不良數量 *", min_value=0, value=0, step=1)
            
            # 自動判定預設值
            default_status = "不合格" if defect_count > 0 else "合格"
            status = st.selectbox("判定結果 *", ["合格", "不合格"], index=0 if default_status == "合格" else 1)
        
        remark = st.text_area("備註 / 異常描述", placeholder="備註或不良現象描述...")
        
        submitted_insp = st.form_submit_button("儲存檢驗紀錄", use_container_width=True)
        if submitted_insp:
            if not selected_part_no or not inspector:
                st.warning("請完整填寫必要欄位！")
            else:
                with st.spinner("檢驗單存檔中..."):
                    res = post_api_data("addInspection", {
                        "partNo": selected_part_no,
                        "partName": part_name_display,
                        "inspectDate": str(inspect_date),
                        "inspector": inspector.strip(),
                        "batchSize": batch_size,
                        "sampleSize": sample_size,
                        "defectCount": defect_count,
                        "status": status,
                        "remark": remark.strip()
                    })
                    if res.get("status") == "success":
                        st.success(f"{res.get('message')} (單號：{res.get('inspectionId')})")
                    else:
                        st.error(f"存檔失敗: {res.get('message')}")

# ==========================================
# 頁面 3：歷史紀錄查詢
# ==========================================
with tab3:
    st.subheader("歷史檢驗紀錄查詢")
    search_kw = st.text_input("關鍵字搜尋（單號 / 料號 / 品名）", "")
    
    history_data = get_api_data("getHistory")
    if history_data:
        df = pd.DataFrame(history_data)
        col_map = {
            "inspectionId": "檢驗單號",
            "inspectDate": "檢驗日期",
            "partNo": "料號",
            "partName": "品名",
            "batchSize": "進貨數量",
            "sampleSize": "抽驗數量",
            "defectCount": "不良數量",
            "status": "判定結果",
            "inspector": "檢驗人員",
            "remark": "備註"
        }
        df = df.rename(columns=col_map)
        
        if search_kw:
            kw = search_kw.lower()
            mask = df["料號"].astype(str).str.lower().str.contains(kw) | \
                   df["品名"].astype(str).str.lower().str.contains(kw) | \
                   df["檢驗單號"].astype(str).str.lower().str.contains(kw)
            df = df[mask]
            
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("目前尚無歷史檢驗紀錄或載入中。")

# ==========================================
# 頁面 4：品質分析看板
# ==========================================
with tab4:
    st.subheader("品質分析看板")
    stats = get_api_data("getDashboardStats")
    if stats:
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("總檢驗批數", stats.get("totalBatches", 0))
        m2.metric("批次合格率", f"{stats.get('passRate', 0)}%")
        m3.metric("數量不良率", f"{stats.get('defectRate', 0)}%")
        m4.metric("不合格批數", stats.get("failCount", 0))
        
        st.markdown("---")
        st.subheader("近期不合格警示清單 (Recent Failures)")
        recent_fails = stats.get("recentFails", [])
        if recent_fails:
            fail_df = pd.DataFrame(recent_fails).rename(columns={
                "inspectionId": "單號",
                "inspectDate": "日期",
                "partNo": "料號",
                "partName": "品名",
                "sampleSize": "抽驗數",
                "defectCount": "不良數",
                "inspector": "檢驗員",
                "remark": "備註"
            })
            st.dataframe(fail_df, use_container_width=True, hide_index=True)
        else:
            st.success("目前無不合格批次紀錄。")
