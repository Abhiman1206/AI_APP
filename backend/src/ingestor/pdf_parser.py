"""PDF parser for large-document ingestion using Docling + RapidOCR.

Implements a staged extraction flow aligned to large-report ingestion:
- Stage 1: preflight metadata and text-layer estimation
- Stage 2: per-page classification and extractor routing lineage
- Stage 3/4: priority-page targeting for deep extraction on large PDFs
- RapidOCR-only OCR path (PaddleOCR removed)
"""

from __future__ import annotations

import os
import importlib
import re
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pdfplumber

fitz = None
try:
    fitz = importlib.import_module("fitz")  # PyMuPDF
    FITZ_AVAILABLE = True
except ImportError:
    FITZ_AVAILABLE = False

# Docling for structure-aware parsing
try:
    DocumentConverter = importlib.import_module("docling.document_converter").DocumentConverter
    InputFormat = importlib.import_module("docling.datamodel.base_models").InputFormat
    PdfPipelineOptions = importlib.import_module("docling.datamodel.pipeline_options").PdfPipelineOptions
    DOCLING_AVAILABLE = True
except ImportError:
    print("[pdf_parser] WARNING: Docling not available. Install with: pip install docling")
    DOCLING_AVAILABLE = False

# RapidOCR (only OCR engine in this parser)
try:
    from rapidocr import RapidOCR

    RAPIDOCR_AVAILABLE = True
except ImportError:
    print("[pdf_parser] WARNING: RapidOCR not available. Install with: pip install rapidocr onnxruntime")
    RAPIDOCR_AVAILABLE = False


PAGE_CLASS_NARRATIVE = "narrative_text"
PAGE_CLASS_FINANCIAL_TABLE = "financial_table"
PAGE_CLASS_MULTI_COLUMN = "multi_column"
PAGE_CLASS_SCANNED = "scanned"
PAGE_CLASS_CHART_FILLER = "chart_or_filler"
PAGE_CLASS_OTHER = "other"


HIGH_VALUE_KEYWORDS = [
    "balance sheet",
    "profit & loss",
    "profit and loss",
    "statement of cash flow",
    "cash flows",
    "financial statements",
    "income statement",
    "auditor's report",
    "independent auditor",
    "liability",
    "assets",
    "revenue from operations",
    "other income",
    "total income",
    "total expenses",
    "earnings per share",
    "ebitda",
    "net profit",
    "gross profit",
    "operating profit",
    "notes to accounts",
    "notes to financial",
    "significant accounting policies",
    "current liabilities",
    "non-current liabilities",
    "shareholders equity",
    "capital work in progress",
    "fixed assets",
    "tangible net worth",
    "property plant and equipment",
    "gstr",
    "tax invoice",
    "input tax credit",
    "output tax",
    "turnover",
    "net worth",
    "paid-up capital",
    "borrowings",
    "secured loan",
    "unsecured loan",
    "term loan",
    "depreciation",
    "amortization",
    "contingent liabilities",
    "consolidated",
    "standalone",
    "financial highlights",
    "key financial indicators",
    "debt service coverage",
    "dscr",
    "working capital",
]

PRIORITY_PAGE_KEYWORDS = [
    "balance sheet",
    "statement of profit",
    "profit and loss",
    "cash flow",
    "notes to accounts",
    "auditor",
    "management discussion",
    "mda",
    "md&a",
]

SECTION_CHUNK_CHARS = 18_000
SECTION_CHUNK_OVERLAP = 1_200

_rapid_ocr = None


def _get_rapid_ocr():
    global _rapid_ocr
    if _rapid_ocr is None and RAPIDOCR_AVAILABLE:
        try:
            _rapid_ocr = RapidOCR()
            print("[pdf_parser] RapidOCR initialized successfully")
        except Exception as e:
            print(f"[pdf_parser] RapidOCR initialization failed: {e}")
    return _rapid_ocr


