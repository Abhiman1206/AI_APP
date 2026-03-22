import os
import shutil
import tempfile
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import io

from src.models import PipelineResponse
from src.ingestor.pdf_parser import parse_pdf
from src.ingestor.gst_analyzer import analyze_gst
from src.ingestor.bank_extractor import extract_bank_data
from src.ingestor.batch_ingestor import ingest_directory
from src.research.live_search import search_company
from src.research.mca_checker import check_mca_status
from src.research.firecrawl_client import ResearchConnectorError
from src.engine.five_cs import calculate_five_cs, detect_circular_trading
from src.engine.cam_generator import generate_cam
from src.engine.cam_pdf_exporter import generate_cam_pdf
from src.engine.risk_model import (
    build_risk_features,
    score_credit_application,
    detect_application_anomaly,
)
from src.ai_extractor import extract_financial_data, validate_financial_consistency

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

app = FastAPI(title="Intelli-Credit API", version="0.4.0")

# Path to the local Data folder (sibling of the backend directory)
DATA_FOLDER = Path(__file__).resolve().parent.parent / "Data"

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
    return {"status": "healthy", "service": "intelli-credit-backend", "version": "0.4.0"}


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
        # Step 1: Save uploaded files and categorize text
        all_texts = []
        categorized_text = {
            "financial": [],
            "bank": [],
            "gst": [],
            "other": []
        }
        
        extracted_data_raw = {}
        parsed_file_metadata = []

        for upload_file in files:
            file_name = upload_file.filename or "upload.pdf"
            file_path = os.path.join(tmp_dir, file_name)
            with open(file_path, "wb") as f:
                content = await upload_file.read()
                f.write(content)

            parsed = parse_pdf(file_path)
            extracted = parsed["extracted_text"]
            all_texts.append(extracted)
            parsed_file_metadata.append(
                {
                    "filename": parsed.get("filename"),
                    "page_count": parsed.get("page_count"),
                    "targeted_pages": parsed.get("targeted_pages"),
                    "targeted_page_numbers": parsed.get("targeted_page_numbers", []),
                    "deep_scan_pages": parsed.get("deep_scan_pages", 0),
                    "deep_scan_page_numbers": parsed.get("deep_scan_page_numbers", []),
                    "metadata": parsed.get("metadata", {}),
                }
            )
            
            # Smart Document Routing based on filename or content keywords
            fname_lower = file_name.lower()
            if any(k in fname_lower for k in ["bank", "statement", "hdfc", "sbi", "icici", "axis"]):
                categorized_text["bank"].append(extracted)
            elif any(k in fname_lower for k in ["gst", "return", "gstr"]):
                categorized_text["gst"].append(extracted)
            elif any(k in fname_lower for k in ["annual", "report", "financial", "standalone", "consolidated", "balance"]):
                categorized_text["financial"].append(extracted)
            else:
                categorized_text["other"].append(extracted)

        combined_text = "\n\n--- NEXT DOCUMENT ---\n\n".join(all_texts)
        
        # Prepare routed strings
        fin_text = "\n\n".join(categorized_text["financial"]) or combined_text
        gst_text = "\n\n".join(categorized_text["gst"]) or combined_text
        bank_text = "\n\n".join(categorized_text["bank"]) or combined_text

        # Step 2: AI-powered financial data extraction (routed)
        try:
            extracted_data_raw = extract_financial_data(fin_text)
        except Exception:
            extracted_data_raw = {}

        # Step 3: GST analysis via AI (routed)
        gst_data = analyze_gst(gst_text, gst_number)

        # Step 4: Bank statement analysis via AI (routed)
        bank_data = extract_bank_data(bank_text)

        # Step 5: Circular trading detection (Pillar 1 — GST vs Bank cross-check)
        circular_flag = detect_circular_trading(gst_data, bank_data)

        # Step 6: Risk research via live connectors + AI synthesis
        try:
            research_data = search_company(company_name, combined_text)
            mca_data = check_mca_status(company_name)
        except ResearchConnectorError as exc:
            raise HTTPException(status_code=502, detail=f"Live research connector failure: {exc}")

        # Step 7: MCA status merge from live connector
        research_data["mca_status"] = mca_data.get("status", "Unknown")
        research_data.setdefault("research_sources", [])
        research_data["research_sources"].extend(mca_data.get("sources", []))

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

        validation_result = validate_financial_consistency(financial_highlights)

        # Step 8: 5Cs Scoring with site visit notes (Pillar 2)
        five_cs = calculate_five_cs(
            extracted_data, bank_data, gst_data, research_data,
            site_visit_notes=site_visit_notes,
        )

        # Step 8.1: ML scoring + anomaly detection + explainability
        risk_features = build_risk_features(financial_highlights, bank_data, gst_data, research_data)
        ml_result = score_credit_application(risk_features)
        anomaly_result = detect_application_anomaly(risk_features)

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
            ml_result=ml_result,
            anomaly_result=anomaly_result,
            validation_result=validation_result,
        )

        # Store for PDF export
        _latest_cam = cam_report.model_dump()

        return PipelineResponse(
            cam_report=cam_report,
            ingestion_metadata={
                "mode": "upload",
                "parsed_files": parsed_file_metadata,
            },
        )

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


