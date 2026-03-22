import os
import sys
import unittest

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.evaluation.metrics import (
    calculate_cer,
    calculate_wer,
    calculate_field_precision_recall_f1,
    calculate_numeric_tolerance_pass_rate,
    calculate_numeric_tolerance_pass_rate_profiled,
    calculate_hallucination_rate,
    calculate_routing_accuracy,
)


class TestMetrics(unittest.TestCase):
    def test_cer_wer_zero_on_identical_text(self):
        self.assertEqual(calculate_cer("abc", "abc"), 0.0)
        self.assertEqual(calculate_wer("a b c", "a b c"), 0.0)

    def test_field_precision_recall_f1_with_numeric_tolerance(self):
        extracted = {"revenue": 104.0, "company": "ACME", "extra": "x"}
        truth = {"revenue": 100.0, "company": "ACME"}
        profile = {
            "currency": 0.05,
            "ratio": 0.05,
            "percentage": 0.05,
            "count": 0.0,
            "default": 0.05,
        }

        metrics = calculate_field_precision_recall_f1(
            extracted,
            truth,
            numeric_tolerance=0.05,
            tolerance_profile=profile,
        )
        self.assertAlmostEqual(metrics["precision"], 2 / 3)
        self.assertEqual(metrics["recall"], 1.0)

    def test_numeric_tolerance_pass_rate(self):
        extracted = {"a": 95, "b": 120, "c": "n/a"}
        truth = {"a": 100, "b": 100}
        self.assertAlmostEqual(calculate_numeric_tolerance_pass_rate(extracted, truth, numeric_tolerance=0.05), 0.5)

    def test_hallucination_rate(self):
        extracted = {"a": 1, "b": 2, "c": 3}
        truth = {"a": 1, "b": 2}
        self.assertAlmostEqual(calculate_hallucination_rate(extracted, truth), 1 / 3)

    def test_routing_accuracy(self):
        self.assertEqual(calculate_routing_accuracy(["bank", "gst"], ["bank", "gst"]), 1.0)
        self.assertEqual(calculate_routing_accuracy(["bank", "financial"], ["bank", "gst"]), 0.5)

    def test_profiled_tolerance_is_stricter_for_ratio_than_currency(self):
        extracted = {
            "current_ratio": 1.03,
            "revenue": 101.5,
        }
        truth = {
            "current_ratio": 1.0,
            "revenue": 100.0,
        }

        profile = {
            "ratio": 0.01,
            "currency": 0.03,
            "default": 0.05,
        }
        metrics = calculate_field_precision_recall_f1(
            extracted,
            truth,
            numeric_tolerance=0.05,
            tolerance_profile=profile,
        )
        # revenue should pass (1.5%), current_ratio should fail (3%)
        self.assertAlmostEqual(metrics["precision"], 0.5)
        self.assertAlmostEqual(metrics["recall"], 0.5)

    def test_profiled_numeric_pass_rate_breakdown(self):
        extracted = {
            "current_ratio": 1.02,
            "revenue": 102.0,
            "filings_on_time": 11,
        }
        truth = {
            "current_ratio": 1.0,
            "revenue": 100.0,
            "filings_on_time": 11,
        }
        profile = {
            "ratio": 0.01,
            "currency": 0.03,
            "count": 0.0,
            "default": 0.05,
        }
        result = calculate_numeric_tolerance_pass_rate_profiled(
            extracted,
            truth,
            tolerance_profile=profile,
            numeric_tolerance=0.05,
        )

        self.assertIn("by_class", result)
        self.assertIn("ratio", result["by_class"])
        self.assertIn("currency", result["by_class"])
        self.assertIn("count", result["by_class"])
        self.assertAlmostEqual(result["overall_pass_rate"], 2 / 3)


if __name__ == "__main__":
    unittest.main()
