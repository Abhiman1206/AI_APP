"""Metrics for extraction benchmark and quality reporting."""

from __future__ import annotations

from typing import Any


DEFAULT_TOLERANCE_PROFILE: dict[str, float] = {
    "currency": 0.03,
    "ratio": 0.01,
    "percentage": 0.02,
    "count": 0.0,
    "default": 0.05,
}


def _levenshtein_distance(a: str, b: str) -> int:
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)

    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, start=1):
        curr = [i]
        for j, cb in enumerate(b, start=1):
            cost = 0 if ca == cb else 1
            curr.append(min(
                prev[j] + 1,      # deletion
                curr[j - 1] + 1,  # insertion
                prev[j - 1] + cost,  # substitution
            ))
        prev = curr
    return prev[-1]


def calculate_cer(reference: str, hypothesis: str) -> float:
    """Character error rate: edit distance / length(reference)."""
    ref = reference or ""
    hyp = hypothesis or ""
    if not ref:
        return 0.0 if not hyp else 1.0
    return _levenshtein_distance(ref, hyp) / len(ref)


def calculate_wer(reference: str, hypothesis: str) -> float:
    """Word error rate: edit distance on whitespace tokens / token count(reference)."""
    ref_tokens = (reference or "").split()
    hyp_tokens = (hypothesis or "").split()
    if not ref_tokens:
        return 0.0 if not hyp_tokens else 1.0
    return _levenshtein_distance("\n".join(ref_tokens), "\n".join(hyp_tokens)) / len(ref_tokens)


def _flatten(obj: Any, prefix: str = "") -> dict[str, Any]:
    flat: dict[str, Any] = {}
    if isinstance(obj, dict):
        for key, value in obj.items():
            child = f"{prefix}.{key}" if prefix else str(key)
            flat.update(_flatten(value, child))
    elif isinstance(obj, list):
        for idx, value in enumerate(obj):
            child = f"{prefix}[{idx}]"
            flat.update(_flatten(value, child))
    else:
        flat[prefix] = obj
    return flat


def _is_empty(value: Any) -> bool:
    return value is None or value == "" or value == [] or value == {}


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _classify_numeric_field(field_name: str) -> str:
    lowered = field_name.lower()
    if any(token in lowered for token in ["ratio", "dte", "debt_to_equity", "current_ratio", "margin"]):
        return "ratio"
    if any(token in lowered for token in ["pct", "percent", "percentage"]):
        return "percentage"
    if any(token in lowered for token in ["count", "total_cases", "filings_on_time", "filings_late", "filings_missed"]):
        return "count"
    if any(token in lowered for token in ["revenue", "profit", "assets", "liabilities", "turnover", "inr", "amount", "credits", "debits", "balance"]):
        return "currency"
    return "default"


def _resolve_tolerance(field_name: str, numeric_tolerance: float, tolerance_profile: dict[str, float] | None) -> float:
    profile = tolerance_profile or DEFAULT_TOLERANCE_PROFILE
    field_class = _classify_numeric_field(field_name)
    if field_class in profile:
        return float(profile[field_class])
    if "default" in profile:
        return float(profile["default"])
    return numeric_tolerance


def _values_match(
    field_name: str,
    extracted: Any,
    truth: Any,
    numeric_tolerance: float,
    tolerance_profile: dict[str, float] | None,
) -> bool:
    if _is_number(extracted) and _is_number(truth):
        tolerance = _resolve_tolerance(field_name, numeric_tolerance, tolerance_profile)
        truth_abs = abs(float(truth))
        if truth_abs == 0.0:
            return abs(float(extracted)) <= tolerance
        return abs(float(extracted) - float(truth)) / truth_abs <= tolerance
    return extracted == truth


def calculate_field_precision_recall_f1(
    extracted_payload: dict[str, Any],
    truth_payload: dict[str, Any],
    numeric_tolerance: float = 0.05,
    tolerance_profile: dict[str, float] | None = None,
) -> dict[str, float]:
    """Compute field-level precision/recall/F1 on flattened payloads."""
    extracted = _flatten(extracted_payload)
    truth = _flatten(truth_payload)

    extracted_keys = {k for k, v in extracted.items() if not _is_empty(v)}
    truth_keys = {k for k, v in truth.items() if not _is_empty(v)}

    if not extracted_keys and not truth_keys:
        return {"precision": 1.0, "recall": 1.0, "f1": 1.0}

    true_pos = 0
    for key in extracted_keys & truth_keys:
        if _values_match(key, extracted[key], truth[key], numeric_tolerance, tolerance_profile):
            true_pos += 1

    false_pos = len(extracted_keys) - true_pos
    false_neg = len(truth_keys) - true_pos

    precision = true_pos / (true_pos + false_pos) if (true_pos + false_pos) else 0.0
    recall = true_pos / (true_pos + false_neg) if (true_pos + false_neg) else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0

    return {"precision": precision, "recall": recall, "f1": f1}


