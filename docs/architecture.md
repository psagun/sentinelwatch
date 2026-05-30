# SentinelWatch Architecture Document

## System Architecture

SentinelWatch is a **modular, event-driven security monitoring platform** with five distinct layers:

```
┌──────────────────────────────────────────────────────────────────┐
│                      DATA COLLECTION LAYER                        │
│                                                                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │   Threat     │  │  Compliance  │  │ Third-Party  │             │
│  │  Collector   │  │  Collector   │  │  Collector   │             │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘             │
│  ┌──────┴───────┐         │                 │                     │
│  │  Brand       │         │                 │                     │
│  │  Monitor     │         │                 │                     │
│  └──────────────┘         │                 │                     │
│         │                 │                 │                     │
│         └─────────────────┴─────────────────┘                     │
│                            │                                       │
│                    Bright Data Platform                            │
│  (Web Unlocker | SERP API | Scraping Browser | MCP Server)        │
└────────────────────────────┬──────────────────────────────────────┘
                             │
┌────────────────────────────▼──────────────────────────────────────┐
│                     ANALYSIS & INTELLIGENCE LAYER                   │
│                                                                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │   Threat     │  │  Compliance  │  │   Risk       │             │
│  │  Analyzer    │  │  Analyzer    │  │   Scorer     │             │
│  └──────────────┘  └──────────────┘  └──────────────┘             │
│  ┌─────────────────────────────────────┐                          │
│  │     Investigation Agent (ReAct)     │                          │
│  │  Reason → Act (Web) → Observe → ... │                          │
│  └─────────────────────────────────────┘                          │
│                            │                                       │
│                        AI/ML API                                   │
└────────────────────────────┬──────────────────────────────────────┘
                             │
┌────────────────────────────▼──────────────────────────────────────┐
│                      MEMORY & STORAGE LAYER                         │
│                                                                    │
│  ┌──────────────────┐  ┌──────────────────┐                       │
│  │    PostgreSQL     │  │    Cognee         │                       │
│  │  (Findings DB)    │  │  (Agent Memory)   │                       │
│  │  - findings       │  │  - Knowledge Graph│                       │
│  │  - alerts         │  │  - Semantic Search│                       │
│  │  - entities       │  │  - History        │                       │
│  └──────────────────┘  └──────────────────┘                       │
└────────────────────────────┬──────────────────────────────────────┘
                             │
┌────────────────────────────▼──────────────────────────────────────┐
│                       ALERTING & REPORTING LAYER                    │
│                                                                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │   Slack      │  │  PagerDuty   │  │    Email     │             │
│  ├──────────────┤  ├──────────────┤  ├──────────────┤             │
│  │  Dashboard   │  │  Webhooks    │  │   API Feed   │             │
│  └──────────────┘  └──────────────┘  └──────────────┘             │
└────────────────────────────┬──────────────────────────────────────┘
                             │
┌────────────────────────────▼──────────────────────────────────────┐
│                      API & INTEGRATION LAYER                        │
│                                                                    │
│  REST API (FastAPI) | Webhooks | SDK Clients                       │
│  POST /api/v1/entities  |  GET /api/v1/findings                   │
│  POST /api/v1/investigate  |  GET /api/v1/dashboard/summary       │
└──────────────────────────────────────────────────────────────────┘
```

## Key Design Decisions

### 1. Bright Data as the Foundation
Bright Data provides the web data infrastructure that makes SentinelWatch possible:
- **Web Unlocker** handles CAPTCHAs, fingerprint rotation, and geo-blocking automatically
- **SERP API** delivers structured search results without parsing HTML
- **Scraping Browser** handles JavaScript-heavy pages (compliance portals, regulatory sites)
- **MCP Server** gives AI agents direct live web access through natural language

### 2. AI/ML API for Intelligence
All analysis layers use AI/ML API for:
- Zero-shot classification of threats and compliance changes
- Structured data extraction from unstructured web text
- Autonomous investigation reasoning (ReAct pattern)
- Framework mapping and gap analysis

### 3. Cognee for Persistent Memory
Cognee provides:
- Knowledge graph connecting entities, findings, and relationships
- Semantic search over past investigations
- Context across monitoring cycles for improved analysis

### 4. Event-Driven Architecture
All collectors produce events consumed by the analysis layer:
- Redis message queue buffers findings during load spikes
- Asyncio event loop enables concurrent collection and analysis
- Alert deduplication window prevents alert storms

## Data Flow

### Threat Intelligence Flow
```
1. ThreatCollector.serp_search("acme corp breach 2026")
2. ThreatAnalyzer.classify_finding(raw_text) → AI/ML API
3. RiskScorer.score(findings) → {"score": 85.5, "level": "critical"}
4. CogneeMemory.store_finding(entity_id, finding)
5. AlertManager.create_alerts(...) → Slack / PagerDuty
```

### Compliance Monitoring Flow
```
1. ComplianceCollector.web_unlocker_get(regulatory_url)
2. ComplianceAnalyzer.analyze_change(regulation, text) → AI/ML API
3. ComplianceAnalyzer.map_to_framework(change, "NIST CSF")
4. AlertManager.create_alerts(...) if impact_level = "high"
```

### Investigation Flow (ReAct)
```
1. POST /api/v1/investigate {indicator: "185.220.101.x"}
2. Check Cognee for similar past investigations
3. Bright Data MCP query: "Search for 185.220.101.x threat reports"
4. AI analysis: classify, extract context, entity correlation
5. Generate verdict: {"verdict": "malicious", "confidence": 0.92}
6. Store in Cognee knowledge graph
7. Return structured assessment
```

## Deployment

### Production Requirements
- Python 3.11+
- PostgreSQL 15+ (with JSONB for flexible schema)
- Redis 7+ (message queue + caching)
- 4+ GB RAM (for AI model inference via API)
- Bright Data account with active credits
- AI/ML API subscription

### Scaling Considerations
- Collectors scale horizontally (more workers = faster collection)
- PostgreSQL can be upgraded to read replicas for dashboard queries
- AI analysis is API-based, so scales with API rate limits
- Consider partitioning the `findings` table by date in production
