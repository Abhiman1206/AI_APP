import os
import shutil
import tempfile
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import io

from src.models import PipelineResponse
from src.ingestor.pdf_parser import parse_pdf
from src.ingestor.gst_analyzer import analyze_gst
from src.ingestor.bank_extractor import extract_bank_data
from src.research.mock_search import search_company
from src.research.mca_checker import check_mca_status
from src.engine.five_cs import calculate_five_cs, detect_circular_trading
from src.engine.cam_generator import generate_cam
from src.engine.cam_pdf_exporter import generate_cam_pdf
from src.ai_extractor import extract_financial_data

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

app = FastAPI(title="Intelli-Credit API", version="0.3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory store for latest CAM report (prototype)
_latest_cam: dict | None = None


@app.get("/")
def health_check():
    return {"status": "healthy", "service": "intelli-credit-backend", "version": "0.3.0"}


@app.post("/api/pipeline/run", response_model=PipelineResponse)
async def run_pipeline(
    company_name: str = Form(...),
    loan_amount: float = Form(...),
    gst_number: Optional[str] = Form(None),
    loan_purpose: str = Form("Working Capital"),
    site_visit_notes: Optional[str] = Form(None),
    files: list[UploadFile] = File(...),
):
    """Execute the full credit analysis pipeline with real PDF processing.

    Steps:
    1. Save uploaded files to temp directory
    2. Extract text from PDFs using pdfplumber
    3. Use Groq AI to extract structured financial data
    4. Analyze GST and Bank data via AI
    5. Detect circular trading (GST vs Bank cross-check)
    6. Perform risk analysis via AI
    7. Calculate 5Cs scoring (with site visit notes)
    8. Generate explainable CAM report
    """
    global _latest_cam
    tmp_dir = tempfile.mkdtemp()

    try:
        # Step 1: Save uploaded files and extract text
        all_texts = []
        extracted_data_raw = {}

        for upload_file in files:
            file_path = os.path.join(tmp_dir, upload_file.filename or "upload.pdf")
            with open(file_path, "wb") as f:
                content = await upload_file.read()
                f.write(content)

            parsed = parse_pdf(file_path)
            all_texts.append(parsed["extracted_text"])

        combined_text = "\n\n--- NEXT DOCUMENT ---\n\n".join(all_texts)

        # Step 2: AI-powered financial data extraction
        try:
            extracted_data_raw = extract_financial_data(combined_text)
        except Exception:
            extracted_data_raw = {}

        # Step 3: GST analysis via AI
        gst_data = analyze_gst(combined_text, gst_number)

        # Step 4: Bank statement analysis via AI
        bank_data = extract_bank_data(combined_text)

        # Step 5: Circular trading detection (Pillar 1 — GST vs Bank cross-check)
        circular_flag = detect_circular_trading(gst_data, bank_data)

        # Step 6: Risk research via AI
        research_data = search_company(company_name, combined_text)

        # Step 7: MCA check (still mock for prototype)
        mca_data = check_mca_status(company_name)
        research_data["mca_status"] = mca_data.get("status", "Unknown")

        # Build extracted_data dict for scoring
        financial_highlights = {
            "revenue": extracted_data_raw.get("revenue"),
            "net_profit": extracted_data_raw.get("net_profit"),
            "total_assets": extracted_data_raw.get("total_assets"),
            "current_ratio": extracted_data_raw.get("current_ratio", 1.0),
            "debt_to_equity": extracted_data_raw.get("debt_to_equity", 1.0),
        }

        extracted_data = {
            "financial_highlights": financial_highlights,
            "tables": extracted_data_raw.get("tables", []),
        }

        # Step 8: 5Cs Scoring with site visit notes (Pillar 2)
        five_cs = calculate_five_cs(
            extracted_data, bank_data, gst_data, research_data,
            site_visit_notes=site_visit_notes,
        )

        # Step 9: Explainable CAM Generation (Pillar 3)
        cam_report = generate_cam(
            company_name=company_name,
            loan_amount=loan_amount,
            extracted_data=extracted_data,
            bank_data=bank_data,
            gst_data=gst_data,
            research_data=research_data,
            five_cs=five_cs,
            circular_flag=circular_flag,
            site_visit_notes=site_visit_notes,
        )

        # Store for PDF export
        _latest_cam = cam_report.model_dump()

        return PipelineResponse(cam_report=cam_report)

    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


@app.get("/api/pipeline/export/pdf")
def export_cam_pdf():
    """Export the latest CAM report as a professional PDF document."""
    global _latest_cam
    if not _latest_cam:
        return {"error": "No CAM report available. Run the pipeline first."}

    pdf_buffer = generate_cam_pdf(_latest_cam)
    company = _latest_cam.get("company_name", "Report").replace(" ", "_")

    return StreamingResponse(
        io.BytesIO(pdf_buffer),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=CAM_{company}.pdf"},
    )
