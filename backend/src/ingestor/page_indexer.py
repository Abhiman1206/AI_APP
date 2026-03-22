"""Page-index JSON artifact generator for ingestion outputs.

This module replaces vector-store indexing with deterministic JSON page indexes.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


def _make_document_id(parsed_doc: Dict[str, Any]) -> str:
    file_name = parsed_doc.get("filename", "unknown.pdf")
    file_size = str(parsed_doc.get("file_size_mb", "0"))
    raw = f"{file_name}:{file_size}"
    digest = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12]
    stem = Path(file_name).stem.replace(" ", "_")
    return f"{stem}_{digest}"


def _confidence_hint(rec: Dict[str, Any]) -> str:
    cls = rec.get("classification")
    if cls == "scanned":
        return "low_to_medium"
    if cls in {"financial_table", "multi_column"}:
        return "medium"
    if cls == "narrative_text":
        return "medium_to_high"
    return "low"


def _extract_normalized_values(rec: Dict[str, Any]) -> Dict[str, Any]:
    # Placeholder for downstream numeric normalization integration.
    return {}


def generate_page_index(parsed_doc: Dict[str, Any], output_dir: str) -> Dict[str, Any]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    document_id = _make_document_id(parsed_doc)
    page_routing: List[Dict[str, Any]] = parsed_doc.get("page_routing", [])

    entries: List[Dict[str, Any]] = []
    for rec in page_routing:
        page_no = int(rec.get("page_no", 0))
        section = "financial" if rec.get("relevance_score", 0) > 0 else "general"
        chunk_id = f"{document_id}_p{page_no:04d}"
        entries.append(
            {
                "document_id": document_id,
                "file_name": parsed_doc.get("filename"),
                "page_no": page_no,
                "section": section,
                "chunk_id": chunk_id,
                "extractor": rec.get("extractor"),
                "classification": rec.get("classification"),
                "routing_reason": rec.get("routing_reason"),
                "keywords": rec.get("keywords", []),
                "normalized_values": _extract_normalized_values(rec),
                "text_snippet": rec.get("text_snippet", ""),
                "confidence_hint": _confidence_hint(rec),
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        )

    artifact = {
        "document_id": document_id,
        "file_name": parsed_doc.get("filename"),
        "page_count": parsed_doc.get("page_count", 0),
        "targeted_pages": parsed_doc.get("targeted_pages", 0),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "entries": entries,
    }

    artifact_file = output_path / f"{document_id}.page_index.json"
    artifact_file.write_text(json.dumps(artifact, indent=2, ensure_ascii=True), encoding="utf-8")

    return {
        "document_id": document_id,
        "artifact_path": str(artifact_file),
        "entry_count": len(entries),
    }
