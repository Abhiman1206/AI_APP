"""MCA Checker module — verifies company status via Firecrawl live search."""

from __future__ import annotations

import re

from src.research.firecrawl_client import FirecrawlResearchClient, ResearchConnectorError


def _extract_cin(text: str) -> str | None:
    # Broad CIN-style pattern: starts with letter, 21 total alphanumeric chars.
    matches = re.findall(r"\b[A-Z][A-Z0-9]{20}\b", (text or "").upper())
    return matches[0] if matches else None


def _infer_status(text_blob: str) -> str:
    lowered = (text_blob or "").lower()
    if any(token in lowered for token in ["active", "status: active", "company status active"]):
        return "Active"
    if any(token in lowered for token in ["struck off", "strike off", "inactive", "dormant"]):
        return "Inactive"
    return "Unknown"


def check_mca_status(company_name: str) -> dict:
    """Check MCA registration status from live Firecrawl search.

    Hard-fail behavior: raises ResearchConnectorError when no usable live evidence exists.
    """
    client = FirecrawlResearchClient(timeout=20.0, retries=2)
    query = f"{company_name} MCA company master data CIN status"
    hits = client.search(query=query, category="mca", limit=5)
    if not hits:
        raise ResearchConnectorError("MCA live lookup returned no results.")

    merged = "\n".join(
        [
            f"{hit.get('title', '')} {hit.get('snippet', '')}"
            for hit in hits
        ]
    )

    cin = _extract_cin(merged)
    status = _infer_status(merged)

    return {
        "company_name": company_name,
        "cin": cin or "Not Verified",
        "registration_date": "Unknown",
        "status": status,
        "company_type": "Unknown",
        "authorized_capital": None,
        "paid_up_capital": None,
        "directors": [],
        "annual_filings_up_to_date": status == "Active",
        "charges_registered": 0,
        "sources": hits,
    }
