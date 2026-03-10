"""CAM (Credit Appraisal Memorandum) Generator — produces the final structured CAM report with explainability."""

from src.models import (
    CAMReport,
    ExtractedData,
    FiveCsScore,
    ResearchResult,
    RiskTimelineEntry,
)


def _build_explainable_summary(
    company_name: str,
    loan_amount: float,
    recommendation: str,
    overall: float,
    five_cs: FiveCsScore,
    research_data: dict,
    circular_flag: dict | None = None,
    site_visit_notes: str | None = None,
) -> str:
    """Build a transparent, explainable summary that walks the reader through the decision logic."""
    parts = [
        f"Credit appraisal for {company_name} requesting ₹{loan_amount:,.0f}.",
        f"Overall 5Cs score: {overall}/100.",
        f"Recommendation: {recommendation}.",
    ]

    # Explain WHY — strongest and weakest scores
    scores = {
        "Character": five_cs.character,
        "Capacity": five_cs.capacity,
        "Capital": five_cs.capital,
        "Collateral": five_cs.collateral,
        "Conditions": five_cs.conditions,
    }
    strongest = max(scores, key=scores.get)
    weakest = min(scores, key=scores.get)

    parts.append(f"Strongest pillar: {strongest} ({scores[strongest]:.0f}/100).")
    parts.append(f"Weakest pillar: {weakest} ({scores[weakest]:.0f}/100).")

    # Circular trading flag
    if circular_flag and circular_flag.get("detected"):
        parts.append(f"⚠️ CIRCULAR TRADING ALERT: {circular_flag['alert']}")

    # Litigation concerns
    litigation = research_data.get("litigation_flags") or []
    if litigation:
        parts.append(f"Litigation concerns: {', '.join(litigation)}.")
    else:
        parts.append("No litigation flags found.")

    # Site visit notes impact
    if site_visit_notes:
        parts.append(f"Field observations noted: \"{site_visit_notes[:100]}...\"" if len(site_visit_notes) > 100 else f"Field observations: \"{site_visit_notes}\"")

    # Decision rationale
    if recommendation == "REJECT":
        reject_reasons = []
        if scores[weakest] < 50:
            reject_reasons.append(f"critically low {weakest} score ({scores[weakest]:.0f})")
        if circular_flag and circular_flag.get("detected"):
            reject_reasons.append("circular trading suspicion")
        if len(litigation) > 2:
            reject_reasons.append("excessive litigation history")
        parts.append(f"Rejection driven by: {'; '.join(reject_reasons) if reject_reasons else 'overall score below threshold'}.")
    elif recommendation == "REFER":
        parts.append(f"Referred for manual review due to borderline score ({overall:.0f}/100).")

    return " ".join(parts)


def generate_cam(
    company_name: str,
    loan_amount: float,
    extracted_data: dict,
    bank_data: dict,
    gst_data: dict,
    research_data: dict,
    five_cs: FiveCsScore,
    circular_flag: dict | None = None,
    site_visit_notes: str | None = None,
) -> CAMReport:
    """Generate a complete CAM report from all analyzed data.

    Uses the 5Cs overall score to determine recommendation:
    - >= 70: APPROVE
    - 50-69: REFER
    - < 50: REJECT

    Circular trading detection can downgrade recommendation.
    """
    overall = five_cs.overall

    if overall >= 70:
        recommendation = "APPROVE"
    elif overall >= 50:
        recommendation = "REFER"
    else:
        recommendation = "REJECT"

    # Downgrade if circular trading detected
    risk_flags = []
    if circular_flag and circular_flag.get("detected"):
        risk_flags.append(circular_flag["alert"])
        if circular_flag.get("variance_pct", 0) > 30 and recommendation == "APPROVE":
            recommendation = "REFER"
            risk_flags.append("Recommendation downgraded from APPROVE to REFER due to high GST-Bank variance.")

    risk_timeline = [
        RiskTimelineEntry(**entry)
        for entry in research_data.get("risk_timeline", [])
    ]

    summary_text = _build_explainable_summary(
        company_name, loan_amount, recommendation, overall,
        five_cs, research_data, circular_flag, site_visit_notes,
    )

    cam = CAMReport(
        company_name=company_name,
        loan_amount=loan_amount,
        recommendation=recommendation,
        confidence=round(min(95, overall + 5), 1),
        extracted_data=ExtractedData(
            company_name=company_name,
            gst_summary=gst_data,
            bank_summary=bank_data.get("summary"),
            financial_highlights=extracted_data.get("financial_highlights"),
            circular_trading_flag=circular_flag,
        ),
        research=ResearchResult(
            mca_status=research_data.get("mca_status", "Active"),
            litigation_flags=research_data.get("litigation_flags", []),
            news_sentiment=research_data.get("news_sentiment"),
            risk_timeline=risk_timeline,
        ),
        five_cs=five_cs,
        summary_text=summary_text,
        site_visit_notes=site_visit_notes,
        risk_flags=risk_flags,
    )

    return cam
