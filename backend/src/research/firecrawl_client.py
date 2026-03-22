"""Firecrawl client utilities for live research connectors.

This module centralizes Firecrawl API calls and response normalization for:
- company/promoter news
- RBI/sector regulation updates
- litigation signals
- MCA/company profile lookups
- generic web enrichment
"""

from __future__ import annotations

import os
import time
from typing import Any

import httpx


FIRECRAWL_BASE_URL = "https://api.firecrawl.dev/v1"


class ResearchConnectorError(RuntimeError):
    """Raised when live research connectors fail or return unusable data."""


class FirecrawlResearchClient:
    def __init__(self, timeout: float = 20.0, retries: int = 2) -> None:
        self.api_key = os.getenv("FIRECRAWL_API_KEY")
        self.timeout = timeout
        self.retries = max(0, retries)

    def _require_api_key(self) -> str:
        if not self.api_key:
            raise ResearchConnectorError("FIRECRAWL_API_KEY is missing. Live research cannot run.")
        return self.api_key

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        api_key = self._require_api_key()
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        url = f"{FIRECRAWL_BASE_URL}{path}"
        last_err: Exception | None = None

        for attempt in range(self.retries + 1):
            try:
                with httpx.Client(timeout=self.timeout) as client:
                    response = client.post(url, json=payload, headers=headers)

                if response.status_code in (401, 403):
                    raise ResearchConnectorError("Firecrawl authentication failed. Check FIRECRAWL_API_KEY.")

                if response.status_code >= 500:
                    raise ResearchConnectorError(
                        f"Firecrawl server error ({response.status_code}): {response.text[:240]}"
                    )

                if response.status_code >= 400:
                    raise ResearchConnectorError(
                        f"Firecrawl request failed ({response.status_code}): {response.text[:240]}"
                    )

                data = response.json()
                if not isinstance(data, dict):
                    raise ResearchConnectorError("Firecrawl returned invalid JSON payload.")
                return data
            except (httpx.TimeoutException, httpx.TransportError, ResearchConnectorError) as exc:
                last_err = exc
                if attempt >= self.retries:
                    break
                time.sleep(0.5 * (attempt + 1))

        raise ResearchConnectorError(f"Firecrawl call failed after retries: {last_err}")

    @staticmethod
    def _extract_items(payload: dict[str, Any]) -> list[dict[str, Any]]:
        if isinstance(payload.get("data"), list):
            return [x for x in payload["data"] if isinstance(x, dict)]

        data = payload.get("data")
        if isinstance(data, dict):
            for key in ("web", "results", "items", "links"):
                value = data.get(key)
                if isinstance(value, list):
                    return [x for x in value if isinstance(x, dict)]

        for key in ("results", "items"):
            value = payload.get(key)
            if isinstance(value, list):
                return [x for x in value if isinstance(x, dict)]

        return []

    @staticmethod
    def _normalize_item(item: dict[str, Any], category: str) -> dict[str, Any] | None:
        metadata = item.get("metadata") if isinstance(item.get("metadata"), dict) else {}
        url = item.get("url") or item.get("link")
        if not url:
            return None

        title = item.get("title") or metadata.get("title") or "Untitled"
        snippet = (
            item.get("description")
            or item.get("snippet")
            or item.get("markdown")
            or item.get("content")
            or ""
        )
        published_at = (
            item.get("publishedDate")
            or item.get("published_at")
            or metadata.get("publishedDate")
            or metadata.get("published_at")
            or ""
        )

        return {
            "url": str(url),
            "title": str(title)[:240],
            "snippet": str(snippet)[:1200],
            "published_at": str(published_at)[:80],
            "category": category,
            "source": str(metadata.get("source") or metadata.get("siteName") or "firecrawl"),
        }

    def search(self, query: str, category: str, limit: int = 5) -> list[dict[str, Any]]:
        payload = {
            "query": query,
            "limit": max(1, min(limit, 10)),
            "scrapeOptions": {"formats": ["markdown"]},
        }
        raw = self._post("/search", payload)
        items = self._extract_items(raw)
        normalized: list[dict[str, Any]] = []
        for item in items:
            entry = self._normalize_item(item, category=category)
            if entry:
                normalized.append(entry)

        # De-duplicate by URL preserving order
        seen = set()
        unique: list[dict[str, Any]] = []
        for hit in normalized:
            url = hit["url"]
            if url in seen:
                continue
            seen.add(url)
            unique.append(hit)
        return unique
