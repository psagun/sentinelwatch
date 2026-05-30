# SentinelWatch Architecture

## System Overview

SentinelWatch is a modular, event-driven security monitoring platform designed around four core layers. Each layer is independently deployable and communicates via well-defined interfaces.

---

## Layer 1: Data Collection Layer

### Components

| Component | Bright Data Tool | Function |
|---|---|---|
| `ThreatCollector` | Web Unlocker + SERP API | Monitors CVE feeds, security blogs, paste sites, dark web forums |
| `ComplianceCollector` | Scraping Browser + MCP Server | Tracks regulatory websites (GDPR, CCPA, SEC, ISO) |
| `ThirdPartyCollector` | Web Scraper API + SERP API | Assesses vendor security posture, news, breaches |
| `BrandMonitor` | SERP API + Web Unlocker | Detects leaked credentials, brand impersonation, data exposure |

### Data Flow

```
Web Sources
    │
    ▼
┌──────────────────────┐
│  Bright Data Layer    │
│  - Web Unlocker       │
│  - SERP API           │
│  - Scraping Browser   │
│  - Web Scraper API    │
│  - MCP Server         │
└──────────┬───────────┘
           │ Raw HTML / JSON / Search Results
           ▼
┌──────────────────────┐
│  Normalizer           │
│  - HTML → Markdown    │
│  - JSON → Schema      │
│  - Deduplication      │
└──────────┬───────────┘
           │ Structured Documents
           ▼
    Message Queue (Redis)
```

### Collection Strategies

Each collector implements a configurable cadence:
- **Threat intel**: Every 15-30 minutes (high priority)
- **Compliance**: Every 6-24 hours (changes are slower)
- **Third-party risk**: Daily (batch assessment)
- **Brand monitoring**: Every 1-4 hours (continuous sweep)

---

## Layer 2: Analysis & Intelligence Layer

### Components

| Component | AI/ML API Model | Function |
|---|---|---|
| `ThreatAnalyzer` | Claude / GPT-4o | Classifies threats, extracts IOCs, assigns severity |
| `ComplianceAnalyzer` | Claude | Parses regulatory text, extracts changes, maps to obligations |
| `RiskScorer` | Custom ML + LLM | Computes composite risk scores (0-100) per entity |
| `InvestigationAgent` | Claude (agentic) | Autonomous deep-dive into indicators, returns structured report |

### Analysis Pipeline

```
Raw Documents (from Data Collection)
    │
    ▼
┌──────────────────────┐
│  Preprocessor         │
│  - Chunking           │
│  - Entity extraction  │
│  - Language detection │
└──────────┬───────────┘
           │ Processed Chunks
           ▼
┌──────────────────────┐
│  AI Analysis (AI/ML)  │
│  - Zero-shot classify │
│  - Structured output  │
│  - Confidence scores  │
└──────────┬───────────┘
           │ Structured Findings
           ▼
┌──────────────────────┐
│  Risk Scorer          │
│  - Composite scoring  │
│  - Trend analysis     │
│  - Threshold checking │
└──────────┬───────────┘
           │ Scored Findings
           ▼
    Store in PostgreSQL + Cognee
```

### Agent Architecture

Investigation agents follow a ReAct pattern:
1. **Reason** about the finding using context from Cognee memory
2. **Act** by invoking Bright Data tools for additional live data
3. **Observe** new information
4. **Repeat** until sufficient confidence for a structured assessment

---

## Layer 3: Memory & Storage Layer

### PostgreSQL Schema (Core Tables)

```
findings
  - id: UUID (PK)
  - source: enum(threat, compliance, third_party, brand)
  - entity_id: string (domain, org name, regulation ID)
  - finding_type: string
  - raw_data: JSONB
  - structured_data: JSONB
  - risk_score: float
  - severity: enum(critical, high, medium, low, info)
  - status: enum(new, investigating, confirmed, false_positive, resolved)
  - created_at: timestamptz
  - updated_at: timestamptz

alerts
  - id: UUID (PK)
  - finding_id: UUID (FK → findings)
  - alert_type: string
  - channel: string (slack, email, webhook, pagerduty)
  - status: enum(pending, sent, acknowledged, resolved)
  - created_at: timestamptz

entities
  - id: UUID (PK)
  - name: string
  - entity_type: enum(organization, domain, regulation, vendor)
  - metadata: JSONB
  - current_risk_score: float
  - last_assessed: timestamptz
```

### Cognee Memory

Cognee provides persistent agent memory:
- **Conversation memory**: What the investigation agent learned across sessions
- **Knowledge graph**: Entities, relationships, and findings connected semantically
- **Context retrieval**: Previous assessments inform new investigations

---

## Layer 4: Alerting & Reporting Layer

### Alert Routing

```
┌─────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Severity   │    │  Alert Manager   │    │  Channels        │
├─────────────┤    ├──────────────────┤    ├─────────────────┤
│ CRITICAL    │───►│ Deduplication    │───►│ PagerDuty       │
│ HIGH        │───►│ Throttling       │───►│ Slack (#secops) │
│ MEDIUM      │───►│ Enrichment       │───►│ Email           │
│ LOW         │───►│ Escalation       │───►│ Webhook export  │
│ INFO        │    │                  │    │ Dashboard feed  │
└─────────────┘    └──────────────────┘    └─────────────────┘
```

### Alert Lifecycle

```
new → acknowledged → investigating → resolved
  ↘                        ↗
   false_positive
```

---

## Layer 5: API & Integration Layer

### REST API Endpoints

```
GET    /api/v1/findings          — List findings (paginated, filterable)
GET    /api/v1/findings/:id      — Get finding detail
PATCH  /api/v1/findings/:id      — Update status / add notes

GET    /api/v1/alerts            — List alerts
POST   /api/v1/alerts/ack/:id    — Acknowledge alert

GET    /api/v1/entities          — List monitored entities
POST   /api/v1/entities          — Add entity to monitor

GET    /api/v1/dashboard/summary — Dashboard aggregate data

POST   /api/v1/investigate       — Trigger ad-hoc investigation
GET    /api/v1/investigate/:id   — Get investigation results

GET    /api/v1/health            — Health check
```

### Webhook Receiver

```
POST /api/v1/webhooks/brightdata — Receive Bright Data callback data
POST /api/v1/webhooks/custom     — Custom third-party webhook integration
```

---

## Deployment Architecture

```
                  ┌──────────────┐
                  │  Nginx / LB  │
                  └──────┬───────┘
                         │
                  ┌──────▼───────┐
                  │  FastAPI App  │
                  │  (3+ replicas)│
                  └──────┬───────┘
                         │
          ┌──────────────┼──────────────┐
          │              │              │
   ┌──────▼─────┐ ┌─────▼──────┐ ┌─────▼──────┐
   │ PostgreSQL  │ │   Redis    │ │   Cognee   │
   │ (findings)  │ │ (queue)    │ │ (memory)   │
   └────────────┘ └────────────┘ └────────────┘
```

### Tech Requirements

- **Python 3.11+**
- **PostgreSQL 15+**
- **Redis 7+**
- **Docker + Docker Compose**
- **Bright Data account** (with $250 hackathon credits)
- **AI/ML API key**
- **Cognee API key** (optional)
