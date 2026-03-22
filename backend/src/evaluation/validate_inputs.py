"""CLI for Day 2 validation: manifest, annotations, and benchmark payload integrity."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.evaluation.validators import (
    validate_manifest,
    validate_annotation_directory,
    validate_benchmark_payload_integrity,
    load_manifest_doc_ids,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate evaluation inputs before benchmark execution")
    parser.add_argument("--project-root", default=".", help="Backend project root path")
    parser.add_argument("--manifest", required=True, help="Manifest JSON path")
    parser.add_argument("--annotations-dir", required=True, help="Directory of annotation JSON files")
    parser.add_argument("--ground-truth", required=True, help="Ground-truth benchmark payload JSON")
    parser.add_argument("--extracted", required=True, help="Extracted benchmark payload JSON")
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    manifest_path = Path(args.manifest)
    annotations_dir = Path(args.annotations_dir)
    ground_truth_path = Path(args.ground_truth)
    extracted_path = Path(args.extracted)

    issues: list[str] = []

    manifest_issues = validate_manifest(manifest_path=manifest_path, project_root=project_root)
    issues.extend([f"manifest: {msg}" for msg in manifest_issues])

    expected_doc_ids = load_manifest_doc_ids(manifest_path) if not manifest_issues else None
    annotation_issues = validate_annotation_directory(
        annotations_dir=annotations_dir,
        expected_doc_ids=expected_doc_ids,
    )
    issues.extend([f"annotations: {msg}" for msg in annotation_issues])

    integrity_issues = validate_benchmark_payload_integrity(
        ground_truth_path=ground_truth_path,
        extracted_path=extracted_path,
        required_doc_ids=expected_doc_ids,
    )
    issues.extend([f"payloads: {msg}" for msg in integrity_issues])

    report = {
        "ok": len(issues) == 0,
        "issue_count": len(issues),
        "issues": issues,
    }
    print(json.dumps(report, indent=2))

    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
