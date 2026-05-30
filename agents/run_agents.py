"""Agent runner — starts all autonomous agents in a continuous loop.

Run:
    python -m agents.run_agents

Uses the cadence intervals from config.py.
"""

import asyncio
import logging
from typing import Any, Dict, List

from src.config import settings
from agents.threat_intel_agent import ThreatIntelligenceAgent
from agents.compliance_monitor_agent import ComplianceMonitorAgent

logger = logging.getLogger(__name__)

# Monitored entities for the hackathon: Bright Data + partner companies
DEFAULT_ENTITIES: List[Dict[str, Any]] = [
    {
        "name": "Bright Data",
        "entity_type": "organization",
        "metadata": {
            "domains": ["brightdata.com"],
            "keywords": [
                "Bright Data", "brightdata", "web data",
                "proxy", "web scraper",
            ],
        },
    },
    {
        "name": "AI/ML API",
        "entity_type": "organization",
        "metadata": {
            "domains": ["aimlapi.com"],
            "keywords": [
                "AI/ML API", "aimlapi", "AI models",
                "API models",
            ],
        },
    },
    {
        "name": "Speechmatics",
        "entity_type": "organization",
        "metadata": {
            "domains": ["speechmatics.com"],
            "keywords": [
                "Speechmatics", "speech to text",
                "conversational AI",
            ],
        },
    },
    {
        "name": "Cognee",
        "entity_type": "organization",
        "metadata": {
            "domains": ["cognee.ai"],
            "keywords": [
                "Cognee", "agent memory",
                "knowledge graph",
            ],
        },
    },
    {
        "name": "TriggerWare.ai",
        "entity_type": "organization",
        "metadata": {
            "domains": ["triggerware.ai"],
            "keywords": [
                "TriggerWare", "event-driven",
                "workflow automation",
            ],
        },
    },
    {
        "name": "Web Data UNLOCKED Hackathon",
        "entity_type": "organization",
        "metadata": {
            "domains": ["lablab.ai"],
            "keywords": [
                "Web Data UNLOCKED", "lablab.ai hackathon",
                "Bright Data hackathon",
            ],
        },
    },
]

DEFAULT_VENDORS: List[Dict[str, Any]] = [
    {
        "name": "Bright Data",
        "domain": "brightdata.com",
    },
    {
        "name": "AI/ML API",
        "domain": "aimlapi.com",
    },
    {
        "name": "Cognee",
        "domain": "cognee.ai",
    },
    {
        "name": "Speechmatics",
        "domain": "speechmatics.com",
    },
    {
        "name": "TriggerWare.ai",
        "domain": "triggerware.ai",
    },
]


async def run_threat_intel_loop():
    """Continuously run threat intelligence monitoring."""
    agent = ThreatIntelligenceAgent(entities=DEFAULT_ENTITIES)
    interval = settings.threat_intel_interval_minutes * 60

    while True:
        try:
            result = await agent.run_cycle()
            logger.info(
                f"Threat intel cycle complete: "
                f"{result['total_findings']} findings, "
                f"{result['critical_count']} critical, "
                f"{result['high_count']} high"
            )
        except Exception as e:
            logger.error(f"Threat intel cycle failed: {e}")

        await asyncio.sleep(interval)


async def run_compliance_monitor_loop():
    """Continuously run compliance monitoring."""
    agent = ComplianceMonitorAgent()
    interval = settings.compliance_interval_minutes * 60

    while True:
        try:
            result = await agent.run_cycle()
            logger.info(
                f"Compliance cycle complete: "
                f"{result['total_findings']} findings, "
                f"{result['high_impact_count']} high impact"
            )
        except Exception as e:
            logger.error(f"Compliance cycle failed: {e}")

        await asyncio.sleep(interval)


async def main():
    """Run all agent loops concurrently."""
    logger.info("Starting SentinelWatch agents")

    await asyncio.gather(
        run_threat_intel_loop(),
        run_compliance_monitor_loop(),
    )


if __name__ == "__main__":
    logging.basicConfig(
        level=settings.log_level.value,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    asyncio.run(main())
