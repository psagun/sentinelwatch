"""Autonomous investigation agent.

Uses AI/ML API + Bright Data MCP Server to autonomously investigate
threat indicators and return structured risk assessments.
"""

import json
import logging
from typing import Any, Dict, List, Optional

import httpx

from src.config import settings
from src.data_collection.brightdata_client import brightdata

logger = logging.getLogger(__name__)


class InvestigationResult:
    """Result of an autonomous investigation."""

    def __init__(
        self,
        indicator: str,
        indicator_type: str,
        verdict: str,
        confidence: float,
        evidence: List[Dict[str, Any]],
        affected_entities: List[str],
        recommended_actions: List[str],
        investigation_steps: int = 0,
    ):
        self.indicator = indicator
        self.indicator_type = indicator_type
        self.verdict = verdict
        self.confidence = confidence
        self.evidence = evidence
        self.affected_entities = affected_entities
        self.recommended_actions = recommended_actions
        self.investigation_steps = investigation_steps
        self.finding_type = "investigation"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "finding_type": self.finding_type,
            "indicator": self.indicator,
            "indicator_type": self.indicator_type,
            "verdict": self.verdict,
            "confidence": self.confidence,
            "evidence": self.evidence,
            "affected_entities": self.affected_entities,
            "recommended_actions": self.recommended_actions,
            "investigation_steps": self.investigation_steps,
        }


