import { PipelineResponse } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function runPipeline(
    companyName: string,
    loanAmount: number,
    files: File[],
    gstNumber?: string,
    loanPurpose?: string,
    siteVisitNotes?: string,
): Promise<PipelineResponse> {
    const formData = new FormData();
    formData.append("company_name", companyName);
    formData.append("loan_amount", loanAmount.toString());
    if (gstNumber) formData.append("gst_number", gstNumber);
    formData.append("loan_purpose", loanPurpose || "Working Capital");
    if (siteVisitNotes) formData.append("site_visit_notes", siteVisitNotes);

    for (const file of files) {
        formData.append("files", file);
    }

    const res = await fetch(`${API_BASE}/api/pipeline/run`, {
        method: "POST",
        body: formData,
    });

    if (!res.ok) {
        const text = await res.text();
        throw new Error(`Pipeline failed: ${res.status} — ${text}`);
    }

    return res.json();
}

export async function downloadCamPdf(): Promise<Blob> {
    const res = await fetch(`${API_BASE}/api/pipeline/export/pdf`);
    if (!res.ok) throw new Error("Failed to download CAM PDF");
    return res.blob();
}
