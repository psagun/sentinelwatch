"""Pydantic schemas for the SentinelWatch API."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class FindingBase(BaseModel):
    finding_type: str
    source_type: str
    source_url: str
    title: str
    description: str
    severity: str = "medium"
    entity_id: Optional[str] = None


class FindingCreate(FindingBase):
    raw_data: Optional[str] = None
    indicators: List[str] = []


class Finding(FindingBase):
    id: str
    status: str = "new"
    risk_score: float = 0.0
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AlertBase(BaseModel):
    finding_id: str
    alert_type: str
    title: str
    description: str
    severity: str


class Alert(AlertBase):
    id: str
    channels: List[str]
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class EntityBase(BaseModel):
    name: str
    entity_type: str
    metadata: Dict[str, Any] = {}


class Entity(EntityBase):
    id: str
    current_risk_score: float = 0.0
    last_assessed: Optional[datetime] = None
    scan_status: str = "pending"
    finding_count: int = 0

    class Config:
        from_attributes = True


class RiskScore(BaseModel):
    score: float
    level: str
    finding_counts: Dict[str, int] = {}
    total_findings: int = 0
    trend: str = "stable"


class InvestigationResult(BaseModel):
    indicator: str
    indicator_type: str
    verdict: str
    confidence: float
    evidence: List[Dict[str, Any]]
    affected_entities: List[str]
    recommended_actions: List[str]


class DashboardSummary(BaseModel):
    total_findings: int
    total_alerts: int
    pending_alerts: int
    monitored_entities: int
    findings_by_type: Dict[str, int]
    findings_by_severity: Dict[str, int]
    overall_risk: RiskScore
    recent_findings: List[Finding]


class PaginatedResponse(BaseModel):
    total: int
    limit: int
    offset: int
    results: List[Any]


class MonitorRequest(BaseModel):
    url: str
    name: Optional[str] = None


# ── Web Scraper Scan ─────────────────────────────────────────── #

class ScanRequest(BaseModel):
    """Request to scan a URL with the WebScraper."""
    url: str = Field(..., description="Target URL to scan (e.g. https://example.com)")
    name: Optional[str] = Field(None, description="Optional label for this scan")
    deep: bool = Field(False, description="Run all checks including SSL and headers (default: all)")


class ScanFinding(BaseModel):
    """A single finding from a WebScraper scan."""
    title: str
    description: str
    severity: str = "info"
    finding_type: str = "vulnerability"
    check_type: str = "general"
    source_url: str = ""
    raw_data: Optional[str] = None
    remediation: Optional[str] = None


class ScanResult(BaseModel):
    """Result of a completed WebScraper scan."""
    id: str
    url: str
    name: str
    status: str = "completed"  # pending | scanning | completed | failed
    summary: Optional[str] = None
    risk_score: Optional[float] = None
    risk_level: str = "none"
    findings: List[ScanFinding] = []
    findings_count: int = 0
    recommendations: List[str] = []
    error: Optional[str] = None
    created_at: str = ""
    completed_at: Optional[str] = None


class ScanSummary(BaseModel):
    """Lightweight scan summary for list views."""
    id: str
    url: str
    name: str
    status: str
    risk_level: str
    findings_count: int
    created_at: str
