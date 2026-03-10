"use client";

import React from "react";
import { FiveCsScore } from "@/lib/types";

interface FiveCsRadarProps {
    scores: FiveCsScore;
}

function ScoreBar({ label, score, rationale }: { label: string; score: number; rationale: string }) {
    const color =
        score >= 70 ? "var(--success)" : score >= 50 ? "var(--warning)" : "var(--danger)";

    return (
        <div style={{ marginBottom: "var(--space-5)" }}>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "var(--space-2)" }}>
                <span style={{ fontWeight: 600, fontSize: "0.9375rem" }}>{label}</span>
                <span style={{ fontWeight: 800, color }}>{score.toFixed(1)}</span>
            </div>
            <div
                style={{
                    height: "8px",
                    background: "var(--bg-primary)",
                    borderRadius: "4px",
                    overflow: "hidden",
                }}
            >
                <div
                    style={{
                        height: "100%",
                        width: `${score}%`,
                        background: color,
                        borderRadius: "4px",
                        transition: "width 0.8s ease",
                    }}
                />
            </div>
            <p style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: "var(--space-1)" }}>
                {rationale}
            </p>
        </div>
    );
}

export function FiveCsRadar({ scores }: FiveCsRadarProps) {
    const recommendation =
        scores.overall >= 70 ? "APPROVE" : scores.overall >= 50 ? "REFER" : "REJECT";
    const recColor =
        recommendation === "APPROVE"
            ? "var(--success)"
            : recommendation === "REFER"
                ? "var(--warning)"
                : "var(--danger)";

    return (
        <div>
            {/* Overall Score */}
            <div
                style={{
                    textAlign: "center",
                    marginBottom: "var(--space-8)",
                    padding: "var(--space-6)",
                    background: "var(--bg-primary)",
                    borderRadius: "var(--radius-lg)",
                    border: `2px solid ${recColor}`,
                }}
            >
                <div style={{ fontSize: "3.5rem", fontWeight: 900, color: recColor, lineHeight: 1 }}>
                    {scores.overall.toFixed(1)}
                </div>
                <div style={{ fontSize: "0.875rem", color: "var(--text-muted)", margin: "var(--space-2) 0" }}>
                    Overall 5Cs Score
                </div>
                <span
                    className={`badge ${recommendation === "APPROVE" ? "badge-success" : recommendation === "REFER" ? "badge-warning" : "badge-danger"}`}
                    style={{ fontSize: "0.875rem", padding: "var(--space-2) var(--space-4)" }}
                >
                    {recommendation}
                </span>
            </div>

            {/* Individual Scores */}
            <ScoreBar label="Character" score={scores.character} rationale={scores.character_rationale} />
            <ScoreBar label="Capacity" score={scores.capacity} rationale={scores.capacity_rationale} />
            <ScoreBar label="Capital" score={scores.capital} rationale={scores.capital_rationale} />
            <ScoreBar label="Collateral" score={scores.collateral} rationale={scores.collateral_rationale} />
            <ScoreBar label="Conditions" score={scores.conditions} rationale={scores.conditions_rationale} />
        </div>
    );
}
