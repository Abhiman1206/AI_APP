"""One-command Day 2 flow: validate inputs, then run benchmark."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from src.evaluation.benchmark_runner import run_benchmark
from src.evaluation.contract_gate import parse_extraction_thresholds, evaluate_extraction_thresholds
from src.evaluation.validators import (
    validate_manifest,
    validate_annotation_directory,
    validate_benchmark_payload_integrity,
    load_manifest_doc_ids,
)


def _load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"JSON object expected at {path}")
    return data


def _parse_reporting_contract(contract_path: Path) -> dict[str, Any]:
    """Parse minimal reporting settings from criteria_contract.yaml without extra dependencies."""
    if not contract_path.exists():
        return {
            "required_outputs": [
                "summary.json",
                "by_criterion.json",
                "by_doc_type.json",
                "ocr_quality_report.json",
                "failures.csv",
            ],
            "fail_on_missing_outputs": True,
        }

    lines = contract_path.read_text(encoding="utf-8").splitlines()
    required_outputs: list[str] = []
    fail_on_missing_outputs = True

    in_required_outputs = False
    required_indent = None

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        indent = len(line) - len(line.lstrip(" "))

        if stripped.startswith("required_outputs:"):
            in_required_outputs = True
            required_indent = indent
            continue

        if in_required_outputs:
            if indent <= (required_indent or 0) and not stripped.startswith("-"):
                in_required_outputs = False
            elif stripped.startswith("-"):
                required_outputs.append(stripped[1:].strip())
                continue

        if stripped.startswith("fail_on_missing_outputs:"):
            value = stripped.split(":", 1)[1].strip().lower()
            fail_on_missing_outputs = value in {"true", "1", "yes"}

    if not required_outputs:
        required_outputs = [
            "summary.json",
            "by_criterion.json",
            "by_doc_type.json",
            "ocr_quality_report.json",
            "failures.csv",
        ]

    return {
        "required_outputs": required_outputs,
        "fail_on_missing_outputs": fail_on_missing_outputs,
    }


def _validate_required_outputs(output_dir: Path, required_outputs: list[str]) -> list[str]:
    missing: list[str] = []
    for filename in required_outputs:
        if not (output_dir / filename).exists():
            missing.append(filename)
    return missing


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Day 2 validation and benchmark in one command")
    parser.add_argument("--project-root", default=".", help="Backend project root path")
    parser.add_argument("--manifest", default="evaluation/datasets/manifest.json")
    parser.add_argument("--annotations-dir", default="evaluation/datasets/annotations")
    parser.add_argument("--ground-truth", default="evaluation/reports/sample_ground_truth.json")
    parser.add_argument("--extracted", default="evaluation/reports/sample_extracted.json")
    parser.add_argument("--output-dir", default="evaluation/reports")
    parser.add_argument("--numeric-tolerance", type=float, default=0.05)
    parser.add_argument("--tolerance-profile", default="evaluation/config/tolerance_profile.json")
    parser.add_argument("--contract", default="evaluation/criteria_contract.yaml")
    parser.add_argument("--enforce-thresholds", action="store_true", help="Fail run when extraction thresholds are violated")
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    manifest_path = Path(args.manifest)
    annotations_dir = Path(args.annotations_dir)
    ground_truth_path = Path(args.ground_truth)
    extracted_path = Path(args.extracted)
    tolerance_profile_path = Path(args.tolerance_profile)
    output_dir = Path(args.output_dir)
    contract_path = Path(args.contract)

    reporting = _parse_reporting_contract(contract_path)

    issues: list[str] = []

    manifest_issues = validate_manifest(manifest_path, project_root=project_root)
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

    if issues:
        print(json.dumps({"ok": False, "issue_count": len(issues), "issues": issues}, indent=2))
        raise SystemExit(1)

    truth = _load_json(ground_truth_path)
    extracted = _load_json(extracted_path)
    tolerance_profile = None
    if tolerance_profile_path.exists():
        tolerance_profile = _load_json(tolerance_profile_path)

    report = run_benchmark(
        extracted_payloads=extracted,
        truth_payloads=truth,
        output_dir=output_dir,
        numeric_tolerance=args.numeric_tolerance,
        tolerance_profile=tolerance_profile,
    )

    thresholds = parse_extraction_thresholds(contract_path)
    threshold_issues = evaluate_extraction_thresholds(report["summary"], thresholds)

    if args.enforce_thresholds and threshold_issues:
        print(json.dumps(
            {
                "ok": False,
                "issue_count": len(threshold_issues),
                "issues": threshold_issues,
            },
            indent=2,
        ))
        raise SystemExit(1)

    if reporting.get("fail_on_missing_outputs", True):
        missing_outputs = _validate_required_outputs(
            output_dir=output_dir,
            required_outputs=list(reporting.get("required_outputs", [])),
        )
        if missing_outputs:
            print(json.dumps(
                {
                    "ok": False,
                    "issue_count": len(missing_outputs),
                    "issues": [f"missing required output: {name}" for name in missing_outputs],
                },
                indent=2,
            ))
            raise SystemExit(1)

    print(json.dumps(
        {
            "ok": True,
            "doc_count": int(report["summary"]["doc_count"]),
            "f1": report["summary"]["f1"],
            "hallucination_rate": report["summary"]["hallucination_rate"],
            "output_dir": str(output_dir.resolve()),
            "required_outputs_checked": reporting.get("required_outputs", []),
            "threshold_enforced": bool(args.enforce_thresholds),
            "threshold_issues": threshold_issues,
        },
        indent=2,
    ))


if __name__ == "__main__":
    main()