def calculate_numeric_tolerance_pass_rate(
    extracted_payload: dict[str, Any],
    truth_payload: dict[str, Any],
    numeric_tolerance: float = 0.05,
    tolerance_profile: dict[str, float] | None = None,
) -> float:
    """Share of numeric ground-truth fields matching within tolerance."""
    extracted = _flatten(extracted_payload)
    truth = _flatten(truth_payload)

    numeric_keys = [k for k, v in truth.items() if _is_number(v)]
    if not numeric_keys:
        return 1.0

    passed = 0
    for key in numeric_keys:
        if key not in extracted or not _is_number(extracted[key]):
            continue
        if _values_match(key, extracted[key], truth[key], numeric_tolerance, tolerance_profile):
            passed += 1
    return passed / len(numeric_keys)


def calculate_numeric_tolerance_pass_rate_profiled(
    extracted_payload: dict[str, Any],
    truth_payload: dict[str, Any],
    tolerance_profile: dict[str, float] | None = None,
    numeric_tolerance: float = 0.05,
) -> dict[str, Any]:
    """Return overall numeric pass rate and per-field-class pass rates."""
    extracted = _flatten(extracted_payload)
    truth = _flatten(truth_payload)

    buckets: dict[str, dict[str, int]] = {}
    overall_total = 0
    overall_passed = 0

    for key, truth_val in truth.items():
        if not _is_number(truth_val):
            continue

        field_class = _classify_numeric_field(key)
        bucket = buckets.setdefault(field_class, {"passed": 0, "total": 0})
        bucket["total"] += 1
        overall_total += 1

        extracted_val = extracted.get(key)
        if _is_number(extracted_val) and _values_match(key, extracted_val, truth_val, numeric_tolerance, tolerance_profile):
            bucket["passed"] += 1
            overall_passed += 1

    by_class = {
        cls: {
            "passed": stats["passed"],
            "total": stats["total"],
            "pass_rate": (stats["passed"] / stats["total"]) if stats["total"] else 1.0,
        }
        for cls, stats in buckets.items()
    }

    return {
        "overall_pass_rate": (overall_passed / overall_total) if overall_total else 1.0,
        "by_class": by_class,
    }


def calculate_hallucination_rate(extracted_payload: dict[str, Any], truth_payload: dict[str, Any]) -> float:
    """Rate of non-empty extracted fields not present in truth field set."""
    extracted = _flatten(extracted_payload)
    truth = _flatten(truth_payload)

    extracted_keys = {k for k, v in extracted.items() if not _is_empty(v)}
    truth_keys = {k for k, v in truth.items() if not _is_empty(v)}

    if not extracted_keys:
        return 0.0

    hallucinated = extracted_keys - truth_keys
    return len(hallucinated) / len(extracted_keys)


def calculate_routing_accuracy(predicted_labels: list[str], true_labels: list[str]) -> float:
    """Simple classification accuracy for routing labels."""
    if len(predicted_labels) != len(true_labels):
        raise ValueError("predicted_labels and true_labels must have identical length")
    if not true_labels:
        return 1.0
    correct = sum(1 for p, t in zip(predicted_labels, true_labels) if p == t)
    return correct / len(true_labels)


def score_document(
    extracted_payload: dict[str, Any],
    truth_payload: dict[str, Any],
    ocr_reference: str = "",
    ocr_hypothesis: str = "",
    numeric_tolerance: float = 0.05,
    tolerance_profile: dict[str, float] | None = None,
) -> dict[str, float]:
    """Compute a standard metric bundle for one document."""
    prf = calculate_field_precision_recall_f1(
        extracted_payload,
        truth_payload,
        numeric_tolerance=numeric_tolerance,
        tolerance_profile=tolerance_profile,
    )
    numeric_profiled = calculate_numeric_tolerance_pass_rate_profiled(
        extracted_payload,
        truth_payload,
        tolerance_profile=tolerance_profile,
        numeric_tolerance=numeric_tolerance,
    )
    return {
        **prf,
        "numeric_tolerance_pass_rate": calculate_numeric_tolerance_pass_rate(
            extracted_payload,
            truth_payload,
            numeric_tolerance=numeric_tolerance,
            tolerance_profile=tolerance_profile,
        ),
        "numeric_tolerance_pass_rate_profiled": numeric_profiled["overall_pass_rate"],
        "hallucination_rate": calculate_hallucination_rate(extracted_payload, truth_payload),
        "ocr_cer": calculate_cer(ocr_reference, ocr_hypothesis),
        "ocr_wer": calculate_wer(ocr_reference, ocr_hypothesis),
    }
