import os
import sys
import unittest
from unittest.mock import patch

sys.path.append(os.path.dirname(__file__))

from src.research.firecrawl_client import ResearchConnectorError
from src.research.mca_checker import check_mca_status
from src.research.live_search import search_company


class TestResearchConnectors(unittest.TestCase):
    def test_missing_firecrawl_key_hard_fails(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ResearchConnectorError):
                search_company("Acme Industries", "sample corpus")

    def test_search_company_requires_all_mandatory_channels(self):
        def fake_search(self, query, category, limit=5):
            if category == "litigation":
                return []
            return [
                {
                    "url": f"https://example.com/{category}",
                    "title": f"{category} title",
                    "snippet": "sample snippet",
                    "published_at": "2026-01-01",
                    "category": category,
                    "source": "firecrawl",
                }
            ]

        with patch.dict(os.environ, {"FIRECRAWL_API_KEY": "dummy-key"}, clear=False), \
            patch("src.research.live_search.FirecrawlResearchClient.search", new=fake_search), \
            patch("src.research.live_search.extract_risk_intelligence", return_value={}):
            with self.assertRaises(ResearchConnectorError) as exc:
                search_company("Acme Industries", "sample corpus")

        self.assertIn("Missing source coverage", str(exc.exception))

    def test_search_company_returns_connector_metadata(self):
        def fake_search(self, query, category, limit=5):
            return [
                {
                    "url": f"https://example.com/{category}",
                    "title": f"{category} title",
                    "snippet": "sample snippet",
                    "published_at": "2026-01-01",
                    "category": category,
                    "source": "firecrawl",
                }
            ]

        risk_payload = {
            "news_sentiment": "Negative",
            "litigation_flags": ["Active dispute reported"],
            "risk_timeline": [
                {
                    "date": "2026-01-01",
                    "event": "Adverse filing update",
                    "severity": "medium",
                    "source": "news",
                }
            ],
            "mca_status": "Active",
            "key_concerns": ["Regulatory headwinds"],
            "key_strengths": ["Steady collections"],
        }

        with patch.dict(os.environ, {"FIRECRAWL_API_KEY": "dummy-key"}, clear=False), \
            patch("src.research.live_search.FirecrawlResearchClient.search", new=fake_search), \
            patch("src.research.live_search.extract_risk_intelligence", return_value=risk_payload):
            result = search_company("Acme Industries", "sample corpus")

        self.assertIn("research_sources", result)
        self.assertIn("connector_status", result)
        self.assertEqual(result["connector_status"]["provider"], "firecrawl")
        self.assertEqual(result["connector_status"]["hard_fail_policy"], "enabled")

    def test_search_company_hard_fails_on_incomplete_risk_payload(self):
        def fake_search(self, query, category, limit=5):
            return [
                {
                    "url": f"https://example.com/{category}",
                    "title": f"{category} title",
                    "snippet": "sample snippet",
                    "published_at": "2026-01-01",
                    "category": category,
                    "source": "firecrawl",
                }
            ]

        with patch.dict(os.environ, {"FIRECRAWL_API_KEY": "dummy-key"}, clear=False), \
            patch("src.research.live_search.FirecrawlResearchClient.search", new=fake_search), \
            patch("src.research.live_search.extract_risk_intelligence", return_value={}):
            with self.assertRaises(ResearchConnectorError) as exc:
                search_company("Acme Industries", "sample corpus")

        self.assertIn("Missing field(s)", str(exc.exception))

    def test_mca_checker_hard_fails_without_live_hits(self):
        with patch.dict(os.environ, {"FIRECRAWL_API_KEY": "dummy-key"}, clear=False), \
            patch("src.research.mca_checker.FirecrawlResearchClient.search", return_value=[]):
            with self.assertRaises(ResearchConnectorError):
                check_mca_status("Acme Industries")


if __name__ == "__main__":
    unittest.main()