def _contains_devanagari(text: str) -> bool:
    return bool(re.search(r"[\u0900-\u097F]", text or ""))


def _score_page_relevance(text: str) -> float:
    text_lower = (text or "").lower()
    return float(sum(text_lower.count(kw) for kw in HIGH_VALUE_KEYWORDS))


def _looks_multi_column(text: str) -> bool:
    if not text:
        return False
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if len(lines) < 5:
        return False
    split_candidates = 0
    for ln in lines[:30]:
        if re.search(r"\s{4,}\S+", ln):
            split_candidates += 1
    return split_candidates >= 4


def _classify_page(text: str, table_count: int) -> Tuple[str, str]:
    text_len = len((text or "").strip())
    relevance = _score_page_relevance(text)
    multi_col = _looks_multi_column(text)

    if text_len < 40 and table_count == 0:
        return PAGE_CLASS_CHART_FILLER, "low_text_density"
    if table_count > 0 and relevance > 0:
        return PAGE_CLASS_FINANCIAL_TABLE, "table_plus_financial_keywords"
    if table_count > 0:
        return PAGE_CLASS_MULTI_COLUMN, "table_detected"
    if multi_col and relevance > 0:
        return PAGE_CLASS_MULTI_COLUMN, "multi_column_with_financial_terms"
    if text_len < 120:
        return PAGE_CLASS_SCANNED, "likely_scanned_or_image_text"
    if relevance > 0:
        return PAGE_CLASS_NARRATIVE, "financial_narrative"
    if text_len > 0:
        return PAGE_CLASS_NARRATIVE, "generic_narrative"
    return PAGE_CLASS_OTHER, "unclassified"


def _select_extractor(classification: str) -> str:
    if classification == PAGE_CLASS_CHART_FILLER:
        return "skip"
    if classification in {PAGE_CLASS_FINANCIAL_TABLE, PAGE_CLASS_MULTI_COLUMN} and DOCLING_AVAILABLE:
        return "docling"
    if classification == PAGE_CLASS_SCANNED and RAPIDOCR_AVAILABLE:
        return "rapidocr"
    return "pdfplumber"


def _looks_like_heading(line: str) -> bool:
    clean = (line or "").strip()
    if not clean or len(clean) < 4 or len(clean) > 120:
        return False
    if re.search(r"\d{3,}", clean):
        return False
    heading_words = [
        "balance sheet",
        "statement of",
        "profit and loss",
        "cash flow",
        "notes to",
        "management discussion",
        "financial highlights",
        "share capital",
        "borrowings",
    ]
    lowered = clean.lower()
    if any(w in lowered for w in heading_words):
        return True
    mostly_upper = sum(1 for ch in clean if ch.isalpha() and ch.isupper())
    total_alpha = sum(1 for ch in clean if ch.isalpha())
    if total_alpha >= 6 and (mostly_upper / max(total_alpha, 1)) >= 0.7:
        return True
    return bool(re.match(r"^(?:\d+\.?)+\s+[A-Za-z].+", clean))


def _extract_heading_candidate(text: str) -> Optional[str]:
    for line in (text or "").splitlines()[:12]:
        line = line.strip()
        if _looks_like_heading(line):
            return line
    return None


