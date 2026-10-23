import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fraudlens.core import from_misp_attribute, normalize_value
from fraudlens.intake import Intake, build_event_payload
from fraudlens.store import Store


class CoreTests(unittest.TestCase):
    def test_normalize_phone(self):
        self.assertEqual(normalize_value("phone-number", "+84 901 234 567"), "0901234567")

    def test_misp_mapping_requires_supported_type(self):
        self.assertIsNone(from_misp_attribute({"type": "ip-src", "value": "192.0.2.1"}))

    def test_misp_mapping_respects_policy_tags(self):
        result = from_misp_attribute(
            {
                "id": "42",
                "type": "bank-account-nr",
                "value": "0123 456 789",
                "comment": "Synthetic test record",
                "Tag": [
                    {"name": "fraudlens:risk=82"},
                    {"name": "fraudlens:status=suspected"},
                    {"name": "fraudlens:scam-type=Giả shipper"},
                ],
            }
        )
        self.assertIsNotNone(result)
        self.assertEqual(result.risk_score, 82)
        self.assertEqual(result.display_value, "0123 **** 89")

    def test_store_uses_exact_match(self):
        from fraudlens.seed import DEMO_INDICATORS

        with tempfile.TemporaryDirectory() as directory:
            store = Store(os.path.join(directory, "test.db"))
            store.upsert(DEMO_INDICATORS[0])
            self.assertIsNotNone(store.lookup("bank-account", "0123 456 789"))
            self.assertIsNone(store.lookup("bank-account", "01234"))

    def test_public_intake_requires_review_exception_for_one_source(self):
        intake = Intake(
            indicator_type="bank-account",
            value="1234567890",
            source_url="https://www.facebook.com/example",
            scenario="Mua bán online nhận tiền rồi ngắt liên lạc",
            reviewed_by="analyst@example.test",
            approve_public=True,
        )
        with self.assertRaises(ValueError):
            build_event_payload(intake)

    def test_approved_intake_tags_indicator_for_projection(self):
        intake = Intake(
            indicator_type="bank-account",
            value="1234567890",
            source_url="https://www.facebook.com/example",
            scenario="Mua bán online nhận tiền rồi ngắt liên lạc",
            reviewed_by="analyst@example.test",
            bank_code="NCB",
            approve_public=True,
            single_source_exception=True,
        )
        payload = build_event_payload(intake)
        tags = [tag["name"] for tag in payload["Event"]["Attribute"][0]["Tag"]]
        self.assertIn("fraudlens:publish=true", tags)
        self.assertNotIn("1234567890", payload["Event"]["Attribute"][0]["comment"])


if __name__ == "__main__":
    unittest.main()
