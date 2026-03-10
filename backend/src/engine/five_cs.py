"""Five Cs Credit Scoring Engine — evaluates borrower across Character, Capacity, Capital, Collateral, Conditions."""

from src.models import FiveCsScore


def detect_circular_trading(gst_data: dict, bank_data: dict) -> dict:
    """Cross-leverage GST turnover vs bank credits to detect revenue inflation.

    Returns a flag dict with variance percentage and alert level.
    """
    gst_12m = gst_data.get("last_12_months") or {}
    bank_summary = bank_data.get("summary") or {}

    gst_turnover = gst_12m.get("total_turnover")
    bank_credits = bank_summary.get("avg_monthly_credits")

    if gst_turnover is None or bank_credits is None:
        return {"detected": False, "variance_pct": None, "alert": "Insufficient data for cross-check"}

    annual_bank_credits = bank_credits * 12
    if annual_bank_credits == 0:
        return {"detected": False, "variance_pct": None, "alert": "Zero bank credits"}

    variance_pct = abs(gst_turnover - annual_bank_credits) / annual_bank_credits * 100

    if variance_pct > 30:
        return {"detected": True, "variance_pct": round(variance_pct, 1), "alert": f"HIGH RISK: {variance_pct:.0f}% GST-Bank variance — possible circular trading or revenue inflation"}
    elif variance_pct > 20:
        return {"detected": True, "variance_pct": round(variance_pct, 1), "alert": f"MODERATE RISK: {variance_pct:.0f}% GST-Bank variance — warrants investigation"}
    else:
        return {"detected": False, "variance_pct": round(variance_pct, 1), "alert": f"Normal: {variance_pct:.0f}% variance within acceptable range"}


def adjust_score_for_site_notes(overall: float, notes: str | None) -> tuple[float, str]:
    """Adjust the 5Cs score based on qualitative site visit notes.

    Uses keyword detection to apply bonus or penalty.
    Returns (adjusted_score, notes_impact_text).
    """
    if not notes or not notes.strip():
        return overall, ""

    notes_lower = notes.lower()
    adjustment = 0
    impacts = []

    # Negative signals
    negative_keywords = {
        "low capacity": -5, "shut down": -10, "idle": -7,
        "under-utilized": -5, "20% capacity": -8, "30% capacity": -6,
        "40% capacity": -4, "poor maintenance": -3, "outdated": -3,
        "dispute": -4, "fraud": -10, "misrepresentation": -10,
        "overstaff": -2, "empty warehouse": -5,
    }
    for keyword, penalty in negative_keywords.items():
        if keyword in notes_lower:
            adjustment += penalty
            impacts.append(f"'{keyword}' ({penalty:+d})")

    # Positive signals
    positive_keywords = {
        "well maintained": 3, "modern equipment": 4, "full capacity": 5,
        "expanding": 4, "strong management": 3, "good hygiene": 2,
        "new machinery": 3, "80% capacity": 3, "90% capacity": 4,
        "100% capacity": 5, "excellent": 3,
    }
    for keyword, bonus in positive_keywords.items():
        if keyword in notes_lower:
            adjustment += bonus
            impacts.append(f"'{keyword}' ({bonus:+d})")

    adjusted = max(0, min(100, overall + adjustment))
    impact_text = f"Site visit adjustment: {adjustment:+.0f} pts. Signals: {', '.join(impacts)}." if impacts else "No impactful signals detected in site visit notes."

    return round(adjusted, 1), impact_text


def calculate_five_cs(
    extracted_data: dict,
    bank_data: dict,
    gst_data: dict,
    research_data: dict,
    site_visit_notes: str | None = None,
) -> FiveCsScore:
    """Calculate 5Cs credit scores from ingested and researched data.

    Weights: Character 20%, Capacity 25%, Capital 20%, Collateral 15%, Conditions 20%
    """
    financials = extracted_data.get("financial_highlights") or {}
    bank_summary = bank_data.get("summary") or {}
    gst_summary = gst_data.get("last_12_months") or {}

    # Character — filing compliance, litigation, MCA status
    val = gst_summary.get("filings_on_time")
    filings_on_time = val if val is not None else 10

    litigation_count = len(research_data.get("litigation_flags") or [])
    character = min(100, (filings_on_time / 12) * 80 + (20 if litigation_count == 0 else max(0, 20 - litigation_count * 10)))

    # Capacity — revenue, cash flow, debt service
    val = financials.get("current_ratio")
    current_ratio = val if val is not None else 1.0
    capacity = min(100, current_ratio * 40 + 30) if current_ratio else 50

    # Capital — net worth, debt-to-equity
    val = financials.get("debt_to_equity")
    dte = val if val is not None else 1.0
    capital = min(100, max(0, 100 - dte * 40))

    # Collateral — asset coverage (simplified)
    val = financials.get("total_assets")
    total_assets = val if val is not None else 0
    collateral = min(100, 65 + (15 if total_assets > 10_00_00_000 else 0))

    # Conditions — market sentiment, industry outlook
    sentiment = research_data.get("news_sentiment") or "Neutral"
    conditions = {"Mostly Positive": 78, "Positive": 85, "Neutral": 60, "Negative": 35}.get(sentiment, 60)

    weights = {"character": 0.20, "capacity": 0.25, "capital": 0.20, "collateral": 0.15, "conditions": 0.20}
    overall = round(
        character * weights["character"]
        + capacity * weights["capacity"]
        + capital * weights["capital"]
        + collateral * weights["collateral"]
        + conditions * weights["conditions"],
        1,
    )

    # Apply site visit notes adjustment
    site_impact = ""
    if site_visit_notes:
        overall, site_impact = adjust_score_for_site_notes(overall, site_visit_notes)

    conditions_rationale = f"Market sentiment: {sentiment}."
    if site_impact:
        conditions_rationale += f" {site_impact}"

    return FiveCsScore(
        character=round(character, 1),
        capacity=round(capacity, 1),
        capital=round(capital, 1),
        collateral=round(collateral, 1),
        conditions=round(conditions, 1),
        overall=overall,
        character_rationale=f"GST filings on time: {filings_on_time}/12. Litigation flags: {litigation_count}.",
        capacity_rationale=f"Current ratio: {current_ratio}. Avg monthly bank credits: ₹{bank_summary.get('avg_monthly_credits', 'N/A')}.",
        capital_rationale=f"Debt-to-equity ratio: {dte}.",
        collateral_rationale=f"Total assets: ₹{total_assets:,}.",
        conditions_rationale=conditions_rationale,
    )
