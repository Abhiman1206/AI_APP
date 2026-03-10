"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { StepProgress } from "@/components/ui/progress";
import { Button } from "@/components/ui/button";
import { FiveCsRadar } from "@/components/FiveCsRadar";
import { WhatIfSlider } from "@/components/WhatIfSlider";
import { PipelineResponse } from "@/lib/types";

export default function ScoringPage() {
    const router = useRouter();
    const [data, setData] = useState<PipelineResponse | null>(null);

    useEffect(() => {
        const stored = sessionStorage.getItem("pipeline_result");
        if (stored) setData(JSON.parse(stored));
        else router.push("/demo/upload");
    }, [router]);

    if (!data) return null;

    const fiveCs = data.cam_report.five_cs;

    return (
        <div className="page-wrapper">
            <div className="container" style={{ paddingTop: "var(--space-10)" }}>
                <StepProgress currentStep={4} />

                <div style={{ maxWidth: "900px", margin: "var(--space-10) auto 0" }}>
                    <h2 className="animate-in" style={{ marginBottom: "var(--space-2)" }}>
                        5Cs Credit Scoring
                    </h2>
                    <p className="animate-in stagger-1" style={{ color: "var(--text-secondary)", marginBottom: "var(--space-8)" }}>
                        Comprehensive scoring across Character, Capacity, Capital, Collateral, and Conditions.
                    </p>

                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "var(--space-8)" }}>
                        {/* Radar / Scores */}
                        <div className="animate-in stagger-2">
                            <FiveCsRadar scores={fiveCs} />
                        </div>

                        {/* What-If Analysis */}
                        <div className="animate-in stagger-3">
                            <h3 style={{ marginBottom: "var(--space-4)", fontSize: "1.125rem" }}>
                                🎛️ What-If Analysis
                            </h3>
                            <p style={{ color: "var(--text-muted)", fontSize: "0.875rem", marginBottom: "var(--space-5)" }}>
                                Adjust parameters to see how changes might affect the credit decision.
                            </p>
                            <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-4)" }}>
                                <WhatIfSlider
                                    label="Loan Amount"
                                    min={10_00_000}
                                    max={10_00_00_000}
                                    step={10_00_000}
                                    defaultValue={data.cam_report.loan_amount}
                                    prefix="₹"
                                />
                                <WhatIfSlider
                                    label="Current Ratio"
                                    min={0.5}
                                    max={3.0}
                                    step={0.05}
                                    defaultValue={1.45}
                                    suffix="x"
                                />
                                <WhatIfSlider
                                    label="Debt-to-Equity"
                                    min={0.1}
                                    max={3.0}
                                    step={0.05}
                                    defaultValue={0.62}
                                    suffix="x"
                                />
                            </div>
                        </div>
                    </div>

                    {/* Navigation */}
                    <div style={{ display: "flex", justifyContent: "space-between", marginTop: "var(--space-10)" }}>
                        <Button variant="ghost" onClick={() => router.push("/demo/research")}>← Back</Button>
                        <Button onClick={() => router.push("/demo/cam")}>View CAM Report →</Button>
                    </div>
                </div>
            </div>
        </div>
    );
}
