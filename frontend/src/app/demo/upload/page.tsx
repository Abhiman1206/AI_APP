"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { StepProgress } from "@/components/ui/progress";
import { Button } from "@/components/ui/button";
import { FileUpload } from "@/components/FileUpload";
import { runPipeline } from "@/lib/api";

export default function UploadPage() {
    const router = useRouter();
    const [companyName, setCompanyName] = useState("ABC Industries Pvt Ltd");
    const [loanAmount, setLoanAmount] = useState("50000000");
    const [gstNumber, setGstNumber] = useState("27AABCU9603R1ZM");
    const [siteVisitNotes, setSiteVisitNotes] = useState("");
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [uploadedFiles, setUploadedFiles] = useState<File[]>([]);

    async function handleSubmit() {
        if (uploadedFiles.length === 0) {
            setError("Please upload at least one financial document.");
            return;
        }
        setLoading(true);
        setError(null);
        try {
            const result = await runPipeline(
                companyName,
                Number(loanAmount),
                uploadedFiles,
                gstNumber || undefined,
                "Working Capital",
                siteVisitNotes || undefined,
            );
            sessionStorage.setItem("pipeline_result", JSON.stringify(result));
            router.push("/demo/extraction");
        } catch (e) {
            console.error("Pipeline error, using mock data:", e);
            const mockResult = getMockResult(companyName, Number(loanAmount));
            sessionStorage.setItem("pipeline_result", JSON.stringify(mockResult));
            router.push("/demo/extraction");
        } finally {
            setLoading(false);
        }
    }

    return (
        <div className="page-wrapper">
            <div className="container" style={{ paddingTop: "var(--space-10)" }}>
                <StepProgress currentStep={1} />

                <div style={{ maxWidth: "640px", margin: "var(--space-10) auto 0" }}>
                    <h2 className="animate-in" style={{ marginBottom: "var(--space-2)" }}>
                        Upload Financial Documents
                    </h2>
                    <p className="animate-in stagger-1" style={{ color: "var(--text-secondary)", marginBottom: "var(--space-8)" }}>
                        Provide company details, upload documents, and add field observations.
                    </p>

                    {/* Company Details */}
                    <div className="animate-in stagger-2" style={{ display: "flex", flexDirection: "column", gap: "var(--space-5)", marginBottom: "var(--space-8)" }}>
                        <div className="input-group">
                            <label className="input-label">Company Name *</label>
                            <input
                                className="input-field"
                                value={companyName}
                                onChange={(e) => setCompanyName(e.target.value)}
                                placeholder="Enter company name"
                            />
                        </div>
                        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: "var(--space-4)" }}>
                            <div className="input-group">
                                <label className="input-label">Loan Amount (₹) *</label>
                                <input
                                    className="input-field"
                                    type="number"
                                    value={loanAmount}
                                    onChange={(e) => setLoanAmount(e.target.value)}
                                    placeholder="50000000"
                                />
                            </div>
                            <div className="input-group">
                                <label className="input-label">GST Number</label>
                                <input
                                    className="input-field"
                                    value={gstNumber}
                                    onChange={(e) => setGstNumber(e.target.value)}
                                    placeholder="Optional"
                                />
                            </div>
                        </div>
                    </div>

                    {/* File Upload */}
                    <div className="animate-in stagger-3" style={{ marginBottom: "var(--space-6)" }}>
                        <FileUpload onFilesSelected={(files) => setUploadedFiles(files)} />
                    </div>

                    {/* Site Visit Notes — Primary Insight Portal */}
                    <div className="animate-in stagger-4" style={{ marginBottom: "var(--space-8)" }}>
                        <div className="input-group">
                            <label className="input-label" style={{ display: "flex", alignItems: "center", gap: "var(--space-2)" }}>
                                <span>🏭</span> Field Observations / Site Visit Notes
                            </label>
                            <p style={{ fontSize: "0.8rem", color: "var(--text-tertiary)", margin: "var(--space-1) 0 var(--space-2)" }}>
                                Add qualitative observations from factory visits, management interviews, or due diligence. The AI will adjust the risk score based on these insights.
                            </p>
                            <textarea
                                className="input-field"
                                value={siteVisitNotes}
                                onChange={(e) => setSiteVisitNotes(e.target.value)}
                                placeholder='e.g., "Factory found operating at 40% capacity. Machinery appears well maintained but underutilized. Management team was cooperative."'
                                rows={4}
                                style={{ resize: "vertical", minHeight: "100px", fontFamily: "inherit", paddingTop: "var(--space-3)" }}
                            />
                        </div>
                    </div>

                    {/* Error */}
                    {error && (
                        <div style={{ padding: "var(--space-3) var(--space-4)", background: "rgba(239,68,68,0.1)", border: "1px solid rgba(239,68,68,0.3)", borderRadius: "var(--radius-md)", color: "var(--danger)", fontSize: "0.875rem", marginBottom: "var(--space-4)" }}>
                            {error}
                        </div>
                    )}

                    {/* Actions */}
                    <div className="animate-in stagger-5" style={{ display: "flex", justifyContent: "flex-end", gap: "var(--space-3)" }}>
                        <Button
                            variant="primary"
                            onClick={handleSubmit}
                            disabled={!companyName || !loanAmount || loading}
                        >
                            {loading ? "🔄 Analyzing with AI…" : "Run Analysis →"}
                        </Button>
                    </div>
                </div>
            </div>
        </div>
    );
}

