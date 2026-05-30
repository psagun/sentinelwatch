"""Analysis agent — classifies findings and generates security reports.

Uses AI/ML API for intelligent analysis when available, falls back to
rule-based keyword matching when AI credits are exhausted.
"""

import json
import logging
from typing import Any, Dict, List, Optional

import httpx

from src.config import settings
from src.intelligence.risk_scorer import RiskScorer

logger = logging.getLogger(__name__)

SEVERITY_KEYWORDS: Dict[str, List[str]] = {
    "critical": [
        "leak", "breach", "exposed", "ransomware", "cve-20",
        "credential", "password", "backdoor", "zero-day", "exploit",
    ],
    "high": [
        "vulnerability", "cve", "injection", "xss", "rce",
        "privilege escalation", "authentication bypass", "expir",
        "data loss", "unauthorized",
    ],
    "medium": [
        "missing", "outdated", "misconfig", "deprecated",
        "information disclosure", "clickjacking", "csrf",
        "self-signed", "weak cipher",
    ],
    "low": [
        "mention", "discussion", "possible", "report",
        "notice", "advisory", "patch",
    ],
}

RECOMMENDATIONS: Dict[str, str] = {
    "critical": "Investigate immediately — this requires urgent remediation.",
    "high": "Schedule remediation within 48 hours. Prioritize in next sprint.",
    "medium": "Add to remediation backlog. Review within 2 weeks.",
    "low": "Monitor. No immediate action required.",
    "info": "Logged for awareness.",
}

FINDING_TYPE_KEYWORDS: Dict[str, List[str]] = {
    "vulnerability": [
        "cve", "vulnerability", "injection", "xss", "rce", "exploit",
        "patch", "security header", "ssl", "tls", "authentication",
        "encryption", "misconfig",
    ],
    "threat_intel": [
        "leak", "breach", "credential", "malware", "phishing",
        "ransomware", "ddos", "chatter", "impersonation", "pastebin",
    ],
    "compliance": [
        "gdpr", "soc", "hipaa", "pci", "compliance", "regulation",
        "data retention", "privacy", "ccpa",
    ],
}


class AnalysisResult:
    """Result of analyzing findings for an entity."""

    def __init__(
        self,
        findings: List[Dict[str, Any]],
        risk_score: Dict[str, Any],
        summary: str,
        recommendations: List[str],
    ):
        self.findings = findings
        self.risk_score = risk_score
        self.summary = summary
        self.recommendations = recommendations


