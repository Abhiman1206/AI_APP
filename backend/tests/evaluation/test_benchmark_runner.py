import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.evaluation.benchmark_runner import run_benchmark


class TestBenchmarkRunner(unittest.TestCase):
    def test_writes_ocr_quality_report(self):
        truth = {
            "doc-1": {
                "document_type": "bank",
                "payload": {"revenue": 100.0},
                "ocr_reference": "abc def",
            }
        }
        extracted = {
            "doc-1": {
                "payload": {"revenue": 101.0},
                "ocr_hypothesis": "abc xyz",
            }
        }

        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp)
            tolerance_profile = {
                "currency": 0.03,
                "ratio": 0.01,
                "percentage": 0.02,
                "count": 0.0,
                "default": 0.05,
            }
            report = run_benchmark(
                extracted_payloads=extracted,
                truth_payloads=truth,
                output_dir=out_dir,
                numeric_tolerance=0.05,
                tolerance_profile=tolerance_profile,
            )

            self.assertIn("ocr_quality", report)
            self.assertIn("worst_hotspots", report["ocr_quality"])
            self.assertIn("numeric_tolerance_by_class", report["by_criterion"]["extraction_accuracy"])
            self.assertEqual(
                report["by_criterion"]["extraction_accuracy"]["tolerance_profile_used"],
                tolerance_profile,
            )
            self.assertTrue((out_dir / "ocr_quality_report.json").exists())


if __name__ == "__main__":
    unittest.main()
