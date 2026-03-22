"""Live Search module — Firecrawl-powered web research + AI risk synthesis."""

from __future__ import annotations

from src.ai_extractor import extract_risk_intelligence
from src.research.firecrawl_client import FirecrawlResearchClient, ResearchConnectorError


def _queries_for_company(company_name: str) -> dict[str, str]:
    return {
        "news": f"{company_name} promoter latest news adverse credit risk India",
        "regulatory": f"RBI regulations NBFC sector headwinds {company_name}",
        "litigation": f"{company_name} promoter litigation court case India",
        "mca": f"{company_name} MCA company status CIN",
        "generic": f"{company_name} credit risk red flags India",
    }


def _render_live_text(sources: list[dict]) -> str:
    if not sources:
        return ""
    blocks: list[str] = []
    for src in sources:
        blocks.append(
            "\n".join(
                [
                    f"Category: {src.get('category', '')}",
                    f"Title: {src.get('title', '')}",
                    f"Date: {src.get('published_at', '')}",
                    f"URL: {src.get('url', '')}",
                    f"Snippet: {src.get('snippet', '')}",
                ]
            )
        )
    return "\n\n--- LIVE SOURCE ---\n\n".join(blocks)


def _validate_risk_payload(risk: dict) -> None:
    required_keys = [
        "news_sentiment",
        "litigation_flags",
        "risk_timeline",
        "mca_status",
        "key_concerns",
        "key_strengths",
    ]
    missing = [key for key in required_keys if key not in risk]
    if missing:
        raise ResearchConnectorError(
            "Risk synthesis incomplete from live Firecrawl data. Missing field(s): " + ", ".join(missing)
        )


def search_company(company_name: str, all_text: str = "") -> dict:
    """Run Firecrawl live research and synthesize risk signals.

    Hard-fail behavior:
    - If any mandatory channel does not return usable results, raise ResearchConnectorError.
    """
    client = FirecrawlResearchClient(timeout=20.0, retries=2)
    queries = _queries_for_company(company_name)
    mandatory_channels = ["news", "regulatory", "litigation", "mca", "generic"]

    source_hits: list[dict] = []
    channel_counts: dict[str, int] = {}

    for channel, query in queries.items():
        results = client.search(query=query, category=channel, limit=5)
        channel_counts[channel] = len(results)
        source_hits.extend(results)

    missing = [ch for ch in mandatory_channels if channel_counts.get(ch, 0) == 0]
    if missing:
        raise ResearchConnectorError(
            "Live research incomplete. Missing source coverage for channel(s): " + ", ".join(missing)
        )

    # Intentionally ignore all_text to keep research strictly internet-sourced via Firecrawl.
    live_text = _render_live_text(source_hits)
    if not live_text:
        raise ResearchConnectorError("Live research returned no analyzable content.")

    risk = extract_risk_intelligence(company_name, live_text)
    if not isinstance(risk, dict):
        raise ResearchConnectorError("Risk synthesis returned invalid payload type.")
    _validate_risk_payload(risk)

    risk["research_sources"] = source_hits
    risk["connector_status"] = {
        "provider": "firecrawl",
        "hard_fail_policy": "enabled",
        "channels": channel_counts,
        "sources_count": len(source_hits),
    }
    return risk
