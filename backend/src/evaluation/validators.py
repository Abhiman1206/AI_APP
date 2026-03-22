"""Validation helpers for evaluation manifest, annotations, and benchmark inputs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ALLOWED_DOC_TYPES = {"bank", "gst", "financial", "other"}
ALLOWED_SCAN_TYPES = {"scanned", "native", "mixed"}
ALLOWED_SPLITS = {"calibration", "evaluation", "holdout"}


def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def validate_manifest(manifest_path: Path, project_root: Path) -> list[str]:
    issues: list[str] = []
    if not manifest_path.exists():
        return [f"manifest file not found: {manifest_path}"]

    data = _load_json(manifest_path)
    if not isinstance(data, dict):
        return ["manifest must be a JSON object"]

    split_policy = data.get("split_policy")
    if not isinstance(split_policy, dict):
        issues.append("split_policy must be an object")
    else:
        expected = ["calibration", "evaluation", "holdout"]
        missing = [k for k in expected if k not in split_policy]
        if missing:
            issues.append(f"split_policy missing keys: {', '.join(missing)}")
        else:
            total = float(split_policy["calibration"]) + float(split_policy["evaluation"]) + float(split_policy["holdout"])
            if abs(total - 1.0) > 1e-6:
                issues.append(f"split_policy must sum to 1.0, found {total}")

    documents = data.get("documents")
    if not isinstance(documents, list) or not documents:
        issues.append("documents must be a non-empty list")
        return issues

    seen_doc_ids: set[str] = set()
    for idx, doc in enumerate(documents):
        prefix = f"documents[{idx}]"
        if not isinstance(doc, dict):
            issues.append(f"{prefix} must be an object")
            continue

        doc_id = doc.get("doc_id")
        if not isinstance(doc_id, str) or not doc_id.strip():
            issues.append(f"{prefix}.doc_id must be a non-empty string")
        elif doc_id in seen_doc_ids:
            issues.append(f"duplicate doc_id detected: {doc_id}")
        else:
            seen_doc_ids.add(doc_id)

        doc_type = doc.get("document_type")
        if doc_type not in ALLOWED_DOC_TYPES:
            issues.append(f"{prefix}.document_type must be one of {sorted(ALLOWED_DOC_TYPES)}")

        scan_type = doc.get("scan_type")
        if scan_type not in ALLOWED_SCAN_TYPES:
            issues.append(f"{prefix}.scan_type must be one of {sorted(ALLOWED_SCAN_TYPES)}")

        split = doc.get("split")
        if split not in ALLOWED_SPLITS:
            issues.append(f"{prefix}.split must be one of {sorted(ALLOWED_SPLITS)}")

        rel_path = doc.get("relative_path")
        if not isinstance(rel_path, str) or not rel_path.strip():
            issues.append(f"{prefix}.relative_path must be a non-empty string")
        else:
            doc_path = project_root / rel_path
            if not doc_path.exists():
                issues.append(f"{prefix}.relative_path does not exist: {rel_path}")

    return issues


def _validate_annotation_shape(annotation: dict[str, Any]) -> list[str]:
    issues: list[str] = []

    for key in ["doc_id", "document_type", "scan_type", "fields"]:
        if key not in annotation:
            issues.append(f"missing required key: {key}")

    doc_type = annotation.get("document_type")
    if doc_type is not None and doc_type not in ALLOWED_DOC_TYPES:
        issues.append(f"document_type must be one of {sorted(ALLOWED_DOC_TYPES)}")

    scan_type = annotation.get("scan_type")
    if scan_type is not None and scan_type not in ALLOWED_SCAN_TYPES:
        issues.append(f"scan_type must be one of {sorted(ALLOWED_SCAN_TYPES)}")

    fields = annotation.get("fields")
    if not isinstance(fields, list) or not fields:
        issues.append("fields must be a non-empty list")
        return issues

    for i, field in enumerate(fields):
        prefix = f"fields[{i}]"
        if not isinstance(field, dict):
            issues.append(f"{prefix} must be an object")
            continue
        if "name" not in field or not isinstance(field["name"], str) or not field["name"].strip():
            issues.append(f"{prefix}.name must be a non-empty string")
        if "value" not in field:
            issues.append(f"{prefix}.value is required")
        criticality = field.get("criticality")
        if criticality is not None and criticality not in {"critical", "important", "nice_to_have"}:
            issues.append(f"{prefix}.criticality has invalid value")
        page = field.get("page")
        if page is not None and (not isinstance(page, int) or page < 1):
            issues.append(f"{prefix}.page must be an integer >= 1 when present")

    return issues


def validate_annotation_file(annotation_path: Path) -> list[str]:
    if not annotation_path.exists():
        return [f"annotation file not found: {annotation_path}"]

    data = _load_json(annotation_path)
    if not isinstance(data, dict):
        return ["annotation must be a JSON object"]
    return _validate_annotation_shape(data)


def validate_annotation_directory(annotations_dir: Path, expected_doc_ids: set[str] | None = None) -> list[str]:
    issues: list[str] = []
    if not annotations_dir.exists():
        return [f"annotations directory not found: {annotations_dir}"]

    files = sorted(annotations_dir.glob("*.json"))
    if not files:
        issues.append("no annotation JSON files found")
        return issues

    seen_doc_ids: set[str] = set()
    for path in files:
        file_issues = validate_annotation_file(path)
        issues.extend([f"{path.name}: {msg}" for msg in file_issues])
        if file_issues:
            continue
        data = _load_json(path)
        doc_id = str(data.get("doc_id"))
        if doc_id in seen_doc_ids:
            issues.append(f"duplicate annotation doc_id across files: {doc_id}")
        seen_doc_ids.add(doc_id)

    if expected_doc_ids is not None:
        missing = expected_doc_ids - seen_doc_ids
        if missing:
            issues.append(f"missing annotation doc_ids: {', '.join(sorted(missing))}")

    return issues


def validate_benchmark_payload_integrity(
    ground_truth_path: Path,
    extracted_path: Path,
    required_doc_ids: set[str] | None = None,
) -> list[str]:
    issues: list[str] = []
    if not ground_truth_path.exists():
        issues.append(f"ground-truth file not found: {ground_truth_path}")
        return issues
    if not extracted_path.exists():
        issues.append(f"extracted file not found: {extracted_path}")
        return issues

    truth = _load_json(ground_truth_path)
    extracted = _load_json(extracted_path)
    if not isinstance(truth, dict):
        issues.append("ground-truth payload must be an object keyed by doc_id")
        return issues
    if not isinstance(extracted, dict):
        issues.append("extracted payload must be an object keyed by doc_id")
        return issues

    truth_doc_ids = set(truth.keys())
    extracted_doc_ids = set(extracted.keys())

    missing_extracted = truth_doc_ids - extracted_doc_ids
    if missing_extracted:
        issues.append(f"missing extracted payloads for doc_ids: {', '.join(sorted(missing_extracted))}")

    missing_truth = extracted_doc_ids - truth_doc_ids
    if missing_truth:
        issues.append(f"missing ground-truth payloads for doc_ids: {', '.join(sorted(missing_truth))}")

    for doc_id, payload in truth.items():
        if not isinstance(payload, dict):
            issues.append(f"ground-truth[{doc_id}] must be an object")
            continue
        if "payload" not in payload:
            issues.append(f"ground-truth[{doc_id}] missing required key 'payload'")

    for doc_id, payload in extracted.items():
        if not isinstance(payload, dict):
            issues.append(f"extracted[{doc_id}] must be an object")
            continue
        if "payload" not in payload:
            issues.append(f"extracted[{doc_id}] missing required key 'payload'")

    if required_doc_ids is not None:
        missing_required = required_doc_ids - truth_doc_ids
        if missing_required:
            issues.append(f"required doc_ids missing from ground-truth: {', '.join(sorted(missing_required))}")

    return issues


def load_manifest_doc_ids(manifest_path: Path) -> set[str]:
    data = _load_json(manifest_path)
    docs = data.get("documents", []) if isinstance(data, dict) else []
    doc_ids: set[str] = set()
    for doc in docs:
        if isinstance(doc, dict) and isinstance(doc.get("doc_id"), str) and doc["doc_id"].strip():
            doc_ids.add(doc["doc_id"])
    return doc_ids
