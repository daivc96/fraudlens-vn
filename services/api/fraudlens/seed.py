from __future__ import annotations

from .core import ProjectionIndicator


DEMO_INDICATORS = [
    ProjectionIndicator(
        indicator_type="bank-account",
        normalized_value="0123456789",
        display_value="0123 **** 89",
        risk_score=86,
        confidence="high",
        status="suspected",
        report_count=7,
        independent_sources=4,
        first_seen="2026-09-28",
        last_seen="2026-10-21",
        scam_types=["Giả shipper", "Phí hoàn đơn"],
        summary="Dữ liệu giả lập: nhiều nguồn mô tả yêu cầu chuyển phí giao hàng nhỏ rồi dẫn sang link giả mạo.",
        source_ref="demo:FL-2026-0017",
    ),
    ProjectionIndicator(
        indicator_type="phone-number",
        normalized_value="0901234567",
        display_value="0901 *** 567",
        risk_score=71,
        confidence="medium",
        status="reported",
        report_count=3,
        independent_sources=2,
        first_seen="2026-10-02",
        last_seen="2026-10-19",
        scam_types=["Giả nhân viên ngân hàng"],
        summary="Dữ liệu giả lập: số điện thoại được báo cáo trong cuộc gọi hỏi OTP.",
        source_ref="demo:FL-2026-0024",
    ),
]
