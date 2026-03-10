"""Generate synthetic test PDFs for the Intelli-Credit prototype.

Creates 3 realistic test PDFs:
1. Balance Sheet / P&L Statement
2. GST Return Summary
3. Bank Statement

Usage: python scripts/generate_test_pdfs.py
"""

import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet


OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "test_pdfs")


def create_balance_sheet():
    """Generate a synthetic balance sheet and P&L PDF."""
    filepath = os.path.join(OUTPUT_DIR, "balance_sheet_abc_industries.pdf")
    doc = SimpleDocTemplate(filepath, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("ABC Industries Pvt Ltd", styles["Title"]))
    elements.append(Paragraph("Annual Financial Statement — FY 2024-25", styles["Heading2"]))
    elements.append(Spacer(1, 20))

    elements.append(Paragraph("Profit & Loss Statement", styles["Heading3"]))
    pl_data = [
        ["Particulars", "FY 2024-25 (₹)", "FY 2023-24 (₹)"],
        ["Revenue from Operations", "15,20,00,000", "12,80,00,000"],
        ["Other Income", "45,00,000", "30,00,000"],
        ["Total Income", "15,65,00,000", "13,10,00,000"],
        ["Cost of Materials", "8,20,00,000", "7,10,00,000"],
        ["Employee Benefit Expense", "2,10,00,000", "1,85,00,000"],
        ["Other Expenses", "1,80,00,000", "1,55,00,000"],
        ["EBITDA", "3,55,00,000", "2,60,00,000"],
        ["Depreciation", "65,00,000", "55,00,000"],
        ["Interest", "45,00,000", "40,00,000"],
        ["Profit Before Tax", "2,45,00,000", "1,65,00,000"],
        ["Tax (30%)", "65,00,000", "45,00,000"],
        ["Net Profit", "1,80,00,000", "1,20,00,000"],
    ]
    table = Table(pl_data, colWidths=[250, 140, 140])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E293B")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F1F5F9")]),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 30))

    elements.append(Paragraph("Balance Sheet", styles["Heading3"]))
    bs_data = [
        ["Particulars", "Amount (₹)"],
        ["ASSETS", ""],
        ["Fixed Assets", "8,50,00,000"],
        ["Current Assets", "14,00,00,000"],
        ["   Inventory", "3,50,00,000"],
        ["   Trade Receivables", "5,20,00,000"],
        ["   Cash & Bank", "3,80,00,000"],
        ["   Other Current Assets", "1,50,00,000"],
        ["Total Assets", "22,50,00,000"],
        ["", ""],
        ["LIABILITIES", ""],
        ["Share Capital", "5,00,00,000"],
        ["Reserves & Surplus", "7,85,00,000"],
        ["Long-term Borrowings", "3,00,00,000"],
        ["Current Liabilities", "6,65,00,000"],
        ["   Trade Payables", "4,20,00,000"],
        ["   Short-term Borrowings", "1,45,00,000"],
        ["   Other Current Liabilities", "1,00,00,000"],
        ["Total Liabilities", "22,50,00,000"],
    ]
    table = Table(bs_data, colWidths=[300, 200])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E293B")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F1F5F9")]),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 20))

    elements.append(Paragraph("Key Ratios", styles["Heading3"]))
    ratios_data = [
        ["Ratio", "Value"],
        ["Current Ratio", "1.45"],
        ["Debt-to-Equity Ratio", "0.62"],
        ["Return on Equity", "14.0%"],
        ["Net Profit Margin", "11.8%"],
        ["Operating Cash Flow / Revenue", "18.5%"],
    ]
    table = Table(ratios_data, colWidths=[250, 150])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E293B")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    elements.append(table)

    doc.build(elements)
    print(f"✅ Created: {filepath}")


