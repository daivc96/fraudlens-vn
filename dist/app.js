import { DEMO_RECORDS, TYPE_LABELS, findRecord, riskMeta, validateSubmission } from "./core.js";

const tabs = [...document.querySelectorAll(".tab")];
const input = document.querySelector("#lookup-input");
const form = document.querySelector("#lookup-form");
const resultRegion = document.querySelector("#result-region");
const demoValue = document.querySelector("#demo-value");
const reportDialog = document.querySelector("#report-dialog");
const reportForm = document.querySelector("#report-form");
const apiDialog = document.querySelector("#api-dialog");
const toast = document.querySelector("#toast");
let activeType = "bank-account";

const demos = {
  "bank-account": { value: "0123456789", placeholder: "Nhập số tài khoản cần kiểm tra", inputMode: "numeric" },
  "phone-number": { value: "0901234567", placeholder: "Nhập số điện thoại cần kiểm tra", inputMode: "tel" },
  url: { value: "giaohang-demo.example", placeholder: "Nhập URL hoặc tên miền cần kiểm tra", inputMode: "url" }
};

function escapeHtml(value) {
  return String(value).replace(/[&<>'"]/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;" })[char]);
}

function setType(type) {
  activeType = type;
  tabs.forEach((tab) => {
    const selected = tab.dataset.type === type;
    tab.classList.toggle("active", selected);
    tab.setAttribute("aria-selected", String(selected));
  });
  input.placeholder = demos[type].placeholder;
  input.inputMode = demos[type].inputMode;
  demoValue.textContent = demos[type].value;
  resultRegion.innerHTML = "";
  input.value = "";
  input.focus();
}

function renderRecord(record) {
  const risk = riskMeta(record.riskScore);
  const tags = record.scamTypes.map((tag) => `<span class="tag">${escapeHtml(tag)}</span>`).join("");
  const sources = record.sources.map((source) => `<div class="source"><div><strong>${escapeHtml(source.label)}</strong><p>${escapeHtml(source.evidence)}</p></div><time>${escapeHtml(source.date)}</time></div>`).join("");
  resultRegion.innerHTML = `
    <article class="result-card">
      <div class="risk-panel ${risk.tone}">
        <div class="risk-score">${record.riskScore}<small>/100</small></div>
        <span class="risk-label">${risk.label}</span>
      </div>
      <div class="result-body">
        <div class="result-head"><div><span class="result-type">${TYPE_LABELS[record.type]}${record.bankCode ? ` · ${escapeHtml(record.bankCode)}` : ""}</span><h3>${escapeHtml(record.displayValue)}</h3></div><span class="case-id">${escapeHtml(record.id)}</span></div>
        <p class="result-summary">${escapeHtml(record.summary)}</p>
        <div class="result-tags">${tags}</div>
        <div class="result-facts">
          <div><span>Báo cáo</span><strong>${record.reportCount}</strong></div>
          <div><span>Nguồn độc lập</span><strong>${record.independentSources}</strong></div>
          <div><span>Phát hiện đầu</span><strong>${record.firstSeen}</strong></div>
          <div><span>Cập nhật cuối</span><strong>${record.lastSeen}</strong></div>
        </div>
        <div class="source-list">${sources}</div>
      </div>
    </article>`;
  resultRegion.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

function renderEmpty(query) {
  resultRegion.innerHTML = `<div class="empty-result"><h3>Chưa tìm thấy báo cáo khớp chính xác</h3><p>“${escapeHtml(query)}” chưa có trong bộ dữ liệu demo. Điều này không đồng nghĩa chỉ báo là an toàn.</p></div>`;
}

function showToast(message) {
  toast.textContent = message;
  toast.classList.add("show");
  window.clearTimeout(showToast.timer);
  showToast.timer = window.setTimeout(() => toast.classList.remove("show"), 3600);
}

tabs.forEach((tab) => tab.addEventListener("click", () => setType(tab.dataset.type)));
demoValue.addEventListener("click", () => { input.value = demos[activeType].value; input.focus(); });
form.addEventListener("submit", (event) => {
  event.preventDefault();
  const query = input.value.trim();
  if (!query) { input.focus(); showToast("Nhập một giá trị để kiểm tra."); return; }
  const record = findRecord(activeType, query, DEMO_RECORDS);
  record ? renderRecord(record) : renderEmpty(query);
});

document.querySelectorAll("[data-open-report]").forEach((button) => button.addEventListener("click", () => reportDialog.showModal()));
document.querySelectorAll("[data-open-api]").forEach((button) => button.addEventListener("click", () => apiDialog.showModal()));
document.querySelectorAll("[data-close-api]").forEach((button) => button.addEventListener("click", () => apiDialog.close()));

reportForm.addEventListener("submit", (event) => {
  event.preventDefault();
  const values = Object.fromEntries(new FormData(reportForm).entries());
  values.hasEvidence = reportForm.elements.hasEvidence.checked;
  const errors = validateSubmission(values);
  const errorBox = document.querySelector("#form-errors");
  if (Object.keys(errors).length) {
    errorBox.innerHTML = Object.values(errors).map((error) => `• ${escapeHtml(error)}`).join("<br>");
    return;
  }
  const reports = JSON.parse(localStorage.getItem("fraudlens-demo-reports") || "[]");
  reports.push({ ...values, id: crypto.randomUUID(), createdAt: new Date().toISOString(), status: "pending-local" });
  localStorage.setItem("fraudlens-demo-reports", JSON.stringify(reports));
  reportForm.reset();
  errorBox.textContent = "";
  reportDialog.close();
  showToast("Đã lưu báo cáo demo trên thiết bị này. Chưa gửi dữ liệu ra ngoài.");
});

for (const dialog of [reportDialog, apiDialog]) {
  dialog.addEventListener("click", (event) => {
    const rect = dialog.getBoundingClientRect();
    const outside = event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom;
    if (outside) dialog.close();
  });
}
