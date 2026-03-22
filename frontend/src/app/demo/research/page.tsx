"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { StepProgress } from "@/components/ui/progress";
import { Button } from "@/components/ui/button";
import { RiskTimeline } from "@/components/RiskTimeline";
import { PipelineResponse } from "@/lib/types";

export default function ResearchPage() {
    const router = useRouter();
    const [data] = useState<PipelineResponse | null>(() => {
        if (typeof window === "undefined") return null;
        const stored = sessionStorage.getItem("pipeline_result");
        return stored ? (JSON.parse(stored) as PipelineResponse) : null;
    });

    useEffect(() => {
        if (!data) router.push("/demo/upload");
    }, [data, router]);

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

                    {research.connector_status && (
                        <div className="animate-in stagger-2" style={{ marginBottom: "var(--space-6)", fontSize: "0.85rem", color: "var(--text-secondary)" }}>
                            Live Connector: {research.connector_status.provider || "Unknown"} | Source Count: {research.connector_status.sources_count ?? 0}
                        </div>
                    )}

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

                    {(research.research_sources || []).length > 0 && (
                        <div className="animate-in stagger-4" style={{ marginBottom: "var(--space-8)" }}>
                            <h3 style={{ marginBottom: "var(--space-4)", fontSize: "1.125rem" }}>🌐 Source Evidence</h3>
                            <div style={{ display: "grid", gap: "var(--space-2)" }}>
                                {(research.research_sources || []).slice(0, 8).map((src, idx) => (
                                    <a
                                        key={`${src.url}-${idx}`}
                                        href={src.url}
                                        target="_blank"
                                        rel="noreferrer"
                                        style={{
                                            display: "block",
                                            border: "1px solid var(--border)",
                                            borderRadius: "var(--radius-md)",
                                            padding: "var(--space-3)",
                                            color: "var(--text-secondary)",
                                            textDecoration: "none",
                                        }}
                                    >
                                        <div style={{ fontWeight: 600, color: "var(--text-primary)", marginBottom: "var(--space-1)" }}>{src.title}</div>
                                        <div style={{ fontSize: "0.8rem" }}>{src.category || "web"} • {src.published_at || "date unknown"}</div>
                                    </a>
                                ))}
                            </div>
                        </div>
                    )}

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