def create_gst_return():
    """Generate a synthetic GST Return Summary PDF."""
    filepath = os.path.join(OUTPUT_DIR, "gst_return_abc_industries.pdf")
    doc = SimpleDocTemplate(filepath, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("GST Return Summary", styles["Title"]))
    elements.append(Paragraph("ABC Industries Pvt Ltd", styles["Heading2"]))
    elements.append(Spacer(1, 10))
    elements.append(Paragraph("GSTIN: 27AABCU9603R1ZM", styles["Normal"]))
    elements.append(Paragraph("Registration Date: 15-Jul-2018", styles["Normal"]))
    elements.append(Paragraph("Status: Active", styles["Normal"]))
    elements.append(Paragraph("Filing Frequency: Monthly", styles["Normal"]))
    elements.append(Paragraph("Compliance Rating: Good", styles["Normal"]))
    elements.append(Spacer(1, 20))

    elements.append(Paragraph("Monthly Filing Summary (Apr 2024 - Mar 2025)", styles["Heading3"]))
    gst_data = [
        ["Month", "Turnover (₹)", "Tax Paid (₹)", "Filing Status", "Filing Date"],
        ["Apr 2024", "1,10,00,000", "19,80,000", "On Time", "20-May-2024"],
        ["May 2024", "1,15,00,000", "20,70,000", "On Time", "18-Jun-2024"],
        ["Jun 2024", "1,22,00,000", "21,96,000", "On Time", "19-Jul-2024"],
        ["Jul 2024", "1,30,00,000", "23,40,000", "On Time", "20-Aug-2024"],
        ["Aug 2024", "1,25,00,000", "22,50,000", "On Time", "18-Sep-2024"],
        ["Sep 2024", "1,35,00,000", "24,30,000", "Late", "25-Oct-2024"],
        ["Oct 2024", "1,28,00,000", "23,04,000", "On Time", "19-Nov-2024"],
        ["Nov 2024", "1,32,00,000", "23,76,000", "On Time", "20-Dec-2024"],
        ["Dec 2024", "1,40,00,000", "25,20,000", "On Time", "18-Jan-2025"],
        ["Jan 2025", "1,38,00,000", "24,84,000", "On Time", "19-Feb-2025"],
        ["Feb 2025", "1,20,00,000", "21,60,000", "On Time", "20-Mar-2025"],
        ["Mar 2025", "1,25,00,000", "22,50,000", "On Time", "18-Apr-2025"],
    ]
    table = Table(gst_data, colWidths=[70, 100, 90, 80, 90])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E293B")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F1F5F9")]),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 15))
    elements.append(Paragraph("Total Turnover: ₹15,20,00,000 | On-time Filings: 11/12 | Late: 1/12 | Missed: 0/12", styles["Normal"]))

    doc.build(elements)
    print(f"✅ Created: {filepath}")


def create_bank_statement():
    """Generate a synthetic Bank Statement PDF."""
    filepath = os.path.join(OUTPUT_DIR, "bank_statement_abc_industries.pdf")
    doc = SimpleDocTemplate(filepath, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("Bank Statement", styles["Title"]))
    elements.append(Paragraph("State Bank of India — Current Account", styles["Heading2"]))
    elements.append(Spacer(1, 10))
    elements.append(Paragraph("Account Holder: ABC Industries Pvt Ltd", styles["Normal"]))
    elements.append(Paragraph("Account Number: XXXX-XXXX-4521", styles["Normal"]))
    elements.append(Paragraph("Period: April 2024 to March 2025", styles["Normal"]))
    elements.append(Spacer(1, 20))

    elements.append(Paragraph("Monthly Cash Flow Summary", styles["Heading3"]))
    bank_data = [
        ["Month", "Credits (₹)", "Debits (₹)", "Closing Balance (₹)"],
        ["Apr 2024", "1,15,00,000", "1,08,00,000", "22,00,000"],
        ["May 2024", "1,20,00,000", "1,12,00,000", "30,00,000"],
        ["Jun 2024", "1,28,00,000", "1,18,00,000", "40,00,000"],
        ["Jul 2024", "1,35,00,000", "1,25,00,000", "50,00,000"],
        ["Aug 2024", "1,22,00,000", "1,20,00,000", "52,00,000"],
        ["Sep 2024", "1,38,00,000", "1,28,00,000", "62,00,000"],
        ["Oct 2024", "1,30,00,000", "1,22,00,000", "70,00,000"],
        ["Nov 2024", "1,34,00,000", "1,26,00,000", "78,00,000"],
        ["Dec 2024", "1,42,00,000", "1,30,00,000", "90,00,000"],
        ["Jan 2025", "1,40,00,000", "1,32,00,000", "98,00,000"],
        ["Feb 2025", "1,18,00,000", "1,15,00,000", "1,01,00,000"],
        ["Mar 2025", "1,28,00,000", "1,20,00,000", "1,09,00,000"],
    ]
    table = Table(bank_data, colWidths=[80, 120, 120, 130])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E293B")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F1F5F9")]),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 15))
    elements.append(Paragraph("Average Monthly Balance: ₹18,50,000", styles["Normal"]))
    elements.append(Paragraph("Average Monthly Credits: ₹1,30,00,000", styles["Normal"]))
    elements.append(Paragraph("Cheque Bounces: 1 (₹85,000 — Jun 2024)", styles["Normal"]))
    elements.append(Paragraph("EMI Regularity: Regular (no defaults)", styles["Normal"]))

    doc.build(elements)
    print(f"✅ Created: {filepath}")


if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    create_balance_sheet()
    create_gst_return()
    create_bank_statement()
    print(f"\n📁 All test PDFs saved to: {OUTPUT_DIR}")
