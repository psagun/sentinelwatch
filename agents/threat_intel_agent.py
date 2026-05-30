"""Threat intelligence autonomous agent.

Continuously monitors open web sources for org-specific threats,
analyzes findings using AI, and triggers alerts.

Integrates:
- Bright Data (Web Unlocker, SERP API) for data collection
- AI/ML API for analysis and classification
- Cognee for persistent memory across monitoring cycles
"""

import asyncio
import logging
from typing import Any, Dict, List

from src.data_collection.threat_collector import ThreatCollector
from src.data_collection.brightdata_client import brightdata
from src.intelligence.threat_analyzer import ThreatAnalyzer
from src.intelligence.risk_scorer import RiskScorer
from src.memory.cognee_client import cognee
from src.alerting.notification import send_alert

logger = logging.getLogger(__name__)


class ThreatIntelligenceAgent:
    """Autonomous agent for threat intelligence monitoring."""

    def __init__(self, entities: List[Dict[str, Any]]):
        self.entities = entities
        self.collector = ThreatCollector(
            monitored_entities=entities
        )
        self.analyzer = ThreatAnalyzer()
        self.risk_scorer = RiskScorer()

    async def run_cycle(self) -> Dict[str, Any]:
        """Execute one full monitoring and analysis cycle."""
        logger.info(
            f"Threat intel cycle starting for "
            f"{len(self.entities)} entities"
        )

        # Step 1: Collect raw findings from web
        findings = await self.collector.collect()
        logger.info(f"Collected {len(findings)} raw findings")

        # Step 2: AI analysis of each finding
        analyzed = []
        for finding in findings:
            analysis = await self.analyzer.analyze_finding(
                title=finding.title,
                description=finding.description,
                source_type=finding.source_type,
            )

            iocs = await self.analyzer.extract_iocs(
                f"{finding.title} {finding.description}"
            )

            enriched = finding.to_dict()
            enriched["analysis"] = analysis
            enriched["iocs"] = iocs
            analyzed.append(enriched)

            # Store in Cognee memory for future context
            await cognee.store_finding(
                entity_id=finding.entity_id or "global",
                finding_type="threat",
                content=enriched,
            )

        # Step 3: Risk scoring
        risk_scores = {}
        for entity in self.entities:
            name = entity.get("name", "unknown")
            entity_findings = [
                f for f in analyzed
                if f.get("entity_id") == name
            ]
            score = self.risk_scorer.score(entity_findings)
            risk_scores[name] = score

        # Step 4: Alert on critical/high findings
        critical_findings = [
            f for f in analyzed
            if f.get("severity") in ("critical", "high")
        ]
        if critical_findings:
            await send_alert("threat", critical_findings)

        return {
            "total_findings": len(analyzed),
            "critical_count": sum(
                1 for f in analyzed
                if f.get("severity") == "critical"
            ),
            "high_count": sum(
                1 for f in analyzed
                if f.get("severity") == "high"
            ),
            "risk_scores": risk_scores,
            "analyzed_findings": analyzed[:10],
        }
