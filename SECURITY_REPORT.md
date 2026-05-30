# SentinelWatch Security Report

**Generated:** 2026-05-29  
**Period:** 2026-05-26 through 2026-05-29 (last 3 days)  
**Platform Version:** SentinelWatch v1.0.0  

---

## 1. Executive Summary

SentinelWatch scanned **6 monitored entities** (Bright Data, AI/ML API, Speechmatics, Cognee, TriggerWare.ai) over the assessment period, producing **15 security findings** and **7 pending alerts**. Two entities have been actively assessed: **Bright Data** carries a **high risk score of 72.5/100**, and **AI/ML API** carries a **medium risk score of 45.0/100**. The remaining four entities (Speechmatics, Cognee, TriggerWare.ai, and a duplicate Bright Data website entry) show a risk score of 0.0, indicating they have not yet been scanned.

The overall security posture is **elevated risk**. Three critical-severity findings require immediate remediation, and five high-severity findings require near-term action. Compliance exposure spans all four tracked frameworks (GDPR, SOC 2, HIPAA, PCI DSS), with credential exposure and data residency violations as the most impactful themes.

---

## 2. Findings Summary

| Metric | Count |
|---|---|
| Total Findings | 15 |
| Critical | 3 |
| High | 5 |
| Medium | 4 |
| Low | 3 |
| Info | 0 |

### 2.1 Findings by Severity

| Severity | Count | % of Total |
|---|---|---|
| Critical | 3 | 20.0% |
| High | 5 | 33.3% |
| Medium | 4 | 26.7% |
| Low | 3 | 20.0% |
| **Total** | **15** | **100%** |

### 2.2 Findings by Type

| Type | Count | % of Total |
|---|---|---|
| Vulnerability | 6 | 40.0% |
| Threat Intelligence | 5 | 33.3% |
| Compliance | 4 | 26.7% |

### 2.3 Findings by Entity

| Entity | Findings | Risk Score | Risk Level |
|---|---|---|---|
| Bright Data | 10 | 72.5/100 | High |
| AI/ML API | 5 | 45.0/100 | Medium |
| Speechmatics | 0 | 0.0/100 | Pending |
| Cognee | 0 | 0.0/100 | Pending |
| TriggerWare.ai | 0 | 0.0/100 | Pending |

---

## 3. Findings by Severity

### 3.1 Critical Findings (3)

| ID | Title | Entity | Risk Score | Type |
|---|---|---|---|---|
| f001 | Exposed API endpoint with weak authentication | Bright Data | 8.5/10 | Vulnerability |
| f009 | Sensitive key exposed in public GitHub repo | Bright Data | 9.0/10 | Threat Intelligence |
| f013 | Data residency requirement not met for EU customers | Bright Data | 8.8/10 | Compliance |

**f001 - Exposed API endpoint with weak authentication**  
The Bright Data dashboard exposes an API endpoint that lacks rate limiting and contains a potential Server-Side Request Forgery (SSRF) vector. This endpoint could be used to enumerate internal infrastructure or perform unauthorized operations against the Bright Data platform.

**f009 - Sensitive key exposed in public GitHub repo**  
An AWS access key was discovered in the public repository "brightdata-sdk-examples." While the key has been rotated, the exposure window creates risk of unauthorized cloud resource access. Credential scanning and automated secret detection should be implemented as a preventive control.

**f013 - Data residency requirement not met for EU customers**  
Customer data for EU-based clients is being stored in the US-east region, which violates GDPR data residency requirements under Article 45 (international transfer provisions). This represents a significant regulatory compliance gap with potential for substantial fines.

### 3.2 High Severity Findings (5)

