from typing import Any, Dict, List

REGULATIONS = ["GDPR", "SOC2", "HIPAA", "PCI_DSS"]

RULES: Dict[str, List[Dict[str, Any]]] = {
    "headers": [
        {"regulation": "SOC2", "article": "CC6.1", "severity": "medium", "description": "Missing security headers impairs system monitoring and access control"},
        {"regulation": "PCI_DSS", "article": "6.5", "severity": "medium", "description": "Missing CSP enables XSS attacks against cardholder data environments"},
    ],
    "ssl": [
        {"regulation": "SOC2", "article": "CC6.7", "severity": "high", "description": "Expired or invalid SSL breaks encryption-in-transit requirements"},
        {"regulation": "HIPAA", "article": "164.312(a)(2)(iv)", "severity": "high", "description": "Failure to encrypt ePHI in transit violates technical safeguards"},
        {"regulation": "PCI_DSS", "article": "4.1", "severity": "high", "description": "Strong cryptography must protect PAN during transmission"},
    ],
    "server_info": [
        {"regulation": "SOC2", "article": "CC6.6", "severity": "low", "description": "Server header disclosure aids attackers in targeting vulnerabilities"},
        {"regulation": "PCI_DSS", "article": "6.5", "severity": "low", "description": "Information leakage through server headers exposes technology stack"},
        {"regulation": "HIPAA", "article": "164.312(e)(1)", "severity": "low", "description": "Integrity controls must protect ePHI from improper alteration"},
    ],
    "well-known": [
        {"regulation": "GDPR", "article": "Art. 33", "severity": "medium", "description": "No security.txt hinders vulnerability reporting for breach notification compliance"},
    ],
    "accessibility": [
        {"regulation": "GDPR", "article": "Art. 32", "severity": "high", "description": "Website inaccessibility may indicate insufficient security of processing"},
        {"regulation": "SOC2", "article": "CC6.7", "severity": "medium", "description": "Mixed HTTP/HTTPS content compromises encryption integrity"},
        {"regulation": "PCI_DSS", "article": "4.1", "severity": "high", "description": "Mixed content loading HTTP resources risks cardholder data exposure"},
    ],
    "browser": [
        {"regulation": "GDPR", "article": "Art. 28", "severity": "medium", "description": "Third-party scripts may process personal data without adequate processor agreements"},
        {"regulation": "SOC2", "article": "CC3.2", "severity": "medium", "description": "Third-party script domains represent uncontrolled vendor data flows"},
        {"regulation": "HIPAA", "article": "164.308(b)(1)", "severity": "medium", "description": "Third-party scripts may expose ePHI without proper BAAs"},
    ],
}

TITLE_KEYWORD_RULES: List[Dict[str, Any]] = [
    {"keywords": ["leak", "breach", "credential", "password", "exposed"], "regulation": "GDPR", "article": "Art. 32", "severity": "critical", "description": "Credential exposure violates security of processing requirements"},
    {"keywords": ["leak", "breach", "credential", "password", "exposed"], "regulation": "SOC2", "article": "CC6.1", "severity": "critical", "description": "Credential exposure indicates access control failure"},
    {"keywords": ["leak", "breach", "credential", "password", "exposed"], "regulation": "HIPAA", "article": "164.312(a)(1)", "severity": "critical", "description": "ePHI access without unique user identification violates technical safeguard"},
    {"keywords": ["leak", "breach", "credential", "password", "exposed"], "regulation": "PCI_DSS", "article": "8.0", "severity": "critical", "description": "Credential exposure violates authentication requirements"},
    {"keywords": ["api", "endpoint", "authentication"], "regulation": "SOC2", "article": "CC6.1", "severity": "high", "description": "API endpoints without proper authentication violate access control"},
    {"keywords": ["api", "endpoint", "authentication"], "regulation": "HIPAA", "article": "164.312(a)(1)", "severity": "high", "description": "API access without unique user identification may expose ePHI"},
    {"keywords": ["api", "endpoint", "authentication"], "regulation": "PCI_DSS", "article": "6.5", "severity": "high", "description": "Weak API authentication can lead to unauthorized cardholder data access"},
    {"keywords": ["data residency", "data retention", "gdpr"], "regulation": "GDPR", "article": "Art. 45", "severity": "critical", "description": "Data residency violations breach international transfer requirements"},
    {"keywords": ["data residency", "data retention", "gdpr"], "regulation": "SOC2", "article": "CC1.1", "severity": "high", "description": "Data governance controls must address data residency and retention"},
    {"keywords": ["soc", "audit", "certification"], "regulation": "SOC2", "article": "CC1.1", "severity": "medium", "description": "SOC 2 audit findings indicate control environment gaps"},
    {"keywords": ["vendor", "third.party", "supplier"], "regulation": "GDPR", "article": "Art. 28", "severity": "medium", "description": "Third-party processing requires adequate processor agreements"},
    {"keywords": ["vendor", "third.party", "supplier"], "regulation": "SOC2", "article": "CC3.2", "severity": "medium", "description": "Vendor management controls must assess third-party risks"},
    {"keywords": ["vendor", "third.party", "supplier"], "regulation": "HIPAA", "article": "164.308(b)(1)", "severity": "medium", "description": "BAAs required for all third-party PHI processing"},
]


def get_regulation_label(regulation: str) -> str:
    labels = {"GDPR": "GDPR", "SOC2": "SOC 2", "HIPAA": "HIPAA", "PCI_DSS": "PCI DSS"}
    return labels.get(regulation, regulation)
