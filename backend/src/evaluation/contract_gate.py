"""Contract threshold parsing and enforcement utilities."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def parse_extraction_thresholds(contract_path: Path) -> dict[str, float]:
    """Parse extraction_accuracy numeric thresholds from criteria_contract.yaml."""
    defaults = {
        "field_f1_min": 0.0,
        "numeric_tolerance_pass_rate_min": 0.0,
        "ocr_cer_max": 1.0,
        "hallucination_rate_max": 1.0,
    }
    if not contract_path.exists():
        return defaults

    lines = contract_path.read_text(encoding="utf-8").splitlines()
    in_extraction = False
    in_thresholds = False
    extraction_indent = 0
    thresholds_indent = 0

    out = dict(defaults)

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        indent = len(line) - len(line.lstrip(" "))

        if stripped.startswith("extraction_accuracy:"):
            in_extraction = True
            in_thresholds = False
            extraction_indent = indent
            continue

        if in_extraction and indent <= extraction_indent and not stripped.startswith("extraction_accuracy:"):
            in_extraction = False
            in_thresholds = False

        if in_extraction and stripped.startswith("thresholds:"):
            in_thresholds = True
            thresholds_indent = indent
            continue

        if in_thresholds and indent <= thresholds_indent and not stripped.startswith("-"):
            in_thresholds = False

        if in_thresholds and ":" in stripped:
            key, val = stripped.split(":", 1)
            key = key.strip()
            val = val.strip()
            if key in out:
                try:
                    out[key] = float(val)
                except ValueError:
                    pass

    return out


def evaluate_extraction_thresholds(summary: dict[str, Any], thresholds: dict[str, float]) -> list[str]:
    """Return human-readable issues if summary metrics violate threshold contract."""
    issues: list[str] = []

    f1 = float(summary.get("f1", 0.0))
    if f1 < float(thresholds.get("field_f1_min", 0.0)):
        issues.append(
            f"field_f1 below threshold: {f1:.6f} < {float(thresholds.get('field_f1_min', 0.0)):.6f}"
        )

    numeric_pass = float(summary.get("numeric_tolerance_pass_rate", 0.0))
    if numeric_pass < float(thresholds.get("numeric_tolerance_pass_rate_min", 0.0)):
        issues.append(
            "numeric_tolerance_pass_rate below threshold: "
            f"{numeric_pass:.6f} < {float(thresholds.get('numeric_tolerance_pass_rate_min', 0.0)):.6f}"
        )

    ocr_cer = float(summary.get("ocr_cer", 1.0))
    if ocr_cer > float(thresholds.get("ocr_cer_max", 1.0)):
        issues.append(
            f"ocr_cer above threshold: {ocr_cer:.6f} > {float(thresholds.get('ocr_cer_max', 1.0)):.6f}"
        )

    hallucination = float(summary.get("hallucination_rate", 1.0))
    if hallucination > float(thresholds.get("hallucination_rate_max", 1.0)):
        issues.append(
            "hallucination_rate above threshold: "
            f"{hallucination:.6f} > {float(thresholds.get('hallucination_rate_max', 1.0)):.6f}"
        )

    return issues