| ID | Title | Entity | Risk Score | Type |
|---|---|---|---|---|
| f002 | Insecure direct object reference in user API | AI/ML API | 7.2/10 | Vulnerability |
| f003 | GDPR compliance gap in data retention policy | Bright Data | 7.8/10 | Compliance |
| f010 | SSL certificate expiring in 7 days | AI/ML API | 7.0/10 | Vulnerability |
| f012 | Credentials leaked in pastebin dump | AI/ML API | 7.5/10 | Threat Intelligence |
| f015 | DDoS chatter targeting proxy infrastructure | Bright Data | 7.3/10 | Threat Intelligence |

**f002 - IDOR Vulnerability** - The AI/ML API user profile endpoint allows user ID enumeration via an Insecure Direct Object Reference. Authorization checks are missing on the endpoint. Remediation: Implement ownership validation on all object-level access.

**f003 - GDPR Retention Policy Gap** - Customer logs are retained for 18 months without documented legitimate purpose. GDPR Article 5(1)(e) requires data to be kept no longer than necessary. Remediation: Implement a 12-month maximum retention policy with automated deletion workflows.

**f010 - SSL Certificate Expiring** - Wildcard SSL certificate for `*.aimlapi.com` expires in 7 days. Auto-renewal is configured but has not been tested end-to-end. Remediation: Verify auto-renewal configuration and perform a manual renewal test immediately.

**f012 - Credentials Leaked in Pastebin** - AI/ML API test environment credentials were found in a pastebin dump. No production impact has been confirmed, but this indicates a gap in credential hygiene for non-production environments.

**f015 - DDoS Chatter Targeting Proxy Infrastructure** - Dark web forums contain discussions of coordinated DDoS attacks targeting major proxy providers, including Bright Data. Remediation: Review DDoS mitigation capacity, ensure WAF rules are current, and coordinate with upstream providers.

### 3.3 Medium Severity Findings (4)

| ID | Title | Entity | Risk Score | Type |
|---|---|---|---|---|
| f004 | Third-party library with known CVE detected | Bright Data | 5.0/10 | Threat Intelligence |
| f005 | Missing Content-Security-Policy header | AI/ML API | 5.5/10 | Vulnerability |
| f006 | SOC 2 Type II certification renewal overdue | Bright Data | 4.8/10 | Compliance |
| f008 | Brand impersonation detected on social media | Bright Data | 4.5/10 | Threat Intelligence |

**f004 - CVE Library** - lodash 4.17.20 (CVE-2024-23346, CVSS 7.2) is used in the main web application bundle. Remediation: Upgrade to lodash 4.17.21 or later.

**f006 - SOC 2 Expired** - The SOC 2 Type II report expired 14 days ago. The renewal audit has been scheduled but not yet completed. Customers requiring current SOC 2 reports may be affected during procurement processes.

### 3.4 Low Severity Findings (3)

| ID | Title | Entity | Risk Score | Type |
|---|---|---|---|---|
| f007 | Privacy policy missing data processing disclosure | AI/ML API | 2.5/10 | Compliance |
| f011 | Open redirect vulnerability on login page | Bright Data | 3.0/10 | Vulnerability |
| f014 | Documentation exposing internal IP addresses | Bright Data | 2.0/10 | Vulnerability |

---

## 4. Compliance Impact

### 4.1 Compliance Tag Distribution

| Regulation | Total Tags | Critical | High | Medium | Low |
|---|---|---|---|---|---|
| SOC 2 | 24 | 3 | 18 | 3 | 0 |
| GDPR | 13 | 6 | 7 | 0 | 0 |
| PCI DSS | 11 | 3 | 8 | 0 | 0 |
| HIPAA | 7 | 3 | 4 | 0 | 0 |

Note: Findings can map to multiple regulations. The "total tags" count exceeds the total finding count because individual findings are tagged with all applicable regulations.

### 4.2 GDPR Impact

**Status: NON-COMPLIANT -- High Risk**

- **Article 45 (International Transfers)** -- EU customer data stored in US-east region without adequate safeguards. This is the most severe GDPR violation detected.
- **Article 32 (Security of Processing)** -- Credential exposure (f009, f012) and DDoS threat chatter (f015) indicate insufficient technical security measures.
- **Article 5 (Accountability)** -- Data retention periods exceeding 12 months (f003) and missing privacy disclosures (f007) demonstrate gaps in accountability and data minimization principles.

