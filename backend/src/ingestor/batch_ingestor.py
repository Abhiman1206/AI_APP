"""Batch Ingestor — processes all PDFs in a directory through the Intelli-Credit pipeline.

This module is the entry point for bulk data ingestion from the Data folder.
It handles:
  - Scanning a directory for PDF files
  - Smart document routing (bank statement / GST return / financial report / other)
  - Per-document parsing and AI extraction
  - Aggregating results across multiple files into a single ingestion payload
    ready for scoring and CAM generation

Usage (programmatic):
    from src.ingestor.batch_ingestor import ingest_directory
    payload = ingest_directory("/path/to/Data")

Usage (standalone script):
    python -m src.ingestor.batch_ingestor --data-dir /path/to/Data
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Optional

from src.ingestor.pdf_parser import parse_pdf_directory
from src.ingestor.page_indexer import generate_page_index
from src.ai_extractor import (
    extract_financial_data,
    extract_gst_data,
    extract_bank_data,
    extract_risk_intelligence,
)

# ---------------------------------------------------------------------------
# Document routing rules
# ---------------------------------------------------------------------------

# Keywords in filenames that classify a PDF as a bank statement
BANK_FILENAME_KEYWORDS = ["bank", "statement", "hdfc", "sbi", "icici", "axis", "kotak", "yes bank"]
# Keywords in filenames that classify a PDF as a GST document
GST_FILENAME_KEYWORDS = ["gst", "gstr", "return", "tax return"]
# Keywords in filenames that classify a PDF as an annual report / financials
FINANCIAL_FILENAME_KEYWORDS = [
    "annual", "report", "financial", "standalone", "consolidated",
    "balance", "itr", "income tax",
]
# Content-level keywords for routing when filename is ambiguous
BANK_CONTENT_KEYWORDS = ["account holder", "opening balance", "closing balance", "bank statement", "cheque"]
GST_CONTENT_KEYWORDS = ["gst number", "gstin", "outward supplies", "inward supplies", "gstr", "tax invoice"]


def _route_document(filename: str, extracted_text: str) -> str:
    """Classify a document into one of: 'bank', 'gst', 'financial', 'other'.

    First tries filename-based classification (fast).
    Falls back to content-based scan for ambiguous filenames.
    """
    fname_lower = filename.lower()

    if any(k in fname_lower for k in BANK_FILENAME_KEYWORDS):
        return "bank"
    if any(k in fname_lower for k in GST_FILENAME_KEYWORDS):
        return "gst"
    if any(k in fname_lower for k in FINANCIAL_FILENAME_KEYWORDS):
        return "financial"

    # Content-based fallback (check first 3,000 chars to stay cheap)
    snippet = extracted_text[:3000].lower()
    if any(k in snippet for k in BANK_CONTENT_KEYWORDS):
        return "bank"
    if any(k in snippet for k in GST_CONTENT_KEYWORDS):
        return "gst"

    return "other"


# ---------------------------------------------------------------------------
# Core batch ingestion function
# ---------------------------------------------------------------------------

def ingest_directory(
    dir_path: str,
    company_name: str = "Unknown",
    gst_number: Optional[str] = None,
) -> dict:
    """Parse and extract structured data from all PDFs in a directory.

    Steps:
    1. Scan directory for PDF files and parse them (text + tables).
    2. Route each PDF to the correct extractor (financial / GST / bank).
    3. Run AI extraction on the aggregated text per category.
    4. Run risk intelligence over the combined corpus.
    5. Return a consolidated ingestion payload.

    Args:
        dir_path: Path to the folder containing PDF files (e.g., the Data folder).
        company_name: Company name (used for risk intelligence prompt).
        gst_number: Known GST number to fall back on if AI cannot find it.

    Returns:
        dict with keys:
            parsed_files       - list of per-file parse metadata
            financial_data     - aggregated financial highlights
            gst_data           - aggregated GST return data
            bank_data          - aggregated bank statement data
            risk_intelligence  - risk signals from the full corpus
            routing_summary    - how many files went to each category
            errors             - list of filenames that failed to parse
    """
    print(f"\n{'='*60}")
    print(f"[batch_ingestor] Starting batch ingestion from: {dir_path}")
    print(f"{'='*60}")

    # Step 1: Parse all PDFs
    parsed_files = parse_pdf_directory(dir_path)

    # Step 2: Route documents and aggregate text per category
    categorized_text: dict[str, list[str]] = {
        "financial": [],
        "bank": [],
        "gst": [],
        "other": [],
    }
    routing_summary: dict[str, list[str]] = {
        "financial": [],
        "bank": [],
        "gst": [],
        "other": [],
    }
    errors: list[str] = []
    page_index_files: list[dict] = []
    all_texts: list[str] = []

    page_index_dir = Path(dir_path) / ".page_index"

    for result in parsed_files:
        fname = result["filename"]
        if result.get("error"):
            errors.append(fname)
            continue

        # Stage 6: Persist page-index JSON artifact per parsed document.
        try:
            index_result = generate_page_index(result, str(page_index_dir))
            result["page_index"] = index_result
            page_index_files.append(index_result)
        except Exception as e:
            print(f"[batch_ingestor] page-index generation error for {fname}: {e}")

        text = result.get("extracted_text", "")
        if not text.strip():
            print(f"[batch_ingestor] WARNING: {fname} yielded empty text, skipping.")
            continue

        category = _route_document(fname, text)
        categorized_text[category].append(text)
        routing_summary[category].append(fname)
        all_texts.append(text)
        print(f"[batch_ingestor] Routed '{fname}' → {category}")

    combined_all = "\n\n--- NEXT DOCUMENT ---\n\n".join(all_texts)

    # Build per-category combined strings; fall back to full corpus if category empty
    fin_text  = "\n\n".join(categorized_text["financial"]) or combined_all
    gst_text  = "\n\n".join(categorized_text["gst"])       or combined_all
    bank_text = "\n\n".join(categorized_text["bank"])      or combined_all

    print(f"\n[batch_ingestor] Routing summary:")
    for cat, fnames in routing_summary.items():
        print(f"  {cat:12s}: {len(fnames)} file(s) — {fnames}")

    # Step 3: AI extraction per category
    print("\n[batch_ingestor] Running AI financial extraction...")
    financial_data: dict = {}
    try:
        financial_data = extract_financial_data(fin_text)
    except Exception as e:
        print(f"[batch_ingestor] financial extraction error: {e}")

    print("\n[batch_ingestor] Running AI GST extraction...")
    gst_data: dict = {}
    try:
        gst_data = extract_gst_data(gst_text)
        # Inject known GST number if AI missed it
        if gst_number and not gst_data.get("gst_number"):
            gst_data["gst_number"] = gst_number
    except Exception as e:
        print(f"[batch_ingestor] GST extraction error: {e}")

    print("\n[batch_ingestor] Running AI bank statement extraction...")
    bank_data: dict = {}
    try:
        bank_data = extract_bank_data(bank_text)
    except Exception as e:
        print(f"[batch_ingestor] bank extraction error: {e}")

    # Step 4: Risk intelligence over the full corpus
    print("\n[batch_ingestor] Running risk intelligence analysis...")
    risk_data: dict = {}
    try:
        risk_data = extract_risk_intelligence(company_name, combined_all)
    except Exception as e:
        print(f"[batch_ingestor] risk intelligence error: {e}")

    print(f"\n[batch_ingestor] Batch ingestion complete. "
          f"{len(all_texts)} documents processed, {len(errors)} errors.\n")

    return {
        "parsed_files": [
            {
                "filename": r["filename"],
                "page_count": r.get("page_count", 0),
                "targeted_pages": r.get("targeted_pages", 0),
                "targeted_page_numbers": r.get("targeted_page_numbers", []),
                "deep_scan_pages": r.get("deep_scan_pages", 0),
                "deep_scan_page_numbers": r.get("deep_scan_page_numbers", []),
                "category": _route_document(r["filename"], r.get("extracted_text", "")),
                "page_index": r.get("page_index"),
                "error": r.get("error"),
            }
            for r in parsed_files
        ],
        "financial_data": financial_data,
        "gst_data": gst_data,
        "bank_data": bank_data,
        "risk_intelligence": risk_data,
        "combined_text": combined_all,
        "routing_summary": routing_summary,
        "page_index_files": page_index_files,
        "errors": errors,
    }


# ---------------------------------------------------------------------------
# CLI entry point for standalone use
# ---------------------------------------------------------------------------

def _cli():
    parser = argparse.ArgumentParser(
        description="Intelli-Credit batch PDF ingestor — processes all PDFs in a directory."
    )
    parser.add_argument(
        "--data-dir",
        required=True,
        help="Path to the directory containing PDF files to ingest.",
    )
    parser.add_argument(
        "--company",
        default="Unknown",
        help="Company name (used for risk prompt). Default: Unknown.",
    )
    parser.add_argument(
        "--gst",
        default=None,
        help="Known GST number (optional fallback if AI extraction misses it).",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Path to write JSON output. If omitted, prints to stdout.",
    )
    args = parser.parse_args()

    # Resolve path relative to CWD
    data_dir = Path(args.data_dir).resolve()
    if not data_dir.is_dir():
        print(f"ERROR: Directory not found: {data_dir}", file=sys.stderr)
        sys.exit(1)

    result = ingest_directory(str(data_dir), company_name=args.company, gst_number=args.gst)

    output_json = json.dumps(result, indent=2, default=str)
    if args.output:
        Path(args.output).write_text(output_json, encoding="utf-8")
        print(f"Output written to {args.output}")
    else:
        print(output_json)


if __name__ == "__main__":
    _cli()
