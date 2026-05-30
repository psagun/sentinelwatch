"""Tests for the ThreatCollector module."""

import pytest
from datetime import datetime, timezone

from src.data_collection.threat_collector import (
    ThreatCollector,
    ThreatFinding,
)


class TestThreatFinding:
    def test_creation(self):
        finding = ThreatFinding(
            source_type="cve_feed",
            source_url="https://nvd.nist.gov/vuln/detail/CVE-2026-1234",
            title="CVE-2026-1234 Critical RCE in ExampleLib",
            description="Remote code execution vulnerability",
            severity="critical",
            indicators=["CVE-2026-1234"],
            entity_id="TestOrg",
        )
        assert finding.finding_type == "threat"
        assert finding.severity == "critical"
        assert "CVE-2026-1234" in finding.indicators
        assert finding.timestamp is not None

    def test_to_dict(self):
        finding = ThreatFinding(
            source_type="security_blog",
            source_url="https://example.com/blog",
            title="Test Alert",
            description="Description",
            severity="high",
            entity_id="Org1",
        )
        d = finding.to_dict()
        assert d["title"] == "Test Alert"
        assert d["severity"] == "high"
        assert d["finding_type"] == "threat"
        assert "timestamp" in d


class TestThreatCollector:
    @pytest.mark.asyncio
    async def test_collect_no_entities(self):
        collector = ThreatCollector(monitored_entities=[])
        findings = await collector.collect()
        assert findings == []

    @pytest.mark.asyncio
    async def test_collect_with_entities(
        self, monkeypatch
    ):
        collector = ThreatCollector(
            monitored_entities=[
                {
                    "name": "Test Corp",
                    "metadata": {
                        "domains": ["testcorp.com"],
                        "keywords": ["testcorp"],
                    },
                }
            ]
        )

        # Mock SERP API
        async def mock_serp_search(*args, **kwargs):
            return [
                {
                    "title": "CVE-2026-9999",
                    "snippet": "Critical vuln in testcorp",
                    "url": "https://nvd.nist.gov/CVE-2026-9999",
                }
            ]

        monkeypatch.setattr(
            "src.data_collection.brightdata_client.brightdata.serp_search",
            mock_serp_search,
        )

        findings = await collector.collect()
        assert len(findings) > 0

    def test_infer_severity(self):
        collector = ThreatCollector()
        assert (
            collector._infer_severity("Critical zero-day exploit")
            == "critical"
        )
        assert (
            collector._infer_severity("New vulnerability found")
            == "high"
        )
        assert (
            collector._infer_severity("Generic news article about tech")
            == "low"
        )
