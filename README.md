# SentinelWatch

**AI-Powered Security & Compliance Monitoring Platform**

SentinelWatch continuously monitors the open web for threats, regulatory changes, third-party risks, and brand exposure — delivering structured, actionable intelligence directly to security and compliance teams.

Built for the **Web Data UNLOCKED Hackathon** — Track 3: Security & Compliance.

---

## What It Does

- **Threat Intelligence Pipeline** — Monitors open web sources (CVE feeds, security blogs, dark web forums, paste sites) for org-specific risk indicators
- **Regulatory Compliance Monitor** — Tracks GDPR, CCPA, SEC, and other regulatory changes, parsing updates into structured alerts
- **Third-Party Risk Assessment** — Continuously assesses supplier and vendor exposure across the web
- **Brand & Data Exposure Detection** — Detects leaked credentials, exposed data, and reputational threats early
- **Autonomous Investigation Agents** — AI agents that investigate threat indicators and return structured risk assessments without human intervention

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Data Collection Layer                      │
│  Bright Data Web Unlocker | SERP API | Scraping Browser      │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                 Analysis & Intelligence Layer                  │
│  Threat Analyzer | Compliance Analyzer | Risk Scorer         │
│  AI/ML API-powered investigation agents                      │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                   Memory & Storage Layer                      │
│  Cognee (persistent agent memory) | PostgreSQL (findings)    │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                  Alerting & Reporting Layer                    │
│  Alert Manager | Slack/Email/PagerDuty | Webhook exports     │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                    API & Integration Layer                     │
│  REST API | Webhook receiver | Dashboard feed                │
└─────────────────────────────────────────────────────────────┘
```

## Bright Data Tools Used

| Tool | Purpose |
|---|---|
| **Web Unlocker** | Bypass bot detection on security forums, paste sites, regulatory pages |
| **SERP API** | Real-time search across Google, Bing for threat indicators |
| **MCP Server** | Connect AI agents directly to live web context |
| **Scraping Browser** | Full browser automation for JS-heavy compliance and risk pages |
| **Web Scraper API** | Structured data from pre-built site scrapers |

## Tech Stack

- **Python 3.11+** — Core application
- **FastAPI** — REST API
- **Bright Data SDK** — Web data collection
- **AI/ML API** — AI reasoning and analysis
- **Cognee** — Agent memory and context
- **PostgreSQL** — Findings and alert storage
- **Docker** — Containerized deployment

## Getting Started

See [SETUP.md](SETUP.md) for full setup instructions.

Quick start:
```bash
cp .env.example .env
# Fill in your API keys
docker-compose up -d
```

## Project Structure

```
sentinelwatch/
├── src/                    # Core application source
│   ├── main.py             # Entry point
│   ├── config.py           # Configuration management
│   ├── data_collection/    # Bright Data integration layer
│   ├── intelligence/       # AI analysis and risk scoring
│   ├── memory/             # Cognee agent memory
│   ├── alerting/           # Alert management and notifications
│   └── api/                # REST API
├── agents/                 # Autonomous AI agent definitions
├── config/                 # YAML configuration files
├── tests/                  # Test suite
├── docs/                   # Documentation
└── docker-compose.yml      # Deployment
```

## Partner Technologies

- **AI/ML API** — Powers the intelligence layer (analysis, reasoning, extraction)
- **Cognee** — Provides persistent agent memory across investigation workflows
- **TriggerWare.ai** — Event-driven workflows triggered by web data changes
- **Speechmatics** — Optional voice-enabled alerting and reporting

## Demo

Watch the product demo or flip through the presentation:

- **📹 Demo Script** — [`docs/demo-script.md`](docs/demo-script.md) — A ~3-minute narrated walkthrough covering entity monitoring, findings, alerts, compliance, and AI reports
- **📊 Presentation** — Open the slide deck at [`/presentation/`](https://frontend-lilac-eta-55.vercel.app/presentation/index.html) (10 slides with screenshots)
- **🌐 Live App** — [frontend-lilac-eta-55.vercel.app](https://frontend-lilac-eta-55.vercel.app)
- **📄 PDF** — Download the presentation as PDF from the slide deck (Ctrl+P → Save as PDF, Landscape, A3)

### Demo Flow

```
Entities → Add Website → Configure Scans → Scan Runs → Dashboard → Findings → Alerts → Compliance → AI Reports
```

## License

Hackathon project — see hackathon terms.
