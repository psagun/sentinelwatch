# SentinelWatch Setup Guide

## Prerequisites

- Python 3.11+
- Docker & Docker Compose
- Bright Data account (promo code: `unlocked` for $250 credits)
- AI/ML API key
- Cognee API key (optional, for agent memory)
- PostgreSQL 15+ (or use the Docker Compose setup)

---

## Quick Start

### 1. Clone and Environment Setup

```bash
cd sentinelwatch
cp .env.example .env
```

### 2. Configure API Keys

Edit `.env` with your credentials:

```env
# Bright Data
BRIGHTDATA_API_KEY=your_brightdata_api_key
BRIGHTDATA_USERNAME=your_brightdata_username

# AI/ML API
AIML_API_KEY=your_aiml_api_key

# Cognee (optional)
COGNEE_API_KEY=your_cognee_api_key

# PostgreSQL
DATABASE_URL=postgresql://sentinel:sentinel@localhost:5432/sentinelwatch

# Redis
REDIS_URL=redis://localhost:6379/0

# Alerting
SLACK_WEBHOOK_URL=your_slack_webhook_url  # optional
PAGERDUTY_API_KEY=your_pagerduty_key       # optional

# App
SECRET_KEY=generate-a-random-secret-key
LOG_LEVEL=INFO
```

### 3. Redeem Bright Data Credits

1. Sign up or log in at [brightdata.com](https://brightdata.com)
2. Go to **Billing → Overview**
3. Click **Apply a promo code**
4. Enter `unlocked` and click **Apply**
5. Your $250 credit will appear in your balance

### 4. Start Dependencies

```bash
docker-compose up -d postgres redis
```

### 5. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 6. Database Setup

```bash
alembic upgrade head
# or if using raw SQL:
python -m src.scripts.init_db
```

### 7. Run the Application

```bash
# Start the API server
uvicorn src.main:app --reload --port 8000

# In a separate terminal, start collectors
python -m src.data_collection.run_collectors

# In another terminal, start investigation agents
python -m agents.run_agents
```

### 8. Verify

```bash
curl http://localhost:8000/api/v1/health
# Expected: {"status": "ok", "version": "1.0.0"}
```

---

## Docker Compose (Full Stack)

```bash
docker-compose up -d
```

This starts: FastAPI app, PostgreSQL, Redis, collector workers, and agent workers.

---

## Adding Entities to Monitor

```bash
# Add an organization to monitor for threats
curl -X POST http://localhost:8000/api/v1/entities \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Acme Corp",
    "entity_type": "organization",
    "metadata": {
      "domains": ["acme.com", "acme.io"],
      "keywords": ["acme", "acme security", "acme breach"]
    }
  }'

# Add a regulation to track
curl -X POST http://localhost:8000/api/v1/entities \
  -H "Content-Type: application/json" \
  -d '{
    "name": "GDPR",
    "entity_type": "regulation",
    "metadata": {
      "jurisdictions": ["EU", "EEA"],
      "sources": ["https://gdpr.eu", "https://ec.europa.eu"]
    }
  }'
```

---

## Bright Data Tool Configuration

### Web Unlocker
```python
from src.data_collection.brightdata_client import BrightDataClient

client = BrightDataClient()
# Web Unlocker automatically handles CAPTCHAs and geo-blocks
html = client.web_unlocker_get("https://pastebin.com/trends")
```

### SERP API
```python
results = client.serp_search(
    query="acme corp data breach 2026",
    source="google_news",
    country="US"
)
```

### MCP Server
```python
# Connect AI agents directly to live web
from src.data_collection.mcp_client import MCPClient

mcp = MCPClient()
web_context = mcp.get_live_context("Acme Corp security incident")
```

---

## Testing

```bash
# Run all tests
pytest

# Run specific test module
pytest tests/test_threat_collector.py

# Run with coverage
pytest --cov=src tests/
```

---

## Monitoring

- API health: `GET /api/v1/health`
- Metrics: `GET /api/v1/metrics` (Prometheus format)
- Dashboard: Access the web UI at `http://localhost:8000/dashboard`

---

## Troubleshooting

| Issue | Solution |
|---|---|
| Bright Data API returns 429 | Check your credit balance; request more via Discord |
| Web Unlocker returns blocked page | Verify the target site is not in Bright Data's restricted list |
| Agents not triggering | Check Redis connection; verify worker processes are running |
| No alerts received | Check alert channel configuration in `.env` |
