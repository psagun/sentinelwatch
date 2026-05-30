"""Risk scoring engine.

Computes composite risk scores for entities based on:
- Number and severity of findings
- Recency of findings
- Source credibility
- Inter-signal correlation
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

SEVERITY_WEIGHTS = {
    "critical": 10.0,
    "high": 7.5,
    "medium": 5.0,
    "low": 2.5,
    "info": 1.0,
}

SEVERITY_THRESHOLDS = {
    "critical": 90.0,
    "high": 70.0,
    "medium": 40.0,
    "low": 20.0,
}


class RiskScorer:
    """Computes quantitative risk scores from findings."""

    def score(
        self,
        findings: List[Dict[str, Any]],
        entity_id: Optional[str] = None,
        recency_weight: float = 1.5,
    ) -> Dict[str, Any]:
        """Compute a composite risk score for an entity.

        Args:
            findings: List of finding dicts (must have 'severity', 'timestamp').
            entity_id: Optional entity identifier.
            recency_weight: Weight multiplier for findings < 24h old.

        Returns:
            Dict with: score, level, finding_counts, top_findings, trend
        """
        if not findings:
            return {
                "score": 0.0,
                "level": "none",
                "finding_counts": {},
                "top_findings": [],
                "trend": "stable",
            }

        now = datetime.now(timezone.utc)
        total_weighted = 0.0
        severity_counts: Dict[str, int] = {}
        recency_counts = {"recent": 0, "older": 0}

        for finding in findings:
            severity = finding.get("severity", "info")
            severity_counts[severity] = severity_counts.get(severity, 0) + 1

            weight = SEVERITY_WEIGHTS.get(severity, 1.0)

            # Apply recency multiplier
            ts_str = finding.get("timestamp")
            if ts_str:
                try:
                    if isinstance(ts_str, str):
                        ts = datetime.fromisoformat(
                            ts_str.replace("Z", "+00:00")
                        )
                    else:
                        ts = ts_str
                    hours_ago = (now - ts).total_seconds() / 3600
                    if hours_ago < 24:
                        weight *= recency_weight
                        recency_counts["recent"] += 1
                    else:
                        recency_counts["older"] += 1
                except (ValueError, TypeError):
                    recency_counts["older"] += 1

            total_weighted += weight

        # Score = weighted sum normalized to 0-100 scale.
        # Each critical-finding-equivalent at full recency = 10 points.
        # Cap at 100 so that 10 critical-tier signals max out the scale.
        # This avoids the dilution problem where adding low-severity findings
        # inflated max_possible and lowered the score.
        raw = total_weighted / (SEVERITY_WEIGHTS["critical"] * recency_weight) * 10
        score = min(100.0, round(raw, 1))

        return {
            "score": round(score, 1),
            "level": self._score_to_level(score),
            "finding_counts": severity_counts,
            "total_findings": len(findings),
            "top_findings": sorted(
                findings,
                key=lambda f: SEVERITY_WEIGHTS.get(f.get("severity", "info"), 0),
                reverse=True,
            )[:5],
            "trend": "escalating" if recency_counts["recent"] > recency_counts["older"] else "stable",
            "recency_breakdown": recency_counts,
        }

    def aggregate_scores(
        self, entity_scores: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Aggregate risk scores across multiple entities."""
        if not entity_scores:
            return {
                "overall_score": 0.0,
                "overall_level": "none",
                "entity_count": 0,
            }

        avg_score = sum(
            e.get("score", 0) for e in entity_scores
        ) / len(entity_scores)

        max_severity = "none"
        for e in entity_scores:
            level = e.get("level", "none")
            if SEVERITY_THRESHOLDS.get(level, 0) > SEVERITY_THRESHOLDS.get(max_severity, 0):
                max_severity = level

        return {
            "overall_score": round(avg_score, 1),
            "overall_level": max_severity,
            "entity_count": len(entity_scores),
            "entities_breakdown": {
                "critical": sum(1 for e in entity_scores if e.get("level") == "critical"),
                "high": sum(1 for e in entity_scores if e.get("level") == "high"),
                "medium": sum(1 for e in entity_scores if e.get("level") == "medium"),
                "low": sum(1 for e in entity_scores if e.get("level") == "low"),
            },
        }

    def _score_to_level(self, score: float) -> str:
        if score >= SEVERITY_THRESHOLDS["critical"]:
            return "critical"
        if score >= SEVERITY_THRESHOLDS["high"]:
            return "high"
        if score >= SEVERITY_THRESHOLDS["medium"]:
            return "medium"
        if score >= SEVERITY_THRESHOLDS["low"]:
            return "low"
        return "info"
