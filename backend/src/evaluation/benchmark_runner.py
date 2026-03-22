"""Benchmark runner for extraction-quality evaluation artifacts."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.evaluation.metrics import score_document, calculate_numeric_tolerance_pass_rate_profiled
from src.evaluation.validators import validate_benchmark_payload_integrity


def _read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"JSON payload at {path} must be an object keyed by doc_id")
    return data


def _aggregate(doc_results: list[dict[str, Any]]) -> dict[str, float]:
    if not doc_results:
        return {
            "doc_count": 0,
            "precision": 0.0,
            "recall": 0.0,
            "f1": 0.0,
            "numeric_tolerance_pass_rate": 0.0,
            "hallucination_rate": 0.0,
            "ocr_cer": 0.0,
            "ocr_wer": 0.0,
        }

    keys = [
        "precision",
        "recall",
        "f1",
        "numeric_tolerance_pass_rate",
        "numeric_tolerance_pass_rate_profiled",
        "hallucination_rate",
        "ocr_cer",
        "ocr_wer",
    ]
    out: dict[str, float] = {"doc_count": float(len(doc_results))}
    for key in keys:
        out[key] = sum(float(row["metrics"][key]) for row in doc_results) / len(doc_results)
    return out


def _criterion_view(
    summary: dict[str, float],
    tolerance_profile: dict[str, float] | None = None,
    numeric_tolerance_by_class: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "extraction_accuracy": {
            "field_f1": summary["f1"],
            "numeric_tolerance_pass_rate": summary["numeric_tolerance_pass_rate"],
            "numeric_tolerance_pass_rate_profiled": summary["numeric_tolerance_pass_rate_profiled"],
            "numeric_tolerance_by_class": numeric_tolerance_by_class or {},
            "tolerance_profile_used": tolerance_profile or {},
            "ocr_cer": summary["ocr_cer"],
            "hallucination_rate": summary["hallucination_rate"],
        }
    }


def _percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    if pct <= 0:
        return min(values)
    if pct >= 100:
        return max(values)
    ordered = sorted(values)
    idx = int(round((pct / 100.0) * (len(ordered) - 1)))
    return ordered[idx]


def _build_ocr_quality_report(doc_results: list[dict[str, Any]]) -> dict[str, Any]:
    if not doc_results:
        return {
            "summary": {
                "doc_count": 0,
                "avg_cer": 0.0,
                "avg_wer": 0.0,
                "p90_cer": 0.0,
                "p90_wer": 0.0,
                "max_cer": 0.0,
                "max_wer": 0.0,
            },
            "by_doc_type": {},
            "per_doc": [],
        }

    cer_values = [float(row["metrics"]["ocr_cer"]) for row in doc_results]
    wer_values = [float(row["metrics"]["ocr_wer"]) for row in doc_results]

    by_type: dict[str, list[dict[str, Any]]] = {}
    per_doc: list[dict[str, Any]] = []

    for row in doc_results:
        doc_type = row["document_type"]
        by_type.setdefault(doc_type, []).append(row)
        ref_chars = int(row["ocr_reference_chars"])
        hyp_chars = int(row["ocr_hypothesis_chars"])
        char_delta = hyp_chars - ref_chars
        ref_tokens = int(row["ocr_reference_tokens"])
        hyp_tokens = int(row["ocr_hypothesis_tokens"])
        token_delta = hyp_tokens - ref_tokens
        per_doc.append(
            {
                "doc_id": row["doc_id"],
                "document_type": row["document_type"],
                "ocr_reference_chars": ref_chars,
                "ocr_hypothesis_chars": hyp_chars,
                "ocr_char_delta": char_delta,
                "ocr_char_delta_ratio": (char_delta / ref_chars) if ref_chars > 0 else 0.0,
                "ocr_reference_tokens": ref_tokens,
                "ocr_hypothesis_tokens": hyp_tokens,
                "ocr_token_delta": token_delta,
                "ocr_token_delta_ratio": (token_delta / ref_tokens) if ref_tokens > 0 else 0.0,
                "ocr_cer": row["metrics"]["ocr_cer"],
                "ocr_wer": row["metrics"]["ocr_wer"],
            }
        )

    by_doc_type = {}
    for doc_type, rows in by_type.items():
        type_cer = [float(r["metrics"]["ocr_cer"]) for r in rows]
        type_wer = [float(r["metrics"]["ocr_wer"]) for r in rows]
        by_doc_type[doc_type] = {
            "doc_count": len(rows),
            "avg_cer": sum(type_cer) / len(type_cer),
            "avg_wer": sum(type_wer) / len(type_wer),
            "p90_cer": _percentile(type_cer, 90),
            "p90_wer": _percentile(type_wer, 90),
            "max_cer": max(type_cer),
            "max_wer": max(type_wer),
        }

    return {
        "summary": {
            "doc_count": len(doc_results),
            "avg_cer": sum(cer_values) / len(cer_values),
            "avg_wer": sum(wer_values) / len(wer_values),
            "p90_cer": _percentile(cer_values, 90),
            "p90_wer": _percentile(wer_values, 90),
            "max_cer": max(cer_values),
            "max_wer": max(wer_values),
        },
        "by_doc_type": by_doc_type,
        "per_doc": sorted(per_doc, key=lambda row: float(row["ocr_cer"]), reverse=True),
        "worst_hotspots": {
            "highest_cer_doc": max(per_doc, key=lambda row: float(row["ocr_cer"]))["doc_id"],
            "highest_wer_doc": max(per_doc, key=lambda row: float(row["ocr_wer"]))["doc_id"],
            "largest_char_delta_doc": max(per_doc, key=lambda row: abs(float(row["ocr_char_delta_ratio"])))["doc_id"],
            "largest_token_delta_doc": max(per_doc, key=lambda row: abs(float(row["ocr_token_delta_ratio"])))["doc_id"],
        },
    }


def _aggregate_numeric_tolerance_by_class(
    extracted_payloads: dict[str, Any],
    truth_payloads: dict[str, Any],
    tolerance_profile: dict[str, float] | None,
    numeric_tolerance: float,
) -> dict[str, Any]:
    bucket_totals: dict[str, dict[str, int]] = {}

    for doc_id, truth in truth_payloads.items():
        extracted = extracted_payloads.get(doc_id)
        if extracted is None:
            continue

        profile_result = calculate_numeric_tolerance_pass_rate_profiled(
            extracted_payload=extracted.get("payload", extracted),
            truth_payload=truth.get("payload", truth),
            tolerance_profile=tolerance_profile,
            numeric_tolerance=numeric_tolerance,
        )
        by_class = profile_result.get("by_class", {})
        for cls, stats in by_class.items():
            bucket = bucket_totals.setdefault(cls, {"passed": 0, "total": 0})
            bucket["passed"] += int(stats.get("passed", 0))
            bucket["total"] += int(stats.get("total", 0))

    return {
        cls: {
            "passed": vals["passed"],
            "total": vals["total"],
            "pass_rate": (vals["passed"] / vals["total"]) if vals["total"] else 1.0,
        }
        for cls, vals in bucket_totals.items()
    }


def run_benchmark(
    extracted_payloads: dict[str, Any],
    truth_payloads: dict[str, Any],
    output_dir: Path,
    numeric_tolerance: float,
    tolerance_profile: dict[str, float] | None = None,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)

    integrity_issues = validate_benchmark_payload_integrity_from_objects(
        truth_payloads=truth_payloads,
        extracted_payloads=extracted_payloads,
    )
    if integrity_issues:
        raise ValueError("Benchmark payload integrity validation failed: " + " | ".join(integrity_issues))

    doc_results: list[dict[str, Any]] = []
    failures: list[dict[str, str]] = []

    for doc_id, truth in truth_payloads.items():
        extracted = extracted_payloads.get(doc_id)
        if extracted is None:
            failures.append({"doc_id": doc_id, "reason": "missing extracted payload"})
            continue

        ocr_reference = str(truth.get("ocr_reference", ""))
        ocr_hypothesis = str(extracted.get("ocr_hypothesis", ""))
        metrics = score_document(
            extracted_payload=extracted.get("payload", extracted),
            truth_payload=truth.get("payload", truth),
            ocr_reference=ocr_reference,
            ocr_hypothesis=ocr_hypothesis,
            numeric_tolerance=numeric_tolerance,
            tolerance_profile=tolerance_profile,
        )
        doc_type = str(truth.get("document_type", "unknown"))
        doc_results.append(
            {
                "doc_id": doc_id,
                "document_type": doc_type,
                "metrics": metrics,
                "ocr_reference_chars": len(ocr_reference),
                "ocr_hypothesis_chars": len(ocr_hypothesis),
                "ocr_reference_tokens": len(ocr_reference.split()),
                "ocr_hypothesis_tokens": len(ocr_hypothesis.split()),
            }
        )

    summary = _aggregate(doc_results)

    by_doc_type: dict[str, list[dict[str, Any]]] = {}
    for row in doc_results:
        by_doc_type.setdefault(row["document_type"], []).append(row)

    by_doc_type_agg = {
        doc_type: _aggregate(rows)
        for doc_type, rows in by_doc_type.items()
    }

    numeric_tolerance_by_class = _aggregate_numeric_tolerance_by_class(
        extracted_payloads=extracted_payloads,
        truth_payloads=truth_payloads,
        tolerance_profile=tolerance_profile,
        numeric_tolerance=numeric_tolerance,
    )

    report = {
        "summary": summary,
        "by_criterion": _criterion_view(
            summary,
            tolerance_profile=tolerance_profile,
            numeric_tolerance_by_class=numeric_tolerance_by_class,
        ),
        "by_doc_type": by_doc_type_agg,
        "ocr_quality": _build_ocr_quality_report(doc_results),
        "doc_results": doc_results,
        "failures": failures,
    }

    (output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2),
        encoding="utf-8",
    )
    (output_dir / "by_criterion.json").write_text(
        json.dumps(report["by_criterion"], indent=2),
        encoding="utf-8",
    )
    (output_dir / "by_doc_type.json").write_text(
        json.dumps(by_doc_type_agg, indent=2),
        encoding="utf-8",
    )
    (output_dir / "ocr_quality_report.json").write_text(
        json.dumps(report["ocr_quality"], indent=2),
        encoding="utf-8",
    )

    generated_files = [
        "summary.json",
        "by_criterion.json",
        "by_doc_type.json",
        "ocr_quality_report.json",
        "failures.csv",
    ]
    run_manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "output_dir": str(output_dir.resolve()),
        "generated_files": generated_files,
        "doc_count": int(summary["doc_count"]),
        "f1": summary["f1"],
        "hallucination_rate": summary["hallucination_rate"],
    }
    (output_dir / "run_manifest.json").write_text(
        json.dumps(run_manifest, indent=2),
        encoding="utf-8",
    )

    with (output_dir / "failures.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["doc_id", "reason"])
        writer.writeheader()
        for row in failures:
            writer.writerow(row)

    return report


def validate_benchmark_payload_integrity_from_objects(
    truth_payloads: dict[str, Any],
    extracted_payloads: dict[str, Any],
) -> list[str]:
    """In-memory integrity checks used by run_benchmark and tests."""
    issues: list[str] = []

    truth_doc_ids = set(truth_payloads.keys())
    extracted_doc_ids = set(extracted_payloads.keys())

    missing_extracted = truth_doc_ids - extracted_doc_ids
    if missing_extracted:
        issues.append(f"missing extracted payloads for doc_ids: {', '.join(sorted(missing_extracted))}")

    missing_truth = extracted_doc_ids - truth_doc_ids
    if missing_truth:
        issues.append(f"missing ground-truth payloads for doc_ids: {', '.join(sorted(missing_truth))}")

    for doc_id, payload in truth_payloads.items():
        if not isinstance(payload, dict):
            issues.append(f"ground-truth[{doc_id}] must be an object")
            continue
        if "payload" not in payload:
            issues.append(f"ground-truth[{doc_id}] missing required key 'payload'")

    for doc_id, payload in extracted_payloads.items():
        if not isinstance(payload, dict):
            issues.append(f"extracted[{doc_id}] must be an object")
            continue
        if "payload" not in payload:
            issues.append(f"extracted[{doc_id}] missing required key 'payload'")

    return issues


def main() -> None:
    parser = argparse.ArgumentParser(description="Run extraction benchmark and emit standard artifacts")
    parser.add_argument("--ground-truth", required=True, help="Path to ground-truth JSON keyed by doc_id")
    parser.add_argument("--extracted", required=True, help="Path to extracted JSON keyed by doc_id")
    parser.add_argument("--output-dir", default="backend/evaluation/reports", help="Artifact output directory")
    parser.add_argument("--numeric-tolerance", type=float, default=0.05, help="Relative tolerance for numeric fields")
    parser.add_argument("--tolerance-profile", default=None, help="Optional JSON file with per-field-class tolerances")
    parser.add_argument("--skip-integrity-check", action="store_true", help="Skip file-level payload integrity checks")
    args = parser.parse_args()

    ground_truth_path = Path(args.ground_truth)
    extracted_path = Path(args.extracted)

    if not args.skip_integrity_check:
        issues = validate_benchmark_payload_integrity(
            ground_truth_path=ground_truth_path,
            extracted_path=extracted_path,
        )
        if issues:
            raise ValueError("Benchmark payload integrity validation failed: " + " | ".join(issues))

    truth = _read_json(ground_truth_path)
    extracted = _read_json(extracted_path)
    tolerance_profile = None
    if args.tolerance_profile:
        tolerance_profile = _read_json(Path(args.tolerance_profile))

    report = run_benchmark(
        extracted_payloads=extracted,
        truth_payloads=truth,
        output_dir=Path(args.output_dir),
        numeric_tolerance=args.numeric_tolerance,
        tolerance_profile=tolerance_profile,
    )

    print(json.dumps(
        {
            "doc_count": int(report["summary"]["doc_count"]),
            "f1": report["summary"]["f1"],
            "hallucination_rate": report["summary"]["hallucination_rate"],
            "output_dir": str(Path(args.output_dir).resolve()),
        },
        indent=2,
    ))


if __name__ == "__main__":
    main()
