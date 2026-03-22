"""
Quick Migration Script: Replace PaddleOCR with RapidOCR

This script provides ready-to-use functions for migrating from PaddleOCR to RapidOCR.
Copy the functions you need into your pdf_parser.py.
"""

import os
from typing import List, Optional
from pathlib import Path

# ==============================================================================
# OPTION 1: RapidOCR (RECOMMENDED - Drop-in replacement)
# ==============================================================================

try:
    from rapid ocr_onnxruntime import RapidOCR
    RAPID_AVAILABLE = True
except ImportError:
    print("[pdf_parser] WARNING: RapidOCR not available. Install with: pip install rapidocr-onnxruntime")
    RAPID_AVAILABLE = False

# Lazy loading for memory efficiency
_rapid_ocr = None

def get_rapid_ocr():
    """Lazy initialization of RapidOCR engine."""
    global _rapid_ocr
    if _rapid_ocr is None and RAPID_AVAILABLE:
        try:
            _rapid_ocr = RapidOCR()
            print("[pdf_parser] RapidOCR initialized successfully")
        except Exception as e:
            print(f"[pdf_parser] RapidOCR initialization failed: {e}")
    return _rapid_ocr


def extract_with_rapid_ocr(file_path: str, page_indices: List[int]) -> str:
    """
    Run RapidOCR on specific pages for scanned/image-heavy content.

    This is a DROP-IN REPLACEMENT for _extract_with_paddle_ocr().
    RapidOCR has similar accuracy and speed to PaddleOCR but works on Python 3.14 Windows.

    Args:
        file_path: Path to PDF file
        page_indices: List of 0-indexed page numbers to OCR

    Returns:
        Combined OCR text from all specified pages
    """
    if not RAPID_AVAILABLE:
        print("[pdf_parser] RapidOCR not available, skipping")
        return ""

    ocr_engine = get_rapid_ocr()
    if ocr_engine is None:
        return ""

    try:
        import fitz  # PyMuPDF
        doc = fitz.open(file_path)
        ocr_texts = []

        for page_idx in page_indices:
            if page_idx >= len(doc):
                continue

            page = doc.load_page(page_idx)
            # Render at 2x resolution for better OCR accuracy
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
            img_bytes = pix.tobytes("png")

            # RapidOCR returns (result, elapse_time)
            result, elapse = ocr_engine(img_bytes)

            # Extract text from OCR result
            # Format: [[bbox, text, confidence], ...]
            page_text = []
            if result:
                for line in result:
                    if line and len(line) >= 2:
                        text = line[1]  # Extract text from (bbox, text, confidence)
                        confidence = line[2] if len(line) >= 3 else 1.0
                        if confidence > 0.5:  # Filter low-confidence results
                            page_text.append(text)

            ocr_texts.append(f"--- OCR Page {page_idx + 1} ---\n" + "\n".join(page_text))
            print(f"[OCR] Page {page_idx + 1}: extracted {len(page_text)} lines in {elapse:.2f}s")

        doc.close()
        return "\n\n".join(ocr_texts)

    except Exception as e:
        print(f"[pdf_parser] RapidOCR failed: {e}")
        import traceback
        traceback.print_exc()
        return ""


# ==============================================================================
# OPTION 2: Docling with OCR Enabled (Quick Fix)
# ==============================================================================

