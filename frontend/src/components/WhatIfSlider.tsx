"use client";

import React, { useState } from "react";

interface WhatIfSliderProps {
    label: string;
    min: number;
    max: number;
    step?: number;
    defaultValue: number;
    prefix?: string;
    suffix?: string;
    onChange?: (value: number) => void;
}

export function WhatIfSlider({
    label,
    min,
    max,
    step = 1,
    defaultValue,
    prefix = "",
    suffix = "",
    onChange,
}: WhatIfSliderProps) {
    const [value, setValue] = useState(defaultValue);

    function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
        const v = Number(e.target.value);
        setValue(v);
        onChange?.(v);
    }

    return (
        <div
            style={{
                padding: "var(--space-4) var(--space-5)",
                background: "var(--bg-card)",
                border: "1px solid var(--border)",
                borderRadius: "var(--radius-md)",
            }}
        >
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "var(--space-3)" }}>
                <span style={{ fontSize: "0.875rem", fontWeight: 600, color: "var(--text-secondary)" }}>
                    {label}
                </span>
                <span style={{ fontSize: "0.9375rem", fontWeight: 700, color: "var(--accent)" }}>
                    {prefix}{value.toLocaleString("en-IN")}{suffix}
                </span>
            </div>
            <input
                type="range"
                className="range-slider"
                min={min}
                max={max}
                step={step}
                value={value}
                onChange={handleChange}
            />
            <div
                style={{
                    display: "flex",
                    justifyContent: "space-between",
                    marginTop: "var(--space-1)",
                    fontSize: "0.75rem",
                    color: "var(--text-muted)",
                }}
            >
                <span>{prefix}{min.toLocaleString("en-IN")}{suffix}</span>
                <span>{prefix}{max.toLocaleString("en-IN")}{suffix}</span>
            </div>
        </div>
    );
}