**Recommended actions:**
1. Migrate EU customer data to a GDPR-compliant region (EU or UK) within 30 days.
2. Implement automated data retention enforcement with maximum 12-month policy.
3. Conduct a Data Protection Impact Assessment (DPIA) for the credential exposure incidents.

### 4.3 SOC 2 Impact

**Status: NOTABLE DEFICIENCIES -- Medium Risk**

- **CC6.1 (Access Control)** -- Credential exposure (f009, f012) and weak API authentication (f001) indicate access control failures.
- **CC6.6 (Vulnerability Management)** -- Multiple vulnerabilities (f001, f002, f005, f010, f011, f014) without coordinated remediation.
- **CC7.2 (Threat Monitoring)** -- DDoS chatter (f015) and brand impersonation (f008) identified via threat intel feeds are being monitored, which is positive.
- **CC1.1 (Control Environment)** -- SOC 2 Type II certification has lapsed (f006), impacting the control environment assessment.

**Recommended actions:**
1. Complete the SOC 2 Type II renewal audit immediately.
2. Formalize vulnerability management with defined SLAs for each severity tier.
3. Review and remediate all access control gaps within 30 days.

### 4.4 HIPAA Impact

**Status: POTENTIAL EXPOSURE -- Medium Risk**

- **164.312(a)(1) (Unique User Identification)** -- Credential exposures (f009, f012) and weak API authentication (f001) could allow unauthorized access to ePHI.
- Multiple API-related findings (f002, f005, f010) lack proper authentication controls.

**Note:** HIPAA applicability assumes the monitored entities handle ePHI or act as business associates. If Bright Data and AI/ML API do not handle ePHI, these tags may be over-classifications. The compliance classifier should be reviewed for HIPAA sensitivity tuning.

### 4.5 PCI DSS Impact

**Status: NON-COMPLIANT -- High Risk**

- **Requirement 8.0 (Authentication)** -- Credential exposure violations (f009, f012) directly impact authentication requirements.
- **Requirement 6.5 (Vulnerability Management)** -- Six vulnerability-type findings (f001, f002, f005, f010, f011, f014) require identification and remediation under PCI DSS 6.5.

**Recommended actions:**
1. Verify whether cardholder data environments are in scope for the affected entities.
2. If in scope, remediate all critical and high vulnerabilities within PCI DSS timelines (critical: 7 days, high: 30 days).
3. Implement automated secret scanning in CI/CD pipelines.

---

## 5. Alerts Requiring Attention

All **7 alerts** are currently **pending** (no acknowledgments, no remediation started).

### 5.1 Critical Alerts

| ID | Alert | Channel | Age |
|---|---|---|---|
| a001 | Critical: Exposed API Endpoint | email, slack | ~2 hours |
| a003 | Critical: AWS Key Exposure | email, slack, pagerduty | ~40 hours |
| a004 | Critical: GDPR Data Residency Violation | email, slack | ~60 hours |

**a003 (AWS Key Exposure)** is the most time-sensitive alert: it was triggered 40 hours ago, routed through PagerDuty, and remains unacknowledged. The key has been rotated per the finding description, but formal incident documentation and root-cause analysis are still needed.

### 5.2 High Alerts

| ID | Alert | Channel | Age |
|---|---|---|---|
| a002 | High: IDOR Vulnerability | email | ~5 hours |
| a005 | High: GDPR Retention Policy Gap | email | ~8 hours |
| a006 | High: SSL Certificate Expiring | email | ~48 hours |
| a007 | High: DDoS Chatter Detected | email, slack | ~70 hours |

**a006 (SSL Certificate Expiring)** -- The SSL certificate for `*.aimlapi.com` expires in **5 days** from today (2026-05-29). This alert has been pending for 48 hours. If the certificate expires, all HTTPS services on AI/ML API will become inaccessible to standards-compliant browsers and clients.