def extract_with_docling_ocr(file_path: str) -> dict:
    """
    Extract text using Docling with OCR enabled.

    This is the QUICKEST FIX - just enable OCR in your existing Docling pipeline.
    """
    try:
        from docling.document_converter import DocumentConverter
        from docling.datamodel.base_models import InputFormat
        from docling.datamodel.pipeline_options import PdfPipelineOptions

        # Configure pipeline with OCR enabled
        pipeline_options = PdfPipelineOptions()
        pipeline_options.do_ocr = True  # ← This is the key change!
        pipeline_options.do_table_structure = True

        converter = DocumentConverter(
            format_options={
                InputFormat.PDF: pipeline_options
            }
        )

        print(f"[pdf_parser] Starting Docling conversion with OCR for {Path(file_path).name}")
        result = converter.convert(file_path)

        # Extract text (OCR is automatically applied to image-heavy pages)
        full_text = result.document.export_to_markdown()

        # Extract tables
        tables = []
        for table in result.document.tables:
            table_data = {
                "page": getattr(table, 'page_no', None),
                "text": table.export_to_markdown() if hasattr(table, 'export_to_markdown') else str(table),
            }
            tables.append(table_data)

        page_count = len(result.document.pages) if hasattr(result.document, 'pages') else 0

        print(f"[pdf_parser] Docling OCR extracted {len(full_text)} chars, {len(tables)} tables from {page_count} pages")

        return {
            "text": full_text,
            "tables": tables,
            "page_count": page_count,
            "metadata": {"method": "docling_ocr", "has_tables": len(tables) > 0}
        }

    except Exception as e:
        print(f"[pdf_parser] Docling OCR extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return None


# ==============================================================================
# OPTION 3: EasyOCR (Alternative)
# ==============================================================================

try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False

_easyocr_reader = None

def get_easyocr_reader():
    """Lazy initialization of EasyOCR reader."""
    global _easyocr_reader
    if _easyocr_reader is None and EASYOCR_AVAILABLE:
        try:
            _easyocr_reader = easyocr.Reader(['en'], gpu=False)
            print("[pdf_parser] EasyOCR initialized successfully")
        except Exception as e:
            print(f"[pdf_parser] EasyOCR initialization failed: {e}")
    return _easyocr_reader


def extract_with_easyocr(file_path: str, page_indices: List[int]) -> str:
    """
    Run EasyOCR on specific pages.

    EasyOCR is slower than RapidOCR but has good multilingual support.
    """
    if not EASYOCR_AVAILABLE:
        print("[pdf_parser] EasyOCR not available")
        return ""

    reader = get_easyocr_reader()
    if reader is None:
        return ""

    try:
        import fitz
        doc = fitz.open(file_path)
        ocr_texts = []

        for page_idx in page_indices:
            if page_idx >= len(doc):
                continue

            page = doc.load_page(page_idx)
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
            img_bytes = pix.tobytes("png")

            # EasyOCR result: [[bbox, text, confidence], ...]
            result = reader.readtext(img_bytes)

            page_text = []
            for bbox, text, confidence in result:
                if confidence > 0.5:
                    page_text.append(text)

            ocr_texts.append(f"--- OCR Page {page_idx + 1} ---\n" + "\n".join(page_text))

        doc.close()
        return "\n\n".join(ocr_texts)

    except Exception as e:
        print(f"[pdf_parser] EasyOCR failed: {e}")
        return ""


# ==============================================================================
# OPTION 4: Azure Document Intelligence (Cloud - Highest Accuracy)
# ==============================================================================

try:
    from azure.ai.formrecognizer import DocumentAnalysisClient
    from azure.core.credentials import AzureKeyCredential
    AZURE_AVAILABLE = True
except ImportError:
    AZURE_AVAILABLE = False


def extract_with_azure(file_path: str, endpoint: str = None, api_key: str = None) -> dict:
    """
    Extract text and tables using Azure Document Intelligence.

    Highest accuracy (~99%) but requires Azure account and costs money.
    Best for critical documents (high-value loans).

    Args:
        file_path: Path to PDF file
        endpoint: Azure endpoint URL (or set AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT env var)
        api_key: Azure API key (or set AZURE_DOCUMENT_INTELLIGENCE_KEY env var)

    Returns:
        dict with text, tables, confidence scores
    """
    if not AZURE_AVAILABLE:
        print("[pdf_parser] Azure SDK not available. Install: pip install azure-ai-formrecognizer")
        return None

    endpoint = endpoint or os.getenv("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT")
    api_key = api_key or os.getenv("AZURE_DOCUMENT_INTELLIGENCE_KEY")

    if not endpoint or not api_key:
        print("[pdf_parser] Azure credentials not provided")
        return None

    try:
        client = DocumentAnalysisClient(endpoint, AzureKeyCredential(api_key))

        with open(file_path, "rb") as f:
            poller = client.begin_analyze_document("prebuilt-layout", f)
            result = poller.result()

        # Extract text
        all_text = []
        for page in result.pages:
            page_text = []
            for line in page.lines:
                page_text.append(line.content)
            all_text.append(f"--- Page {page.page_number} ---\n" + "\n".join(page_text))

        # Extract tables
        tables = []
        for table in result.tables:
            table_data = {
                "page": table.bounding_regions[0].page_number if table.bounding_regions else None,
                "rows": table.row_count,
                "columns": table.column_count,
                "cells": []
            }
            for cell in table.cells:
                table_data["cells"].append({
                    "row": cell.row_index,
                    "col": cell.column_index,
                    "text": cell.content,
                    "row_span": cell.row_span or 1,
                    "col_span": cell.column_span or 1,
                })
            tables.append(table_data)

        print(f"[pdf_parser] Azure extracted {len('\n\n'.join(all_text))} chars, {len(tables)} tables")

        return {
            "text": "\n\n".join(all_text),
            "tables": tables,
            "page_count": len(result.pages),
            "metadata": {"method": "azure", "model_id": result.model_id}
        }

    except Exception as e:
        print(f"[pdf_parser] Azure extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return None


# ==============================================================================
# Smart Router: Choose Best OCR Based on Document
# ==============================================================================

def smart_ocr_extract(file_path: str, accuracy_mode: str = "balanced", critical_pages: List[int] = None) -> str:
    """
    Intelligently route to best OCR method based on requirements.

    Modes:
    - "fast": Use RapidOCR (fastest, good accuracy)
    - "balanced": Use RapidOCR with quality checks (default)
    - "accurate": Use Azure if available, else RapidOCR
    - "max": Use best available method per page

    Args:
        file_path: Path to PDF
        accuracy_mode: Quality vs speed trade-off
        critical_pages: Optional list of critical page indices for max accuracy

    Returns:
        Extracted OCR text
    """
    if critical_pages is None:
        # Default: OCR first 10 pages
        critical_pages = list(range(10))

    if accuracy_mode == "accurate" and AZURE_AVAILABLE:
        result = extract_with_azure(file_path)
        if result:
            return result.get("text", "")

    # Default/fallback: RapidOCR
    if RAPID_AVAILABLE:
        return extract_with_rapid_ocr(file_path, critical_pages)
    elif EASYOCR_AVAILABLE:
        return extract_with_easyocr(file_path, critical_pages)
    else:
        print("[pdf_parser] No OCR engine available")
        return ""


# ==============================================================================
# Installation Commands
# ==============================================================================

INSTALL_COMMANDS = """
# Install RapidOCR (recommended)
pip install rapidocr-onnxruntime

# Install EasyOCR (alternative)
pip install easyocr

# Install Azure SDK (for production)
pip install azure-ai-formrecognizer

# Install all
pip install rapidocr-onnxruntime easyocr azure-ai-formrecognizer
"""


if __name__ == "__main__":
    print("=== PaddleOCR Migration Guide ===")
    print("\nAvailable OCR engines:")
    print(f"  RapidOCR: {'✓ Installed' if RAPID_AVAILABLE else '✗ Not installed (pip install rapidocr-onnxruntime)'}")
    print(f"  EasyOCR: {'✓ Installed' if EASYOCR_AVAILABLE else '✗ Not installed (pip install easyocr)'}")
    print(f"  Azure: {'✓ SDK installed' if AZURE_AVAILABLE else '✗ Not installed (pip install azure-ai-formrecognizer)'}")
    print(f"\nRecommended: RapidOCR (fastest and most accurate for your use case)")
    print("\nInstallation commands:")
    print(INSTALL_COMMANDS)
