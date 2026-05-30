"""Compliance change analyzer.

Uses AI/ML API to parse regulatory updates, classify change types,
map to specific obligations, and assess organizational impact.
"""

import json
import logging
from typing import Any, Dict, List, Optional

import httpx

from src.config import settings

logger = logging.getLogger(__name__)


class ComplianceAnalyzer:
    """Analyzes regulatory compliance changes using AI."""

    def __init__(self):
        self.api_key = settings.aiml_api_key
        self.api_base = settings.aiml_api_base
        self.model = settings.aiml_default_model

    async def analyze_change(
        self,
        regulation: str,
        title: str,
        summary: str,
        change_type: str,
    ) -> Dict[str, Any]:
        """Analyze a regulatory change and assess organizational impact.

        Returns:
            Dict with: regulation, change_type, summary, obligations,
            impact_level, deadline, recommended_actions
        """
        prompt = f"""You are a compliance analyst. Analyze this regulatory change:

REGULATION: {regulation}
TITLE: {title}
SUMMARY: {summary}
CHANGE TYPE: {change_type}

Return JSON with:
- "summary": one-paragraph analysis
- "obligations": list of specific compliance obligations created
- "impact_level": "high" | "medium" | "low" | "info"
- "deadline": deadline if applicable, or null
- "affected_departments": list of affected org departments
- "recommended_actions": list of recommended action items
- "similar_regulations": list of potentially related regulations

Return ONLY valid JSON, no markdown."""
        try:
            result = await self._call_llm(prompt)
            return self._parse_response(result)
        except Exception as e:
            logger.error(f"Compliance analysis failed: {e}")
            return {
                "summary": "Analysis failed — manual review required",
                "obligations": [],
                "impact_level": "medium",
                "deadline": None,
                "affected_departments": ["legal", "security"],
                "recommended_actions": ["Review change manually"],
                "similar_regulations": [],
            }

    async def map_to_framework(
        self, regulation: str, text: str, framework: str = "NIST CSF"
    ) -> Dict[str, Any]:
        """Map a regulatory change to an existing compliance framework."""
        prompt = f"""Map this {regulation} change to the {framework} framework:

{text[:2000]}

Return JSON mapping control IDs to change relevance:
{{
  "framework": "{framework}",
  "mappings": [
    {{"control_id": "ID.AM-1", "relevance": "high",
      "notes": "..."}}
  ],
  "gap_analysis": "brief gap assessment"
}}"""
        try:
            result = await self._call_llm(prompt)
            return self._parse_response(result)
        except Exception as e:
            logger.warning(f"Framework mapping failed: {e}")
            return {"framework": framework, "mappings": [],
                    "gap_analysis": "Mapping unavailable"}

    async def _call_llm(self, prompt: str) -> str:
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
                    "max_tokens": 1500,
                    "temperature": 0.1,
                },
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

    def _parse_response(self, text: str) -> Dict[str, Any]:
        text = text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[-1]
            text = text.rsplit("```", 1)[0].strip()
        return json.loads(text)
