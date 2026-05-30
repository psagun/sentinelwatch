"""Tests for the AlertManager module."""

import pytest

from src.alerting.alert_manager import AlertManager


class TestAlertManager:
    def setup_method(self):
        self.manager = AlertManager()

    def test_no_alerts_for_low_severity(self):
        findings = [
            {
                "id": "1",
                "severity": "low",
                "title": "Low priority item",
                "description": "Not important",
            }
        ]
        alerts = self.manager.create_alerts("test", findings)
        assert len(alerts) == 0

    def test_alerts_for_critical_severity(self):
        findings = [
            {
                "id": "1",
                "severity": "critical",
                "title": "Critical threat detected",
                "description": "Active breach in progress",
                "source_url": "https://example.com",
            }
        ]
        alerts = self.manager.create_alerts("threat", findings)
        assert len(alerts) == 1
        assert alerts[0].severity == "critical"
        assert "pagerduty" in alerts[0].channels

    def test_alerts_for_high_severity(self):
        findings = [
            {
                "id": "2",
                "severity": "high",
                "title": "High severity finding",
                "description": "Urgent investigation needed",
                "source_url": "https://example.com/high",
            }
        ]
        alerts = self.manager.create_alerts("compliance", findings)
        assert len(alerts) == 1
        assert "pagerduty" not in alerts[0].channels
        assert "slack" in alerts[0].channels

    def test_dedup_same_finding(self):
        findings = [
            {
                "id": "1",
                "severity": "critical",
                "title": "Duplicate title",
                "description": "Test",
                "source_url": "https://example.com",
            }
        ]
        first = self.manager.create_alerts("threat", findings)
        second = self.manager.create_alerts("threat", findings)
        assert len(first) == 1
        assert len(second) == 0  # Deduplicated

    def test_multiple_severities(self):
        findings = [
            {
                "id": "1",
                "severity": "critical",
                "title": "Critical",
                "description": "Critical event",
                "source_url": "https://a.com",
            },
            {
                "id": "2",
                "severity": "high",
                "title": "High",
                "description": "High event",
                "source_url": "https://b.com",
            },
            {
                "id": "3",
                "severity": "medium",
                "title": "Medium",
                "description": "Medium event",
                "source_url": "https://c.com",
            },
            {
                "id": "4",
                "severity": "low",
                "title": "Low",
                "description": "Low event",
                "source_url": "https://d.com",
            },
        ]
        alerts = self.manager.create_alerts("test", findings)
        assert len(alerts) == 3  # critical, high, medium
