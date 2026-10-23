import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fraudlens.core import from_misp_attribute, normalize_value
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


if __name__ == "__main__":
    unittest.main()
