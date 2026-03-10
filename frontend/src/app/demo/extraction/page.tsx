"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { StepProgress } from "@/components/ui/progress";
import { Button } from "@/components/ui/button";
import { Card, StatCard } from "@/components/ui/card";
import { PipelineResponse } from "@/lib/types";

export default function ExtractionPage() {
    const router = useRouter();
    const [data, setData] = useState<PipelineResponse | null>(null);

    useEffect(() => {
        const stored = sessionStorage.getItem("pipeline_result");
        if (stored) setData(JSON.parse(stored));
        else router.push("/demo/upload");
    }, [router]);

    if (!data) return null;

    const report = data.cam_report;
    const fin = report.extracted_data.financial_highlights as Record<string, number> | undefined;
    const gst = report.extracted_data.gst_summary as Record<string, unknown> | undefined;
    const bank = report.extracted_data.bank_summary as Record<string, unknown> | undefined;

    return (
        <div className="page-wrapper">
            <div className="container" style={{ paddingTop: "var(--space-10)" }}>
                <StepProgress currentStep={2} />

                <div style={{ maxWidth: "900px", margin: "var(--space-10) auto 0" }}>
                    <h2 className="animate-in" style={{ marginBottom: "var(--space-2)" }}>
                        Extracted Financial Data
                    </h2>
                    <p className="animate-in stagger-1" style={{ color: "var(--text-secondary)", marginBottom: "var(--space-8)" }}>
                        Key metrics parsed from uploaded documents for <strong>{report.company_name}</strong>.
                    </p>

                    {/* Financial Highlights */}
                    {fin && (
                        <div className="animate-in stagger-2" style={{ marginBottom: "var(--space-8)" }}>
                            <h3 style={{ marginBottom: "var(--space-4)", fontSize: "1.125rem" }}>📊 Financial Highlights</h3>
                            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: "var(--space-4)" }}>
                                <StatCard label="Revenue" value={`₹${(fin.revenue / 10000000).toFixed(1)} Cr`} color="var(--accent)" />
                                <StatCard label="Net Profit" value={`₹${(fin.net_profit / 10000000).toFixed(1)} Cr`} color="var(--success)" />
                                <StatCard label="Total Assets" value={`₹${(fin.total_assets / 10000000).toFixed(1)} Cr`} />
                                <StatCard label="Current Ratio" value={fin.current_ratio?.toFixed(2)} color="var(--info)" />
                                <StatCard label="Debt/Equity" value={fin.debt_to_equity?.toFixed(2)} color="var(--warning)" />
                            </div>
                        </div>
                    )}

                    {/* GST Summary */}
                    {gst && (
                        <Card className="animate-in stagger-3" style={{ marginBottom: "var(--space-6)" }}>
                            <h3 style={{ marginBottom: "var(--space-4)", fontSize: "1.125rem" }}>🧾 GST Summary</h3>
                            <table className="data-table">
                                <tbody>
                                    <tr><td style={{ fontWeight: 600 }}>GST Number</td><td>{String(gst.gst_number || "N/A")}</td></tr>
                                    <tr><td style={{ fontWeight: 600 }}>Status</td><td><span className="badge badge-success">{String(gst.status || "N/A")}</span></td></tr>
                                    <tr><td style={{ fontWeight: 600 }}>Compliance</td><td>{String(gst.compliance_rating || "N/A")}</td></tr>
                                </tbody>
                            </table>
                        </Card>
                    )}

                    {/* Bank Summary */}
                    {bank && (
                        <Card className="animate-in stagger-4" style={{ marginBottom: "var(--space-8)" }}>
                            <h3 style={{ marginBottom: "var(--space-4)", fontSize: "1.125rem" }}>🏦 Bank Statement Summary</h3>
                            <table className="data-table">
                                <tbody>
                                    <tr><td style={{ fontWeight: 600 }}>Avg Monthly Balance</td><td>₹{Number(bank.avg_monthly_balance).toLocaleString("en-IN")}</td></tr>
                                    <tr><td style={{ fontWeight: 600 }}>Avg Monthly Credits</td><td>₹{Number(bank.avg_monthly_credits).toLocaleString("en-IN")}</td></tr>
                                    <tr><td style={{ fontWeight: 600 }}>Cheque Bounces</td><td>{String(bank.cheque_bounces)}</td></tr>
                                    <tr><td style={{ fontWeight: 600 }}>EMI Regularity</td><td><span className="badge badge-success">{String(bank.emi_regularity)}</span></td></tr>
                                </tbody>
                            </table>
                        </Card>
                    )}

                    {/* Navigation */}
                    <div style={{ display: "flex", justifyContent: "space-between" }}>
                        <Button variant="ghost" onClick={() => router.push("/demo/upload")}>← Back</Button>
                        <Button onClick={() => router.push("/demo/research")}>Risk Research →</Button>
                    </div>
                </div>
            </div>
        </div>
    );
}
