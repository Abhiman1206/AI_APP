"""AI Extractor — Uses Groq API (LLaMA 3) for intelligent financial data extraction from PDF text."""

import json
import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

MODEL = "llama-3.3-70b-versatile"


def _call_groq(system_prompt: str, user_content: str) -> dict:
    """Call Groq API and parse JSON response."""
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        temperature=0.1,
        max_tokens=4096,
        response_format={"type": "json_object"},
    )
    text = response.choices[0].message.content
    return json.loads(text)


def extract_financial_data(pdf_text: str) -> dict:
    """Extract financial highlights from PDF text using AI."""
    system_prompt = """You are a financial document parser. Extract key financial data from the provided text.
Return a JSON object with these fields (use null if not found):
{
    "revenue": <number in INR or null>,
    "net_profit": <number in INR or null>,
    "total_assets": <number in INR or null>,
    "total_liabilities": <number in INR or null>,
    "current_ratio": <number or null>,
    "debt_to_equity": <number or null>,
    "ebitda": <number in INR or null>,
    "working_capital": <number in INR or null>,
    "tables": [{"title": "...", "rows": [{"item": "...", "value": "..."}]}]
}
Convert all monetary values to raw numbers in INR (e.g., "15.2 Cr" → 152000000).
"""
    return _call_groq(system_prompt, f"Extract financial data from this document:\n\n{pdf_text[:8000]}")


def extract_gst_data(pdf_text: str) -> dict:
    """Extract GST filing data from PDF text using AI."""
    system_prompt = """You are a GST return document parser. Extract GST data from the provided text.
Return a JSON object with these fields (use null if not found):
{
    "gst_number": <string or null>,
    "entity_name": <string or null>,
    "status": "Active" or "Inactive" or null,
    "compliance_rating": "Good" or "Average" or "Poor" or null,
    "last_12_months": {
        "total_turnover": <number in INR or null>,
        "avg_monthly_turnover": <number in INR or null>,
        "filings_on_time": <number 0-12 or null>,
        "filings_late": <number or null>,
        "filings_missed": <number or null>
    },
    "turnover_trend": [{"month": "MMM YYYY", "turnover": <number>}]
}
Convert all monetary values to raw numbers in INR.
"""
    return _call_groq(system_prompt, f"Extract GST data from this document:\n\n{pdf_text[:8000]}")


def extract_bank_data(pdf_text: str) -> dict:
    """Extract bank statement data from PDF text using AI."""
    system_prompt = """You are a bank statement parser. Extract cash flow data from the provided text.
Return a JSON object with these fields (use null if not found):
{
    "account_holder": <string or null>,
    "bank_name": <string or null>,
    "account_type": <string or null>,
    "period": <string or null>,
    "summary": {
        "avg_monthly_balance": <number in INR or null>,
        "avg_monthly_credits": <number in INR or null>,
        "avg_monthly_debits": <number in INR or null>,
        "peak_balance": <number or null>,
        "lowest_balance": <number or null>,
        "cheque_bounces": <number or null>,
        "emi_regularity": "Regular" or "Irregular" or null
    },
    "cash_flow_months": [{"month": "MMM YYYY", "inflow": <number>, "outflow": <number>}]
}
Convert all monetary values to raw numbers in INR.
"""
    return _call_groq(system_prompt, f"Extract bank statement data from this document:\n\n{pdf_text[:8000]}")


def extract_risk_intelligence(company_name: str, all_text: str) -> dict:
    """Analyze all extracted text for risk signals using AI."""
    system_prompt = """You are a credit risk analyst. Analyze the provided company documents for risk signals.
Return a JSON object:
{
    "news_sentiment": "Positive" or "Mostly Positive" or "Neutral" or "Negative",
    "litigation_flags": ["<description of any legal/dispute mentions>"],
    "risk_timeline": [
        {"date": "YYYY-MM-DD", "event": "<description>", "severity": "low"|"medium"|"high", "source": "<where found>"}
    ],
    "mca_status": "Active" or "Unknown",
    "key_concerns": ["<concern 1>", "<concern 2>"],
    "key_strengths": ["<strength 1>", "<strength 2>"]
}
If no risks found, return empty arrays. Be factual, not speculative.
"""
    return _call_groq(
        system_prompt,
        f"Analyze risk signals for company '{company_name}' from these documents:\n\n{all_text[:10000]}",
    )
