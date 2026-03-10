"""Mock Search module — uses AI to analyze risk from extracted document text."""

from src.ai_extractor import extract_risk_intelligence


def search_company(company_name: str, all_text: str = "") -> dict:
    """Search for risk signals about a company using AI analysis.

    If document text is available, AI analyzes it for risk signals.
    Falls back to minimal data if AI fails.
    """
    try:
        if all_text:
            return extract_risk_intelligence(company_name, all_text)
        return {
            "news_sentiment": "Neutral",
            "litigation_flags": [],
            "risk_timeline": [],
            "mca_status": "Unknown",
            "key_concerns": [],
            "key_strengths": [],
        }
    except Exception as e:
        return {
            "news_sentiment": "Neutral",
            "litigation_flags": [],
            "risk_timeline": [],
            "mca_status": "Unknown",
            "error": str(e),
        }