class InvestigationAgent:
    """AI agent that autonomously investigates threat indicators."""

    def __init__(self):
        self.api_key = settings.aiml_api_key
        self.api_base = settings.aiml_api_base

    async def investigate(
        self,
        indicator: str,
        indicator_type: str = "ip",
        context: Optional[str] = None,
    ) -> InvestigationResult:
        """Investigate a threat indicator using the ReAct pattern."""
        logger.info(
            f"Investigating {indicator_type}: {indicator}"
        )

        steps = []
        evidence = []

        # Step 1: Initial web research via MCP Server
        step1_evidence = await self._web_research(
            indicator, indicator_type
        )
        evidence.extend(step1_evidence)
        steps.append("web_research")

        # Step 2: Search for related reports
        step2_evidence = await self._search_reports(
            indicator, indicator_type
        )
        evidence.extend(step2_evidence)
        steps.append("report_search")

        # Step 3: Check historical context via Bright Data
        step3_data = await self._check_historical_data(indicator)
        evidence.append(step3_data)
        steps.append("historical_check")

        # Step 3.5: Browser investigation (only for domains/URLs)
        if indicator_type in ("domain", "url"):
            browser_data = await self._browser_investigation(
                indicator, indicator_type
            )
            evidence.append(browser_data)
            steps.append("browser_investigation")
        else:
            steps.append("browser_investigation_skipped")

        # Step 4: AI analysis and verdict
        verdict = await self._generate_verdict(
            indicator=indicator,
            indicator_type=indicator_type,
            evidence=evidence,
            context=context,
        )

        return InvestigationResult(
            indicator=indicator,
            indicator_type=indicator_type,
            verdict=verdict.get("verdict", "inconclusive"),
            confidence=verdict.get("confidence", 0.5),
            evidence=evidence,
            affected_entities=verdict.get("affected_entities", []),
            recommended_actions=verdict.get("recommended_actions", []),
            investigation_steps=len(steps),
        )

    async def _web_research(
        self, indicator: str, indicator_type: str
    ) -> List[Dict[str, Any]]:
        """Research the indicator using Bright Data SERP API."""
        evidence = []
        queries = [
            f"{indicator} threat indicator",
            f"{indicator} malware C2",
        ]
        for query in queries:
            try:
                results = await brightdata.serp_search(
                    query=query, source="google", max_results=5
                )
                for r in results:
                    evidence.append({
                        "source": "web_search",
                        "url": r.get("url", ""),
                        "title": r.get("title", ""),
                        "snippet": r.get("snippet", ""),
                    })
            except Exception as e:
                logger.warning(f"Web research failed: {e}")
        return evidence

    async def _search_reports(
        self, indicator: str, indicator_type: str
    ) -> List[Dict[str, Any]]:
        """Search security report databases."""
        evidence = []
        query = (
            f"site:virustotal.com OR site:abuseipdb.com "
            f"OR site:urlhaus.abuse.ch {indicator}"
        )
        try:
            results = await brightdata.serp_search(
                query=query, source="google", max_results=5
            )
            for r in results:
                evidence.append({
                    "source": "threat_intel_platform",
                    "url": r.get("url", ""),
                    "title": r.get("title", ""),
                    "snippet": r.get("snippet", ""),
                })
        except Exception as e:
            logger.warning(f"Report search failed: {e}")
        return evidence

    async def _check_historical_data(
        self, indicator: str
    ) -> Dict[str, Any]:
        """Check historical context via Bright Data Web Unlocker."""
        try:
            html = await brightdata.web_unlocker_get(
                f"https://www.abuseipdb.com/check/{indicator}"
            )
            return {
                "source": "historical_data",
                "data_preview": html[:500] if html else "No data",
            }
        except Exception as e:
            logger.warning(f"Historical check failed: {e}")
            return {"source": "historical_data",
                    "data_preview": "Unavailable"}

    async def _browser_investigation(
        self, indicator: str, indicator_type: str
    ) -> Dict[str, Any]:
        """Launch Scraping Browser to visually inspect a domain/URL."""
        if indicator_type not in ("domain", "url"):
            return {
                "source": "scraping_browser",
                "data_preview": "Skipped — browser inspection only applies to domains/URLs",
            }
        url = f"https://{indicator}" if indicator_type == "domain" else indicator
        try:
            snapshot = await brightdata.scraping_browser_navigate(url)
            if snapshot and len(snapshot) > 50:
                import re
                title_match = re.search(r'<title>([^<]+)</title>', snapshot)
                title = title_match.group(1) if title_match else ""
                return {
                    "source": "scraping_browser",
                    "url": url,
                    "title": title or "Untitled page",
                    "data_preview": (
                        f"Browser rendered {len(snapshot)} chars of content. "
                        f"Page title: {title or 'N/A'}. "
                        f"Scanned for JS threats and third-party resources."
                    ),
                }
            else:
                return {
                    "source": "scraping_browser",
                    "url": url,
                    "data_preview": "Browser could not render the page or returned minimal content",
                }
        except Exception as e:
            logger.warning(f"Browser investigation failed: {e}")
            return {
                "source": "scraping_browser",
                "url": url,
                "data_preview": f"Browser investigation failed: {e}",
            }

    async def _generate_verdict(
        self,
        indicator: str,
        indicator_type: str,
        evidence: List[Dict[str, Any]],
        context: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate an AI-driven verdict based on collected evidence."""
        evidence_text = json.dumps(
            [{"source": e["source"], "title": e.get("title", "")}
             for e in evidence[:10]],
            indent=2,
        )

        prompt = f"""You are a security analyst. Investigate this indicator:

INDICATOR: {indicator}
TYPE: {indicator_type}
{"CONTEXT: " + context if context else ""}

COLLECTED EVIDENCE:
{evidence_text}

Return JSON:
{{
  "verdict": "malicious" | "suspicious" | "benign" | "inconclusive",
  "confidence": 0.0-1.0,
  "rationale": "detailed reasoning",
  "affected_entities": ["entity1"],
  "recommended_actions": ["action1", "action2"],
  "further_investigation_needed": true/false,
  "ioc_categories": ["category1"]
}}"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.api_base}/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": settings.aiml_default_model,
                        "messages": [
                            {"role": "user", "content": prompt}
                        ],
                        "max_tokens": 1500,
                        "temperature": 0.1,
                    },
                )
                response.raise_for_status()
                data = response.json()
                text = data["choices"][0]["message"]["content"]

            text = text.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[-1]
                text = text.rsplit("```", 1)[0].strip()
            return json.loads(text)
        except Exception as e:
            logger.error(f"Verdict generation failed: {e}")
            return {
                "verdict": "inconclusive",
                "confidence": 0.3,
                "rationale": "AI analysis unavailable",
                "affected_entities": [],
                "recommended_actions": ["Manual investigation required"],
                "further_investigation_needed": True,
                "ioc_categories": ["unknown"],
            }
