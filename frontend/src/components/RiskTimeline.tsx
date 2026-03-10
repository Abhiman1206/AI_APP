"use client";

import React from "react";
import { RiskTimelineEntry } from "@/lib/types";

interface RiskTimelineProps {
    entries: RiskTimelineEntry[];
}

export function RiskTimeline({ entries }: RiskTimelineProps) {
    return (
        <div className="timeline">
            {entries.map((entry, i) => (
                <div key={i} className="timeline-item animate-in" style={{ animationDelay: `${i * 0.1}s` }}>
                    <div className={`timeline-dot ${entry.severity}`} />
                    <div style={{ marginLeft: "var(--space-2)" }}>
                        <div style={{ display: "flex", alignItems: "center", gap: "var(--space-3)", marginBottom: "var(--space-1)" }}>
                            <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
                                {entry.date}
                            </span>
                            <span className={`badge badge-${entry.severity === "high" ? "danger" : entry.severity === "medium" ? "warning" : "success"}`}>
                                {entry.severity}
                            </span>
                        </div>
                        <p style={{ fontSize: "0.9375rem", fontWeight: 500 }}>{entry.event}</p>
                        {entry.source && (
                            <p style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: "var(--space-1)" }}>
                                Source: {entry.source}
                            </p>
                        )}
                    </div>
                </div>
            ))}
        </div>
    );
}
