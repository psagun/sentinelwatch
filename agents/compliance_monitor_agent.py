"""Compliance monitoring autonomous agent.

Tracks regulatory changes across jurisdictions, analyzes impact,
and delivers structured compliance alerts.

Integrates:
- Bright Data (Web Unlocker, Scraping Browser) for page monitoring
- AI/ML API for regulatory text analysis and obligation mapping
- Cognee for tracking regulatory history
"""

import logging
from typing import Any, Dict, List

from src.data_collection.compliance_collector import ComplianceCollector
from src.intelligence.compliance_analyzer import ComplianceAnalyzer
from src.memory.cognee_client import cognee
from src.alerting.notification import send_alert

logger = logging.getLogger(__name__)


class ComplianceMonitorAgent:
    """Autonomous agent for compliance regulatory monitoring."""

    def __init__(self):
        self.collector = ComplianceCollector()
        self.analyzer = ComplianceAnalyzer()

    async def run_cycle(self) -> Dict[str, Any]:
        """Execute one full compliance monitoring cycle."""
        logger.info("Compliance monitoring cycle starting")

        # Step 1: Collect raw compliance signals
        findings = await self.collector.collect()
        logger.info(f"Collected {len(findings)} compliance signals")

        # Step 2: AI analysis of each regulatory change
        analyzed = []
        for finding in findings:
            analysis = await self.analyzer.analyze_change(
                regulation=finding.regulation,
                title=finding.title,
                summary=finding.summary,
                change_type=finding.change_type,
            )

            enriched = finding.to_dict()
            enriched["analysis"] = analysis
            analyzed.append(enriched)

            # Persist to memory
            await cognee.store_finding(
                entity_id=finding.regulation,
                finding_type="compliance",
                content=enriched,
            )

        # Step 3: Map to compliance framework
        framework_mappings = []
        for finding in analyzed[:5]:
            mapping = await self.analyzer.map_to_framework(
                regulation=finding.get("regulation", ""),
                text=finding.get("summary", ""),
                framework="NIST CSF",
            )
            framework_mappings.append(mapping)

        # Step 4: Alert on high-impact changes
        high_impact = [
            f for f in analyzed
            if f.get("analysis", {}).get("impact_level") == "high"
        ]
        if high_impact:
            await send_alert("compliance", high_impact)

        return {
            "total_findings": len(analyzed),
            "high_impact_count": len(high_impact),
            "regulations_affected": list(set(
                f.get("regulation", "") for f in analyzed
            )),
            "framework_mappings": framework_mappings,
            "analyzed_findings": analyzed[:10],
        }
