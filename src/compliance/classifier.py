import logging
from typing import Any, Dict, List

from src.compliance.rules import RULES, TITLE_KEYWORD_RULES

logger = logging.getLogger(__name__)


def classify_finding(finding: Dict[str, Any]) -> Dict[str, Any]:
    """Enrich a finding with compliance regulation tags."""
    compliance_tags: List[Dict[str, Any]] = []
    seen: set = set()

    check_type = finding.get("check_type", "")
    title = (finding.get("title", "") + " " + finding.get("description", "")).lower()

    if check_type in RULES:
        for rule in RULES[check_type]:
            key = (rule["regulation"], rule["article"])
            if key not in seen:
                compliance_tags.append(dict(rule))
                seen.add(key)

    for rule in TITLE_KEYWORD_RULES:
        if any(kw.lower() in title for kw in rule["keywords"]):
            key = (rule["regulation"], rule["article"])
            if key not in seen:
                compliance_tags.append(dict(rule))
                seen.add(key)

    finding_type = finding.get("finding_type", "")
    type_rules = _get_type_rules(finding_type)
    for rule in type_rules:
        key = (rule["regulation"], rule["article"])
        if key not in seen:
            compliance_tags.append(dict(rule))
            seen.add(key)

    sev_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
    compliance_tags.sort(key=lambda r: (sev_order.get(r.get("severity", "info"), 5), r["regulation"]))

    finding["compliance"] = compliance_tags
    finding["agent_meta"] = _get_agent_meta(finding)
    return finding


def _get_agent_meta(finding: Dict[str, Any]) -> Dict[str, Any]:
    """Determine which agent discovered this finding and how."""
    check_type = finding.get("check_type", "")
    source_type = finding.get("source_type", "")
    title = finding.get("title", "").lower()

    # Check-type based classification (Web Scraper / Scraping Browser)
    if check_type in ("headers", "ssl", "server_info", "well-known"):
        return {
            "agent": "Web Scraper Agent",
            "step": 2,
            "method": ("Inspected HTTP response headers for security standards compliance"
                       if check_type == "headers" else
                       "Inspected SSL certificate chain and expiry via direct socket connection"
                       if check_type == "ssl" else
                       "Checked Server and X-Powered-By headers for information disclosure"
                       if check_type == "server_info" else
                       "Fetched /.well-known/security.txt and /robots.txt via Bright Data Web Unlocker"),
            "brightdata_tool": "Bright Data Web Unlocker — CAPTCHA-bypassing HTTP fetch + SSL socket inspection",
            "classification": f"Found via {check_type} check on the target URL",
        }
    if check_type == "browser":
        return {
            "agent": "Scraping Browser Agent",
            "step": 3,
            "method": "Launched headless Chromium via Bright Data Scraping Browser, rendered full page with JS execution, analyzed accessibility tree",
            "brightdata_tool": "Bright Data Scraping Browser — Headless Chromium with full JS execution",
            "classification": "Detected by analyzing rendered DOM for third-party resources, inline scripts, and mixed content",
        }
    if check_type == "accessibility":
        return {
            "agent": "Web Scraper Agent",
            "step": 2,
            "method": "Attempted to fetch the target URL via Bright Data Web Unlocker and analyzed response",
            "brightdata_tool": "Bright Data Web Unlocker — Page fetch with anti-bot bypass",
            "classification": "Accessibility check via direct page fetch",
        }

    # Source-type based classification (SERP / Threat Intel)
    if source_type in ("serp_search", "serp_news"):
        # Check for specific threat types
        if any(w in title for w in ["leak", "breach", "credential", "password", "exposed"]):
            return {
                "agent": "Threat Intelligence Agent",
                "step": 1,
                "method": "Searched Google via Bright Data SERP API with security keywords matching credential exposure patterns",
                "brightdata_tool": "Bright Data SERP API — Google Search with geo-targeting and freshness filtering",
                "classification": "Keyword matching classified this as a credential exposure threat",
            }
        if any(w in title for w in ["cve", "vulnerability", "exploit"]):
            return {
                "agent": "Threat Intelligence Agent",
                "step": 1,
                "method": "Searched Google via Bright Data SERP API for CVE and vulnerability mentions",
                "brightdata_tool": "Bright Data SERP API — Google Search",
                "classification": "SERP result matched vulnerability/CVE keyword patterns",
            }
        if any(w in title for w in ["ddos", "chatter", "attack"]):
            return {
                "agent": "Threat Intelligence Agent",
                "step": 1,
                "method": "Searched Google via Bright Data SERP API for dark web and forum mentions of targeted attacks",
                "brightdata_tool": "Bright Data SERP API — Google Search",
                "classification": "SERP result matched threat actor chatter patterns",
            }
        if any(w in title for w in ["impersonation", "phishing", "brand"]):
            return {
                "agent": "Threat Intelligence Agent",
                "step": 1,
                "method": "Searched Google via Bright Data SERP API for brand impersonation and phishing domain mentions",
                "brightdata_tool": "Bright Data SERP API — Google Search",
                "classification": "SERP result matched brand protection keyword patterns",
            }
        return {
            "agent": "Threat Intelligence Agent",
            "step": 1,
            "method": "Searched Google via Bright Data SERP API for security-related mentions",
            "brightdata_tool": "Bright Data SERP API — Google Search",
            "classification": "SERP result classified via keyword matching",
        }

    # Default
    return {
        "agent": "AI Investigation Agent",
        "step": 5,
        "method": "Analyzed collected evidence via AI/ML API for classification and scoring",
        "brightdata_tool": "AI/ML API — LLM-powered threat analysis",
        "classification": "AI-classified based on evidence context and severity indicators",
    }


