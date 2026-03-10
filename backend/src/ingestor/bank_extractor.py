"""Bank Statement Extractor — parses bank statement data from document text using AI."""

from src.ai_extractor import extract_bank_data as ai_extract_bank


def extract_bank_data(pdf_text: str) -> dict:
    """Extract bank statement data from PDF text using Groq AI.

    Falls back to minimal data if AI extraction fails.
    """
    try:
        return ai_extract_bank(pdf_text)
    except Exception as e:
        return {
            "account_holder": None,
            "bank_name": None,
            "account_type": None,
            "period": None,
            "error": str(e),
            "summary": {},
            "cash_flow_months": [],
        }
