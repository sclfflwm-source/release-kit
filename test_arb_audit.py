import json
import tempfile
import unittest
from pathlib import Path

from arb_audit import audit, main


class ArbAuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def write(self, name, data):
        path = self.root / name
        path.write_text(json.dumps(data), encoding="utf-8")
        return path

    def test_reports_missing_extra_and_placeholder_mismatch(self):
        source = self.write("app_en.arb", {
            "@@locale": "en", "hello": "Hi {name}", "count": "{count} items",
            "@hello": {"description": "Greeting"},
        })
        target = self.write("app_ko.arb", {
            "@@locale": "ko", "hello": "안녕 {person}", "other": "기타",
        })
        issues = audit(source, [target])
        self.assertEqual(
            [(item["kind"], item["key"]) for item in issues],
            [("missing-key", "count"), ("extra-key", "other"),
             ("placeholder-mismatch", "hello")],
        )

    def test_valid_translation_passes(self):
        source = self.write("app_en.arb", {"hello": "Hi {name}"})
        target = self.write("app_ko.arb", {"hello": "{name}님 안녕하세요"})
        self.assertEqual(main([str(source), str(target)]), 0)

    def test_invalid_message_fails_with_input_error(self):
        source = self.write("app_en.arb", {"hello": 42})
        target = self.write("app_ko.arb", {"hello": "안녕"})
        self.assertEqual(main([str(source), str(target)]), 2)


if __name__ == "__main__":
    unittest.main()
