export interface PipelineRequest {
    company_name: string;
    gst_number?: string;
    pan_number?: string;
    loan_amount: number;
    loan_purpose?: string;
}

export interface ExtractedData {
    company_name: string;
    gst_summary?: Record<string, unknown>;
    bank_summary?: Record<string, unknown>;
    financial_highlights?: Record<string, unknown>;
    circular_trading_flag?: {
        detected: boolean;
        variance_pct: number | null;
        alert: string;
    };
}

export interface FiveCsScore {
    character: number;
    capacity: number;
    capital: number;
    collateral: number;
    conditions: number;
    overall: number;
    character_rationale: string;
    capacity_rationale: string;
    capital_rationale: string;
    collateral_rationale: string;
    conditions_rationale: string;
}

export interface RiskTimelineEntry {
    date: string;
    event: string;
    severity: "low" | "medium" | "high";
    source: string;
}

export interface ResearchResult {
    mca_status?: string;
    litigation_flags: string[];
    news_sentiment?: string;
    risk_timeline: RiskTimelineEntry[];
}

export interface CAMReport {
    company_name: string;
    generated_at: string;
    loan_amount: number;
    recommendation: "APPROVE" | "REJECT" | "REFER";
    confidence: number;
    extracted_data: ExtractedData;
    research: ResearchResult;
    five_cs: FiveCsScore;
    summary_text: string;
    site_visit_notes?: string | null;
    risk_flags?: string[];
}

export interface PipelineResponse {
    status: string;
    cam_report: CAMReport;
}
