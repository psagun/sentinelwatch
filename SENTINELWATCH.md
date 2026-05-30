# SentinelWatch — AI-Powered Security & Compliance Monitoring

Built for the **Web Data UNLOCKED AI Hackathon** by Bright Data × lablab.ai.

**Track:** Track 3 — Security & Compliance

**Team:** SentinelWatch

---

## Overview

SentinelWatch is a real-time security monitoring platform that uses **Bright Data** (Web Unlocker, SERP API, Scraping Browser) to gather threat intelligence, vulnerability data, and compliance information about monitored entities. **AI/ML API** analyzes the collected data to assess risk, severity, and recommend remediation actions.

The result is a Grafana/Kibana-inspired dashboard that gives security teams a single pane of glass for their organization's security posture.

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                    Frontend (React)                  │
│  Port 5173 — Dark SOC/NOC Dashboard                 │
│  Recharts, Tailwind CSS, Lucide Icons               │
│  ┌───┐ ┌───┐ ┌───┐ ┌───┐ ┌───┐                     │
│  │ D │ │ F │ │ A │ │ E │ │ I │                     │
│  │ a │ │ i │ │ l │ │ n │ │ n │                     │
│  │ s │ │ n │ │ e │ │ t │ │ v │                     │
│  │ h │ │ d │ │ r │ │ i │ │ e │                     │
│  │   │ │ i │ │ t │ │ t │ │ s │                     │
│  │   │ │ n │ │ s │ │ i │ │ t │                     │
│  └───┘ │ g │ │   │ │ e │ │ i │                     │
│         │ s │ │   │ │ s │ │ g │                     │
│         └───┘ └───┘ └───┘ │ a │                     │
│                           │ t │                     │
│                           │ i │                     │
│                           │ o │                     │
│                           │ n │                     │
│                           │ s │                     │
│                           └───┘                     │
└──────────────────────┬──────────────────────────────┘
                       │ HTTP / Proxy
                       ▼
┌─────────────────────────────────────────────────────┐
│                  FastAPI Backend                      │
│  Port 8000 — REST API                                │
│  - /api/v1/dashboard/summary                         │
│  - /api/v1/findings, /api/v1/alerts                  │
│  - /api/v1/entities, /api/v1/investigate             │
│  - /api/v1/seed (demo data)                          │
└───────────┬────────────────────┬─────────────────────┘
            │                    │
            ▼                    ▼
┌───────────────────┐  ┌──────────────────────────┐
│ Bright Data CLI   │  │ AI/ML API                │
│ (bdata.cmd)       │  │ (threat analysis)        │
│ ┌───────────────┐ │  │                          │
│ │Web Unlocker   │ │  │ Analyzes collected data  │
│ │SERP API       │ │  │ Generates severity       │
│ │ScrapingBrowser│ │  │ Generates recommendations│
│ └───────────────┘ │  └──────────────────────────┘
└───────────────────┘
```

---

## Bright Data Integration

SentinelWatch uses three Bright Data products via the `bdata` CLI:

### 1. Web Unlocker
Bypasses bot detection and CAPTCHAs to scrape security-relevant content from:
- Company documentation portals
- GitHub repositories (exposed secrets)
- Status pages (SSL certs, uptime)

### 2. SERP API
Searches for threat intelligence across news sources:
- Vulnerability disclosures (CVEs)
- Data breach reports
- Dark web chatter about targets
- Regulatory compliance changes

### 3. Scraping Browser
Full browser automation for JavaScript-heavy pages:
- Login flow testing
- API endpoint discovery
- Content rendering verification

---

## Data Flow

```
1. COLLECT → Bright Data scrapes web sources for each entity
                ↓
2. ANALYZE  → AI/ML API classifies findings:
               - Severity (critical/high/medium/low/info)
               - Type (vulnerability, threat_intel, compliance)
               - Risk score (0-100)
                ↓
3. STORE    → In-memory database (FastAPI routes)
                ↓
4. ALERT    → If severity exceeds threshold → alert created
                ↓
5. DISPLAY  → React dashboard renders widgets + charts
```

---

## Features

### Data Collection
- Multi-source threat intelligence gathering (web scraping, SERP news)
- 3 collector modules: `threat_collector`, `compliance_collector`, `third_party_collector`
- Entity-based monitoring with configurable targets

### Risk Scoring
- Severity classification across 5 levels
- Aggregate risk scoring for entities (0-100 scale)
- Trend tracking over time

### Alerting
- Severity-based alert thresholds
- Alert acknowledge workflow
- Pending alert tracking

### Frontend Dashboard
- 5-page React SPA with sidebar navigation
- Live data visualization (donut charts, area charts, arc gauges)
- Animated stat counters with scroll-triggered count-up
- Severity-filterable findings with live search
- Entity cards with color-coded risk scores

---

## Seeded Demo Data

The `POST /api/v1/seed` endpoint populates 15 realistic findings and 7 alerts:

**Findings by severity:**
- Critical (3): Exposed API, AWS key exposure, GDPR data residency violation
- High (5): IDOR vulnerability, GDPR retention gap, SSL cert expiring, credential leak, DDoS chatter
- Medium (4): CVE library, missing CSP header, SOC 2 overdue, brand impersonation
- Low (3): Privacy policy gap, open redirect, internal IP exposure

**Monitored entities:**
- **Bright Data** — Risk score: 73 (high) — 9 findings
- **AI/ML API** — Risk score: 45 (medium) — 6 findings

---

## Files

```
sentinelwatch/
├── SENTINELWATCH.md              ← this file
├── .env                          # API keys (Bright Data, AI/ML)
├── src/
│   ├── main.py                   # FastAPI app entry
│   ├── config.py                 # Settings + constants
│   ├── api/
│   │   ├── routes.py             # REST API endpoints
│   │   └── schemas.py            # Pydantic models
│   ├── data_collection/
│   │   ├── brightdata_client.py  # Bright Data CLI wrapper
│   │   ├── threat_collector.py   # Threat intel gathering
│   │   ├── compliance_collector.py # Compliance checking
│   │   └── third_party_collector.py # Vendor risk assessment
│   ├── intelligence/
│   │   ├── investigation_agent.py # AI analysis agent
│   │   └── risk_scorer.py        # Risk scoring engine
│   └── alerting/
│       └── alert_manager.py      # Alert rules engine
├── agents/
│   ├── run_pipeline.py           # Multi-stage data pipeline
│   └── run_agents.py             # Simple agent runner
├── tests/                        # Pytest test suite
└── frontend/
    └── README.md                 # Frontend documentation
```

---

## Running the Project

```bash
# Terminal 1 — Backend
cd sentinelwatch
python -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2 — Seed data + add entities
curl -X POST http://localhost:8000/api/v1/entities \
  -H "Content-Type: application/json" \
  -d '{"name":"Bright Data","entity_type":"organization","metadata":{"domains":["brightdata.com"]}}'
curl -X POST http://localhost:8000/api/v1/entities \
  -H "Content-Type: application/json" \
  -d '{"name":"AI/ML API","entity_type":"organization","metadata":{"domains":["aimlapi.com"]}}'
curl -X POST http://localhost:8000/api/v1/seed

# Terminal 3 — Frontend
cd sentinelwatch/frontend
npm install
npm run dev

# Open: http://localhost:5173
```
