"""Tests for the ComplianceCollector module."""

import pytest

from src.data_collection.compliance_collector import (
    ComplianceCollector,
    ComplianceFinding,
)


class TestComplianceFinding:
    def test_creation(self):
        finding = ComplianceFinding(
            regulation="GDPR",
            jurisdiction="EU/EEA",
            source_url="https://gdpr.eu",
            title="GDPR Update 2026",
            summary="New enforcement guidelines",
            change_type="guidance",
            impact_level="medium",
            effective_date="2026-07-01",
        )
        assert finding.finding_type == "compliance"
        assert finding.regulation == "GDPR"
        assert finding.change_type == "guidance"

    def test_to_dict(self):
        finding = ComplianceFinding(
            regulation="CCPA",
            jurisdiction="California",
            source_url="https://oag.ca.gov",
            title="CCPA Amendment",
            summary="Amendment text",
            change_type="amendment",
            impact_level="high",
        )
        d = finding.to_dict()
        assert d["regulation"] == "CCPA"
        assert d["finding_type"] == "compliance"


class TestComplianceCollector:
    def test_classify_change(self):
        collector = ComplianceCollector()
        assert (
            collector._classify_change("New regulation proposed")
            == "new_regulation"
        )
        assert (
            collector._classify_change("Amendment to section 5")
            == "amendment"
        )
        assert (
            collector._classify_change("Enforcement action")
            == "enforcement_action"
        )
        assert (
            collector._classify_change("Some other update")
            == "update"
        )

    def test_assess_impact(self):
        collector = ComplianceCollector()
        assert (
            collector._assess_impact("Major overhaul of regulation")
            == "high"
        )
        assert (
            collector._assess_impact("Minor clarification")
            == "low"
        )
        assert (
            collector._assess_impact("Something else")
            == "info"
        )
