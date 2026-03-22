"""CAM PDF Exporter — generates a professional PDF Credit Appraisal Memorandum using reportlab."""

import io
import base64
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable, Image,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm


BRAND_DARK = colors.HexColor("#0F172A")
BRAND_TEAL = colors.HexColor("#14B8A6")
BRAND_AMBER = colors.HexColor("#F59E0B")
BRAND_RED = colors.HexColor("#EF4444")
BRAND_LIGHT = colors.HexColor("#F1F5F9")


def _fmt_inr(val) -> str:
    """Format a number as INR string."""
    if val is None:
        return "N/A"
    try:
        return f"₹{float(val):,.0f}"
    except (TypeError, ValueError):
        return str(val)


def generate_cam_pdf(cam_data: dict) -> bytes:
    """Generate a professional CAM PDF report from a CAM dict."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=20*mm, bottomMargin=15*mm)
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle("CAMTitle", parent=styles["Title"], fontSize=18, textColor=BRAND_DARK, spaceAfter=4)
    heading_style = ParagraphStyle("CAMHeading", parent=styles["Heading2"], textColor=BRAND_DARK, spaceAfter=6, spaceBefore=14)
    normal_style = ParagraphStyle("CAMNormal", parent=styles["Normal"], fontSize=9, leading=13)
    small_style = ParagraphStyle("CAMSmall", parent=styles["Normal"], fontSize=8, textColor=colors.grey)

    elements = []

    # Header
    elements.append(Paragraph("CREDIT APPRAISAL MEMORANDUM", title_style))
    elements.append(Paragraph(f"<b>{cam_data.get('company_name', 'N/A')}</b>", styles["Heading3"]))
    elements.append(Paragraph(f"Generated: {cam_data.get('generated_at', 'N/A')[:10]}", small_style))
    elements.append(Spacer(1, 8))
    elements.append(HRFlowable(width="100%", thickness=1, color=BRAND_TEAL))
    elements.append(Spacer(1, 12))

    # Recommendation Banner
    rec = cam_data.get("recommendation", "N/A")
    rec_color = {"APPROVE": BRAND_TEAL, "REJECT": BRAND_RED, "REFER": BRAND_AMBER}.get(rec, colors.grey)
    rec_table = Table(
        [[f"RECOMMENDATION:  {rec}", f"Confidence: {cam_data.get('confidence', 0):.1f}%", f"Loan Amount: {_fmt_inr(cam_data.get('loan_amount'))}"]],
        colWidths=[200, 140, 180],
    )
    rec_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), rec_color),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.white),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 11),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("ROUNDEDCORNERS", [6, 6, 6, 6]),
    ]))
    elements.append(rec_table)
    elements.append(Spacer(1, 14))

    # Executive Summary
    elements.append(Paragraph("Executive Summary", heading_style))
    summary = cam_data.get("summary_text", "No summary available.")
    elements.append(Paragraph(summary, normal_style))
    elements.append(Spacer(1, 10))

    # ML Risk Model Summary
    ml = cam_data.get("ml_recommendation") or {}
    if ml:
        elements.append(Paragraph("ML Risk Scoring (XGBoost + SMOTE)", heading_style))
        ml_data = [
            ["Metric", "Value"],
            ["Default Probability", f"{float(ml.get('default_probability', 0)) * 100:.1f}%"],
            ["ML Credit Score", f"{ml.get('ml_credit_score', 'N/A')}/100"],
            ["Model Recommendation", str(ml.get('model_recommendation', 'N/A'))],
        ]
        ml_table = Table(ml_data, colWidths=[200, 320])
        ml_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), BRAND_DARK),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        elements.append(ml_table)
        elements.append(Spacer(1, 8))

        contrib = ml.get("feature_contributions") or {}
        if contrib:
            elements.append(Paragraph("Top Feature Contributions", normal_style))
            for key, val in list(contrib.items())[:8]:
                elements.append(Paragraph(f"• {key}: {val:+.4f}", normal_style))
            elements.append(Spacer(1, 6))

    # Pricing rationale
    pricing = cam_data.get("pricing_rationale") or {}
    if pricing:
        elements.append(Paragraph("Risk-Based Pricing Rationale", heading_style))
        elements.append(Paragraph(f"Recommended premium: {pricing.get('risk_premium_bps', 'N/A')} bps over base rate.", normal_style))
        elements.append(Paragraph(f"Suggested sanction limit: {pricing.get('loan_limit_pct', 'N/A')}% of requested amount.", normal_style))
        elements.append(Paragraph(f"Model basis: {pricing.get('basis', 'N/A')}", normal_style))
        elements.append(Spacer(1, 8))

    # Anomaly detection summary
    anomaly = cam_data.get("anomaly_detection") or {}
    if anomaly:
        elements.append(Paragraph("Anomaly Detection", heading_style))
        elements.append(Paragraph(f"Detected: {'Yes' if anomaly.get('detected') else 'No'}", normal_style))
        if anomaly.get("anomaly_score") is not None:
            elements.append(Paragraph(f"Isolation score: {anomaly.get('anomaly_score')}", normal_style))
        for alert in anomaly.get("alerts") or []:
            elements.append(Paragraph(f"• {alert}", ParagraphStyle("AnomalyAlert", parent=normal_style, textColor=BRAND_AMBER)))
        elements.append(Spacer(1, 8))

    # SHAP explainability chart
    explainability = cam_data.get("explainability") or {}
    shap_png_b64 = explainability.get("shap_plot_png_b64")
    if shap_png_b64:
        try:
            image_bytes = base64.b64decode(shap_png_b64)
            elements.append(Paragraph("SHAP Explainability", heading_style))
            elements.append(Paragraph("Feature-level contribution of variables to predicted default risk.", small_style))
            elements.append(Spacer(1, 5))
            elements.append(Image(io.BytesIO(image_bytes), width=165 * mm, height=82 * mm))
            elements.append(Spacer(1, 8))
        except Exception:
            pass

    # Risk Flags
    risk_flags = cam_data.get("risk_flags", [])
    if risk_flags:
        elements.append(Paragraph("⚠ Risk Flags", heading_style))
        for flag in risk_flags:
            elements.append(Paragraph(f"• {flag}", ParagraphStyle("RiskFlag", parent=normal_style, textColor=BRAND_RED)))
        elements.append(Spacer(1, 10))

    # Five Cs Scoring
    elements.append(Paragraph("Five Cs Credit Score", heading_style))
    five_cs = cam_data.get("five_cs", {})
    cs_data = [
        ["Pillar", "Score", "Rationale"],
        ["Character", f"{five_cs.get('character', 0):.0f}/100", five_cs.get("character_rationale", "")],
        ["Capacity", f"{five_cs.get('capacity', 0):.0f}/100", five_cs.get("capacity_rationale", "")],
        ["Capital", f"{five_cs.get('capital', 0):.0f}/100", five_cs.get("capital_rationale", "")],
        ["Collateral", f"{five_cs.get('collateral', 0):.0f}/100", five_cs.get("collateral_rationale", "")],
        ["Conditions", f"{five_cs.get('conditions', 0):.0f}/100", five_cs.get("conditions_rationale", "")],
        ["OVERALL", f"{five_cs.get('overall', 0):.0f}/100", "Weighted average"],
    ]
    cs_table = Table(cs_data, colWidths=[80, 70, 370])
    cs_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BRAND_DARK),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, BRAND_LIGHT]),
        ("BACKGROUND", (0, -1), (-1, -1), BRAND_DARK),
        ("TEXTCOLOR", (0, -1), (-1, -1), colors.white),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
    ]))
    elements.append(cs_table)
    elements.append(Spacer(1, 12))

    # Financial Highlights
    extracted = cam_data.get("extracted_data", {})
    fin = extracted.get("financial_highlights") or {}
    if fin:
        elements.append(Paragraph("Financial Highlights", heading_style))
        fin_data = [
            ["Metric", "Value"],
            ["Revenue", _fmt_inr(fin.get("revenue"))],
            ["Net Profit", _fmt_inr(fin.get("net_profit"))],
            ["Total Assets", _fmt_inr(fin.get("total_assets"))],
            ["Current Ratio", str(fin.get("current_ratio", "N/A"))],
            ["Debt-to-Equity", str(fin.get("debt_to_equity", "N/A"))],
        ]
        fin_table = Table(fin_data, colWidths=[200, 320])
        fin_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), BRAND_DARK),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        elements.append(fin_table)
        elements.append(Spacer(1, 10))

    # Circular Trading Check
    circ = extracted.get("circular_trading_flag")
    if circ:
        elements.append(Paragraph("Circular Trading Cross-Check", heading_style))
        alert_style = ParagraphStyle("AlertStyle", parent=normal_style, textColor=BRAND_RED if circ.get("detected") else BRAND_TEAL)
        elements.append(Paragraph(f"Status: {circ.get('alert', 'N/A')}", alert_style))
        if circ.get("variance_pct") is not None:
            elements.append(Paragraph(f"GST-Bank Variance: {circ['variance_pct']}%", normal_style))
        elements.append(Spacer(1, 10))

    # Research & Risk
    research = cam_data.get("research", {})
    elements.append(Paragraph("Research & Risk Intelligence", heading_style))
    elements.append(Paragraph(f"MCA Status: {research.get('mca_status', 'N/A')}", normal_style))
    elements.append(Paragraph(f"News Sentiment: {research.get('news_sentiment', 'N/A')}", normal_style))
    connector_status = research.get("connector_status") or {}
    if connector_status:
        elements.append(
            Paragraph(
                f"Live Connector: {connector_status.get('provider', 'N/A')} | Sources: {connector_status.get('sources_count', 'N/A')}",
                normal_style,
            )
        )
    lits = research.get("litigation_flags", [])
    if lits:
        elements.append(Paragraph("Litigation Flags:", normal_style))
        for lit in lits:
            elements.append(Paragraph(f"  • {lit}", normal_style))

    sources = (research.get("research_sources") or [])[:5]
    if sources:
        elements.append(Paragraph("Key Web Sources:", normal_style))
        for src in sources:
            title = src.get("title") or "Untitled"
            url = src.get("url") or ""
            category = src.get("category") or "web"
            elements.append(Paragraph(f"  • [{category}] {title} - {url}", small_style))
    elements.append(Spacer(1, 10))

    # Site Visit Notes
    notes = cam_data.get("site_visit_notes")
    if notes:
        elements.append(Paragraph("Field Observations (Site Visit)", heading_style))
        elements.append(Paragraph(notes, normal_style))
        elements.append(Spacer(1, 10))

    # Footer
    elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.grey))
    elements.append(Paragraph("This report was generated by Intelli-Credit AI Engine. For internal use only.", small_style))

    doc.build(elements)
    return buffer.getvalue()
