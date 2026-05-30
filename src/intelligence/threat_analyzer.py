"""Threat intelligence analysis engine.

Uses AI/ML API to analyze raw threat findings, classify them,
extract IOCs (Indicators of Compromise), and assign severity scores.
"""

import json
import logging
from typing import Any, Dict, List, Optional

import httpx

from src.config import settings

logger = logging.getLogger(__name__)


class ThreatAnalyzer:
    """Analyzes raw threat findings using AI/ML API."""

    def __init__(self):
        self.api_key = settings.aiml_api_key
        self.api_base = settings.aiml_api_base
        self.model = settings.aiml_default_model

    async def analyze_finding(
        self, title: str, description: str, source_type: str
    ) -> Dict[str, Any]:
        """Analyze a threat finding using AI.

        Returns:
            Dict with keys: classification, severity, iocs, confidence,
            recommended_action
        """
        prompt = f"""You are a security threat analyst. Analyze the following finding:

SOURCE TYPE: {source_type}
TITLE: {title}
DESCRIPTION: {description}

Return a JSON object with:
- "classification": one of ["cve", "malware", "phishing", "data_breach",
   "ransomware", "social_engineering", "ddos", "insider_threat",
   "brand_impersonation", "other"]
- "severity": one of ["critical", "high", "medium", "low", "info"]
- "iocs": list of extracted indicators (IPs, domains, hashes, CVE IDs)
- "confidence": 0.0 to 1.0
- "recommended_action": brief action recommendation

Return ONLY valid JSON, no markdown."""
        try:
            result = await self._call_llm(prompt)
            return self._parse_response(result)
        except Exception as e:
            logger.error(f"Threat analysis failed: {e}")
            return {
                "classification": "other",
                "severity": "medium",
                "iocs": [],
                "confidence": 0.3,
                "recommended_action": "Manual review required",
            }

    async def extract_iocs(self, text: str) -> List[str]:
        """Extract indicators of compromise from raw text."""
        prompt = f"""Extract all IOCs (Indicators of Compromise) from this text.
Return categories:
- IP addresses
- Domain names
- URLs
- File hashes (MD5, SHA1, SHA256)
- CVE identifiers
- Email addresses

Return as JSON: {{"iocs": ["item1", "item2", ...]}}

Text:
{text[:3000]}"""
        try:
            result = await self._call_llm(prompt)
            parsed = json.loads(result)
            return parsed.get("iocs", [])
        except Exception as e:
            logger.warning(f"IOC extraction failed: {e}")
            return []

    async def _call_llm(self, prompt: str) -> str:
        """Call AI/ML API for LLM inference."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.api_base}/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 1000,
                    "temperature": 0.1,
                },
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

    def _parse_response(self, text: str) -> Dict[str, Any]:
        """Parse LLM response, handling markdown code blocks."""
        text = text.strip()
        # Strip markdown code fences
        if text.startswith("```"):
            text = text.split("\n", 1)[-1]
            text = text.rsplit("```", 1)[0].strip()
        return json.loads(text)
