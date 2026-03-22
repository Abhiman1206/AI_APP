"""Evaluation utilities for extraction benchmark and criteria tracking."""

from src.evaluation.metrics import (
    calculate_cer,
    calculate_wer,
    calculate_field_precision_recall_f1,
    calculate_numeric_tolerance_pass_rate,
    calculate_hallucination_rate,
    calculate_routing_accuracy,
)
from src.evaluation.validators import (
    validate_manifest,
    validate_annotation_file,
    validate_annotation_directory,
    validate_benchmark_payload_integrity,
    load_manifest_doc_ids,
)
from src.evaluation.contract_gate import (
    parse_extraction_thresholds,
    evaluate_extraction_thresholds,
)

__all__ = [
    "calculate_cer",
    "calculate_wer",
    "calculate_field_precision_recall_f1",
    "calculate_numeric_tolerance_pass_rate",
    "calculate_hallucination_rate",
    "calculate_routing_accuracy",
    "validate_manifest",
    "validate_annotation_file",
    "validate_annotation_directory",
    "validate_benchmark_payload_integrity",
    "load_manifest_doc_ids",
    "parse_extraction_thresholds",
    "evaluate_extraction_thresholds",
]