class AnalysisAgent:
    """Analyzes raw collector findings and enriches them with:
    - Severity classification
    - Risk scoring
    - Human-readable descriptions
    - Remediation recommendations
    - Entity-level risk assessment
    """

    def __init__(self):
        self.api_key = settings.aiml_api_key
        self.api_base = settings.aiml_api_base
        self.risk_scorer = RiskScorer()

    async def analyze_findings(
        self,
        findings: List[Dict[str, Any]],
        entity_name: str,
    ) -> AnalysisResult:
        """Enrich findings with severity, scores, and recommendations.

        Tries AI/ML API first. Falls back to rule-based classification
        if the API is unavailable or credits are exhausted.
        """
        if not findings:
            return AnalysisResult(
                findings=[],
                risk_score={"score": 0.0, "level": "none", "finding_counts": {}},
                summary=f"No findings for {entity_name}.",
                recommendations=[],
            )

        # Try AI-powered analysis
        try:
            return await self._ai_analysis(findings, entity_name)
        except Exception as e:
            logger.warning(
                f"AI analysis failed for {entity_name}, "
                f"falling back to rules: {e}"
            )
            return self._rule_analysis(findings, entity_name)

    async def _ai_analysis(
        self,
        findings: List[Dict[str, Any]],
        entity_name: str,
    ) -> AnalysisResult:
        """Use AI/ML API to classify findings and generate a report."""
        findings_input = [
            {
                "title": f.get("title", ""),
                "description": f.get("description", f.get("summary", "")),
                "source": f.get("source_type", ""),
                "url": f.get("source_url", ""),
            }
            for f in findings[:15]
        ]

        prompt = f"""You are a security analyst. Analyze these findings for "{entity_name}":

FINDINGS:
{json.dumps(findings_input, indent=2)}

For each finding, classify:
1. severity: "critical" | "high" | "medium" | "low" | "info"
2. finding_type: "vulnerability" | "threat_intel" | "compliance" | "brand"
3. risk_score: 0.0-10.0
4. remediation: One-sentence recommendation

Also provide:
5. executive_summary: 2-3 sentences on overall posture
6. overall_risk_score: 0-100
7. top_recommendations: 3 priority actions

Return JSON with keys: "findings" (array of {title, severity, finding_type, risk_score, remediation}), "executive_summary", "overall_risk_score", "top_recommendations"."""

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.api_base}/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": settings.aiml_default_model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 2000,
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

        result = json.loads(text)

        # Merge AI classifications back into findings
        ai_map = {f["title"]: f for f in result.get("findings", [])}
        enriched = []
        for f in findings:
            ai = ai_map.get(f.get("title", ""), {})
            f["severity"] = ai.get("severity", "info")
            f["finding_type"] = ai.get("finding_type", "threat_intel")
            f["risk_score"] = ai.get("risk_score", f.get("risk_score", 5.0))
            f["description"] = f.get("description", f.get("summary", ""))
            f["remediation"] = ai.get("remediation", "Review and assess.")
            enriched.append(f)

        risk_result = self.risk_scorer.score(enriched)

        return AnalysisResult(
            findings=enriched,
            risk_score=risk_result,
            summary=result.get(
                "executive_summary",
                f"{len(enriched)} findings identified for {entity_name}.",
            ),
            recommendations=result.get("top_recommendations", []),
        )

    def _rule_analysis(
        self,
        findings: List[Dict[str, Any]],
        entity_name: str,
    ) -> AnalysisResult:
        """Rule-based fallback: classify findings by keyword matching."""
        enriched = []
        for f in findings:
            title = (f.get("title", "") + " " + f.get("description", "") + " " + f.get("summary", "")).lower()

            severity = "info"
            for level, keywords in SEVERITY_KEYWORDS.items():
                if any(kw in title for kw in keywords):
                    severity = level
                    break

            finding_type = "threat_intel"
            for ftype, keywords in FINDING_TYPE_KEYWORDS.items():
                if any(kw in title for kw in keywords):
                    finding_type = ftype
                    break

            f["severity"] = f.get("severity", severity)
            f["finding_type"] = f.get("finding_type", finding_type)
            f["risk_score"] = f.get("risk_score", 5.0)
            f["description"] = f.get("description", f.get("summary", ""))
            f["remediation"] = RECOMMENDATIONS.get(f["severity"], "Review.")
            enriched.append(f)

        risk_result = self.risk_scorer.score(enriched)

        # Build summary from top findings
        top = enriched[:3]
        summary_parts = [
            f"{e.get('title', '')} ({e.get('severity', 'info')})"
            for e in top
        ]
        summary = (
            f"Analysis for {entity_name}: "
            + "; ".join(summary_parts)
            + f". {len(enriched)} total findings."
        )

        sev_counts = risk_result.get("finding_counts", {})
        recommendations = []
        if sev_counts.get("critical", 0) > 0:
            recommendations.append(f"Address {sev_counts['critical']} critical finding(s) immediately.")
        if sev_counts.get("high", 0) > 0:
            recommendations.append(f"Schedule remediation for {sev_counts['high']} high-severity finding(s).")
        if sev_counts.get("medium", 0) > 0:
            recommendations.append(f"Review {sev_counts['medium']} medium-severity finding(s) in next sprint.")
        if not recommendations:
            recommendations.append("No urgent issues detected. Continue routine monitoring.")

        return AnalysisResult(
            findings=enriched,
            risk_score=risk_result,
            summary=summary,
            recommendations=recommendations,
        )
