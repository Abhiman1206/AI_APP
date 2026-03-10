"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { StepProgress } from "@/components/ui/progress";
import { Button } from "@/components/ui/button";
import { RiskTimeline } from "@/components/RiskTimeline";
import { PipelineResponse } from "@/lib/types";

export default function ResearchPage() {
    const router = useRouter();
    const [data, setData] = useState<PipelineResponse | null>(null);

    useEffect(() => {
        const stored = sessionStorage.getItem("pipeline_result");
        if (stored) setData(JSON.parse(stored));
        else router.push("/demo/upload");
    }, [router]);

    if (!data) return null;

    const research = data.cam_report.research;

    return (
        <div className="page-wrapper">
            <div className="container" style={{ paddingTop: "var(--space-10)" }}>
                <StepProgress currentStep={3} />

                <div style={{ maxWidth: "800px", margin: "var(--space-10) auto 0" }}>
                    <h2 className="animate-in" style={{ marginBottom: "var(--space-2)" }}>
                        Risk Research & Timeline
                    </h2>
                    <p className="animate-in stagger-1" style={{ color: "var(--text-secondary)", marginBottom: "var(--space-8)" }}>
                        External research findings including MCA status, news sentiment, and event timeline.
                    </p>

                    {/* Quick Stats */}
                    <div
                        className="animate-in stagger-2"
                        style={{
                            display: "grid",
                            gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
                            gap: "var(--space-4)",
                            marginBottom: "var(--space-8)",
                        }}
                    >
                        <div className="stat-card">
                            <div className="stat-label">MCA Status</div>
                            <div style={{ fontWeight: 700, fontSize: "1.125rem" }}>
                                <span className="badge badge-success">{research.mca_status}</span>
                            </div>
                        </div>
                        <div className="stat-card">
                            <div className="stat-label">News Sentiment</div>
                            <div style={{ fontWeight: 700, fontSize: "1.125rem" }}>
                                <span className="badge badge-accent">{research.news_sentiment}</span>
                            </div>
                        </div>
                        <div className="stat-card">
                            <div className="stat-label">Litigation Flags</div>
                            <div style={{ fontWeight: 700, fontSize: "1.125rem", color: research.litigation_flags.length > 0 ? "var(--warning)" : "var(--success)" }}>
                                {research.litigation_flags.length}
                            </div>
                        </div>
                    </div>

                    {/* Litigation Details */}
                    {research.litigation_flags.length > 0 && (
                        <div className="animate-in stagger-3" style={{ marginBottom: "var(--space-8)" }}>
                            <h3 style={{ marginBottom: "var(--space-3)", fontSize: "1.125rem" }}>⚠️ Litigation Flags</h3>
                            {research.litigation_flags.map((flag, i) => (
                                <div
                                    key={i}
                                    style={{
                                        padding: "var(--space-3) var(--space-4)",
                                        background: "rgba(245, 158, 11, 0.08)",
                                        border: "1px solid rgba(245, 158, 11, 0.2)",
                                        borderRadius: "var(--radius-md)",
                                        fontSize: "0.9375rem",
                                        color: "var(--warning)",
                                        marginBottom: "var(--space-2)",
                                    }}
                                >
                                    {flag}
                                </div>
                            ))}
                        </div>
                    )}

                    {/* Risk Timeline */}
                    <div className="animate-in stagger-4" style={{ marginBottom: "var(--space-8)" }}>
                        <h3 style={{ marginBottom: "var(--space-4)", fontSize: "1.125rem" }}>📅 Risk Event Timeline</h3>
                        <RiskTimeline entries={research.risk_timeline} />
                    </div>

                    {/* Navigation */}
                    <div style={{ display: "flex", justifyContent: "space-between" }}>
                        <Button variant="ghost" onClick={() => router.push("/demo/extraction")}>← Back</Button>
                        <Button onClick={() => router.push("/demo/scoring")}>5Cs Scoring →</Button>
                    </div>
                </div>
            </div>
        </div>
    );
}
