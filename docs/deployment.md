# SentinelWatch Deployment Guide

## Local Development

### Prerequisites
- Python 3.11+
- Docker & Docker Compose
- Bright Data account ($250 credits with code `unlocked`)
- AI/ML API key

### Steps
```bash
# 1. Clone and configure
cd sentinelwatch
cp .env.example .env
# Edit .env with your API keys

# 2. Start dependencies
docker-compose up -d postgres redis

# 3. Install and run
pip install -r requirements.txt
uvicorn src.main:app --reload --port 8000
```

---

## Docker Deployment (Production)

```bash
# Build and run full stack
docker-compose up -d --build
```

Services:
- `api` — FastAPI (port 8000)
- `collector` — Data collection worker
- `agent-worker` — AI agent worker
- `postgres` — Database (port 5432)
- `redis` — Message queue (port 6379)

### Scaling Workers
```bash
docker-compose up -d --scale collector=3 --scale agent-worker=2
```

---

## Kubernetes Deployment

### Requirements
- Kubernetes 1.24+
- cert-manager (for TLS)
- Ingress controller

### Quick Start
```bash
kubectl create namespace sentinelwatch
kubectl create secret generic sentinelwatch-secrets \
  --from-literal=BRIGHTDATA_API_KEY=... \
  --from-literal=AIML_API_KEY=...

kubectl apply -f k8s/
```

---

## Monitoring & Observability

### Prometheus Metrics
Available at `GET /api/v1/metrics`:
- `sentinel_findings_total` — Total findings by type
- `sentinel_alerts_total` — Total alerts by severity
- `sentinel_collection_duration_seconds` — Collection latency
- `sentinel_investigations_total` — Investigation count

### Logging
Structured JSON logs via stdout. Log levels:
- `INFO`: Normal operations
- `WARNING`: Collection failures, rate limits
- `ERROR`: System malfunctions

### Alert Channel Configuration

| Channel | Config Key | When Used |
|---|---|---|
| Slack | `SLACK_WEBHOOK_URL` | Critical, High, Medium |
| PagerDuty | `PAGERDUTY_API_KEY` | Critical only |
| Email | `SMTP_*` vars | Critical, High |

---

## Bright Data Credit Management

- Initial: $250 per participant (promo `unlocked`)
- Request more: On-site or via Discord
- Monitor usage: `GET /api/v1/metrics` or Bright Data dashboard
- Estimated daily consumption: ~$2-5 at default cadences

### Cost Optimization
- Reduce `threat_intel_interval_minutes` from 15 to 30
- Limit monitored entities to essential ones
- Cache SERP API results (Redis TTL = interval/2)
