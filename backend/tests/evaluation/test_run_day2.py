import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.evaluation.run_day2 import _parse_reporting_contract, _validate_required_outputs


class TestRunDay2Contract(unittest.TestCase):
    def test_parse_reporting_contract_defaults_when_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            missing_contract = Path(tmp) / "missing.yaml"
            parsed = _parse_reporting_contract(missing_contract)
            self.assertTrue(parsed["fail_on_missing_outputs"])
            self.assertIn("summary.json", parsed["required_outputs"])
            self.assertIn("ocr_quality_report.json", parsed["required_outputs"])

    def test_parse_reporting_contract_reads_required_outputs(self):
        content = """\
reporting:
  required_outputs:
    - summary.json
    - custom.json
  fail_on_missing_outputs: false
"""
        with tempfile.TemporaryDirectory() as tmp:
            contract = Path(tmp) / "criteria_contract.yaml"
            contract.write_text(content, encoding="utf-8")
            parsed = _parse_reporting_contract(contract)
            self.assertEqual(parsed["required_outputs"], ["summary.json", "custom.json"])
            self.assertFalse(parsed["fail_on_missing_outputs"])

    def test_validate_required_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            (out / "summary.json").write_text("{}", encoding="utf-8")
            missing = _validate_required_outputs(out, ["summary.json", "by_doc_type.json"])
            self.assertEqual(missing, ["by_doc_type.json"])


if __name__ == "__main__":
    unittest.main()
