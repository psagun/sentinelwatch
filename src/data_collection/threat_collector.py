"""Threat intelligence collector — monitors open web for org-specific threats.

Sources monitored:
- CVE feeds (NVD, MITRE)
- Security blogs and advisory pages
- Dark web forums and paste sites
- Social media (Twitter/X, Reddit) for early indicators
- Exploit databases
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from src.config import settings
from src.data_collection.brightdata_client import brightdata

logger = logging.getLogger(__name__)


class ThreatFinding:
    """Normalized threat finding from web sources."""

    def __init__(
        self,
        source_type: str,
        source_url: str,
        title: str,
        description: str,
        severity: str,
        indicators: Optional[List[str]] = None,
        raw_data: Optional[str] = None,
        entity_id: Optional[str] = None,
    ):
        self.source_type = source_type
        self.source_url = source_url
        self.title = title
        self.description = description
        self.severity = severity
        self.indicators = indicators or []
        self.raw_data = raw_data
        self.entity_id = entity_id
        self.timestamp = datetime.now(timezone.utc)
        self.finding_type = "threat"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "finding_type": self.finding_type,
            "source_type": self.source_type,
            "source_url": self.source_url,
            "title": self.title,
            "description": self.description,
            "severity": self.severity,
            "indicators": self.indicators,
            "entity_id": self.entity_id,
            "timestamp": self.timestamp.isoformat(),
        }


class ThreatCollector:
    """Collects threat intelligence from across the open web."""

    def __init__(self, monitored_entities: Optional[List[Dict]] = None):
        self.monitored_entities = monitored_entities or []

    async def collect(self) -> List[ThreatFinding]:
        """Run all threat collection workflows."""
        findings: List[ThreatFinding] = []

        for entity in self.monitored_entities:
            entity_name = entity.get("name", "")
            domains = entity.get("metadata", {}).get("domains", [])
            keywords = entity.get("metadata", {}).get("keywords", [])

            logger.info(f"Collecting threat intel for entity: {entity_name}")

            # Collect from multiple source types
            findings.extend(
                await self._search_cve_feeds(entity_name, keywords)
            )
            findings.extend(
                await self._search_security_blogs(entity_name, keywords)
            )
            findings.extend(
                await self._search_paste_sites(entity_name, domains, keywords)
            )
            findings.extend(
                await self._search_social_media(entity_name, keywords)
            )
            findings.extend(
                await self._search_exploit_db(entity_name, keywords)
            )

        return findings

    async def _search_cve_feeds(
        self, entity_name: str, keywords: List[str]
    ) -> List[ThreatFinding]:
        """Search CVE/NVD feeds for vulnerabilities relevant to entity."""
        findings = []
        for keyword in keywords[:3]:
            query = f"{keyword} CVE vulnerability 2026"
            try:
                results = await brightdata.serp_search(
                    query=query,
                    source="google",
                    country="US",
                    max_results=5,
                )
                for result in results:
                    title = result.get("title", "")
                    snippet = result.get("snippet", "")
                    url = result.get("url", "")
                    if "CVE" in title.upper() or "CVE" in snippet.upper():
                        findings.append(ThreatFinding(
                            source_type="cve_feed",
                            source_url=url,
                            title=title,
                            description=snippet,
                            severity="high",
                            indicators=[title.split("CVE-")[1].split()[0]]
                            if "CVE-" in title else [],
                            entity_id=entity_name,
                        ))
            except Exception as e:
                logger.warning(f"CVE search failed for '{keyword}': {e}")
        return findings

    async def _search_security_blogs(
        self, entity_name: str, keywords: List[str]
    ) -> List[ThreatFinding]:
        """Search security blogs for threat indicators."""
        findings = []
        blog_sources = [
            "krebsonsecurity.com",
            "therecord.media",
            "bleepingcomputer.com",
            "thehackernews.com",
            "darkreading.com",
        ]
        for keyword in keywords[:2]:
            for source in blog_sources[:3]:
                query = f"site:{source} {keyword} security breach attack"
                try:
                    results = await brightdata.serp_search(
                        query=query, source="google", max_results=3
                    )
                    for result in results:
                        findings.append(ThreatFinding(
                            source_type="security_blog",
                            source_url=result.get("url", ""),
                            title=result.get("title", ""),
                            description=result.get("snippet", ""),
                            severity=self._infer_severity(
                                result.get("title", "")
                            ),
                            entity_id=entity_name,
                        ))
                except Exception as e:
                    logger.warning(f"Blog search failed: {e}")
        return findings

    async def _search_paste_sites(
        self,
        entity_name: str,
        domains: List[str],
        keywords: List[str],
    ) -> List[ThreatFinding]:
        """Monitor paste sites for leaked credentials or data dumps."""
        findings = []
        paste_keywords = keywords + domains
        for keyword in paste_keywords[:5]:
            try:
                html = await brightdata.web_unlocker_get(
                    f"https://pastebin.com/search?q={keyword.replace(' ', '+')}"
                )
                if html and keyword.lower() in html.lower():
                    findings.append(ThreatFinding(
                        source_type="paste_site",
                        source_url="https://pastebin.com/search",
                        title=f"Potential paste mention: {keyword}",
                        description="Entity keyword found on pastebin search",
                        severity="critical",
                        indicators=[keyword],
                        entity_id=entity_name,
                    ))
            except Exception as e:
                logger.warning(f"Paste site search failed: {e}")

        # Search Google for paste site mentions
        for keyword in paste_keywords[:3]:
            query = f"site:pastebin.com OR site:ghostbin.com {keyword} password OR leak OR credential"
            try:
                results = await brightdata.serp_search(
                    query=query, source="google", max_results=5
                )
                for result in results:
                    findings.append(ThreatFinding(
                        source_type="paste_site",
                        source_url=result.get("url", ""),
                        title=result.get("title", ""),
                        description=result.get("snippet", ""),
                        severity="critical",
                        entity_id=entity_name,
                    ))
            except Exception as e:
                logger.warning(f"Paste site Google search failed: {e}")
        return findings

    async def _search_social_media(
        self, entity_name: str, keywords: List[str]
    ) -> List[ThreatFinding]:
        """Monitor social media for threat mentions."""
        findings = []
        for keyword in keywords[:2]:
            query = f"{keyword} data breach security incident"
            try:
                results = await brightdata.serp_news(
                    query=query,
                    country="US",
                )
                for result in results:
                    findings.append(ThreatFinding(
                        source_type="social_media",
                        source_url=result.get("url", ""),
                        title=result.get("title", ""),
                        description=result.get("snippet", ""),
                        severity=self._infer_severity(
                            result.get("title", "")
                        ),
                        entity_id=entity_name,
                    ))
            except Exception as e:
                logger.warning(f"Social media search failed: {e}")
        return findings

    async def _search_exploit_db(
        self, entity_name: str, keywords: List[str]
    ) -> List[ThreatFinding]:
        """Check exploit databases for relevant exploits."""
        findings = []
        for keyword in keywords[:2]:
            query = f"site:exploit-db.com {keyword}"
            try:
                results = await brightdata.serp_search(
                    query=query, source="google", max_results=5
                )
                for result in results:
                    findings.append(ThreatFinding(
                        source_type="exploit_db",
                        source_url=result.get("url", ""),
                        title=result.get("title", ""),
                        description=result.get("snippet", ""),
                        severity="critical",
                        entity_id=entity_name,
                    ))
            except Exception as e:
                logger.warning(f"Exploit DB search failed: {e}")
        return findings

    def _infer_severity(self, text: str) -> str:
        """Heuristic severity inference from text content."""
        critical = (
            "critical", "zero-day", "0-day", "ransomware", "data breach",
            "CVE-", "exploit", "worm",
        )
        high = ("vulnerability", "attack", "malware", "backdoor", "phishing")
        medium = ("advisory", "patch", "update", "fix", "CVE")
        text_lower = text.lower()
        if any(c in text_lower for c in critical):
            return "critical"
        if any(h in text_lower for h in high):
            return "high"
        if any(m in text_lower for m in medium):
            return "medium"
        return "low"
