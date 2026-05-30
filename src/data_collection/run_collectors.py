"""Orchestrated data collection runner.

Runs all collectors on their configured cadences and pushes
findings into the processing pipeline.
"""

import asyncio
import logging
from typing import List

from src.config import settings
from src.data_collection.threat_collector import ThreatCollector, ThreatFinding
from src.data_collection.compliance_collector import (
    ComplianceCollector,
    ComplianceFinding,
)
from src.data_collection.third_party_collector import (
    ThirdPartyCollector,
    ThirdPartyRiskFinding,
)
from src.data_collection.brand_monitor import BrandMonitor, BrandExposureFinding

logger = logging.getLogger(__name__)


async def run_threat_collection(
    entities: List[dict],
) -> List[ThreatFinding]:
    """Run threat intelligence collection."""
    collector = ThreatCollector(monitored_entities=entities)
    findings = await collector.collect()
    logger.info(f"Threat collection complete: {len(findings)} findings")
    return findings


async def run_compliance_collection() -> List[ComplianceFinding]:
    """Run regulatory compliance monitoring."""
    collector = ComplianceCollector()
    findings = await collector.collect()
    logger.info(f"Compliance collection complete: {len(findings)} findings")
    return findings


async def run_third_party_collection(
    vendors: List[dict],
) -> List[ThirdPartyRiskFinding]:
    """Run third-party risk assessment."""
    collector = ThirdPartyCollector(vendors=vendors)
    findings = await collector.collect()
    logger.info(
        f"Third-party collection complete: {len(findings)} findings"
    )
    return findings


async def run_brand_monitoring(
    domains: List[str],
    keywords: List[str],
) -> List[BrandExposureFinding]:
    """Run brand and data exposure monitoring."""
    monitor = BrandMonitor(domains=domains, brand_keywords=keywords)
    findings = await monitor.collect()
    logger.info(f"Brand monitoring complete: {len(findings)} findings")
    return findings


async def run_all_collections(
    entities: List[dict],
    vendors: List[dict],
    domains: List[str],
    brand_keywords: List[str],
) -> dict:
    """Run all collectors concurrently."""
    threat_task = run_threat_collection(entities)
    compliance_task = run_compliance_collection()
    third_party_task = run_third_party_collection(vendors)
    brand_task = run_brand_monitoring(domains, brand_keywords)

    results = await asyncio.gather(
        threat_task,
        compliance_task,
        third_party_task,
        brand_task,
        return_exceptions=True,
    )

    return {
        "threat_findings": results[0] if not isinstance(
            results[0], Exception
        ) else [],
        "compliance_findings": results[1] if not isinstance(
            results[1], Exception
        ) else [],
        "third_party_findings": results[2] if not isinstance(
            results[2], Exception
        ) else [],
        "brand_findings": results[3] if not isinstance(
            results[3], Exception
        ) else [],
    }
