# SentinelWatch API Reference

Base URL: `http://localhost:8000/api/v1`

## Authentication

All API requests require the `X-API-Key` header:
```
X-API-Key: your-api-key-here
```

---

## Health Check

### `GET /health`

Returns API status.

**Response:**
```json
{
  "status": "ok",
  "version": "1.0.0"
}
```

---

## Entities

### `GET /entities`

List all monitored entities.

**Response:**
```json
{
  "total": 2,
  "results": [
    {
      "id": "uuid",
      "name": "Acme Corp",
      "entity_type": "organization",
      "metadata": {
        "domains": ["acme.com"],
        "keywords": ["acme"]
      },
      "current_risk_score": 42.5,
      "last_assessed": "2026-05-28T12:00:00Z"
    }
  ]
}
```

### `POST /entities`

Add a new entity to monitor.

**Request:**
```json
{
  "name": "Acme Corp",
  "entity_type": "organization",
  "metadata": {
    "domains": ["acme.com", "acme.io"],
    "keywords": ["acme", "acme security"]
  }
}
```

---

## Findings

### `GET /findings`

List findings with optional filters.

**Query Parameters:**
- `finding_type`: "threat" | "compliance" | "third_party_risk" | "brand_exposure" | "investigation"
- `severity`: "critical" | "high" | "medium" | "low" | "info"
- `status`: "new" | "investigating" | "confirmed" | "false_positive" | "resolved"
- `entity_id`: Filter by entity
- `limit`: Max results (default 50, max 200)
- `offset`: Pagination offset

### `GET /findings/:id`

Get a single finding by ID.

### `PATCH /findings/:id`

Update finding status.

**Request:**
```json
{
  "status": "investigating",
  "notes": "Confirmed via internal logs"
}
```

---

## Alerts

### `GET /alerts`

List alerts with optional filters.

### `POST /alerts/:id/acknowledge`

Acknowledge a pending alert.

---

## Dashboard

### `GET /dashboard/summary`

Get aggregate dashboard data.

**Response:**
```json
{
  "total_findings": 150,
  "total_alerts": 23,
  "pending_alerts": 5,
  "monitored_entities": 12,
  "findings_by_type": {
    "threat": 85,
    "compliance": 30,
    "third_party_risk": 25,
    "brand_exposure": 10
  },
  "findings_by_severity": {
    "critical": 8,
    "high": 22,
    "medium": 45,
    "low": 55,
    "info": 20
  },
  "overall_risk": {
    "overall_score": 52.3,
    "overall_level": "medium",
    "entity_count": 12
  },
  "recent_findings": []
}
```

---

## Investigations

### `POST /investigate`

Trigger an ad-hoc investigation.

**Request:**
```json
{
  "indicator": "185.220.101.45",
  "indicator_type": "ip",
  "context": "Observed in login attempts from unknown source"
}
```

**Response:**
```json
{
  "indicator": "185.220.101.45",
  "indicator_type": "ip",
  "verdict": "suspicious",
  "confidence": 0.78,
  "evidence": [
    {"source": "web_search", "url": "...", "title": "...", "snippet": "..."}
  ],
  "affected_entities": ["Acme Corp"],
  "recommended_actions": [
    "Block IP at firewall",
    "Review auth logs for related attempts"
  ],
  "investigation_steps": 3
}
```

### `GET /investigate/:id`

Get a previous investigation result.

---

## Error Responses

```json
{
  "detail": "Finding not found"
}
```

HTTP status codes:
- `200`: Success
- `404`: Resource not found
- `422`: Validation error
- `429`: Rate limited
- `500`: Internal server error