def _chunk_with_overlap(text: str, chunk_chars: int = SECTION_CHUNK_CHARS, overlap: int = SECTION_CHUNK_OVERLAP) -> List[str]:
    clean = (text or "").strip()
    if not clean:
        return []
    if len(clean) <= chunk_chars:
        return [clean]

    chunks: List[str] = []
    start = 0
    while start < len(clean):
        end = min(len(clean), start + chunk_chars)
        chunk = clean[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(clean):
            break
        start = max(0, end - overlap)
    return chunks


def _serialize_pdfplumber_tables(tables: List[List[List[Any]]], page_no: int) -> List[Dict[str, Any]]:
    serialized: List[Dict[str, Any]] = []
    for table in tables:
        if not table or len(table) <= 1:
            continue
        headers = [str(h).strip() if h else f"col_{j}" for j, h in enumerate(table[0])]
        rows: List[Dict[str, str]] = []
        for row in table[1:]:
            row_dict = {
                headers[j] if j < len(headers) else f"col_{j}": str(cell).strip() if cell else ""
                for j, cell in enumerate(row)
            }
            if any(v for v in row_dict.values()):
                rows.append(row_dict)
        if rows:
            serialized.append({"page": page_no, "headers": headers, "rows": rows})
    return serialized


def _extract_with_docling(file_path: str, max_pages: Optional[int] = None) -> Optional[Dict[str, Any]]:
    if not DOCLING_AVAILABLE:
        return None

    try:
        pipeline_options = PdfPipelineOptions()
        pipeline_options.do_ocr = False
        pipeline_options.do_table_structure = True

        converter = DocumentConverter(format_options={InputFormat.PDF: pipeline_options})
        print(f"[pdf_parser] Starting Docling conversion for {Path(file_path).name}")
        result = converter.convert(file_path)

        full_text = result.document.export_to_markdown()
        tables = []
        for table in result.document.tables:
            tables.append(
                {
                    "page": getattr(table, "page_no", None),
                    "text": table.export_to_markdown() if hasattr(table, "export_to_markdown") else str(table),
                    "rows": [],
                }
            )

        page_count = len(result.document.pages) if hasattr(result.document, "pages") else 0
        if max_pages is not None and page_count > max_pages:
            page_count = max_pages

        return {
            "text": full_text,
            "tables": tables,
            "page_count": page_count,
            "metadata": {"method": "docling", "has_tables": len(tables) > 0},
        }
    except Exception as e:
        print(f"[pdf_parser] Docling extraction failed: {e}")
        traceback.print_exc()
        return None


def _preflight_pdf(file_path: str, max_pages: Optional[int] = None) -> Dict[str, Any]:
    file_size_mb = Path(file_path).stat().st_size / (1024 * 1024)
    with pdfplumber.open(file_path) as pdf:
        total_pages = len(pdf.pages)
        pages_to_scan = min(total_pages, max_pages) if max_pages else total_pages

        sample_count = min(10, pages_to_scan)
        if sample_count <= 0:
            sample_indices: List[int] = []
        elif sample_count == pages_to_scan:
            sample_indices = list(range(pages_to_scan))
        else:
            step = max(1, pages_to_scan // sample_count)
            sample_indices = sorted(set(min(i * step, pages_to_scan - 1) for i in range(sample_count)))

        sampled_chars: List[int] = []
        text_layer_pages = 0
        devnagari_hits = 0
        for idx in sample_indices:
            text = pdf.pages[idx].extract_text() or ""
            txt_len = len(text.strip())
            sampled_chars.append(txt_len)
            if txt_len > 50:
                text_layer_pages += 1
            if _contains_devanagari(text):
                devnagari_hits += 1

    avg_chars = (sum(sampled_chars) / len(sampled_chars)) if sampled_chars else 0.0
    scanned_ratio = 1.0 - (text_layer_pages / len(sampled_chars)) if sampled_chars else 1.0
    language_hints = ["en"]
    if devnagari_hits > 0:
        language_hints.append("hi")

    return {
        "file_size_mb": round(file_size_mb, 2),
        "page_count": total_pages,
        "sampled_pages": len(sampled_chars),
        "avg_chars_per_sampled_page": round(avg_chars, 2),
        "text_layer_detected": text_layer_pages > 0,
        "text_layer_page_ratio": round((text_layer_pages / len(sampled_chars)) if sampled_chars else 0.0, 3),
        "scanned_page_ratio_estimate": round(scanned_ratio, 3),
        "language_hints": language_hints,
    }


def _build_page_routing(
    file_path: str, max_pages: Optional[int] = None
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[int, str]]:
    page_records: List[Dict[str, Any]] = []
    all_tables: List[Dict[str, Any]] = []
    page_text_map: Dict[int, str] = {}

    with pdfplumber.open(file_path) as pdf:
        pages_to_process = min(len(pdf.pages), max_pages) if max_pages else len(pdf.pages)

        for idx in range(pages_to_process):
            page_no = idx + 1
            page = pdf.pages[idx]
            text = page.extract_text() or ""
            page_text_map[page_no] = text
            tables = page.extract_tables() or []
            table_count = len(tables)
            classification, routing_reason = _classify_page(text, table_count)
            relevance = _score_page_relevance(text)

            if table_count:
                all_tables.extend(_serialize_pdfplumber_tables(tables, page_no))

            page_records.append(
                {
                    "page_no": page_no,
                    "classification": classification,
                    "routing_reason": routing_reason,
                    "extractor": _select_extractor(classification),
                    "text_length": len(text.strip()),
                    "table_count": table_count,
                    "relevance_score": relevance,
                    "text_snippet": text.strip().replace("\n", " ")[:500],
                    "keywords": [kw for kw in HIGH_VALUE_KEYWORDS if kw in text.lower()][:20],
                }
            )

    return page_records, all_tables, page_text_map


def _select_target_pages(page_records: List[Dict[str, Any]], page_count: int) -> List[int]:
    if page_count <= 200:
        return [rec["page_no"] - 1 for rec in page_records]

    priority_candidates = [
        rec
        for rec in page_records
        if any(kw in rec["text_snippet"].lower() for kw in PRIORITY_PAGE_KEYWORDS)
        or rec["classification"] in {PAGE_CLASS_FINANCIAL_TABLE, PAGE_CLASS_MULTI_COLUMN}
    ]
    priority_sorted = sorted(priority_candidates, key=lambda r: r["relevance_score"], reverse=True)
    priority_pages = {rec["page_no"] - 1 for rec in priority_sorted[:30]}

    scored = sorted(page_records, key=lambda r: r["relevance_score"], reverse=True)
    top_100 = {rec["page_no"] - 1 for rec in scored[:100]}

    return sorted(priority_pages.union(top_100))


def _assemble_text_from_pages(
    page_records: List[Dict[str, Any]],
    target_page_indices: List[int],
    page_text_map: Optional[Dict[int, str]] = None,
) -> Tuple[str, List[int], int]:
    target_set = set(target_page_indices)
    selected_parts: List[str] = []
    pages_to_ocr: List[int] = []
    section_count = 0
    current_section_title = "General"
    current_section_pages: List[int] = []
    current_section_blocks: List[str] = []

    def _flush_section() -> None:
        nonlocal section_count
        if not current_section_blocks:
            return
        section_count += 1
        page_span = (
            f"{current_section_pages[0]}-{current_section_pages[-1]}"
            if len(current_section_pages) > 1
            else str(current_section_pages[0])
        )
        section_text = "\n\n".join(current_section_blocks)
        chunked = _chunk_with_overlap(section_text)
        for chunk_idx, chunk in enumerate(chunked, 1):
            selected_parts.append(
                f"=== Section {section_count}: {current_section_title} | Pages {page_span} | Chunk {chunk_idx}/{len(chunked)} ===\n{chunk}"
            )

    for rec in page_records:
        page_idx = rec["page_no"] - 1
        if page_idx not in target_set:
            continue

        cls = rec["classification"]
        if cls == PAGE_CLASS_CHART_FILLER:
            continue

        raw_page_text = ""
        if page_text_map:
            raw_page_text = (page_text_map.get(rec["page_no"]) or "").strip()
        snippet = rec.get("text_snippet", "")
        page_text = raw_page_text or snippet

        heading = _extract_heading_candidate(page_text)
        if heading and current_section_blocks:
            _flush_section()
            current_section_pages = []
            current_section_blocks = []
        if heading:
            current_section_title = heading

        if page_text:
            current_section_blocks.append(f"--- Page {rec['page_no']} ({cls}) ---\n{page_text}")
            current_section_pages.append(rec["page_no"])

        if cls == PAGE_CLASS_SCANNED or rec.get("text_length", 0) < 80:
            pages_to_ocr.append(page_idx)

    _flush_section()
    return "\n\n".join(selected_parts), sorted(set(pages_to_ocr)), section_count


def _extract_with_rapid_ocr(file_path: str, page_indices: List[int]) -> str:
    if not page_indices:
        return ""
    if not RAPIDOCR_AVAILABLE:
        print("[pdf_parser] RapidOCR not available, skipping OCR")
        return ""
    if not FITZ_AVAILABLE:
        print("[pdf_parser] PyMuPDF not available, cannot render OCR images")
        return ""

    ocr_engine = _get_rapid_ocr()
    if ocr_engine is None:
        return ""

    try:
        doc = fitz.open(file_path)
        ocr_texts: List[str] = []

        for page_idx in page_indices:
            if page_idx >= len(doc):
                continue
            page = doc.load_page(page_idx)
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
            img_bytes = pix.tobytes("png")

            result = ocr_engine(img_bytes)
            page_lines: List[str] = []
            txts = getattr(result, "txts", None)
            if txts:
                page_lines = [str(t).strip() for t in txts if str(t).strip()]

            if page_lines:
                ocr_texts.append(f"--- OCR Page {page_idx + 1} ---\n" + "\n".join(page_lines))

        doc.close()
        return "\n\n".join(ocr_texts)
    except Exception as e:
        print(f"[pdf_parser] RapidOCR failed: {e}")
        return ""


def parse_pdf(file_path: str, use_ocr: bool = True, max_pages: Optional[int] = None) -> dict:
    """Parse a PDF with preflight, page routing, priority targeting, and RapidOCR fallback."""
    file_name = os.path.basename(file_path)
    print(f"\n[pdf_parser] Processing: {file_name}")

    preflight = _preflight_pdf(file_path, max_pages=max_pages)
    page_records, fallback_tables, page_text_map = _build_page_routing(file_path, max_pages=max_pages)

    page_count = preflight["page_count"]
    target_pages = _select_target_pages(page_records, page_count)
    assembled_text, pages_to_ocr, section_count = _assemble_text_from_pages(
        page_records,
        target_pages,
        page_text_map=page_text_map,
    )

    # Docling is preferred for complex table/multi-column documents when available.
    docling_result = None
    has_complex_layout = any(
        rec["classification"] in {PAGE_CLASS_FINANCIAL_TABLE, PAGE_CLASS_MULTI_COLUMN} for rec in page_records
    )
    if DOCLING_AVAILABLE and has_complex_layout:
        docling_result = _extract_with_docling(file_path, max_pages=max_pages)

    ocr_text = ""
    if use_ocr:
        # Run OCR only on target pages that look scanned.
        ocr_pages = [idx for idx in pages_to_ocr if idx in set(target_pages)]
        ocr_text = _extract_with_rapid_ocr(file_path, ocr_pages)

    base_text = assembled_text
    tables = fallback_tables
    all_page_numbers = list(range(1, page_count + 1))
    deep_scan_page_numbers = [idx + 1 for idx in target_pages]

    metadata: Dict[str, Any] = {
        "method": "pdfplumber-routing",
        "preflight": preflight,
        "page_class_counts": {
            PAGE_CLASS_NARRATIVE: sum(1 for r in page_records if r["classification"] == PAGE_CLASS_NARRATIVE),
            PAGE_CLASS_FINANCIAL_TABLE: sum(1 for r in page_records if r["classification"] == PAGE_CLASS_FINANCIAL_TABLE),
            PAGE_CLASS_MULTI_COLUMN: sum(1 for r in page_records if r["classification"] == PAGE_CLASS_MULTI_COLUMN),
            PAGE_CLASS_SCANNED: sum(1 for r in page_records if r["classification"] == PAGE_CLASS_SCANNED),
            PAGE_CLASS_CHART_FILLER: sum(1 for r in page_records if r["classification"] == PAGE_CLASS_CHART_FILLER),
            PAGE_CLASS_OTHER: sum(1 for r in page_records if r["classification"] == PAGE_CLASS_OTHER),
        },
        "priority_page_numbers": sorted([idx + 1 for idx in target_pages[:30]]),
        "deep_scan_pages": len(target_pages),
        "deep_scan_page_numbers": deep_scan_page_numbers,
        "section_count": section_count,
        "assembled_chunk_count": assembled_text.count("=== Section "),
    }

    if docling_result and docling_result.get("text"):
        base_text = docling_result["text"]
        if docling_result.get("tables"):
            tables = docling_result["tables"]
        metadata["method"] = "docling+routing"

    combined_text = base_text
    if ocr_text:
        combined_text += f"\n\n=== RAPIDOCR EXTRACTED TEXT ===\n{ocr_text}"

    return {
        "filename": file_name,
        "page_count": page_count,
        "targeted_pages": page_count,
        "targeted_page_numbers": all_page_numbers,
        "deep_scan_pages": len(target_pages),
        "deep_scan_page_numbers": deep_scan_page_numbers,
        "extracted_text": combined_text,
        "tables": tables,
        "page_routing": page_records,
        "metadata": metadata,
        "file_size_mb": preflight["file_size_mb"],
    }


def parse_pdf_directory(
    dir_path: str,
    extensions: tuple = (".pdf",),
    use_parallel: bool = True,
    max_workers: int = 3,
) -> list:
    """Scan a directory and parse all matching PDF files."""
    results: List[Dict[str, Any]] = []
    path_obj = Path(dir_path)

    if not path_obj.is_dir():
        raise ValueError(f"Not a directory: {path_obj}")

    pdf_files = sorted([f for f in path_obj.iterdir() if f.is_file() and f.suffix.lower() in extensions])

    print(f"\n[batch] Found {len(pdf_files)} PDF file(s) in {path_obj}")
    print(f"[batch] Parallel processing: {use_parallel} (workers: {max_workers})")

    if use_parallel and len(pdf_files) > 1:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_file = {executor.submit(parse_pdf, str(pdf_file)): pdf_file for pdf_file in pdf_files}

            for i, future in enumerate(as_completed(future_to_file), 1):
                pdf_file = future_to_file[future]
                print(f"\n[batch] Progress: {i}/{len(pdf_files)} - {pdf_file.name}")
                try:
                    results.append(future.result())
                except Exception as e:
                    print(f"[batch] ERROR parsing {pdf_file.name}: {e}")
                    results.append(
                        {
                            "filename": pdf_file.name,
                            "page_count": 0,
                            "targeted_pages": 0,
                            "targeted_page_numbers": [],
                            "extracted_text": "",
                            "tables": [],
                            "page_routing": [],
                            "metadata": {},
                            "error": str(e),
                        }
                    )
    else:
        for i, pdf_file in enumerate(pdf_files, 1):
            print(f"\n[batch] Processing {i}/{len(pdf_files)}: {pdf_file.name}")
            try:
                results.append(parse_pdf(str(pdf_file)))
            except Exception as e:
                print(f"[batch] ERROR parsing {pdf_file.name}: {e}")
                traceback.print_exc()
                results.append(
                    {
                        "filename": pdf_file.name,
                        "page_count": 0,
                        "targeted_pages": 0,
                        "targeted_page_numbers": [],
                        "extracted_text": "",
                        "tables": [],
                        "page_routing": [],
                        "metadata": {},
                        "error": str(e),
                    }
                )

    print(
        f"\n[batch] Completed: {len([r for r in results if not r.get('error')])} successful, "
        f"{len([r for r in results if r.get('error')])} errors"
    )

    return results
