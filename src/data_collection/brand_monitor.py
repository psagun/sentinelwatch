"""Brand and data exposure monitor.

Detects:
- Leaked credentials and password dumps
- Brand impersonation / phishing sites
- Exposed corporate data (source code, internal docs)
- Social engineering campaigns targeting the organization
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from src.data_collection.brightdata_client import brightdata

logger = logging.getLogger(__name__)


class BrandExposureFinding:
    """A brand or data exposure finding."""

    def __init__(
        self,
        exposure_type: str,
        title: str,
        description: str,
        severity: str,
        source_url: str,
        affected_domain: Optional[str] = None,
        leaked_data_types: Optional[List[str]] = None,
        raw_data: Optional[str] = None,
    ):
        self.exposure_type = exposure_type
        self.title = title
        self.description = description
        self.severity = severity
        self.source_url = source_url
        self.affected_domain = affected_domain
        self.leaked_data_types = leaked_data_types or []
        self.raw_data = raw_data
        self.timestamp = datetime.now(timezone.utc)
        self.finding_type = "brand_exposure"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "finding_type": self.finding_type,
            "exposure_type": self.exposure_type,
            "title": self.title,
            "description": self.description,
            "severity": self.severity,
            "source_url": self.source_url,
            "affected_domain": self.affected_domain,
            "leaked_data_types": self.leaked_data_types,
            "timestamp": self.timestamp.isoformat(),
        }


class BrandMonitor:
    """Monitors brand and data exposure across the web."""

    def __init__(self, domains: Optional[List[str]] = None,
                 brand_keywords: Optional[List[str]] = None):
        self.domains = domains or []
        self.brand_keywords = brand_keywords or []

    async def collect(self) -> List[BrandExposureFinding]:
        """Run all brand monitoring workflows."""
        findings: List[BrandExposureFinding] = []

        findings.extend(await self._check_credential_leaks())
        findings.extend(await self._check_phishing_domains())
        findings.extend(await self._check_code_exposure())
        findings.extend(await self._check_dark_web_mentions())
        findings.extend(await self._check_impersonation())

        return findings

    async def _check_credential_leaks(self) -> List[BrandExposureFinding]:
        """Search for leaked credentials related to monitored domains."""
        findings = []
        for domain in self.domains[:3]:
            queries = [
                f"site:pastebin.com {domain} password",
                f"site:github.com {domain} credential OR password OR .env",
                f"\"{domain}\" leaked OR dump OR database",
            ]
            for query in queries:
                try:
                    results = await brightdata.serp_search(
                        query=query, source="google", max_results=5
                    )
                    for result in results:
                        findings.append(BrandExposureFinding(
                            exposure_type="credential_leak",
                            title=result.get("title", ""),
                            description=result.get("snippet", ""),
                            severity="critical",
                            source_url=result.get("url", ""),
                            affected_domain=domain,
                            leaked_data_types=["credentials"],
                        ))
                except Exception as e:
                    logger.warning(
                        f"Credential leak check failed for {domain}: {e}"
                    )
        return findings

    async def _check_phishing_domains(self) -> List[BrandExposureFinding]:
        """Look for lookalike domains registered for phishing."""
        findings = []
        for domain in self.domains[:3]:
            base = domain.split(".")[0]
            # Search for common typosquatting patterns
            query = (
                f"{base}-security OR {base}-support OR {base}-login "
                f"OR secure-{base} phishing"
            )
            try:
                results = await brightdata.serp_search(
                    query=query, source="google", max_results=5
                )
                for result in results:
                    findings.append(BrandExposureFinding(
                        exposure_type="phishing_domain",
                        title=result.get("title", ""),
                        description=result.get("snippet", ""),
                        severity="critical",
                        source_url=result.get("url", ""),
                        affected_domain=domain,
                    ))
            except Exception as e:
                logger.warning(
                    f"Phishing domain check failed for {domain}: {e}"
                )
        return findings

    async def _check_code_exposure(self) -> List[BrandExposureFinding]:
        """Check for exposed source code and internal documents."""
        findings = []
        for domain in self.domains[:3]:
            queries = [
                f"site:github.com \"{domain}\" internal OR confidential",
                f"site:pastebin.com \"{domain}\" config OR .env OR secret",
            ]
            for query in queries:
                try:
                    results = await brightdata.serp_search(
                        query=query, source="google", max_results=5
                    )
                    for result in results:
                        findings.append(BrandExposureFinding(
                            exposure_type="code_exposure",
                            title=result.get("title", ""),
                            description=result.get("snippet", ""),
                            severity="high",
                            source_url=result.get("url", ""),
                            affected_domain=domain,
                            leaked_data_types=["source_code"],
                        ))
                except Exception as e:
                    logger.warning(f"Code exposure check failed: {e}")
        return findings

    async def _check_dark_web_mentions(self) -> List[BrandExposureFinding]:
        """Search for dark web mentions of the brand."""
        findings = []
        for keyword in self.brand_keywords[:5]:
            try:
                # Search across surface web for dark web references
                query = (
                    f"site:breachforums.st OR site:exploit.in "
                    f"\"{keyword}\" leak OR dump OR sell"
                )
                results = await brightdata.serp_search(
                    query=query, source="google", max_results=5
                )
                for result in results:
                    findings.append(BrandExposureFinding(
                        exposure_type="dark_web_mention",
                        title=result.get("title", ""),
                        description=result.get("snippet", ""),
                        severity="critical",
                        source_url=result.get("url", ""),
                        leaked_data_types=["unknown"],
                    ))
            except Exception as e:
                logger.warning(f"Dark web check failed: {e}")
        return findings

    async def _check_impersonation(self) -> List[BrandExposureFinding]:
        """Detect brand impersonation on social media and web."""
        findings = []
        for keyword in self.brand_keywords[:3]:
            queries = [
                f"\"{keyword}\" fake OR impersonation OR scam",
            ]
            for query in queries:
                try:
                    results = await brightdata.serp_search(
                        query=query, source="google", max_results=5
                    )
                    for result in results:
                        findings.append(BrandExposureFinding(
                            exposure_type="impersonation",
                            title=result.get("title", ""),
                            description=result.get("snippet", ""),
                            severity="high",
                            source_url=result.get("url", ""),
                        ))
                except Exception as e:
                    logger.warning(f"Impersonation check failed: {e}")
        return findings
