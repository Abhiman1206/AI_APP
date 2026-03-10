from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class PipelineRequest(BaseModel):
    company_name: str = Field(..., description="Name of the company to analyze")
    gst_number: Optional[str] = Field(None, description="GST registration number")
    pan_number: Optional[str] = Field(None, description="PAN of the company/individual")
    loan_amount: float = Field(..., description="Requested loan amount in INR")
    loan_purpose: str = Field("Working Capital", description="Purpose of the loan")


class ExtractedData(BaseModel):
    company_name: str
    gst_summary: Optional[dict] = None
    bank_summary: Optional[dict] = None
    financial_highlights: Optional[dict] = None
    circular_trading_flag: Optional[dict] = None


class FiveCsScore(BaseModel):
    character: float = Field(..., ge=0, le=100, description="Character score (0-100)")
    capacity: float = Field(..., ge=0, le=100, description="Capacity score (0-100)")
    capital: float = Field(..., ge=0, le=100, description="Capital score (0-100)")
    collateral: float = Field(..., ge=0, le=100, description="Collateral score (0-100)")
    conditions: float = Field(..., ge=0, le=100, description="Conditions score (0-100)")
    overall: float = Field(..., ge=0, le=100, description="Weighted overall score")

    character_rationale: str = ""
    capacity_rationale: str = ""
    capital_rationale: str = ""
    collateral_rationale: str = ""
    conditions_rationale: str = ""


class RiskTimelineEntry(BaseModel):
    date: str
    event: str
    severity: str = Field(..., description="low | medium | high")
    source: str = ""


class ResearchResult(BaseModel):
    mca_status: Optional[str] = None
    litigation_flags: list[str] = []
    news_sentiment: Optional[str] = None
    risk_timeline: list[RiskTimelineEntry] = []


class CAMReport(BaseModel):
    company_name: str
    generated_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    loan_amount: float
    recommendation: str = Field(..., description="APPROVE | REJECT | REFER")
    confidence: float = Field(..., ge=0, le=100)
    extracted_data: ExtractedData
    research: ResearchResult
    five_cs: FiveCsScore
    summary_text: str = ""
    site_visit_notes: Optional[str] = None
    risk_flags: list[str] = []


class PipelineResponse(BaseModel):
    status: str = "success"
    cam_report: CAMReport
