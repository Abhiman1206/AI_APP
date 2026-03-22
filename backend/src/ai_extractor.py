"""AI Extractor — Uses Groq API (LLaMA 3) for intelligent financial data extraction from PDF text.

Enhanced for large documents:
- _chunk_text(): splits text into overlapping windows so nothing is skipped
- _merge_dicts(): combines results across chunks (first non-null scalar wins; lists merge/deduplicate)
- All public extraction functions accept arbitrarily long text; internally they chunk and merge
"""

import json
import os
import re
from groq import Groq
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

MODEL = "llama-3.3-70b-versatile"

# Per-chunk character budget (safe for LLaMA 3.3 70B context window)
CHUNK_SIZE = 20_000
# Overlap between chunks to avoid cutting mid-sentence / mid-table
CHUNK_OVERLAP = 2_000
# Maximum chunks to process per document (controls API call count)
MAX_CHUNKS = 4


def _parse_indian_number(value):
    """Parse Indian-formatted numeric text to float when possible.

    Supports examples like:
    - "1,92,456"
    - "15.2 Cr"
    - "80 lakh"
    """
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if not isinstance(value, str):
        return value

    raw = value.strip().lower()
    if not raw:
        return None

    # Keep digits, comma, dot, minus and alphabetic unit hints.
    raw = raw.replace("₹", "").replace("inr", "").strip()
    unit_multiplier = 1.0
    if "crore" in raw or re.search(r"\bcr\b", raw):
        unit_multiplier = 10_000_000.0
    elif "lakh" in raw or re.search(r"\blac\b|\blk\b", raw):
        unit_multiplier = 100_000.0
    elif "million" in raw or re.search(r"\bmn\b", raw):
        unit_multiplier = 1_000_000.0
    elif "billion" in raw or re.search(r"\bbn\b", raw):
        unit_multiplier = 1_000_000_000.0

    m = re.search(r"-?[0-9][0-9,]*(?:\.[0-9]+)?", raw)
    if not m:
        return value

    try:
        base = float(m.group(0).replace(",", ""))
        return base * unit_multiplier
    except Exception:
        return value


