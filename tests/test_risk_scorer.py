"""Tests for the RiskScorer module."""

import pytest
from datetime import datetime, timedelta, timezone

from src.intelligence.risk_scorer import RiskScorer


class TestRiskScorer:
    def setup_method(self):
        self.scorer = RiskScorer()

    def test_empty_findings(self):
        result = self.scorer.score([])
        assert result["score"] == 0.0
        assert result["level"] == "none"

    def test_low_severity(self):
        findings = [
            {"severity": "low", "timestamp": datetime.now(timezone.utc)}
        ]
        result = self.scorer.score(findings)
        assert result["score"] < 40.0
        assert result["level"] in ("low", "info")

    def test_critical_severity(self):
        findings = [
            {
                "severity": "critical",
                "timestamp": datetime.now(timezone.utc),
            }
        ]
        result = self.scorer.score(findings)
        assert result["score"] > 50.0
        assert result["level"] in ("critical", "high")

    def test_multiple_findings_increases_score(self):
        now = datetime.now(timezone.utc)
        single = self.scorer.score(
            [{"severity": "info", "timestamp": now}]
        )
        multiple = self.scorer.score(
            [
                {"severity": "critical", "timestamp": now},
                {"severity": "high", "timestamp": now},
                {"severity": "medium", "timestamp": now},
            ]
        )
        assert multiple["score"] > single["score"]

    def test_recency_affects_score(self):
        now = datetime.now(timezone.utc)
        recent = self.scorer.score(
            [{"severity": "critical", "timestamp": now}],
            recency_weight=1.5,
        )
        old = self.scorer.score(
            [
                {
                    "severity": "critical",
                    "timestamp": now - timedelta(days=30),
                }
            ],
            recency_weight=1.5,
        )
        assert recent["score"] >= old["score"]

    def test_aggregate_scores(self):
        scores = [
            {"score": 85.0, "level": "critical"},
            {"score": 45.0, "level": "medium"},
            {"score": 15.0, "level": "low"},
        ]
        agg = self.scorer.aggregate_scores(scores)
        assert agg["overall_level"] == "critical"
        assert agg["overall_score"] == pytest.approx(
            48.3, rel=0.1
        )
        assert agg["entity_count"] == 3

    def test_aggregate_empty(self):
        agg = self.scorer.aggregate_scores([])
        assert agg["overall_score"] == 0.0
        assert agg["overall_level"] == "none"

    def test_score_to_level(self):
        assert self.scorer._score_to_level(95) == "critical"
        assert self.scorer._score_to_level(75) == "high"
        assert self.scorer._score_to_level(50) == "medium"
        assert self.scorer._score_to_level(25) == "low"
        assert self.scorer._score_to_level(10) == "info"
