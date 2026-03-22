import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.evaluation.contract_gate import parse_extraction_thresholds, evaluate_extraction_thresholds


class TestContractGate(unittest.TestCase):
    def test_parse_extraction_thresholds(self):
        with tempfile.TemporaryDirectory() as tmp:
            contract = Path(tmp) / "criteria_contract.yaml"
            contract.write_text(
                """\
criteria:
  extraction_accuracy:
    thresholds:
      field_f1_min: 0.95
      numeric_tolerance_pass_rate_min: 0.90
      ocr_cer_max: 0.10
      hallucination_rate_max: 0.02
""",
                encoding="utf-8",
            )
            parsed = parse_extraction_thresholds(contract)
            self.assertEqual(parsed["field_f1_min"], 0.95)
            self.assertEqual(parsed["numeric_tolerance_pass_rate_min"], 0.90)
            self.assertEqual(parsed["ocr_cer_max"], 0.10)
            self.assertEqual(parsed["hallucination_rate_max"], 0.02)

    def test_evaluate_thresholds_reports_violations(self):
        summary = {
            "f1": 0.8,
            "numeric_tolerance_pass_rate": 0.7,
            "ocr_cer": 0.2,
            "hallucination_rate": 0.1,
        }
        thresholds = {
            "field_f1_min": 0.95,
            "numeric_tolerance_pass_rate_min": 0.95,
            "ocr_cer_max": 0.08,
            "hallucination_rate_max": 0.03,
        }
        issues = evaluate_extraction_thresholds(summary, thresholds)
        self.assertEqual(len(issues), 4)


if __name__ == "__main__":
    unittest.main()
