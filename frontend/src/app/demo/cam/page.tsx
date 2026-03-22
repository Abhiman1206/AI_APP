"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { StepProgress } from "@/components/ui/progress";
import { Button } from "@/components/ui/button";
import { CAMPreview } from "@/components/CAMPreview";
import { PipelineResponse } from "@/lib/types";
import { downloadCamPdf } from "@/lib/api";

export default function CAMPage() {
    const router = useRouter();
    const [data] = useState<PipelineResponse | null>(() => {
        if (typeof window === "undefined") return null;
        const stored = sessionStorage.getItem("pipeline_result");
        return stored ? (JSON.parse(stored) as PipelineResponse) : null;
    });
    const [downloading, setDownloading] = useState(false);

    useEffect(() => {
        if (!data) router.push("/demo/upload");
    }, [data, router]);

    if (!data) return null;

    function handleDownloadJSON() {
        const json = JSON.stringify(data!.cam_report, null, 2);
        const blob = new Blob([json], { type: "application/json" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `CAM_${data!.cam_report.company_name.replace(/\s+/g, "_")}.json`;
        a.click();
        URL.revokeObjectURL(url);
    }

    async function handleDownloadPDF() {
        setDownloading(true);
        try {
            const blob = await downloadCamPdf();
            const url = URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = `CAM_${data!.cam_report.company_name.replace(/\s+/g, "_")}.pdf`;
            a.click();
            URL.revokeObjectURL(url);
        } catch (e) {
            console.error("PDF download failed:", e);
            alert("PDF export failed. Please ensure the backend is running.");
        } finally {
            setDownloading(false);
        }
    }

    const report = data.cam_report;
    const parsedFiles = data.ingestion_metadata?.parsed_files || [];

    return (
        <div className="page-wrapper">
            <div className="container" style={{ paddingTop: "var(--space-10)" }}>
                <StepProgress currentStep={5} />

                <div style={{ maxWidth: "960px", margin: "var(--space-10) auto 0" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "var(--space-6)" }}>
                        <div>
                            <h2 className="animate-in" style={{ marginBottom: "var(--space-2)" }}>
                                Credit Appraisal Memorandum
                            </h2>
                            <p className="animate-in stagger-1" style={{ color: "var(--text-secondary)" }}>
                                Complete CAM report with AI-powered explainability.
                            </p>
                        </div>
                        <div className="animate-in stagger-1" style={{ display: "flex", gap: "var(--space-2)" }}>
                            <Button onClick={handleDownloadJSON}>
                                📄 JSON
                            </Button>
                            <Button variant="primary" onClick={handleDownloadPDF} disabled={downloading}>
                                {downloading ? "⏳ Generating…" : "📥 Download PDF"}
                            </Button>
                        </div>
                    </div>

                    {/* Risk Flags */}
                    {report.risk_flags && report.risk_flags.length > 0 && (
                        <div className="animate-in stagger-2" style={{
                            padding: "var(--space-4)",
                            background: "rgba(239,68,68,0.08)",
                            border: "1px solid rgba(239,68,68,0.25)",
                            borderRadius: "var(--radius-lg)",
                            marginBottom: "var(--space-6)",
                        }}>
                            <h4 style={{ color: "var(--danger)", marginBottom: "var(--space-2)", fontSize: "0.9rem" }}>⚠️ Risk Flags</h4>
                            {report.risk_flags.map((flag: string, i: number) => (
                                <p key={i} style={{ color: "var(--danger)", fontSize: "0.85rem", margin: "var(--space-1) 0" }}>• {flag}</p>
                            ))}
                        </div>
                    )}

                    {/* Circular Trading Alert */}
                    {report.extracted_data?.circular_trading_flag?.detected && (
                        <div className="animate-in stagger-2" style={{
                            padding: "var(--space-4)",
                            background: "rgba(245,158,11,0.08)",
                            border: "1px solid rgba(245,158,11,0.25)",
                            borderRadius: "var(--radius-lg)",
                            marginBottom: "var(--space-6)",
                        }}>
                            <h4 style={{ color: "var(--warning)", marginBottom: "var(--space-2)", fontSize: "0.9rem" }}>🔄 Circular Trading Detection</h4>
                            <p style={{ color: "var(--warning)", fontSize: "0.85rem" }}>{report.extracted_data.circular_trading_flag.alert}</p>
                            <p style={{ color: "var(--text-secondary)", fontSize: "0.8rem", marginTop: "var(--space-1)" }}>
                                GST-Bank Variance: {report.extracted_data.circular_trading_flag.variance_pct}%
                            </p>
                        </div>
                    )}

                    {/* Site Visit Notes */}
                    {report.site_visit_notes && (
                        <div className="animate-in stagger-2" style={{
                            padding: "var(--space-4)",
                            background: "rgba(20,184,166,0.06)",
                            border: "1px solid rgba(20,184,166,0.2)",
                            borderRadius: "var(--radius-lg)",
                            marginBottom: "var(--space-6)",
                        }}>
                            <h4 style={{ color: "var(--primary)", marginBottom: "var(--space-2)", fontSize: "0.9rem" }}>🏭 Field Observations</h4>
                            <p style={{ color: "var(--text-secondary)", fontSize: "0.85rem", fontStyle: "italic" }}>
                                &quot;{report.site_visit_notes}&quot;
                            </p>
                        </div>
                    )}

                    {/* Ingestion Details */}
                    {parsedFiles.length > 0 && (
                        <div
                            className="animate-in stagger-2"
                            style={{
                                padding: "var(--space-4)",
                                background: "rgba(26,197,174,0.06)",
                                border: "1px solid rgba(26,197,174,0.22)",
                                borderRadius: "var(--radius-lg)",
                                marginBottom: "var(--space-6)",
                            }}
                        >
                            <h4 style={{ color: "var(--accent)", marginBottom: "var(--space-3)", fontSize: "0.95rem" }}>
                                🧭 Ingestion Details
                            </h4>

                            <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-3)" }}>
                                {parsedFiles.map((f) => (
                                    <details
                                        key={f.filename}
                                        style={{
                                            background: "rgba(11, 17, 27, 0.45)",
                                            border: "1px solid var(--border)",
                                            borderRadius: "var(--radius-md)",
                                            padding: "var(--space-3) var(--space-4)",
                                        }}
                                    >
                                        <summary
                                            style={{
                                                cursor: "pointer",
                                                fontWeight: 700,
                                                color: "var(--text-primary)",
                                                display: "flex",
                                                alignItems: "center",
                                                justifyContent: "space-between",
                                                gap: "var(--space-3)",
                                            }}
                                        >
                                            <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                                                {f.filename}
                                            </span>
                                            <span className="badge badge-info" style={{ textTransform: "none" }}>
                                                {f.page_count} pages
                                            </span>
                                        </summary>

                                        <div style={{ marginTop: "var(--space-3)", display: "grid", gap: "var(--space-2)" }}>
                                            <div style={{ fontSize: "0.8125rem", color: "var(--text-secondary)" }}>
                                                Targeted Pages: <strong>{f.targeted_pages}</strong>
                                            </div>
                                            <div style={{ fontSize: "0.8125rem", color: "var(--text-secondary)" }}>
                                                Deep Scan Pages: <strong>{f.deep_scan_pages ?? 0}</strong>
                                            </div>

                                            {f.targeted_page_numbers && f.targeted_page_numbers.length > 0 && (
                                                <div>
                                                    <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginBottom: "var(--space-1)" }}>
                                                        Full Targeted Page Numbers
                                                    </div>
                                                    <div
                                                        style={{
                                                            fontSize: "0.78rem",
                                                            color: "var(--text-secondary)",
                                                            lineHeight: 1.55,
                                                            maxHeight: "90px",
                                                            overflowY: "auto",
                                                            padding: "var(--space-2)",
                                                            background: "rgba(15, 23, 42, 0.55)",
                                                            border: "1px solid var(--border)",
                                                            borderRadius: "var(--radius-sm)",
                                                        }}
                                                    >
                                                        {f.targeted_page_numbers.join(", ")}
                                                    </div>
                                                </div>
                                            )}

                                            {f.deep_scan_page_numbers && f.deep_scan_page_numbers.length > 0 && (
                                                <div>
                                                    <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginBottom: "var(--space-1)" }}>
                                                        Deep Scan Page Numbers
                                                    </div>
                                                    <div
                                                        style={{
                                                            fontSize: "0.78rem",
                                                            color: "var(--text-secondary)",
                                                            lineHeight: 1.55,
                                                            maxHeight: "90px",
                                                            overflowY: "auto",
                                                            padding: "var(--space-2)",
                                                            background: "rgba(15, 23, 42, 0.55)",
                                                            border: "1px solid var(--border)",
                                                            borderRadius: "var(--radius-sm)",
                                                        }}
                                                    >
                                                        {f.deep_scan_page_numbers.join(", ")}
                                                    </div>
                                                </div>
                                            )}
                                        </div>
                                    </details>
                                ))}
                            </div>
                        </div>
                    )}

                    <div className="animate-in stagger-3">
                        <CAMPreview report={data.cam_report} />
                    </div>

                    {/* Navigation */}
                    <div style={{ display: "flex", justifyContent: "space-between", marginTop: "var(--space-8)" }}>
                        <Button variant="ghost" onClick={() => router.push("/demo/scoring")}>← Back</Button>
                        <Button variant="secondary" onClick={() => {
                            sessionStorage.removeItem("pipeline_result");
                            router.push("/demo/upload");
                        }}>
                            🔄 New Analysis
                        </Button>
                    </div>
                </div>
            </div>
        </div>
    );
}
