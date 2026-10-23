import test from "node:test";
import assert from "node:assert/strict";
import { findRecord, normalizeValue, riskMeta, validateSubmission } from "../dist/core.js";

test("normalizes Vietnamese phone numbers", () => {
  assert.equal(normalizeValue("phone-number", "+84 901 234 567"), "0901234567");
});

test("normalizes and matches URLs without scheme", () => {
  assert.equal(normalizeValue("url", "https://www.giaohang-demo.example/hoan-tien/"), "giaohang-demo.example/hoan-tien");
  assert.equal(findRecord("url", "giaohang-demo.example/hoan-tien")?.id, "FL-2026-0031");
});

test("exact matching prevents partial enumeration", () => {
  assert.equal(findRecord("bank-account", "01234"), null);
  assert.equal(findRecord("bank-account", "0123 456 789")?.id, "FL-2026-0017");
});

test("risk labels are deterministic", () => {
  assert.equal(riskMeta(86).tone, "critical");
  assert.equal(riskMeta(55).tone, "medium");
});

test("submission requires evidence context", () => {
  const errors = validateSubmission({ type: "bank-account", value: "123456", description: "Một mô tả đủ dài cho báo cáo thử nghiệm.", sourceUrl: "", hasEvidence: false });
  assert.equal(errors.evidence, "Cần URL nguồn hoặc xác nhận có bằng chứng.");
});