# ---------------------------------------------------------------------------
# Batch ingestion endpoints — process from the local Data folder
# ---------------------------------------------------------------------------

@app.get("/api/pipeline/data-folder")
def list_data_folder_files():
    """List all PDF files available in the local Data folder.

    Returns file names, sizes (bytes), and a total count so the frontend can
    display what documents will be consumed by /api/pipeline/run-batch.
    """
    if not DATA_FOLDER.is_dir():
        raise HTTPException(
            status_code=404,
            detail=f"Data folder not found at expected path: {DATA_FOLDER}",
        )

    pdf_files = sorted(
        f for f in DATA_FOLDER.iterdir()
        if f.is_file() and f.suffix.lower() == ".pdf"
    )

    file_list = [
        {"filename": f.name, "size_bytes": f.stat().st_size}
        for f in pdf_files
    ]
    total_mb = sum(f["size_bytes"] for f in file_list) / (1024 * 1024)

    return {
        "data_folder": str(DATA_FOLDER),
        "total_files": len(file_list),
        "total_size_mb": round(total_mb, 2),
        "files": file_list,
    }


@app.post("/api/pipeline/run-batch", response_model=PipelineResponse)
async def run_batch_pipeline(
    company_name: str = Form(...),
    loan_amount: float = Form(...),
    gst_number: Optional[str] = Form(None),
    loan_purpose: str = Form("Working Capital"),
    site_visit_notes: Optional[str] = Form(None),
):
    """Execute the full credit analysis pipeline using PDFs from the Data folder.

    Unlike /api/pipeline/run (which requires file uploads), this endpoint reads
    all PDFs already present in the local Data folder.  Useful for bulk
    processing, demos, and hackathon evaluation with the provided dataset.

    Steps:
    1. Batch-ingest all PDFs from the Data folder (parse + AI extraction)
    2. Detect circular trading (GST vs bank cross-check)
    3. Merge AI-extracted risk intelligence with mock MCA status
    4. Calculate 5Cs scoring (with optional site visit notes)
    5. Generate explainable CAM report
    """
    global _latest_cam

    if not DATA_FOLDER.is_dir():
        raise HTTPException(
            status_code=404,
            detail=f"Data folder not found: {DATA_FOLDER}",
        )

    # Step 1: Batch ingestion from Data folder
    ingestion = ingest_directory(
        str(DATA_FOLDER),
        company_name=company_name,
        gst_number=gst_number,
    )

    financial_data = ingestion.get("financial_data", {})
    gst_data       = ingestion.get("gst_data", {})
    bank_data      = ingestion.get("bank_data", {})
    risk_ai        = ingestion.get("risk_intelligence", {})

    # Ensure gst_data has a known gst_number if supplied
    if gst_number and not gst_data.get("gst_number"):
        gst_data["gst_number"] = gst_number

    # Step 2: Circular trading detection
    circular_flag = detect_circular_trading(gst_data, bank_data)

    # Step 3: Merge ingested risk data with live research connectors
    try:
        research_data = search_company(company_name, ingestion.get("combined_text", ""))
        mca_data = check_mca_status(company_name)
    except ResearchConnectorError as exc:
        raise HTTPException(status_code=502, detail=f"Live research connector failure: {exc}")

    # Backfill with ingestion-level risk AI fields if present.
    for key in ("news_sentiment", "litigation_flags", "risk_timeline", "key_concerns", "key_strengths"):
        if key not in research_data and key in risk_ai:
            research_data[key] = risk_ai[key]

    research_data["mca_status"] = mca_data.get("status", "Unknown")
    research_data.setdefault("research_sources", [])
    research_data["research_sources"].extend(mca_data.get("sources", []))

    # Step 4: Build financial highlights for scoring
    financial_highlights = {
        "revenue":        financial_data.get("revenue"),
        "net_profit":     financial_data.get("net_profit"),
        "total_assets":   financial_data.get("total_assets"),
        "current_ratio":  financial_data.get("current_ratio", 1.0),
        "debt_to_equity": financial_data.get("debt_to_equity", 1.0),
    }

    extracted_data = {
        "financial_highlights": financial_highlights,
        "tables": financial_data.get("tables", []),
    }

    validation_result = validate_financial_consistency(financial_highlights)

    # Step 5: 5Cs scoring
    five_cs = calculate_five_cs(
        extracted_data, bank_data, gst_data, research_data,
        site_visit_notes=site_visit_notes,
    )

    # Step 5.1: ML scoring + anomaly detection + explainability
    risk_features = build_risk_features(financial_highlights, bank_data, gst_data, research_data)
    ml_result = score_credit_application(risk_features)
    anomaly_result = detect_application_anomaly(risk_features)

    # Step 6: Explainable CAM generation
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
        ml_result=ml_result,
        anomaly_result=anomaly_result,
        validation_result=validation_result,
    )

    _latest_cam = cam_report.model_dump()
    return PipelineResponse(
        cam_report=cam_report,
        ingestion_metadata={
            "mode": "batch",
            "parsed_files": ingestion.get("parsed_files", []),
            "routing_summary": ingestion.get("routing_summary", {}),
            "page_index_files": ingestion.get("page_index_files", []),
            "errors": ingestion.get("errors", []),
        },
    )
