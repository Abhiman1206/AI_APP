"use client";

import React from "react";

const STEPS = ["Upload", "Extraction", "Research", "Scoring", "CAM"];

interface StepProgressProps {
    currentStep: number; // 1-based
}

export function StepProgress({ currentStep }: StepProgressProps) {
    return (
        <div className="step-progress">
            {STEPS.map((label, i) => {
                const step = i + 1;
                const isCompleted = step < currentStep;
                const isActive = step === currentStep;
                return (
                    <React.Fragment key={label}>
                        <div className="step-item">
                            <div
                                className={`step-circle ${isActive ? "active" : ""} ${isCompleted ? "completed" : ""}`}
                            >
                                {isCompleted ? "✓" : step}
                            </div>
                            <span
                                className={`step-label ${isActive ? "active" : ""}`}
                            >
                                {label}
                            </span>
                        </div>
                        {i < STEPS.length - 1 && (
                            <div
                                className={`step-connector ${isCompleted ? "completed" : ""}`}
                            />
                        )}
                    </React.Fragment>
                );
            })}
        </div>
    );
}