---

## 6. Recommendations for Remediation

### 6.1 Immediate Actions (within 24 hours)

1. **Acknowledge and investigate all 7 pending alerts** -- Assign owners and begin documented response workflows.
2. **Verify AWS key rotation** (f009/a003) -- Confirm the exposed key in the GitHub repo has been fully deactivated and conduct a post-incident review.
3. **Test SSL auto-renewal** (f010/a006) -- Verify the wildcard certificate renewal process for `*.aimlapi.com` before the 5-day deadline.
4. **Begin EU data migration assessment** (f013/a004) -- Check with legal team on feasibility of moving EU customer data to a compliant region.

### 6.2 Short-Term Actions (within 7 days)

5. **Patch the exposed API endpoint** (f001/a001) -- Add rate limiting, input validation, and authentication to the Bright Data dashboard API.
6. **Fix the IDOR vulnerability** (f002/a002) -- Implement object-level authorization checks on the AI/ML API user profile endpoint.
7. **Implement data retention enforcement** (f003/a005) -- Configure automated log lifecycle management to enforce a 12-month maximum retention period.
8. **Review and update DDoS mitigation** (f015/a007) -- Confirm WAF rules, rate limiting, and upstream DDoS protection capacity.

### 6.3 Medium-Term Actions (within 30 days)

9. **Complete SOC 2 Type II renewal audit** (f006) -- Prioritize the audit to restore current certification status.
10. **Implement automated secret scanning** -- Deploy tools (e.g., GitLeaks, TruffleHog) in CI/CD pipelines to prevent credential exposure.
11. **Update privacy policies** (f007) -- Add third-party data processing disclosures to AI/ML API privacy policy.
12. **Patch open redirect vulnerability** (f011) -- Implement redirect URI validation on the Bright Data login page.
13. **Remove internal IP addresses** (f014) -- Sanitize developer documentation to remove network topology details.
14. **Upgrade lodash dependency** (f004) -- Update to 4.17.21 or later across all affected applications.
15. **Add Content-Security-Policy header** (f005) -- Configure CSP headers on the AI/ML API documentation portal.
16. **Address brand impersonation** (f008) -- Submit a takedown request to Twitter/X for the impersonating account.

### 6.4 Strategic Recommendations

17. **Establish a vulnerability management program** with defined SLAs per severity:
    - Critical: remediate within 7 days
    - High: remediate within 30 days
    - Medium: remediate within 90 days
18. **Implement a compliance dashboard** to track GDPR, SOC 2, HIPAA, and PCI DSS posture in near-real time.
19. **Conduct a penetration test** on both Bright Data and AI/ML API external-facing surfaces.
20. **Review entity onboarding** -- The four entities (Speechmatics, Cognee, TriggerWare.ai, and the duplicate Bright Data entry) with 0.0 risk scores have never been scanned. Investigate whether they should be assessed or removed from monitoring.
21. **Tune the compliance classifier** -- HIPAA tags may be over-applied to entities that do not handle ePHI. Review and adjust the keyword-based classification rules.

---

## 7. Risk Score Methodology

Risk scores are calculated on a scale of **0.0 (lowest) to 10.0 (highest)** for individual findings, and **0.0 to 100.0** for entity-level aggregated scores. Severity-to-score mapping:

| Severity | Score Range |
|---|---|
| Critical | 8.0 - 10.0 |
| High | 6.0 - 7.9 |
| Medium | 3.0 - 5.9 |
| Low | 1.0 - 2.9 |
| Info | 0.0 |

Entity-level risk scores aggregate individual finding scores weighted by severity and recency. An entity score above 70.0 is considered "High Risk," above 40.0 is "Medium Risk," and below 20.0 is "Low Risk."

---

*Report generated by SentinelWatch v1.0.0. Data sources: SQLite persistence store (sentinelwatch.db), in-memory findings and alerts databases, compliance classification engine.*