def _get_type_rules(finding_type: str) -> List[Dict[str, Any]]:
    type_map = {
        "vulnerability": [
            {"regulation": "PCI_DSS", "article": "6.5", "severity": "high", "description": "Security vulnerabilities must be identified per PCI DSS"},
            {"regulation": "SOC2", "article": "CC6.6", "severity": "high", "description": "Vulnerability management controls required for SOC 2"},
        ],
        "threat_intel": [
            {"regulation": "GDPR", "article": "Art. 32", "severity": "high", "description": "Threat intelligence indicates security of processing risks"},
            {"regulation": "SOC2", "article": "CC7.2", "severity": "high", "description": "Threat monitoring feeds are critical for SOC 2"},
        ],
        "compliance": [
            {"regulation": "GDPR", "article": "Art. 5", "severity": "high", "description": "Compliance gaps impact GDPR accountability principles"},
            {"regulation": "SOC2", "article": "CC1.1", "severity": "high", "description": "Compliance deviations indicate control environment deficiencies"},
        ],
        "brand": [
            {"regulation": "SOC2", "article": "CC3.2", "severity": "low", "description": "Brand exposure may indicate broader security weaknesses"},
        ],
    }
    return type_map.get(finding_type, [])


def classify_findings(findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [classify_finding(f) for f in findings]


def get_compliance_summary(findings: List[Dict[str, Any]]) -> Dict[str, Any]:
    summary: Dict[str, Dict[str, Any]] = {}
    for reg in ["GDPR", "SOC2", "HIPAA", "PCI_DSS"]:
        summary[reg] = {
            "label": _reg_label(reg),
            "total": 0, "critical": 0, "high": 0, "medium": 0, "low": 0,
            "findings": [],
        }
    for f in findings:
        for c in f.get("compliance", []):
            reg = c["regulation"]
            sev = c.get("severity", "info")
            if reg in summary:
                summary[reg]["total"] += 1
                if sev in summary[reg]:
                    summary[reg][sev] += 1
                summary[reg]["findings"].append({
                    "id": f.get("id", ""),
                    "title": f.get("title", ""),
                    "severity": sev,
                    "article": c.get("article", ""),
                })
    return summary


def _reg_label(reg: str) -> str:
    labels = {"GDPR": "GDPR", "SOC2": "SOC 2", "HIPAA": "HIPAA", "PCI_DSS": "PCI DSS"}
    return labels.get(reg, reg)
