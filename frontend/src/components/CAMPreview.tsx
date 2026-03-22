"use client";

import React from "react";
import { CAMReport } from "@/lib/types";

interface CAMPreviewProps {
    report: CAMReport;
}

export function CAMPreview({ report }: CAMPreviewProps) {
    const recColor =
        report.recommendation === "APPROVE"
            ? "var(--success)"
            : report.recommendation === "REFER"
                ? "var(--warning)"
                : "var(--danger)";

    return (
        <div
            style={{
                background: "var(--bg-card)",
                border: "1px solid var(--border)",
                borderRadius: "var(--radius-lg)",
                overflow: "hidden",
            }}
        >
            {/* Header */}
            <div
                style={{
                    padding: "var(--space-6) var(--space-8)",
                    borderBottom: "1px solid var(--border)",
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                }}
            >
                <div>
                    <h3 style={{ marginBottom: "var(--space-1)" }}>
                        Credit Appraisal Memorandum
                    </h3>
                    <p style={{ fontSize: "0.875rem", color: "var(--text-muted)" }}>
                        Generated: {new Date(report.generated_at).toLocaleString()}
                    </p>
                </div>
                <span
                    className={`badge ${report.recommendation === "APPROVE" ? "badge-success" : report.recommendation === "REFER" ? "badge-warning" : "badge-danger"}`}
                    style={{ fontSize: "1rem", padding: "var(--space-2) var(--space-5)" }}
                >
                    {report.recommendation}
                </span>
            </div>

            {/* Body */}
            <div style={{ padding: "var(--space-6) var(--space-8)" }}>
                {/* Key Facts */}
                <div
                    style={{
                        display: "grid",
                        gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
                        gap: "var(--space-4)",
                        marginBottom: "var(--space-6)",
                    }}
                >
                    <div className="stat-card">
                        <div className="stat-label">Company</div>
                        <div style={{ fontWeight: 700, fontSize: "1.125rem" }}>{report.company_name}</div>
                    </div>
                    <div className="stat-card">
                        <div className="stat-label">Loan Amount</div>
                        <div style={{ fontWeight: 700, fontSize: "1.125rem" }}>
                            ₹{report.loan_amount.toLocaleString("en-IN")}
                        </div>
                    </div>
                    <div className="stat-card">
                        <div className="stat-label">Confidence</div>
                        <div style={{ fontWeight: 700, fontSize: "1.125rem", color: recColor }}>
                            {report.confidence}%
                        </div>
                    </div>
                    <div className="stat-card">
                        <div className="stat-label">5Cs Score</div>
                        <div style={{ fontWeight: 700, fontSize: "1.125rem", color: recColor }}>
                            {report.five_cs.overall}/100
                        </div>
                    </div>
                </div>

                {/* Summary */}
                <div style={{ marginBottom: "var(--space-6)" }}>
                    <h4 style={{ marginBottom: "var(--space-3)", color: "var(--text-secondary)" }}>
                        Executive Summary
                    </h4>
                    <p style={{ fontSize: "0.9375rem", lineHeight: 1.7, color: "var(--text-secondary)" }}>
                        {report.summary_text}
                    </p>
                </div>

                {/* Validation Checks */}
                {report.validation_checks && (
                    <div style={{ marginBottom: "var(--space-6)" }}>
                        <h4 style={{ marginBottom: "var(--space-3)", color: "var(--text-secondary)" }}>
                            Validation Checks
                        </h4>
                        <div style={{ display: "flex", gap: "var(--space-2)", flexWrap: "wrap", marginBottom: "var(--space-3)" }}>
                            <span className="badge badge-info">Engine: {report.validation_checks.engine}</span>
                            <span
                                className={`badge ${
                                    report.validation_checks.status === "pass"
                                        ? "badge-success"
                                        : report.validation_checks.status === "fail"
                                            ? "badge-danger"
                                            : "badge-warning"
                                }`}
                            >
                                Status: {report.validation_checks.status}
                            </span>
                        </div>

                        {report.validation_checks.checks.length > 0 && (
                            <table className="data-table" style={{ marginBottom: "var(--space-3)" }}>
                                <thead>
                                    <tr>
                                        <th>Check</th>
                                        <th>Status</th>
                                        <th>Details</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {report.validation_checks.checks.map((check, idx) => (
                                        <tr key={`${check.name}-${idx}`}>
                                            <td style={{ fontWeight: 600 }}>{check.name}</td>
                                            <td>
                                                <span
                                                    className={`badge ${
                                                        check.status === "pass"
                                                            ? "badge-success"
                                                            : check.status === "fail"
                                                                ? "badge-danger"
                                                                : check.status === "unknown"
                                                                    ? "badge-info"
                                                                    : "badge-warning"
                                                    }`}
                                                >
                                                    {check.status}
                                                </span>
                                            </td>
                                            <td>{check.details}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        )}

                        {report.validation_checks.warnings.length > 0 && (
                            <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-2)" }}>
                                {report.validation_checks.warnings.map((w, i) => (
                                    <div
                                        key={`${w}-${i}`}
                                        style={{
                                            fontSize: "0.8125rem",
                                            color: "var(--warning)",
                                            background: "rgba(245, 158, 11, 0.12)",
                                            border: "1px solid rgba(245, 158, 11, 0.22)",
                                            borderRadius: "var(--radius-sm)",
                                            padding: "var(--space-2) var(--space-3)",
                                        }}
                                    >
                                        {w}
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                )}

                {/* Research Highlights */}
                <div style={{ marginBottom: "var(--space-6)" }}>
                    <h4 style={{ marginBottom: "var(--space-3)", color: "var(--text-secondary)" }}>
                        Research Highlights
                    </h4>
                    <div style={{ display: "flex", gap: "var(--space-3)", flexWrap: "wrap" }}>
                        <span className="badge badge-info">MCA: {report.research.mca_status}</span>
                        <span className="badge badge-accent">
                            Sentiment: {report.research.news_sentiment}
                        </span>
                        {report.research.litigation_flags.length > 0 && (
                            <span className="badge badge-warning">
                                {report.research.litigation_flags.length} litigation flag(s)
                            </span>
                        )}
                    </div>

                    {report.research.connector_status && (
                        <div style={{ marginTop: "var(--space-3)", fontSize: "0.8125rem", color: "var(--text-muted)" }}>
                            Live Connector: {report.research.connector_status.provider || "Unknown"} | Sources: {report.research.connector_status.sources_count ?? 0}
                        </div>
                    )}

                    {(report.research.research_sources || []).length > 0 && (
                        <div style={{ marginTop: "var(--space-3)", display: "grid", gap: "var(--space-2)" }}>
                            {(report.research.research_sources || []).slice(0, 5).map((src, idx) => (
                                <a
                                    key={`${src.url}-${idx}`}
                                    href={src.url}
                                    target="_blank"
                                    rel="noreferrer"
                                    style={{
                                        display: "block",
                                        padding: "var(--space-2) var(--space-3)",
                                        border: "1px solid var(--border)",
                                        borderRadius: "var(--radius-sm)",
                                        textDecoration: "none",
                                        color: "var(--text-secondary)",
                                        fontSize: "0.8125rem",
                                    }}
                                >
                                    <strong style={{ color: "var(--text-primary)" }}>{src.title}</strong>
                                    <div>{src.category || "web"} • {src.published_at || "date unknown"}</div>
                                </a>
                            ))}
                        </div>
                    )}
                </div>

                {/* 5Cs Breakdown Table */}
                <div>
                    <h4 style={{ marginBottom: "var(--space-3)", color: "var(--text-secondary)" }}>
                        5Cs Breakdown
                    </h4>
                    <table className="data-table">
                        <thead>
                            <tr>
                                <th>Dimension</th>
                                <th>Score</th>
                                <th>Rationale</th>
                            </tr>
                        </thead>
                        <tbody>
                            {(["character", "capacity", "capital", "collateral", "conditions"] as const).map(
                                (dim) => (
                                    <tr key={dim}>
                                        <td style={{ fontWeight: 600, textTransform: "capitalize" }}>{dim}</td>
                                        <td
                                            style={{
                                                fontWeight: 700,
                                                color:
                                                    report.five_cs[dim] >= 70
                                                        ? "var(--success)"
                                                        : report.five_cs[dim] >= 50
                                                            ? "var(--warning)"
                                                            : "var(--danger)",
                                            }}
                                        >
                                            {report.five_cs[dim].toFixed(1)}
                                        </td>
                                        <td>{report.five_cs[`${dim}_rationale`]}</td>
                                    </tr>
                                )
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}
