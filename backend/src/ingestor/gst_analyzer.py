"""GST Analyzer module — extracts GST data from document text using AI."""

from src.ai_extractor import extract_gst_data


def analyze_gst(pdf_text: str, gst_number: str | None = None) -> dict:
    """Analyze GST data from extracted PDF text using Groq AI.

    Falls back to minimal data if AI extraction fails.
    """
    try:
        result = extract_gst_data(pdf_text)
        if gst_number and not result.get("gst_number"):
            result["gst_number"] = gst_number
        return result
    except Exception as e:
        return {
            "gst_number": gst_number,
            "entity_name": None,
            "status": "Unknown",
            "compliance_rating": None,
            "error": str(e),
            "last_12_months": {},
            "turnover_trend": [],
        }
