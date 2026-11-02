import streamlit as st
import requests
import pandas as pd
from datetime import date

# 請填入您的 Apps Script Web App API 網址
GAS_API_URL = "https://script.google.com/macros/s/AKfycbzeQ7G0xJ-c9D0ExQ_dmo4OqugJ9XauRKy8M6s2-Dti_ZCvzq9XhXzG2sweI3gJdybAmw/exec"

st.set_page_config(page_title="IQC 進料品質管理系統", layout="wide")

st.title("IQC 進料品質管理系統")
st.caption("連動雲端 IQC 試算表現有欄位與歷史資料")

def get_api_data(action):
    try:
        res = requests.get(f"{GAS_API_URL}?action={action}", timeout=10)
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
        res = requests.post(GAS_API_URL, json={"action": action, "data": payload}, timeout=10)
        if res.status_code == 200:
            return res.json()
        return {"status": "error", "message": f"HTTP {res.status_code}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

tab1, tab2, tab3 = st.tabs(["1. 新增進料檢驗單", "2. 歷史紀錄查詢", "3. 品質分析看板"])

# ==========================================
# 頁面 1：新增進料檢驗單
# ==========================================
with tab1:
    st.subheader("新增進料檢驗單")
    
    existing_items = get_api_data("getItemMaster")
    item_dict = {item["partNo"]: item["partNameSpec"] for item in existing_items} if existing_items else {}
    
    with st.form("form_add_inspection", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            inspect_date = st.date_input("檢驗日期 *", value=date.today())
            
            use_custom = st.checkbox("手動輸入全新料號 (不在既有試算表中)")
            if not use_custom and item_dict:
                selected_part_no = st.selectbox(
                    "選擇既有料號 *", 
                    options=list(item_dict.keys()),
                    format_func=lambda x: f"{x} - {item_dict[x]}"
                )
                part_no = selected_part_no
                part_name_spec = item_dict.get(selected_part_no, "")
                st.text_input("品名規格 (自動帶入)", value=part_name_spec, disabled=True)
            else:
                part_no = st.text_input("料號 *", placeholder="例：1335005-03-S")
                part_name_spec = st.text_input("品名規格 *", placeholder="例：APEX Passive")
                
            lot_no = st.text_input("批號", placeholder="可留空")
            sample_size = st.number_input("抽檢數量 *", min_value=1, value=10, step=1)

        with col2:
            visual_inspect = st.selectbox("外觀/結構檢驗", ["OK", "NG", "N/A"], index=0)
            elec_inspect = st.selectbox("電測/功能檢驗", ["OK", "NG", "N/A"], index=0)
            key_data = st.text_input("關鍵量測數據", placeholder="例：0.433 / 150±3ohm")
            sop_doc = st.text_input("檢驗手冊/SOP", value="Pass")
            result = st.selectbox("判定結果 (Pass/Fail) *", ["Pass", "Fail"], index=0)
            inspector = st.text_input("檢驗人員 *", placeholder="例：Eddie")
            
        defect_reason = st.text_area("不良原因描述 / 備註", placeholder="例：檢測有1PCS過規")

        submitted = st.form_submit_button("寫入雲端 IQC 試算表", use_container_width=True)
        if submitted:
            if not part_no or not part_name_spec or not inspector:
                st.warning("請完整填寫料號、品名規格與檢驗人員！")
            else:
                with st.spinner("資料寫入中..."):
                    res = post_api_data("addInspection", {
                        "inspectDate": str(inspect_date),
                        "partNo": part_no.strip(),
                        "partNameSpec": part_name_spec.strip(),
                        "lotNo": lot_no.strip(),
                        "sampleSize": sample_size,
                        "visualInspect": visual_inspect,
                        "elecInspect": elec_inspect,
                        "keyData": key_data.strip(),
                        "sopDoc": sop_doc.strip(),
                        "result": result,
                        "inspector": inspector.strip(),
                        "defectReason": defect_reason.strip()
                    })
                    if res.get("status") == "success":
                        st.success("✅ " + res.get("message"))
                    else:
                        st.error("❌ 寫入失敗：" + res.get("message"))

# ==========================================
# 頁面 2：歷史紀錄查詢
# ==========================================
with tab2:
    st.subheader("歷史檢驗紀錄查詢 (同步試算表現有資料)")
    search_kw = st.text_input("搜尋關鍵字 (料號 / 品名規格 / 檢驗人員 / 不良描述)", "")
    
    history_data = get_api_data("getHistory")
    if history_data:
        df = pd.DataFrame(history_data)
        col_map = {
            "inspectDate": "檢驗日期",
            "partNo": "料號",
            "partNameSpec": "品名規格",
            "lotNo": "批號",
            "sampleSize": "抽檢數量",
            "visualInspect": "外觀/結構檢驗",
            "elecInspect": "電測/功能檢驗",
            "keyData": "關鍵量測數據",
            "sopDoc": "檢驗手冊/SOP",
            "result": "Pass/Fail",
            "inspector": "檢驗人員",
            "defectReason": "不良原因描述"
        }
        df = df.rename(columns=col_map)
        
        if search_kw:
            kw = search_kw.lower()
            mask = df["料號"].astype(str).str.lower().str.contains(kw) | \
                   df["品名規格"].astype(str).str.lower().str.contains(kw) | \
                   df["檢驗人員"].astype(str).str.lower().str.contains(kw) | \
                   df["不良原因描述"].astype(str).str.lower().str.contains(kw)
            df = df[mask]
            
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("尚無紀錄或連線中...")

# ==========================================
# 頁面 3：品質分析看板
# ==========================================
with tab3:
    st.subheader("品質分析看板")
    stats = get_api_data("getDashboardStats")
    if stats:
        c1, c2, c3 = st.columns(3)
        c1.metric("總檢驗筆數", stats.get("total", 0))
        c2.metric("合格率 (Pass Rate)", f"{stats.get('passRate', 0)}%")
        c3.metric("不合格筆數 (Fail Count)", stats.get("failCount", 0))
        
        st.markdown("---")
        st.subheader("近期不合格 / 異常警示列表 (Fail)")
        fails = stats.get("recentFails", [])
        if fails:
            fail_df = pd.DataFrame(fails).rename(columns={
                "inspectDate": "檢驗日期",
                "partNo": "料號",
                "partNameSpec": "品名規格",
                "sampleSize": "抽檢數量",
                "result": "Pass/Fail",
                "inspector": "檢驗人員",
                "defectReason": "不良原因描述"
            })
            st.dataframe(fail_df, use_container_width=True, hide_index=True)
        else:
            st.success("目前無不合格 (Fail) 紀錄。")
