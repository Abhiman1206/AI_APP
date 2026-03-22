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
    research_sources?: {
        url: string;
        title: string;
        snippet?: string;
        published_at?: string;
        category?: string;
        source?: string;
    }[];
    connector_status?: {
        provider?: string;
        hard_fail_policy?: string;
        channels?: Record<string, number>;
        sources_count?: number;
    };
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
    validation_checks?: ValidationChecks;
}

export interface ValidationCheckItem {
    name: string;
    status: "pass" | "warn" | "fail" | "unknown";
    details: string;
}

export interface ValidationDeterministicCheck {
    status: "pass" | "warn" | "fail" | "unknown";
    details: string;
}

export interface ValidationChecks {
    engine: string;
    status: "pass" | "warn" | "fail" | "unknown";
    checks: ValidationCheckItem[];
    warnings: string[];
    recommended_null_fields: string[];
    deterministic?: Record<string, ValidationDeterministicCheck>;
}

export interface ParsedFileIngestion {
    filename: string;
    page_count: number;
    targeted_pages: number;
    targeted_page_numbers?: number[];
    deep_scan_pages?: number;
    deep_scan_page_numbers?: number[];
    category?: string;
    page_index?: {
        document_id: string;
        artifact_path: string;
        entry_count: number;
    };
    metadata?: Record<string, unknown>;
    error?: string;
}

export interface IngestionMetadata {
    mode: "upload" | "batch" | string;
    parsed_files: ParsedFileIngestion[];
    page_index_files?: {
        document_id: string;
        artifact_path: string;
        entry_count: number;
    }[];
}

export interface PipelineResponse {
    status: string;
    cam_report: CAMReport;
    ingestion_metadata?: IngestionMetadata;
}
