<!DOCTYPE html>
<html lang="zh-TW">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>IQC 進料品質管理系統</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
  <style>
    body { background-color: #f4f6f9; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
    .card { border: none; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }
    .nav-pills .nav-link { font-weight: 500; color: #495057; }
    .nav-pills .nav-link.active { background-color: #0d6efd; font-weight: 600; }
    .stat-card { border-left: 5px solid #0d6efd; }
    .stat-card.pass { border-left-color: #198754; }
    .stat-card.fail { border-left-color: #dc3545; }
    .loading-spinner { display: inline-block; width: 1.2rem; height: 1.2rem; border: 0.2em solid currentColor; border-right-color: transparent; border-radius: 50%; animation: spinner-border .75s linear infinite; }
  </style>
</head>
<body>

<div class="container py-4">
  <div class="text-center mb-4">
    <h2 class="fw-bold text-primary">IQC 進料品質管理系統</h2>
    <p class="text-muted small">Google Sheets 後端連動 × GitHub Pages 即時監控</p>
  </div>

  <!-- 主功能導覽列 -->
  <ul class="nav nav-pills justify-content-center mb-4" id="mainTab" role="tablist">
    <li class="nav-item"><button class="nav-link active" onclick="switchTab('tab-item-master', this)">1. 新增料件主檔</button></li>
    <li class="nav-item"><button class="nav-link" onclick="switchTab('tab-add-inspection', this)">2. 新增進料檢驗</button></li>
    <li class="nav-item"><button class="nav-link" onclick="switchTab('tab-history', this)">3. 歷史紀錄查詢</button></li>
    <li class="nav-item"><button class="nav-link" onclick="switchTab('tab-dashboard', this)">4. 品質分析看板</button></li>
  </ul>

  <!-- 1. 新增料件主檔 -->
  <div id="tab-item-master" class="tab-content">
    <div class="card p-4 mx-auto" style="max-width: 600px;">
      <h4 class="card-title mb-3 fw-bold">新增料件主檔</h4>
      <form id="form-item-master">
        <div class="mb-3">
          <label class="form-label">料號 *</label>
          <input type="text" id="master-partNo" class="form-control" placeholder="例如：PCBA-2026-001" required>
        </div>
        <div class="mb-3">
          <label class="form-label">品名 *</label>
          <input type="text" id="master-partName" class="form-control" placeholder="例如：控制主板" required>
        </div>
        <div class="mb-3">
          <label class="form-label">規格描述</label>
          <input type="text" id="master-spec" class="form-control" placeholder="例如：Rev B / RoHS">
        </div>
        <div class="mb-3">
          <label class="form-label">供應商</label>
          <input type="text" id="master-supplier" class="form-control" placeholder="例如：台積電 / 鴻海">
        </div>
        <div class="mb-3">
          <label class="form-label">AQL 允收水準</label>
          <select id="master-aql" class="form-select">
            <option value="0.4">0.4 (嚴格)</option>
            <option value="0.65" selected>0.65 (標準)</option>
            <option value="1.0">1.0 (放寬)</option>
          </select>
        </div>
        <button type="button" id="btn-master-submit" class="btn btn-primary w-100 py-2" onclick="submitItemMaster()">儲存料件主檔</button>
      </form>
    </div>
  </div>

  <!-- 2. 新增進料檢驗 -->
  <div id="tab-add-inspection" class="tab-content d-none">
    <div class="card p-4 mx-auto" style="max-width: 650px;">
      <h4 class="card-title mb-3 fw-bold">新增進料檢驗單</h4>
      <form id="form-add-inspection">
        <div class="row">
          <div class="col-md-6 mb-3">
            <label class="form-label">選擇料號 *</label>
            <select id="insp-partNo" class="form-select" onchange="autoFillPartName()" required>
              <option value="">載入中...</option>
            </select>
          </div>
          <div class="col-md-6 mb-3">
            <label class="form-label">品名</label>
            <input type="text" id="insp-partName" class="form-control bg-light" readonly>
          </div>
        </div>
        <div class="row">
          <div class="col-md-6 mb-3">
            <label class="form-label">檢驗日期 *</label>
            <input type="date" id="insp-date" class="form-control" required>
          </div>
          <div class="col-md-6 mb-3">
            <label class="form-label">檢驗人員 *</label>
            <input type="text" id="insp-inspector" class="form-control" placeholder="請輸入姓名/工號" required>
          </div>
        </div>
        <div class="row">
          <div class="col-md-4 mb-3">
            <label class="form-label">進貨數量 *</label>
            <input type="number" id="insp-batchSize" class="form-control" min="1" required>
          </div>
          <div class="col-md-4 mb-3">
            <label class="form-label">抽驗數量 *</label>
            <input type="number" id="insp-sampleSize" class="form-control" min="1" required>
          </div>
          <div class="col-md-4 mb-3">
            <label class="form-label">不良數量 *</label>
            <input type="number" id="insp-defectCount" class="form-control" min="0" value="0" oninput="autoDetermineStatus()" required>
          </div>
        </div>
        <div class="mb-3">
          <label class="form-label">判定結果 *</label>
          <select id="insp-status" class="form-select">
            <option value="合格">合格 (PASS)</option>
            <option value="不合格">不合格 (FAIL)</option>
          </select>
        </div>
        <div class="mb-3">
          <label class="form-label">備註 / 異常描述</label>
          <textarea id="insp-remark" class="form-control" rows="2" placeholder="備註或不良現象描述..."></textarea>
        </div>
        <button type="button" id="btn-insp-submit" class="btn btn-success w-100 py-2" onclick="submitInspection()">儲存檢驗紀錄</button>
      </form>
    </div>
  </div>

  <!-- 3. 歷史紀錄查詢 -->
  <div id="tab-history" class="tab-content d-none">
    <div class="card p-4">
      <div class="d-flex justify-content-between align-items-center mb-3">
        <h4 class="card-title m-0 fw-bold">歷史檢驗紀錄查詢</h4>
        <input type="text" id="search-keyword" class="form-control w-auto" placeholder="關鍵字搜尋料號/品名..." oninput="renderHistoryTable()">
      </div>
      <div class="table-responsive">
        <table class="table table-hover align-middle">
          <thead class="table-light">
            <tr>
              <th>單號</th><th>日期</th><th>料號</th><th>品名</th><th>進貨數</th><th>抽驗數</th><th>不良數</th><th>判定</th><th>檢驗員</th>
            </tr>
          </thead>
          <tbody id="history-table-body">
            <tr><td colspan="9" class="text-center py-4">資料載入中...</td></tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>

  <!-- 4. 品質分析看板 -->
  <div id="tab-dashboard" class="tab-content d-none">
    <div class="row g-3 mb-4">
      <div class="col-md-3">
        <div class="card p-3 stat-card">
          <div class="text-muted small">總檢驗批數</div>
          <div class="h2 fw-bold m-0" id="stat-total">0</div>
        </div>
      </div>
      <div class="col-md-3">
        <div class="card p-3 stat-card pass">
          <div class="text-muted small">批次合格率</div>
          <div class="h2 fw-bold text-success m-0" id="stat-pass-rate">0%</div>
        </div>
      </div>
      <div class="col-md-3">
        <div class="card p-3 stat-card fail">
          <div class="text-muted small">數量不良率</div>
          <div class="h2 fw-bold text-danger m-0" id="stat-defect-rate">0%</div>
        </div>
      </div>
      <div class="col-md-3">
        <div class="card p-3 stat-card fail">
          <div class="text-muted small">不合格批數</div>
          <div class="h2 fw-bold text-danger m-0" id="stat-fail-count">0</div>
        </div>
      </div>
    </div>
    
    <div class="card p-4">
      <h5 class="card-title text-danger mb-3 fw-bold">近期不合格警示清單 (Recent Failure Logs)</h5>
      <ul class="list-group list-group-flush" id="recent-fails-list">
        <li class="list-group-item text-muted py-3">載入中...</li>
      </ul>
    </div>
  </div>
</div>

<script>
  // 已帶入您部署好的 Apps Script Web App URL
  const GAS_API_URL = "https://script.google.com/macros/s/AKfycbzeQ7G0xJ-c9D0ExQ_dmo4OqugJ9XauRKy8M6s2-Dti_ZCvzq9XhXzG2sweI3gJdybAmw/exec";

  let itemMasterCache = [];
  let historyLogsCache = [];

  document.addEventListener("DOMContentLoaded", () => {
    document.getElementById("insp-date").valueAsDate = new Date();
    loadItemMaster();
  });

  function switchTab(tabId, btnElement) {
    document.querySelectorAll(".tab-content").forEach(el => el.classList.add("d-none"));
    document.querySelectorAll("#mainTab .nav-link").forEach(el => el.classList.remove("active"));
    
    document.getElementById(tabId).classList.remove("d-none");
    btnElement.classList.add("active");

    if (tabId === 'tab-add-inspection') loadItemMaster();
    if (tabId === 'tab-history') loadHistory();
    if (tabId === 'tab-dashboard') loadDashboard();
  }

  // 1. 新增料件主檔
  async function submitItemMaster() {
    const btn = document.getElementById("btn-master-submit");
    const data = {
      partNo: document.getElementById("master-partNo").value.trim(),
      partName: document.getElementById("master-partName").value.trim(),
      spec: document.getElementById("master-spec").value.trim(),
      supplier: document.getElementById("master-supplier").value.trim(),
      aql: document.getElementById("master-aql").value
    };

    if (!data.partNo || !data.partName) return alert("請填寫料號與品名！");

    btn.disabled = true;
    btn.innerHTML = '<span class="loading-spinner"></span> 儲存中...';

    try {
      const res = await fetch(GAS_API_URL, {
        method: "POST",
        body: JSON.stringify({ action: "addItemMaster", data })
      }).then(r => r.json());

      if (res.status === "success") {
        alert(res.message);
        document.getElementById("form-item-master").reset();
      } else {
        alert("失敗: " + res.message);
      }
    } catch (err) {
      alert("傳送失敗，請確認網路連線或 API 狀態：" + err);
    } finally {
      btn.disabled = false;
      btn.innerText = "儲存料件主檔";
    }
  }

  // 載入料件選單
  async function loadItemMaster() {
    try {
      const res = await fetch(`${GAS_API_URL}?action=getItemMaster`).then(r => r.json());
      if (res.status === "success") {
        itemMasterCache = res.data;
        const select = document.getElementById("insp-partNo");
        select.innerHTML = '<option value="">-- 請選擇料號 --</option>';
        itemMasterCache.forEach(item => {
          select.innerHTML += `<option value="${item.partNo}">${item.partNo} (${item.partName})</option>`;
        });
      }
    } catch (err) {
      console.error("載入料件選單失敗:", err);
    }
  }

  function autoFillPartName() {
    const selectedPartNo = document.getElementById("insp-partNo").value;
    const item = itemMasterCache.find(i => i.partNo === selectedPartNo);
    document.getElementById("insp-partName").value = item ? item.partName : "";
  }

  function autoDetermineStatus() {
    const defect = Number(document.getElementById("insp-defectCount").value);
    document.getElementById("insp-status").value = defect > 0 ? "不合格" : "合格";
  }

  // 2. 新增進料檢驗
  async function submitInspection() {
    const btn = document.getElementById("btn-insp-submit");
    const data = {
      partNo: document.getElementById("insp-partNo").value,
      partName: document.getElementById("insp-partName").value,
      inspectDate: document.getElementById("insp-date").value,
      inspector: document.getElementById("insp-inspector").value.trim(),
      batchSize: document.getElementById("insp-batchSize").value,
      sampleSize: document.getElementById("insp-sampleSize").value,
      defectCount: document.getElementById("insp-defectCount").value,
      status: document.getElementById("insp-status").value,
      remark: document.getElementById("insp-remark").value.trim()
    };

    if (!data.partNo || !data.inspector || !data.batchSize || !data.sampleSize) {
      return alert("請完整填寫必要欄位！");
    }

    btn.disabled = true;
    btn.innerHTML = '<span class="loading-spinner"></span> 存檔中...';

    try {
      const res = await fetch(GAS_API_URL, {
        method: "POST",
        body: JSON.stringify({ action: "addInspection", data })
      }).then(r => r.json());

      if (res.status === "success") {
        alert(`${res.message}\n單號：${res.inspectionId}`);
        document.getElementById("form-add-inspection").reset();
        document.getElementById("insp-date").valueAsDate = new Date();
      } else {
        alert("失敗: " + res.message);
      }
    } catch (err) {
      alert("存檔失敗：" + err);
    } finally {
      btn.disabled = false;
      btn.innerText = "儲存檢驗紀錄";
    }
  }

  // 3. 讀取與查詢歷史紀錄
  async function loadHistory() {
    const tbody = document.getElementById("history-table-body");
    tbody.innerHTML = '<tr><td colspan="9" class="text-center py-4"><span class="loading-spinner"></span> 資料載入中...</td></tr>';
    
    try {
      const res = await fetch(`${GAS_API_URL}?action=getHistory`).then(r => r.json());
      if (res.status === "success") {
        historyLogsCache = res.data;
        renderHistoryTable();
      }
    } catch (err) {
      tbody.innerHTML = '<tr><td colspan="9" class="text-center text-danger">讀取失敗</td></tr>';
    }
  }

  function renderHistoryTable() {
    const kw = document.getElementById("search-keyword").value.toLowerCase();
    const tbody = document.getElementById("history-table-body");
    const filtered = historyLogsCache.filter(i => 
      i.partNo.toLowerCase().includes(kw) || 
      i.partName.toLowerCase().includes(kw) ||
      i.inspectionId.toLowerCase().includes(kw)
    );

    if (filtered.length === 0) {
      tbody.innerHTML = '<tr><td colspan="9" class="text-center py-4 text-muted">無符合條件的檢驗紀錄</td></tr>';
      return;
    }

    tbody.innerHTML = filtered.map(i => `
      <tr>
        <td class="fw-bold">${i.inspectionId}</td>
        <td>${i.inspectDate}</td>
        <td>${i.partNo}</td>
        <td>${i.partName}</td>
        <td>${i.batchSize}</td>
        <td>${i.sampleSize}</td>
        <td class="${i.defectCount > 0 ? 'text-danger fw-bold' : ''}">${i.defectCount}</td>
        <td><span class="badge ${i.status === '合格' ? 'bg-success' : 'bg-danger'}">${i.status}</span></td>
        <td>${i.inspector}</td>
      </tr>
    `).join("");
  }

  // 4. 品質分析看板
  async function loadDashboard() {
    try {
      const res = await fetch(`${GAS_API_URL}?action=getDashboardStats`).then(r => r.json());
      if (res.status === "success") {
        const d = res.data;
        document.getElementById("stat-total").innerText = d.totalBatches;
        document.getElementById("stat-pass-rate").innerText = d.passRate + "%";
        document.getElementById("stat-defect-rate").innerText = d.defectRate + "%";
        document.getElementById("stat-fail-count").innerText = d.failCount;

        const failList = document.getElementById("recent-fails-list");
        if (d.recentFails.length === 0) {
          failList.innerHTML = '<li class="list-group-item text-muted py-3">無不合格批次紀錄</li>';
        } else {
          failList.innerHTML = d.recentFails.map(f => `
            <li class="list-group-item d-flex justify-content-between align-items-center">
              <div>
                <strong>${f.inspectDate} - ${f.partNo} (${f.partName})</strong>
                <div class="text-muted small">檢驗員: ${f.inspector} | 抽樣數: ${f.sampleSize} | 不良數: <span class="text-danger fw-bold">${f.defectCount}</span> | 備註: ${f.remark || '無'}</div>
              </div>
              <span class="badge bg-danger">${f.inspectionId}</span>
            </li>
          `).join("");
        }
      }
    } catch (err) {
      console.error("看板讀取失敗:", err);
    }
  }
</script>

</body>
</html>
