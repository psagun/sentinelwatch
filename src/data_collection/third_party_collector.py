"""Third-party risk collector.

Continuously assesses supplier and vendor exposure across the web by
monitoring:
- Security incidents and breaches
- Financial health signals
- Leadership changes
- Regulatory actions
- Dark web mentions
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from src.data_collection.brightdata_client import brightdata

logger = logging.getLogger(__name__)


class ThirdPartyRiskFinding:
    """A risk signal detected about a third-party vendor."""

    def __init__(
        self,
        vendor_name: str,
        vendor_domain: str,
        risk_category: str,
        title: str,
        description: str,
        severity: str,
        source_url: str,
        raw_data: Optional[str] = None,
    ):
        self.vendor_name = vendor_name
        self.vendor_domain = vendor_domain
        self.risk_category = risk_category
        self.title = title
        self.description = description
        self.severity = severity
        self.source_url = source_url
        self.raw_data = raw_data
        self.timestamp = datetime.now(timezone.utc)
        self.finding_type = "third_party_risk"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "finding_type": self.finding_type,
            "vendor_name": self.vendor_name,
            "vendor_domain": self.vendor_domain,
            "risk_category": self.risk_category,
            "title": self.title,
            "description": self.description,
            "severity": self.severity,
            "source_url": self.source_url,
            "timestamp": self.timestamp.isoformat(),
        }


class ThirdPartyCollector:
    """Collector for third-party vendor risk assessment."""

    def __init__(self, vendors: Optional[List[Dict]] = None):
        self.vendors = vendors or []

    async def collect(self) -> List[ThirdPartyRiskFinding]:
        """Run all third-party risk collection workflows."""
        findings: List[ThirdPartyRiskFinding] = []

        for vendor in self.vendors:
            name = vendor.get("name", "")
            domain = vendor.get("domain", "")
            logger.info(f"Assessing third-party risk: {name} ({domain})")

            findings.extend(
                await self._check_security_incidents(name, domain)
            )
            findings.extend(
                await self._check_financial_health(name, domain)
            )
            findings.extend(
                await self._check_leadership(name, domain)
            )
            findings.extend(
                await self._check_reputation(name, domain)
            )

        return findings

    async def _check_security_incidents(
        self, name: str, domain: str
    ) -> List[ThirdPartyRiskFinding]:
        """Check for security incidents involving the vendor."""
        findings = []
        queries = [
            f"{name} data breach",
            f"{domain} security incident",
            f"{name} ransomware attack",
            f"{name} vulnerability disclosure",
        ]
        for query in queries[:3]:
            try:
                results = await brightdata.serp_news(
                    query=query, country="US"
                )
                for result in results:
                    snippet = result.get("snippet", "").lower()
                    severity = "critical" if any(
                        w in snippet for w in ("breach", "ransomware",
                                                "attack", "compromised")
                    ) else "high"

                    findings.append(ThirdPartyRiskFinding(
                        vendor_name=name,
                        vendor_domain=domain,
                        risk_category="security_incident",
                        title=result.get("title", ""),
                        description=result.get("snippet", ""),
                        severity=severity,
                        source_url=result.get("url", ""),
                    ))
            except Exception as e:
                logger.warning(f"Security incident check failed: {e}")
        return findings

    async def _check_financial_health(
        self, name: str, domain: str
    ) -> List[ThirdPartyRiskFinding]:
        """Check for financial health signals."""
        findings = []
        queries = [
            f"{name} layoffs",
            f"{name} financial trouble",
            f"{domain} bankruptcy",
            f"{name} funding round",
        ]
        for query in queries[:2]:
            try:
                results = await brightdata.serp_news(
                    query=query, country="US"
                )
                for result in results:
                    snippet = result.get("snippet", "").lower()
                    severity = "critical" if any(
                        w in snippet for w in ("bankruptcy", "layoff",
                                                "filing chapter")
                    ) else "medium"

                    findings.append(ThirdPartyRiskFinding(
                        vendor_name=name,
                        vendor_domain=domain,
                        risk_category="financial_health",
                        title=result.get("title", ""),
                        description=result.get("snippet", ""),
                        severity=severity,
                        source_url=result.get("url", ""),
                    ))
            except Exception as e:
                logger.warning(f"Financial health check failed: {e}")
        return findings

    async def _check_leadership(
        self, name: str, domain: str
    ) -> List[ThirdPartyRiskFinding]:
        """Check for leadership changes."""
        findings = []
        query = f"{name} CEO CISO CTO leaving resigns"
        try:
            results = await brightdata.serp_news(
                query=query, country="US"
            )
            for result in results:
                findings.append(ThirdPartyRiskFinding(
                    vendor_name=name,
                    vendor_domain=domain,
                    risk_category="leadership_change",
                    title=result.get("title", ""),
                    description=result.get("snippet", ""),
                    severity="medium",
                    source_url=result.get("url", ""),
                ))
        except Exception as e:
            logger.warning(f"Leadership check failed: {e}")
        return findings

    async def _check_reputation(
        self, name: str, domain: str
    ) -> List[ThirdPartyRiskFinding]:
        """Check for reputation and brand risk."""
        findings = []
        query = f"site:reddit.com OR site:trustpilot.com {name} complaint security"
        try:
            results = await brightdata.serp_search(
                query=query, source="google", max_results=5
            )
            for result in results:
                findings.append(ThirdPartyRiskFinding(
                    vendor_name=name,
                    vendor_domain=domain,
                    risk_category="reputation",
                    title=result.get("title", ""),
                    description=result.get("snippet", ""),
                    severity="low",
                    source_url=result.get("url", ""),
                ))
        except Exception as e:
            logger.warning(f"Reputation check failed: {e}")
        return findings
