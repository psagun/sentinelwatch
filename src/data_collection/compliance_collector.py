"""Compliance regulatory monitoring collector.

Monitors regulatory bodies and standards organizations for changes to:
- GDPR (Europe)
- CCPA / CPRA (California)
- SEC regulations (US securities)
- ISO standards (27001, 27701, 42001)
- NIST frameworks (CSF, SP 800-53)
- National data protection authorities
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from src.data_collection.brightdata_client import brightdata

logger = logging.getLogger(__name__)


class ComplianceFinding:
    """Normalized compliance monitoring finding."""

    def __init__(
        self,
        regulation: str,
        jurisdiction: str,
        source_url: str,
        title: str,
        summary: str,
        change_type: str,
        impact_level: str,
        effective_date: Optional[str] = None,
        entity_id: Optional[str] = None,
        raw_data: Optional[str] = None,
        is_source_monitoring: bool = False,
    ):
        self.regulation = regulation
        self.jurisdiction = jurisdiction
        self.source_url = source_url
        self.title = title
        self.summary = summary
        self.change_type = change_type
        self.impact_level = impact_level
        self.effective_date = effective_date
        self.entity_id = entity_id
        self.raw_data = raw_data
        self.timestamp = datetime.now(timezone.utc)
        self.finding_type = "compliance"
        self.is_source_monitoring = is_source_monitoring

    def to_dict(self) -> Dict[str, Any]:
        return {
            "finding_type": self.finding_type,
            "regulation": self.regulation,
            "jurisdiction": self.jurisdiction,
            "source_url": self.source_url,
            "title": self.title,
            "summary": self.summary,
            "change_type": self.change_type,
            "impact_level": self.impact_level,
            "effective_date": self.effective_date,
            "entity_id": self.entity_id,
            "timestamp": self.timestamp.isoformat(),
            "is_source_monitoring": self.is_source_monitoring,
        }


class ComplianceCollector:
    """Monitors regulatory sources for compliance changes."""

    def __init__(self):
        self.regulations = [
            {
                "name": "GDPR",
                "jurisdiction": "EU/EEA",
                "sources": [
                    "https://gdpr.eu",
                ],
            },
            {
                "name": "CCPA",
                "jurisdiction": "California, USA",
                "sources": [
                    "https://www.oag.ca.gov/privacy/ccpa",
                ],
            },
            {
                "name": "SEC",
                "jurisdiction": "USA",
                "sources": [],
            },
            {
                "name": "NIST",
                "jurisdiction": "USA",
                "sources": [],
            },
            {
                "name": "ISO",
                "jurisdiction": "International",
                "sources": [
                    "https://www.iso.org/home.html",
                ],
            },
        ]

    async def collect(self) -> List[ComplianceFinding]:
        """Run all compliance monitoring workflows."""
        findings: List[ComplianceFinding] = []

        for regulation in self.regulations:
            logger.info(
                f"Collecting compliance data for: {regulation['name']}"
            )
            for source_url in regulation["sources"][:2]:
                try:
                    html = await brightdata.web_unlocker_get(
                        source_url, country="us"
                    )
                    findings.extend(
                        self._parse_regulation_page(
                            regulation=regulation["name"],
                            jurisdiction=regulation["jurisdiction"],
                            source_url=source_url,
                            html=html,
                        )
                    )
                except Exception as e:
                    logger.warning(
                        f"Failed to collect {source_url}: {e}"
                    )

            # Search for recent regulatory news
            try:
                news = await brightdata.serp_news(
                    query=f"{regulation['name']} regulation change update",
                    country="US",
                    freshness="30d",
                )
                for item in news[:5]:
                    item_url = item.get("url", "")
                    # Mark news items from regulatory source domains as source monitoring
                    is_src_mon = any(
                        domain in item_url
                        for domain in ["gdpr.eu", "iso.org"]
                    )
                    findings.append(ComplianceFinding(
                        regulation=regulation["name"],
                        jurisdiction=regulation["jurisdiction"],
                        source_url=item_url,
                        title=item.get("title", ""),
                        summary=item.get("snippet", ""),
                        change_type=self._classify_change(
                            item.get("title", "")
                        ),
                        impact_level=self._assess_impact(
                            item.get("title", "")
                        ),
                        is_source_monitoring=is_src_mon,
                    ))
            except Exception as e:
                logger.warning(
                    f"Compliance news search failed: {e}"
                )

        return findings

    def _parse_regulation_page(
        self,
        regulation: str,
        jurisdiction: str,
        source_url: str,
        html: str,
    ) -> List[ComplianceFinding]:
        """Parse a regulation page for changes and updates."""
        findings = []
        # In production, use proper HTML parsing + AI extraction.
        # Here we use keyword heuristics as a first pass.
        change_keywords = [
            "new regulation", "amendment", "update", "proposal",
            "enforcement", "guidance", "penalty", "fine",
            "compliance deadline", "effective date",
        ]
        for keyword in change_keywords:
            if keyword in html.lower():
                findings.append(ComplianceFinding(
                    regulation=regulation,
                    jurisdiction=jurisdiction,
                    source_url=source_url,
                    title=f"Potential {regulation} change detected",
                    summary=f"Keyword '{keyword}' found on {source_url}",
                    change_type=self._classify_change(keyword),
                    impact_level="medium",
                    is_source_monitoring=True,
                ))
        return findings

    def _classify_change(self, text: str) -> str:
        """Classify the type of regulatory change."""
        text_lower = text.lower()
        if any(w in text_lower for w in ("new", "proposal", "proposed")):
            return "new_regulation"
        if any(w in text_lower for w in ("amendment", "amend", "revised")):
            return "amendment"
        if any(w in text_lower for w in ("enforcement", "penalty", "fine")):
            return "enforcement_action"
        if any(w in text_lower for w in ("guidance", "interpretation")):
            return "guidance"
        if any(w in text_lower for w in ("deadline", "effective", "delay")):
            return "timeline_change"
        return "update"

    def _assess_impact(self, text: str) -> str:
        """Assess potential impact level of a regulatory change."""
        text_lower = text.lower()
        if any(w in text_lower for w in ("major", "significant", "overhaul",
                                         "critical", "urgent")):
            return "high"
        if any(w in text_lower for w in ("moderate", "update", "change")):
            return "medium"
        if any(w in text_lower for w in ("minor", "clarification",
                                         "guidance")):
            return "low"
        return "info"
