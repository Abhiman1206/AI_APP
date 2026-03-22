import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.evaluation.validators import (
    validate_manifest,
    validate_annotation_file,
    validate_benchmark_payload_integrity,
)


class TestValidators(unittest.TestCase):
    def test_manifest_valid(self):
        project_root = Path(__file__).resolve().parents[2]
        manifest_path = project_root / "evaluation/datasets/manifest.json"
        issues = validate_manifest(manifest_path, project_root=project_root)
        self.assertEqual(issues, [])

    def test_annotation_file_valid(self):
        annotation_path = Path(__file__).resolve().parents[2] / "evaluation/datasets/annotations/seed-bank-001.json"
        issues = validate_annotation_file(annotation_path)
        self.assertEqual(issues, [])

    def test_payload_integrity_catches_missing_doc(self):
        with tempfile.TemporaryDirectory() as tmp:
            gt = Path(tmp) / "gt.json"
            ex = Path(tmp) / "ex.json"
            gt.write_text('{"a": {"payload": {"x": 1}}}', encoding="utf-8")
            ex.write_text('{"b": {"payload": {"x": 1}}}', encoding="utf-8")
            issues = validate_benchmark_payload_integrity(gt, ex)
            self.assertTrue(any("missing extracted payloads" in msg for msg in issues))
            self.assertTrue(any("missing ground-truth payloads" in msg for msg in issues))


if __name__ == "__main__":
    unittest.main()
