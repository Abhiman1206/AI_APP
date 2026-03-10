import React from "react";

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
    children: React.ReactNode;
    accent?: boolean;
}

export function Card({ children, accent, className = "", ...props }: CardProps) {
    return (
        <div className={`card ${accent ? "card-accent" : ""} ${className}`} {...props}>
            {children}
        </div>
    );
}

export function StatCard({
    label,
    value,
    color,
}: {
    label: string;
    value: string | number;
    color?: string;
}) {
    return (
        <div className="stat-card">
            <div className="stat-label">{label}</div>
            <div className="stat-value" style={color ? { color } : undefined}>
                {value}
            </div>
        </div>
    );
}