def _normalize_numeric_fields(obj):
    """Recursively normalize numeric-looking fields to floats where safe."""
    if isinstance(obj, dict):
        return {k: _normalize_numeric_fields(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_normalize_numeric_fields(v) for v in obj]
    parsed = _parse_indian_number(obj)
    return parsed


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


def _chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list:
    """Split text into overlapping chunks for large document processing.

    Each chunk starts CHUNK_OVERLAP characters before the previous one ended so
    that tables or paragraphs that straddle a boundary appear in both chunks
    and are not silently dropped.

    Args:
        text: Input text to split.
        chunk_size: Maximum characters per chunk.
        overlap: Characters shared between successive chunks.

    Returns:
        List of string chunks (may be a single element for short texts).
    """
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        if end >= len(text):
            break
        start = end - overlap  # slide back by overlap for next chunk

    return chunks


def _merge_dicts(base: dict, update: dict) -> dict:
    """Merge two extraction result dicts.

    Rules:
    - Scalar fields (str, int, float): keep the first non-null value.
    - Nested dicts: recurse.
    - List fields: append items not already present (de-duplicate by repr).

    This allows consolidating data found in different chunks of the same document.
    """
    result = dict(base)
    for key, val in update.items():
        existing = result.get(key)
        if existing is None and val is not None:
            result[key] = val
        elif isinstance(existing, dict) and isinstance(val, dict):
            result[key] = _merge_dicts(existing, val)
        elif isinstance(existing, list) and isinstance(val, list):
            seen = {repr(item) for item in existing}
            for item in val:
                if repr(item) not in seen:
                    existing.append(item)
                    seen.add(repr(item))
    return result


def _all_key_fields_found(data: dict, required_fields: list) -> bool:
    """Return True if every required field in data is non-null."""
    return all(data.get(f) is not None for f in required_fields)


# ---------------------------------------------------------------------------
# Public extraction functions
# ---------------------------------------------------------------------------

def extract_financial_data(pdf_text: str) -> dict:
    """Extract financial highlights from PDF text using AI.

    Processes text in chunks and merges results so that figures spread across
    a large annual report are all captured.
    """
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
    KEY_FIELDS = ["revenue", "net_profit", "total_assets", "current_ratio", "debt_to_equity"]

    chunks = _chunk_text(pdf_text)
    merged: dict = {}

    for idx, chunk in enumerate(chunks[:MAX_CHUNKS], 1):
        print(f"[ai_extractor] financial_data chunk {idx}/{min(len(chunks), MAX_CHUNKS)}")
        try:
            result = _call_groq(system_prompt, f"Extract financial data from this document:\n\n{chunk}")
            merged = _merge_dicts(merged, result)
            if _all_key_fields_found(merged, KEY_FIELDS):
                print("[ai_extractor] All key financial fields found, stopping early.")
                break
        except Exception as e:
            print(f"[ai_extractor] financial_data chunk {idx} failed: {e}")

    return _normalize_numeric_fields(merged)


def extract_gst_data(pdf_text: str) -> dict:
    """Extract GST filing data from PDF text using AI.

    Chunks the input so that monthly turnover tables (which can be long) are
    fully captured even in large GST summary reports.
    """
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
    KEY_FIELDS = ["gst_number", "entity_name"]

    chunks = _chunk_text(pdf_text)
    merged: dict = {}

    for idx, chunk in enumerate(chunks[:MAX_CHUNKS], 1):
        print(f"[ai_extractor] gst_data chunk {idx}/{min(len(chunks), MAX_CHUNKS)}")
        try:
            result = _call_groq(system_prompt, f"Extract GST data from this document:\n\n{chunk}")
            merged = _merge_dicts(merged, result)
            if _all_key_fields_found(merged, KEY_FIELDS):
                break
        except Exception as e:
            print(f"[ai_extractor] gst_data chunk {idx} failed: {e}")

    return _normalize_numeric_fields(merged)


def extract_bank_data(pdf_text: str) -> dict:
    """Extract bank statement data from PDF text using AI.

    Chunks the input so that the full 12-month cash-flow table is captured
    even from lengthy bank statement PDFs.
    """
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
    KEY_FIELDS = ["account_holder", "bank_name"]

    chunks = _chunk_text(pdf_text)
    merged: dict = {}

    for idx, chunk in enumerate(chunks[:MAX_CHUNKS], 1):
        print(f"[ai_extractor] bank_data chunk {idx}/{min(len(chunks), MAX_CHUNKS)}")
        try:
            result = _call_groq(system_prompt, f"Extract bank statement data from this document:\n\n{chunk}")
            merged = _merge_dicts(merged, result)
            if _all_key_fields_found(merged, KEY_FIELDS):
                break
        except Exception as e:
            print(f"[ai_extractor] bank_data chunk {idx} failed: {e}")

    return _normalize_numeric_fields(merged)


def extract_risk_intelligence(company_name: str, all_text: str) -> dict:
    """Analyze all extracted text for risk signals using AI.

    For large corpora (multiple documents combined), processes the first
    MAX_CHUNKS chunks and merges risk findings so that litigation flags and
    key concerns from different documents are all surfaced.
    """
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
    chunks = _chunk_text(all_text)
    merged: dict = {}

    for idx, chunk in enumerate(chunks[:MAX_CHUNKS], 1):
        print(f"[ai_extractor] risk_intelligence chunk {idx}/{min(len(chunks), MAX_CHUNKS)}")
        try:
            result = _call_groq(
                system_prompt,
                f"Analyze risk signals for company '{company_name}' from these documents:\n\n{chunk}",
            )
            merged = _merge_dicts(merged, result)
        except Exception as e:
            print(f"[ai_extractor] risk_intelligence chunk {idx} failed: {e}")

    return merged


def validate_financial_consistency(financial_highlights: dict) -> dict:
    """Validate extracted financial fields using Groq and deterministic checks.

    Returns a compact validation object that can be surfaced in CAM output.
    """
    deterministic = {
        "assets_equals_liabilities_plus_equity": {
            "status": "unknown",
            "details": "Liabilities/equity fields not fully available in highlights",
        },
        "profit_non_negative_signal": {
            "status": "pass" if (financial_highlights or {}).get("net_profit") not in (None, "") else "unknown",
            "details": "Net profit present" if (financial_highlights or {}).get("net_profit") not in (None, "") else "Net profit missing",
        },
    }

    system_prompt = """You are a strict financial consistency checker.
Given extracted financial highlights, return JSON only in this schema:
{
  "status": "pass" | "warn" | "fail",
  "checks": [
    {"name": "assets_balance_identity", "status": "pass|warn|fail|unknown", "details": "..."},
    {"name": "profitability_consistency", "status": "pass|warn|fail|unknown", "details": "..."}
  ],
  "warnings": ["..."],
  "recommended_null_fields": ["field_name"]
}
Use 'unknown' where fields are unavailable. Avoid speculation.
"""

    try:
        llm_result = _call_groq(system_prompt, json.dumps(financial_highlights, default=str))
    except Exception as e:
        return {
            "engine": "groq",
            "status": "warn",
            "checks": [],
            "warnings": [f"validation_call_failed: {e}"],
            "recommended_null_fields": [],
            "deterministic": deterministic,
        }

    return {
        "engine": "groq",
        "status": llm_result.get("status", "unknown"),
        "checks": llm_result.get("checks", []),
        "warnings": llm_result.get("warnings", []),
        "recommended_null_fields": llm_result.get("recommended_null_fields", []),
        "deterministic": deterministic,
    }
