export const DEMO_RECORDS = [
  {
    id: "FL-2026-0017",
    type: "bank-account",
    value: "0123456789",
    displayValue: "0123 **** 89",
    bankCode: "ACB",
    riskScore: 86,
    confidence: "high",
    status: "suspected",
    reportCount: 7,
    independentSources: 4,
    firstSeen: "2026-09-28",
    lastSeen: "2026-10-21",
    scamTypes: ["Giả shipper", "Phí hoàn đơn"],
    summary: "Nhiều báo cáo độc lập mô tả yêu cầu chuyển khoản phí giao hàng nhỏ, sau đó dẫn dụ nạn nhân sang đường link giả mạo.",
    sources: [
      { label: "Bài cảnh báo cộng đồng", date: "21/10/2026", evidence: "Ảnh giao dịch đã được duyệt" },
      { label: "Báo cáo người dùng", date: "18/10/2026", evidence: "Kịch bản và STK trùng khớp" },
      { label: "Nguồn đối tác", date: "03/10/2026", evidence: "Tín hiệu được chia sẻ hạn chế" }
    ]
  },
  {
    id: "FL-2026-0024",
    type: "phone-number",
    value: "0901234567",
    displayValue: "0901 *** 567",
    riskScore: 71,
    confidence: "medium",
    status: "reported",
    reportCount: 3,
    independentSources: 2,
    firstSeen: "2026-10-02",
    lastSeen: "2026-10-19",
    scamTypes: ["Giả nhân viên ngân hàng"],
    summary: "Số điện thoại xuất hiện trong các báo cáo cuộc gọi yêu cầu cung cấp OTP. Chưa có xác nhận từ nguồn có thẩm quyền.",
    sources: [
      { label: "Báo cáo người dùng", date: "19/10/2026", evidence: "Nhật ký cuộc gọi" },
      { label: "Bài cảnh báo cộng đồng", date: "02/10/2026", evidence: "Nội dung cuộc gọi tương đồng" }
    ]
  },
  {
    id: "FL-2026-0031",
    type: "url",
    value: "https://giaohang-demo.example/hoan-tien",
    displayValue: "giaohang-demo[.]example/hoan-tien",
    riskScore: 94,
    confidence: "high",
    status: "high-risk",
    reportCount: 11,
    independentSources: 6,
    firstSeen: "2026-10-13",
    lastSeen: "2026-10-22",
    scamTypes: ["Website giả mạo", "Đánh cắp tài khoản"],
    summary: "Trang giả mạo quy trình hoàn tiền giao hàng, thu thập thông tin đăng nhập và mã xác thực của nạn nhân.",
    sources: [
      { label: "Phân tích kỹ thuật", date: "22/10/2026", evidence: "Trang thu thập thông tin xác thực" },
      { label: "Báo cáo cộng đồng", date: "20/10/2026", evidence: "5 báo cáo có cùng URL" }
    ]
  }
];

export const TYPE_LABELS = {
  "bank-account": "Số tài khoản",
  "phone-number": "Số điện thoại",
  url: "URL / tên miền"
};

export function normalizeValue(type, rawValue) {
  const value = String(rawValue || "").trim();
  if (type === "bank-account") return value.replace(/[^0-9a-z]/gi, "").toUpperCase();
  if (type === "phone-number") {
    const digits = value.replace(/\D/g, "");
    if (digits.startsWith("84") && digits.length >= 11) return `0${digits.slice(2)}`;
    return digits;
  }
  if (type === "url") {
    try {
      const withScheme = /^https?:\/\//i.test(value) ? value : `https://${value}`;
      const url = new URL(withScheme);
      return `${url.hostname.toLowerCase().replace(/^www\./, "")}${url.pathname.replace(/\/$/, "")}`;
    } catch {
      return value.toLowerCase().replace(/^https?:\/\//, "").replace(/^www\./, "").replace(/\/$/, "");
    }
  }
  return value;
}

export function findRecord(type, query, records = DEMO_RECORDS) {
  const needle = normalizeValue(type, query);
  if (!needle) return null;
  return records.find((record) => normalizeValue(type, record.value) === needle && record.type === type) || null;
}

export function riskMeta(score) {
  if (score >= 80) return { label: "Rủi ro rất cao", tone: "critical" };
  if (score >= 60) return { label: "Nghi vấn cao", tone: "high" };
  if (score >= 30) return { label: "Cần thận trọng", tone: "medium" };
  return { label: "Chưa đủ dữ liệu", tone: "low" };
}

export function validateSubmission(payload) {
  const errors = {};
  if (!payload.type || !TYPE_LABELS[payload.type]) errors.type = "Chọn loại chỉ báo.";
  if (normalizeValue(payload.type, payload.value).length < 5) errors.value = "Nhập một giá trị hợp lệ.";
  if (!payload.description || payload.description.trim().length < 20) errors.description = "Mô tả ít nhất 20 ký tự.";
  if (!payload.sourceUrl && !payload.hasEvidence) errors.evidence = "Cần URL nguồn hoặc xác nhận có bằng chứng.";
  return errors;
}
