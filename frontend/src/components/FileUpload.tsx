"use client";

import React, { useState } from "react";

interface FileUploadProps {
    onFilesSelected?: (files: File[]) => void;
}

export function FileUpload({ onFilesSelected }: FileUploadProps) {
    const [dragActive, setDragActive] = useState(false);
    const [files, setFiles] = useState<File[]>([]);

    function handleDrag(e: React.DragEvent) {
        e.preventDefault();
        e.stopPropagation();
        setDragActive(e.type === "dragenter" || e.type === "dragover");
    }

    function handleDrop(e: React.DragEvent) {
        e.preventDefault();
        e.stopPropagation();
        setDragActive(false);
        const dropped = Array.from(e.dataTransfer.files);
        setFiles(dropped);
        onFilesSelected?.(dropped);
    }

    function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
        if (e.target.files) {
            const selected = Array.from(e.target.files);
            setFiles(selected);
            onFilesSelected?.(selected);
        }
    }

    return (
        <div>
            <div
                className={`upload-zone ${dragActive ? "active" : ""}`}
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
                onClick={() => document.getElementById("file-input")?.click()}
            >
                <div style={{ fontSize: "3rem", marginBottom: "var(--space-4)" }}>
                    📄
                </div>
                <p style={{ fontSize: "1.125rem", fontWeight: 600, marginBottom: "var(--space-2)" }}>
                    Drop financial documents here
                </p>
                <p style={{ color: "var(--text-muted)", fontSize: "0.875rem" }}>
                    PDF, Excel, or CSV — Balance sheets, P&L, GST returns, Bank statements
                </p>
                <input
                    id="file-input"
                    type="file"
                    multiple
                    accept=".pdf,.csv,.xlsx,.xls"
                    onChange={handleChange}
                    style={{ display: "none" }}
                />
            </div>

            {files.length > 0 && (
                <div style={{ marginTop: "var(--space-4)", display: "flex", flexDirection: "column", gap: "var(--space-2)" }}>
                    {files.map((f) => (
                        <div
                            key={f.name}
                            style={{
                                display: "flex",
                                alignItems: "center",
                                gap: "var(--space-3)",
                                padding: "var(--space-3) var(--space-4)",
                                background: "var(--bg-card)",
                                borderRadius: "var(--radius-md)",
                                border: "1px solid var(--border)",
                            }}
                        >
                            <span>📎</span>
                            <span style={{ flex: 1, fontSize: "0.875rem" }}>{f.name}</span>
                            <span className="badge badge-success">Ready</span>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
