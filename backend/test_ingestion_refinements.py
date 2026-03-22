import json
import os
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.append(os.path.dirname(__file__))

from src.ai_extractor import validate_financial_consistency
from src.ingestor import pdf_parser
from src.ingestor.batch_ingestor import ingest_directory
from src.ingestor.page_indexer import generate_page_index


class TestIngestionRefinements(unittest.TestCase):
    def test_assemble_text_uses_section_boundaries(self):
        page_records = [
            {
                "page_no": 1,
                "classification": "narrative_text",
                "text_length": 600,
                "text_snippet": "Balance Sheet overview",
            },
            {
                "page_no": 2,
                "classification": "narrative_text",
                "text_length": 550,
                "text_snippet": "Profit and Loss details",
            },
        ]
        page_text_map = {
            1: "BALANCE SHEET\n" + ("Assets and liabilities summary. " * 400),
            2: "PROFIT AND LOSS\n" + ("Revenue and expense summary. " * 400),
        }

        assembled, pages_to_ocr, section_count = pdf_parser._assemble_text_from_pages(
            page_records=page_records,
            target_page_indices=[0, 1],
            page_text_map=page_text_map,
        )

        self.assertIn("=== Section", assembled)
        self.assertGreaterEqual(section_count, 2)
        self.assertEqual(pages_to_ocr, [])

    def test_select_extractor_rapidocr_only_path(self):
        with patch.object(pdf_parser, "DOCLING_AVAILABLE", True), patch.object(pdf_parser, "RAPIDOCR_AVAILABLE", True):
            self.assertEqual(pdf_parser._select_extractor(pdf_parser.PAGE_CLASS_SCANNED), "rapidocr")
            self.assertEqual(pdf_parser._select_extractor(pdf_parser.PAGE_CLASS_FINANCIAL_TABLE), "docling")

        with patch.object(pdf_parser, "DOCLING_AVAILABLE", False), patch.object(pdf_parser, "RAPIDOCR_AVAILABLE", False):
            self.assertEqual(pdf_parser._select_extractor(pdf_parser.PAGE_CLASS_SCANNED), "pdfplumber")
            self.assertEqual(pdf_parser._select_extractor(pdf_parser.PAGE_CLASS_MULTI_COLUMN), "pdfplumber")

    def test_validation_result_propagation(self):
        llm_payload = {
            "status": "warn",
            "checks": [{"name": "profitability_consistency", "status": "warn", "details": "Margin dropped"}],
            "warnings": ["profit trend volatile"],
            "recommended_null_fields": ["debt_to_equity"],
        }

        with patch("src.ai_extractor._call_groq", return_value=llm_payload):
            result = validate_financial_consistency({"net_profit": 1000000})

        self.assertEqual(result["engine"], "groq")
        self.assertEqual(result["status"], "warn")
        self.assertEqual(result["checks"][0]["name"], "profitability_consistency")
        self.assertIn("deterministic", result)

    def test_validation_fallback_when_llm_fails(self):
        with patch("src.ai_extractor._call_groq", side_effect=RuntimeError("api down")):
            result = validate_financial_consistency({"net_profit": None})

        self.assertEqual(result["status"], "warn")
        self.assertTrue(result["warnings"])
        self.assertEqual(result["engine"], "groq")

    def test_page_index_json_schema(self):
        parsed_doc = {
            "filename": "sample.pdf",
            "file_size_mb": 1.2,
            "page_count": 2,
            "targeted_pages": 2,
            "page_routing": [
                {
                    "page_no": 1,
                    "extractor": "pdfplumber",
                    "classification": "narrative_text",
                    "routing_reason": "financial_narrative",
                    "keywords": ["balance sheet"],
                    "text_snippet": "Balance Sheet",
                    "relevance_score": 2,
                },
                {
                    "page_no": 2,
                    "extractor": "rapidocr",
                    "classification": "scanned",
                    "routing_reason": "likely_scanned_or_image_text",
                    "keywords": [],
                    "text_snippet": "",
                    "relevance_score": 0,
                },
            ],
        }

        with tempfile.TemporaryDirectory() as tmp:
            result = generate_page_index(parsed_doc, tmp)
            self.assertEqual(result["entry_count"], 2)
            self.assertTrue(os.path.exists(result["artifact_path"]))

            with open(result["artifact_path"], "r", encoding="utf-8") as f:
                artifact = json.loads(f.read())
            self.assertEqual(artifact["file_name"], "sample.pdf")
            self.assertEqual(len(artifact["entries"]), 2)
            self.assertIn("chunk_id", artifact["entries"][0])

    def test_batch_ingestor_returns_page_index_references(self):
        fake_parsed = [
            {
                "filename": "test_financial.pdf",
                "page_count": 1,
                "targeted_pages": 1,
                "extracted_text": "Balance Sheet content",
                "page_routing": [],
            }
        ]
        fake_index = {
            "document_id": "testdoc",
            "artifact_path": "tmp/testdoc.page_index.json",
            "entry_count": 1,
        }

        with tempfile.TemporaryDirectory() as tmp, \
            patch("src.ingestor.batch_ingestor.parse_pdf_directory", return_value=fake_parsed), \
            patch("src.ingestor.batch_ingestor.generate_page_index", return_value=fake_index), \
            patch("src.ingestor.batch_ingestor.extract_financial_data", return_value={"revenue": 100}), \
            patch("src.ingestor.batch_ingestor.extract_gst_data", return_value={}), \
            patch("src.ingestor.batch_ingestor.extract_bank_data", return_value={}), \
            patch("src.ingestor.batch_ingestor.extract_risk_intelligence", return_value={}):
            output = ingest_directory(tmp, company_name="Test Co", gst_number=None)

        self.assertEqual(len(output["page_index_files"]), 1)
        self.assertEqual(output["parsed_files"][0]["page_index"]["document_id"], "testdoc")


if __name__ == "__main__":
    unittest.main()