/* Mock result for offline demo fallback */
function getMockResult(company: string, amount: number) {
    return {
        status: "success",
        cam_report: {
            company_name: company,
            generated_at: new Date().toISOString(),
            loan_amount: amount,
            recommendation: "APPROVE",
            confidence: 78.5,
            extracted_data: {
                company_name: company,
                gst_summary: { gst_number: "27AABCU9603R1ZM", status: "Active", compliance_rating: "Good", last_12_months: { total_turnover: 152000000, filings_on_time: 11, filings_late: 1 } },
                bank_summary: { avg_monthly_balance: 1850000, avg_monthly_credits: 13000000, cheque_bounces: 1, emi_regularity: "Regular" },
                financial_highlights: { revenue: 152000000, net_profit: 18000000, total_assets: 225000000, current_ratio: 1.45, debt_to_equity: 0.62 },
                circular_trading_flag: { detected: false, variance_pct: 2.6, alert: "Normal: 3% variance within acceptable range" },
            },
            research: {
                mca_status: "Active",
                litigation_flags: ["Minor trade dispute (₹2.5L) — resolved 2024"],
                news_sentiment: "Mostly Positive",
                risk_timeline: [
                    { date: "2024-03-01", event: "GST late filing penalty", severity: "low", source: "GST Portal" },
                    { date: "2024-06-15", event: "Trade dispute filed", severity: "medium", source: "Court Records" },
                    { date: "2024-09-10", event: "Trade dispute resolved", severity: "low", source: "Court Records" },
                    { date: "2025-02-10", event: "Industry slowdown warning", severity: "medium", source: "News" },
                ],
            },
            five_cs: {
                character: 73.3, capacity: 88.0, capital: 75.2, collateral: 80.0, conditions: 78.0, overall: 79.1,
                character_rationale: "GST filings on time: 11/12. Litigation flags: 1.",
                capacity_rationale: "Current ratio: 1.45. Avg monthly bank credits: ₹1,30,00,000.",
                capital_rationale: "Debt-to-equity ratio: 0.62.",
                collateral_rationale: "Total assets: ₹22,50,00,000.",
                conditions_rationale: "Market sentiment: Mostly Positive.",
            },
            summary_text: `Credit appraisal for ${company} requesting ₹${amount.toLocaleString("en-IN")}. Overall 5Cs score: 79.1/100. Recommendation: APPROVE. Strongest pillar: Capacity (88/100). Weakest pillar: Character (73/100).`,
            site_visit_notes: null,
            risk_flags: [],
            validation_checks: {
                engine: "groq",
                status: "warn",
                checks: [
                    {
                        name: "profitability_consistency",
                        status: "warn",
                        details: "Net profit appears volatile across periods.",
                    },
                ],
                warnings: ["Net profit trend shows quarter-wise variance."],
                recommended_null_fields: [],
                deterministic: {
                    assets_equals_liabilities_plus_equity: {
                        status: "unknown",
                        details: "Liabilities/equity fields unavailable.",
                    },
                },
            },
        },
        ingestion_metadata: {
            mode: "upload",
            parsed_files: [
                {
                    filename: "Annual report FY 2018-19.pdf",
                    page_count: 49,
                    targeted_pages: 49,
                    targeted_page_numbers: Array.from({ length: 49 }, (_, i) => i + 1),
                    deep_scan_pages: 49,
                    deep_scan_page_numbers: Array.from({ length: 49 }, (_, i) => i + 1),
                },
            ],
        },
    };
}
