"""REST API route definitions."""

import asyncio
import datetime
import json
import logging
import uuid

import httpx
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from src.config import settings
from src.intelligence.risk_scorer import RiskScorer
from src.data_collection.web_scraper import WebScraper, WebScraperFinding
from src.intelligence.analysis_agent import AnalysisAgent
from src.api.schemas import ScanRequest
from src import database as db
from src.compliance.classifier import classify_findings, get_compliance_summary
from src.memory.cognee_client import cognee

logger = logging.getLogger(__name__)
router = APIRouter()
risk_scorer = RiskScorer()

# In-memory stores backed by SQLite for persistence.
# See src/database.py for the write-through implementation.
_findings_db = db._findings_db
_alerts_db = db._alerts_db
_entities_db = db._entities_db
_investigations_db = db._investigations_db
_scans_db = db._scans_db


# ── Pydantic models ────────────────────────────────────────────── #

class EntityCreate(BaseModel):
    name: str
    entity_type: str
    metadata: Optional[Dict[str, Any]] = {}


class FindingUpdate(BaseModel):
    status: str
    notes: Optional[str] = None


class InvestigationRequest(BaseModel):
    indicator: str
    indicator_type: str = "ip"
    context: Optional[str] = None


class AcknowledgeRequest(BaseModel):
    notes: Optional[str] = None


class ScanConfig(BaseModel):
    scans: List[str] = ["web_unlocker", "serp", "scraping_browser"]
    compliance: List[str] = ["GDPR", "SOC2", "HIPAA", "PCI_DSS"]
    checks: List[str] = ["headers", "ssl", "server_info", "well_known", "browser"]


class MonitorRequest(BaseModel):
    url: str
    name: Optional[str] = None
    scan_config: Optional[ScanConfig] = None


# ── Health ─────────────────────────────────────────────────────── #

@router.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}


# ── Web Scraper Scan ────────────────────────────────────────── #

async def _run_scan(scan_id: str, target_url: str, scan_name: str):
    """Background task: run WebScraper checks, analyze findings."""
    scan = next((s for s in _scans_db if s["id"] == scan_id), None)
    if not scan:
        return
    scan["status"] = "scanning"

    try:
        scraper = WebScraper(target_url=target_url)
        raw_findings = await scraper.collect()

        # Normalize findings
        findings = []
        for f in raw_findings:
            d = f.to_dict() if hasattr(f, "to_dict") else {}
            findings.append({
                "title": d.get("title", ""),
                "description": d.get("description", ""),
                "severity": d.get("severity", "info"),
                "finding_type": d.get("finding_type", "vulnerability"),
                "check_type": d.get("check_type", "general"),
                "source_url": d.get("source_url", target_url),
                "raw_data": d.get("raw_data"),
            })

        if findings:
            # Try AI analysis for enrichment
            agent = AnalysisAgent()
            analysis = await agent.analyze_findings(findings, scan_name)
            if analysis and analysis.findings:
                for i, f in enumerate(analysis.findings):
                    if i < len(findings):
                        findings[i]["remediation"] = f.get("remediation", "")
                        findings[i]["severity"] = f.get("severity", findings[i]["severity"])
                        findings[i]["risk_score"] = f.get("risk_score", 0.0)

        # Calculate aggregate risk
        sev_map = {"critical": 9, "high": 7, "medium": 5, "low": 2, "info": 0}
        scores = [sev_map.get(f["severity"], 0) for f in findings]
        avg_score = sum(scores) / len(scores) if scores else 0

        if avg_score >= 7:
            risk_level = "high"
        elif avg_score >= 4:
            risk_level = "medium"
        elif avg_score > 0:
            risk_level = "low"
        else:
            risk_level = "none"

        recommendations = []
        sev_counts = {}
        for f in findings:
            sev_counts[f["severity"]] = sev_counts.get(f["severity"], 0) + 1
        if sev_counts.get("critical", 0) > 0:
            recommendations.append(f"Address {sev_counts['critical']} critical finding(s) immediately.")
        if sev_counts.get("high", 0) > 0:
            recommendations.append(f"Schedule remediation for {sev_counts['high']} high-severity finding(s).")
        if sev_counts.get("medium", 0) > 0:
            recommendations.append(f"Review {sev_counts['medium']} medium-severity finding(s).")

        severity_order = ["critical", "high", "medium", "low", "info"]
        worst = next((s for s in severity_order if sev_counts.get(s, 0) > 0), "none")
        summary = (
            f"Scanned {target_url}: {len(findings)} findings — "
            f"worst severity: {worst.upper()}. "
            f"Risk level: {risk_level.upper()}. "
            f"{sev_counts.get('critical', 0)} critical, {sev_counts.get('high', 0)} high, "
            f"{sev_counts.get('medium', 0)} medium."
        )

        scan["findings"] = findings
        scan["findings_count"] = len(findings)
        scan["risk_level"] = risk_level
        scan["risk_score"] = round(avg_score, 1)
        scan["summary"] = summary
        scan["recommendations"] = recommendations
        scan["status"] = "completed"
        scan["completed_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        await db.save_scan(scan)

    except Exception as e:
        logger.error(f"Scan {scan_id} failed: {e}", exc_info=True)
        scan["status"] = "failed"
        scan["error"] = str(e)
        scan["completed_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        await db.save_scan(scan)


@router.post("/scan")
async def create_scan(request: ScanRequest):
    """Submit a URL for security scanning via WebScraper + Bright Data."""
    scan_id = str(uuid.uuid4())
    scan_name = request.name or request.url
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()

    scan = {
        "id": scan_id,
        "url": request.url,
        "name": scan_name,
        "status": "pending",
        "risk_level": "none",
        "risk_score": 0.0,
        "findings": [],
        "findings_count": 0,
        "summary": None,
        "recommendations": [],
        "error": None,
        "created_at": now,
        "completed_at": None,
    }
    _scans_db.append(scan)
    await db.save_scan(scan)

    # Launch background scan
    asyncio.create_task(_run_scan(scan_id, request.url, scan_name))

    return {"scan_id": scan_id, "status": "pending", "url": request.url}


@router.get("/scan/{scan_id}")
async def get_scan(scan_id: str):
    """Get the results of a WebScraper scan."""
    for s in _scans_db:
        if s["id"] == scan_id:
            return s
    raise HTTPException(status_code=404, detail="Scan not found")


@router.get("/scans")
async def list_scans(
    status: Optional[str] = Query(None),
    risk_level: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
):
    """List all WebScraper scans with optional filtering."""
    results = _scans_db[:]
    if status:
        results = [s for s in results if s.get("status") == status]
    if risk_level:
        results = [s for s in results if s.get("risk_level") == risk_level]
    # Sort by created_at descending (newest first)
    results.sort(key=lambda s: s.get("created_at", ""), reverse=True)
    return {
        "total": len(results),
        "limit": limit,
        "results": [{
            "id": s["id"],
            "url": s["url"],
            "name": s["name"],
            "status": s["status"],
            "risk_level": s["risk_level"],
            "findings_count": s["findings_count"],
            "created_at": s["created_at"],
        } for s in results[:limit]],
    }


# ── Findings ───────────────────────────────────────────────────── #

@router.get("/findings")
async def list_findings(
    finding_type: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    entity_id: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
):
    results = _findings_db

    if finding_type:
        results = [f for f in results
                   if f.get("finding_type") == finding_type]
    if severity:
        results = [f for f in results
                   if f.get("severity") == severity]
    if status:
        results = [f for f in results
                   if f.get("status") == status]
    if entity_id:
        results = [f for f in results
                   if f.get("entity_id") == entity_id]

    return {
        "total": len(results),
        "limit": limit,
        "offset": offset,
        "results": results[offset:offset + limit],
    }


@router.get("/findings/{finding_id}")
async def get_finding(finding_id: str):
    for f in _findings_db:
        if f.get("id") == finding_id:
            return f
    raise HTTPException(status_code=404, detail="Finding not found")


@router.patch("/findings/{finding_id}")
async def update_finding(finding_id: str, update: FindingUpdate):
    for f in _findings_db:
        if f.get("id") == finding_id:
            f["status"] = update.status
            await db.save_finding(f)
            if update.notes:
                f["notes"] = update.notes
            f["updated_at"] = datetime.datetime.now().isoformat()
            return f
    raise HTTPException(status_code=404, detail="Finding not found")


@router.delete("/findings/{finding_id}")
async def delete_finding_endpoint(finding_id: str):
    """Delete a finding."""
    for i, f in enumerate(_findings_db):
        if f.get("id") == finding_id:
            _findings_db.pop(i)
            await db.delete_finding(finding_id)
            return {"status": "deleted", "finding_id": finding_id}
    raise HTTPException(status_code=404, detail="Finding not found")


# ── Alerts ─────────────────────────────────────────────────────── #

@router.get("/alerts")
async def list_alerts(
    status: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
):
    results = _alerts_db
    if status:
        results = [a for a in results if a.get("status") == status]
    if severity:
        results = [a for a in results if a.get("severity") == severity]
    # Attach finding details and compliance info to each alert
    enriched = []
    for alert in results:
        a = dict(alert)
        finding_id = a.get("finding_id", "")
        finding = next(
            (f for f in _findings_db if f.get("id") == finding_id), None
        )
        if finding:
            a["finding"] = {
                "id": finding.get("id"),
                "title": finding.get("title"),
                "description": finding.get("description"),
                "severity": finding.get("severity"),
                "source_type": finding.get("source_type"),
                "source_url": finding.get("source_url"),
                "entity_id": finding.get("entity_id"),
                "check_type": finding.get("check_type"),
                "risk_score": finding.get("risk_score"),
            }
            a["compliance"] = finding.get("compliance", [])
        enriched.append(a)
    return {"total": len(enriched), "results": enriched[:limit]}


@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str, body: AcknowledgeRequest):
    for a in _alerts_db:
        if a.get("id") == alert_id:
            a["status"] = "acknowledged"
            if body.notes:
                a["notes"] = body.notes
            a["acknowledged_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
            await db.save_alert(a)
            return a
    raise HTTPException(status_code=404, detail="Alert not found")


@router.delete("/alerts/{alert_id}")
async def delete_alert(alert_id: str):
    """Delete an alert."""
    for i, a in enumerate(_alerts_db):
        if a.get("id") == alert_id:
            _alerts_db.pop(i)
            return {"status": "deleted", "alert_id": alert_id}
    raise HTTPException(status_code=404, detail="Alert not found")


# ── Entities ───────────────────────────────────────────────────── #

@router.get("/entities")
async def list_entities():
    return {"total": len(_entities_db), "results": _entities_db}


@router.post("/entities")
async def create_entity(entity: EntityCreate):
    ent = {
        "id": str(uuid.uuid4()),
        "name": entity.name,
        "entity_type": entity.entity_type,
        "metadata": entity.metadata or {},
        "current_risk_score": 0.0,
        "last_assessed": None,
        "scan_status": "pending",
        "finding_count": 0,
    }
    _entities_db.append(ent)
    await db.save_entity(ent)
    return ent


# ── Entity Monitoring (Self-Service Scan) ─────────────────────── #

def _infer_entity_config(url: str) -> Dict[str, Any]:
    """Extract entity name, domains, and keywords from a URL."""
    try:
        parsed = urlparse(url)
        hostname = parsed.hostname or ""
    except Exception:
        hostname = url.strip("/").split("/")[0]

    hostname = hostname.removeprefix("www.").lower()

    # Extract the brand stem
    parts = hostname.split(".")
    if len(parts) >= 2:
        stem = parts[-2]
    else:
        stem = parts[0]

    # Capitalize into a readable name
    name = stem.split("-")
    name = " ".join(w.capitalize() for w in name)
    name = name.split(".")
    name = " ".join(w.capitalize() for w in name)
    # Fix common brands
    brand_overrides = {
        "github": "GitHub",
        "gitlab": "GitLab",
        "google": "Google",
        "facebook": "Facebook",
        "twitter": "Twitter (X)",
        "linkedin": "LinkedIn",
        "amazon": "Amazon",
        "microsoft": "Microsoft",
        "apple": "Apple",
        "brightdata": "Bright Data",
        "aimlapi": "AI/ML API",
    }
    name_lower = name.lower().replace(" ", "")
    if name_lower in brand_overrides:
        name = brand_overrides[name_lower]

    keywords = [name, stem, hostname]
    keywords = list(set(kw for kw in keywords if kw))

    return {
        "name": name,
        "entity_type": "website",
        "metadata": {
            "domains": [hostname],
            "keywords": keywords,
        },
    }


def _normalize_finding(obj: Any, entity_name: str) -> Dict[str, Any]:
    """Convert any collector finding object into a canonical finding dict."""
    now = datetime.datetime.now(datetime.timezone.utc)

    if hasattr(obj, "to_dict"):
        d = obj.to_dict()
    else:
        d = obj if isinstance(obj, dict) else {}

    return {
        "id": str(uuid.uuid4()),
        "finding_type": d.get("finding_type", getattr(obj, "finding_type", "threat_intel")),
        "source_type": d.get("source_type", getattr(obj, "source_type", "scanner")),
        "source_url": d.get("source_url", getattr(obj, "source_url", "")),
        "title": d.get("title", getattr(obj, "title", "Unknown finding")),
        "description": d.get("description", d.get("summary", getattr(obj, "summary", getattr(obj, "description", "")))),
        "severity": d.get("severity", getattr(obj, "severity", "medium")),
        "entity_id": entity_name,
        "status": "new",
        "risk_score": 0.0,
        "created_at": now.isoformat(),
        "updated_at": None,
        "is_source_monitoring": d.get("is_source_monitoring", False),
    }


async def _run_entity_scan(entity: Dict[str, Any]):
    """Background task: run collectors, analyze findings, update entity."""
    entity_id = entity["id"]
    name = entity["name"]
    domains = entity.get("metadata", {}).get("domains", [])
    keywords = entity.get("metadata", {}).get("keywords", [])

    entity["scan_status"] = "scanning"

    try:
        from src.data_collection.threat_collector import ThreatCollector
        from src.data_collection.brand_monitor import BrandMonitor
        from src.data_collection.compliance_collector import ComplianceCollector
        from src.data_collection.web_scraper import WebScraper
        from src.intelligence.analysis_agent import AnalysisAgent

        # Read scan config from entity (with defaults)
        scan_cfg = entity.get("scan_config", {})
        enabled_scans = scan_cfg.get("scans", ["web_unlocker", "serp", "scraping_browser"])
        enabled_compliance = scan_cfg.get("compliance", ["GDPR", "SOC2", "HIPAA", "PCI_DSS"])
        enabled_checks = scan_cfg.get("checks", ["headers", "ssl", "server_info", "well_known", "browser"])

        # Run collectors in parallel (respecting scan config)
        gather_coros = []

        if "serp" in enabled_scans:
            threat_collector = ThreatCollector(
                monitored_entities=[entity]
            )
            brand_monitor = BrandMonitor(
                domains=domains,
                brand_keywords=keywords,
            )
            gather_coros.append(threat_collector.collect())
            gather_coros.append(brand_monitor.collect())

        if "web_unlocker" in enabled_scans:
            compliance_collector = ComplianceCollector()
            gather_coros.append(compliance_collector.collect())
            original_url = entity.get("metadata", {}).get("url", "")
            if original_url:
                web_scraper = WebScraper(target_url=original_url)
                gather_coros.append(web_scraper.collect())

        results = await asyncio.gather(*gather_coros, return_exceptions=True)

        raw_findings = []
        for result in results:
            if isinstance(result, Exception):
                logger.warning(f"Collector failed: {result}")
                continue
            raw_findings.extend(result)

        # Normalize findings
        normalized = [
            _normalize_finding(f, name) for f in raw_findings
        ]

        # Analyze and enrich with severity/risk/recommendations
        agent = AnalysisAgent()
        analysis = await agent.analyze_findings(normalized, name)

        # Store enriched findings
        for f in analysis.findings:
            f["id"] = f.get("id") or str(uuid.uuid4())
            f["entity_id"] = name
        # Add compliance classification tags
        analysis.findings = classify_findings(analysis.findings)

        # Tag any remaining source-monitoring findings not already flagged
        # (catch-all for any compliance collector findings that missed the flag)
        SOURCE_MONITOR_DOMAINS = {"gdpr.eu", "iso.org"}
        for f in analysis.findings:
            if not f.get("is_source_monitoring"):
                src_url = f.get("source_url", "")
                title = f.get("title", "")
                if any(d in src_url for d in SOURCE_MONITOR_DOMAINS):
                    f["is_source_monitoring"] = True
                elif "Potential" in title and "change detected" in title:
                    f["is_source_monitoring"] = True

        _findings_db.extend(analysis.findings)

        # Update entity — only count non-source-monitoring findings as entity findings
        real_findings = [f for f in analysis.findings if not f.get("is_source_monitoring")]
        risk = analysis.risk_score
        entity["current_risk_score"] = risk.get("score", 0.0)
        entity["last_assessed"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        entity["finding_count"] = len(real_findings)
        entity["scan_status"] = "completed"

        # Create alerts for critical/high findings (skip monitoring-infrastructure and source-monitoring)
        INFRA_CHECK_TYPES = {"accessibility", "browser"}
        for f in analysis.findings:
            if f.get("is_source_monitoring"):
                continue
            sev = f.get("severity", "info")
            if f.get("check_type") in INFRA_CHECK_TYPES:
                continue
            if sev in ("critical", "high"):
                _alerts_db.append({
                    "id": str(uuid.uuid4()),
                    "finding_id": f.get("id", ""),
                    "alert_type": "entity_scan",
                    "title": f"{sev.upper()}: {f.get('title', '')}",
                    "description": f.get("description", ""),
                    "severity": sev,
                    "channels": ["email"],
                    "status": "pending",
                    "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                })

        # Store entity context in Cognee memory
        asyncio.create_task(_store_entity_memory(entity, analysis.findings))

    except Exception as e:
        logger.error(f"Entity scan failed for {name}: {e}", exc_info=True)
        entity["scan_status"] = "failed"


async def _store_entity_memory(entity: Dict[str, Any], findings: List[Dict[str, Any]]) -> None:
    """Store entity scan results in Cognee memory for persistent context."""
    name = entity.get("name", "Unknown")
    entity_id = entity.get("id", "")

    # Store entity profile in Cognee
    await cognee.store_finding(
        entity_id=entity_id,
        finding_type="entity_scan",
        content={
            "entity_name": name,
            "entity_type": entity.get("entity_type", ""),
            "url": entity.get("metadata", {}).get("url", ""),
            "domains": entity.get("metadata", {}).get("domains", []),
            "keywords": entity.get("metadata", {}).get("keywords", []),
            "risk_score": entity.get("current_risk_score", 0.0),
            "finding_count": len(findings),
            "scan_status": entity.get("scan_status", ""),
            "last_assessed": entity.get("last_assessed", ""),
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        },
    )

    # Store critical/high findings individually for semantic recall
    for f in findings:
        sev = f.get("severity", "info")
        if sev in ("critical", "high", "medium"):
            await cognee.store_finding(
                entity_id=entity_id,
                finding_type=f.get("finding_type", "unknown"),
                content={
                    "title": f.get("title", ""),
                    "description": f.get("description", ""),
                    "severity": sev,
                    "source_url": f.get("source_url", ""),
                    "check_type": f.get("check_type", ""),
                    "entity_name": name,
                    "risk_score": f.get("risk_score", 0),
                    "timestamp": f.get("created_at", ""),
                },
            )

    logger.info(f"Stored Cognee memory for entity: {name} ({len(findings)} findings)")


async def _seed_cognee_memory(findings: List[Dict[str, Any]], entities: List[Dict[str, Any]]) -> None:
    """Seed Cognee memory with demo data after /seed endpoint."""
    for entity in entities:
        name = entity.get("name", "Unknown")
        entity_id = entity.get("id", "")
        entity_findings = [f for f in findings if f.get("entity_id") == name]

        if not entity_findings:
            continue

        # Store entity profile
        await cognee.store_finding(
            entity_id=entity_id,
            finding_type="entity_profile",
            content={
                "entity_name": name,
                "entity_type": entity.get("entity_type", ""),
                "url": entity.get("metadata", {}).get("url", ""),
                "risk_score": entity.get("current_risk_score", 0),
                "finding_count": len(entity_findings),
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            },
        )

        # Store each finding
        for f in entity_findings:
            await cognee.store_finding(
                entity_id=entity_id,
                finding_type=f.get("finding_type", "unknown"),
                content={
                    "title": f.get("title", ""),
                    "description": f.get("description", ""),
                    "severity": f.get("severity", "info"),
                    "source_url": f.get("source_url", ""),
                    "entity_name": name,
                    "risk_score": f.get("risk_score", 0),
                    "timestamp": f.get("created_at", ""),
                },
            )

        logger.info(f"Seeded Cognee memory: {name} ({len(entity_findings)} findings)")


@router.post("/entities/monitor")
async def monitor_entity(request: MonitorRequest):
    """Add a website to monitor. Creates entity and launches background scan."""
    inferred = _infer_entity_config(request.url)
    name = request.name or inferred["name"]

    scan_config = None
    if request.scan_config:
        scan_config = request.scan_config.model_dump() if hasattr(request.scan_config, 'model_dump') else dict(request.scan_config)

    entity = {
        "id": str(uuid.uuid4()),
        "name": name,
        "entity_type": inferred["entity_type"],
        "metadata": {
            **inferred["metadata"],
            "url": request.url,
        },
        "scan_config": scan_config or {
            "scans": ["web_unlocker", "serp", "scraping_browser"],
            "compliance": ["GDPR", "SOC2", "HIPAA", "PCI_DSS"],
            "checks": ["headers", "ssl", "server_info", "well_known", "browser"],
        },
        "current_risk_score": 0.0,
        "last_assessed": None,
        "scan_status": "pending",
        "finding_count": 0,
    }
    _entities_db.append(entity)
    await db.save_entity(entity)

    # Launch background scan
    asyncio.create_task(_run_entity_scan(entity))

    return entity


@router.get("/entities/{entity_id}")
async def get_entity(entity_id: str):
    """Get a single entity with live finding count (excluding source-monitoring)."""
    for e in _entities_db:
        if e["id"] == entity_id:
            e["finding_count"] = sum(
                1 for f in _findings_db
                if f.get("entity_id") == e["name"]
                and not f.get("is_source_monitoring")
            )
            return e
    raise HTTPException(status_code=404, detail="Entity not found")


@router.delete("/entities/{entity_id}")
async def delete_entity(entity_id: str):
    """Remove an entity and its associated findings."""
    entity = next(
        (e for e in _entities_db if e["id"] == entity_id), None
    )
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")

    entity_name = entity["name"]
    _entities_db[:] = [e for e in _entities_db if e["id"] != entity_id]
    _findings_db[:] = [f for f in _findings_db if f.get("entity_id") != entity_name]

    await db.save_entity(entity)  # no-op — entity removed from list
    # Clear associated findings from DB
    for f in list(_findings_db):
        if f.get("entity_id") == entity_name:
            await db.delete_finding(f.get("id", ""))

    return {"status": "deleted", "entity_id": entity_id, "name": entity_name}


@router.post("/entities/{entity_id}/rescan")
async def rescan_entity(entity_id: str):
    """Trigger a fresh scan for an existing entity."""
    entity = next(
        (e for e in _entities_db if e["id"] == entity_id), None
    )
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    if entity.get("scan_status") == "scanning":
        raise HTTPException(
            status_code=409,
            detail="Scan already in progress for this entity",
        )

    # Reset and re-scan
    entity_name = entity["name"]
    entity["scan_status"] = "pending"
    entity["finding_count"] = 0

    # Remove old findings for this entity
    _findings_db[:] = [
        f for f in _findings_db
        if f.get("entity_id") != entity_name
    ]

    asyncio.create_task(_run_entity_scan(entity))
    return {"status": "scan_queued", "entity_id": entity_id}


# ── Cognee Memory Endpoints ───────────────────────────────────── #

@router.get("/memory/{entity_id}")
async def get_entity_memory(entity_id: str):
    """Get persistent memory context for an entity from Cognee."""
    context = await cognee.get_entity_context(entity_id)
    if context.get("memory_count", 0) == 0:
        raise HTTPException(
            status_code=404,
            detail=f"No Cognee memory found for entity {entity_id}",
        )
    return context


@router.get("/memory/{entity_id}/findings")
async def get_similar_findings(
    entity_id: str,
    query: str = "",
    limit: int = 5,
):
    """Query Cognee for similar findings across entity memory."""
    if not query:
        raise HTTPException(
            status_code=400,
            detail="Query parameter is required",
        )
    results = await cognee.query_memory(query, entity_id=entity_id, limit=limit)
    return {"results": results, "count": len(results)}


@router.get("/memory")
async def list_all_memory():
    """List all entities with Cognee memory (returns entity_ids with memory count)."""
    summary = {}
    for entity in _entities_db:
        ctx = await cognee.get_entity_context(entity["id"])
        if ctx.get("memory_count", 0) > 0:
            summary[entity["name"]] = {
                "entity_id": entity["id"],
                "memory_count": ctx["memory_count"],
                "last_assessed": entity.get("last_assessed", ""),
                "risk_score": entity.get("current_risk_score", 0),
            }
    return {"entities": summary, "total": len(summary)}


# ── Dashboard ──────────────────────────────────────────────────── #

@router.get("/dashboard/summary")
async def dashboard_summary(
    entity_id: Optional[str] = Query(None),
):
    # Filter findings by entity if specified
    filtered_findings = _findings_db[:]
    if entity_id:
        filtered_findings = [
            f for f in filtered_findings
            if f.get("entity_id", "").strip().lower() == entity_id.strip().lower()
        ]

    by_type: Dict[str, int] = {}
    by_severity: Dict[str, int] = {}
    for f in filtered_findings:
        by_type[f.get("finding_type", "unknown")] = (
            by_type.get(f.get("finding_type", "unknown"), 0) + 1
        )
        by_severity[f.get("severity", "unknown")] = (
            by_severity.get(f.get("severity", "unknown"), 0) + 1
        )

    alerts_pending = sum(
        1 for a in _alerts_db if a.get("status") == "pending"
    )

    scores = risk_scorer.aggregate_scores(
        [
            {"score": e.get("current_risk_score", 0),
             "level": risk_scorer._score_to_level(
                 e.get("current_risk_score", 0)
             )}
            for e in _entities_db
        ]
    )

    # Build timeline data (last 14 days)
    import datetime
    from collections import defaultdict
    now = datetime.datetime.now()
    daily: Dict[str, Dict[str, int]] = defaultdict(
        lambda: {"critical": 0, "high": 0, "medium": 0, "low": 0}
    )
    for f in filtered_findings:
        created = f.get("created_at", "")
        if created:
            day = created[:10]
            sev = f.get("severity", "low")
            if sev in ("critical", "high", "medium", "low"):
                daily[day][sev] += 1
    timeline_data = []
    for i in range(13, -1, -1):
        day = (now - datetime.timedelta(days=i)).strftime("%b %d")
        date_key = (now - datetime.timedelta(days=i)).strftime("%Y-%m-%d")
        entry = {"date": day, **daily.get(date_key, {"critical": 0, "high": 0, "medium": 0, "low": 0})}
        timeline_data.append(entry)

    # Compliance summary
    from src.compliance.classifier import get_compliance_summary as _get_compliance_summary
    compliance_summary = _get_compliance_summary(filtered_findings)

    # Separate compliance-tagged vs security-only findings
    compliance_tagged = len([f for f in filtered_findings if f.get("compliance")])
    security_only = len(filtered_findings) - compliance_tagged

    return {
        "total_findings": len(filtered_findings),
        "total_alerts": len(_alerts_db),
        "pending_alerts": alerts_pending,
        "monitored_entities": len(_entities_db),
        "findings_by_type": by_type,
        "findings_by_severity": by_severity,
        "overall_risk": scores,
        "recent_findings": _findings_db[-10:],
        "timeline_data": timeline_data,
        "compliance_summary": compliance_summary,
        "compliance_tagged": compliance_tagged,
        "security_only": security_only,
    }


# ── Investigations ─────────────────────────────────────────────── #

# ── AI Report Generation ─────────────────────────────────────── #

@router.post("/reports/generate")
async def generate_ai_report():
    """Generate a comprehensive narrative security report using AI/ML API."""
    findings_summary = []
    for f in _findings_db[-30:]:
        findings_summary.append({
            "title": f.get("title", ""),
            "severity": f.get("severity", "info"),
            "finding_type": f.get("finding_type", ""),
            "entity_id": f.get("entity_id", ""),
            "description": f.get("description", ""),
            "compliance": [
                {"regulation": c["regulation"], "article": c["article"]}
                for c in (f.get("compliance") or [])
            ],
        })

    alerts_summary = [
        {"title": a.get("title", ""), "severity": a.get("severity", ""),
         "status": a.get("status", ""), "alert_type": a.get("alert_type", "")}
        for a in _alerts_db
    ]

    entities_summary = [
        {"name": e.get("name", ""), "risk_score": e.get("current_risk_score", 0),
         "finding_count": e.get("finding_count", 0)}
        for e in _entities_db
    ]

    prompt = f"""You are a senior security analyst writing an executive security report.

DATA:
- Entities: {len(entities_summary)} monitored
- Total Findings: {len(_findings_db)} ({sum(1 for f in _findings_db if f.get('severity') == 'critical')} critical, {sum(1 for f in _findings_db if f.get('severity') == 'high')} high)
- Active Alerts: {sum(1 for a in _alerts_db if a.get('status') != 'acknowledged')}

ENTITIES:
{json.dumps(entities_summary, indent=2)}

FINDINGS:
{json.dumps(findings_summary, indent=2)}

ALERTS:
{json.dumps(alerts_summary, indent=2)}

Write a professional narrative security report with these sections:
1. **Executive Summary** — Overall security posture in 2-3 paragraphs
2. **Key Risk Indicators** — Highlight the most critical risks and why they matter
3. **Entity Risk Analysis** — Per-entity breakdown of findings and risk levels
4. **Compliance Impact** — GDPR, SOC 2, HIPAA, PCI DSS exposure with specific article references
5. **Critical & High Priority Findings** — Deep dive into what needs immediate attention
6. **Agent Methodology** — How Bright Data products (Web Unlocker, SERP API, Scraping Browser) and AI/ML API were used to discover these findings
7. **Prioritized Remediation Plan** — Action items grouped by urgency (Immediate 24h, Short-term 7d, Medium-term 30d)
8. **Recommendations** — Strategic improvements for security posture

IMPORTANT GUIDELINES:
- SERP/OSINT findings (e.g., "Potential paste mention") are INTELLIGENCE LEADS, not confirmed breaches. Classify as HIGH at most, never CRITICAL, until human verification.
- "Website unreachable via proxy" and "browser render failure" are MONITORING INFRASTRUCTURE NOTES. Mention them only as operational context, NOT as findings against the entity.
- Compliance source monitoring (gdpr.eu, iso.org changes) is ENVIRONMENTAL INTELLIGENCE. Note separately from entity security findings.
- Do NOT map to PCI DSS or HIPAA unless the entity type indicates cardholder data or PHI handling.
- A block by a major news site (NYTimes.com) is likely benign anti-automation — note as a positive signal, not a vulnerability.
- Alert resolution rate is meaningful only with >7 days history. For new alerts, just note their generation time.

Format as professional markdown. Be specific — reference actual finding titles and entity names."""

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{settings.aiml_api_base}/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.aiml_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": settings.aiml_default_model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 4000,
                    "temperature": 0.3,
                },
            )
            response.raise_for_status()
            data = response.json()
            report_text = data["choices"][0]["message"]["content"]

        # Clean markdown code blocks if present
        report_text = report_text.strip()
        if report_text.startswith("```"):
            report_text = report_text.split("\n", 1)[-1]
            report_text = report_text.rsplit("```", 1)[0].strip()

        return {
            "status": "success",
            "report": report_text,
            "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "metrics": {
                "entities": len(entities_summary),
                "findings": len(_findings_db),
                "alerts": len(alerts_summary),
            },
        }
    except Exception as e:
        logger.error(f"AI report generation failed: {e}")
        return {
            "status": "error",
            "error": str(e),
            "report": None,
        }


@router.post("/reports/generate/{entity_name}")
async def generate_entity_ai_report(entity_name: str):
    """Generate a per-entity AI security report."""
    entity = next((e for e in _entities_db if e["name"].lower() == entity_name.lower()), None)
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")

    entity_findings = [f for f in _findings_db if f.get("entity_id", "").lower() == entity_name.lower()]
    entity_alerts = [a for a in _alerts_db if a.get("finding_id") and any(
        f.get("id") == a["finding_id"] for f in entity_findings
    )]

    findings_summary = [{
        "title": f.get("title", ""),
        "severity": f.get("severity", "info"),
        "finding_type": f.get("finding_type", ""),
        "description": f.get("description", ""),
        "check_type": f.get("check_type", ""),
        "agent_meta": f.get("agent_meta", {}),
        "compliance": [{"regulation": c["regulation"], "article": c["article"]} for c in (f.get("compliance") or [])],
    } for f in entity_findings]

    prompt = f"""You are a senior security analyst. Generate a detailed narrative security report for "{entity_name}".

ENTITY DATA:
- Name: {entity_name}
- Risk Score: {entity.get('current_risk_score', 0)}/100
- Type: {entity.get('entity_type', 'N/A')}
- Findings: {len(entity_findings)} total
- Alerts: {len(entity_alerts)}

FINDINGS:
{__import__('json').dumps(findings_summary, indent=2)}

Write a professional report with:
1. **Executive Summary** — Security posture for this entity
2. **Finding Details** — Each finding with: what was found, which agent discovered it (include agent name, step number, and methodology), what Bright Data tool was used, how it was classified, compliance impact
3. **Agent Logic** — For each finding, explain the detection logic:
   - Which SentinelWatch agent found it
   - What specific method/check was used
   - Which Bright Data product was involved
   - How the severity was determined
   - What compliance regulations are affected
4. **Remediation Plan** — Specific steps with effort estimates
5. **Compliance Impact** — GDPR, SOC 2, HIPAA, PCI DSS mappings

Format as professional markdown. Be specific — reference actual finding titles and agent names."""

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{settings.aiml_api_base}/v1/chat/completions",
                headers={"Authorization": f"Bearer {settings.aiml_api_key}", "Content-Type": "application/json"},
                json={"model": settings.aiml_default_model, "messages": [{"role": "user", "content": prompt}], "max_tokens": 4000, "temperature": 0.3},
            )
            response.raise_for_status()
            data = response.json()
            report_text = data["choices"][0]["message"]["content"].strip()
            if report_text.startswith("```"):
                report_text = report_text.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
        return {"status": "success", "report": report_text, "entity": entity_name, "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat()}
    except Exception as e:
        logger.error(f"Entity AI report failed: {e}")
        return {"status": "error", "error": str(e), "report": None}


@router.get("/reports/html")
async def get_html_report():
    """Generate a standalone HTML security report page."""
    findings_count = len(_findings_db)
    critical_count = sum(1 for f in _findings_db if f.get("severity") == "critical")
    high_count = sum(1 for f in _findings_db if f.get("severity") == "high")
    medium_count = sum(1 for f in _findings_db if f.get("severity") == "medium")
    low_count = sum(1 for f in _findings_db if f.get("severity") == "low")
    pending_alerts = sum(1 for a in _alerts_db if a.get("status") != "acknowledged")

    findings_rows = ""
    for f in _findings_db[-20:]:
        agent = f.get("agent_meta", {})
        findings_rows += f"""<tr>
            <td class="sev-{f.get('severity', 'info')}">{f.get('severity', 'info').upper()}</td>
            <td>{f.get('title', '')}</td>
            <td>{f.get('entity_id', '—')}</td>
            <td>{agent.get('agent', '—')}</td>
            <td class="tool-cell">{agent.get('brightdata_tool', '—')[:60]}</td>
        </tr>"""

    entities_cards = ""
    for e in _entities_db:
        ef = [f for f in _findings_db if f.get("entity_id") == e["name"]]
        entities_cards += f"""<div class="entity-card">
            <h3>{e['name']}</h3>
            <div class="entity-stats">
                <span class="risk-badge risk-{'high' if e.get('current_risk_score',0) >= 70 else 'med' if e.get('current_risk_score',0) >= 40 else 'low'}">{e.get('current_risk_score', 0):.0f}/100</span>
                <span>{len(ef)} findings</span>
                <span>{sum(1 for f in ef if f.get('severity') == 'critical')} critical</span>
                <span>{sum(1 for f in ef if f.get('severity') == 'high')} high</span>
            </div>
        </div>"""

    html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><title>SentinelWatch Security Report</title>
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif; background:#0B0F19; color:#E2E8F0; padding:40px; }}
.container {{ max-width:1200px; margin:0 auto; }}
h1 {{ font-size:28px; font-weight:700; margin-bottom:8px; color:#22D3EE; }}
h2 {{ font-size:18px; font-weight:600; margin:32px 0 16px; color:#E2E8F0; border-bottom:1px solid #1E2433; padding-bottom:8px; }}
h3 {{ font-size:14px; font-weight:600; margin:20px 0 8px; color:#22D3EE; }}
.subtitle {{ color:#8892A6; font-size:14px; margin-bottom:24px; }}
.stats {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); gap:12px; margin-bottom:32px; }}
.stat-card {{ background:#131826; border:1px solid #1E2433; border-radius:12px; padding:20px; text-align:center; }}
.stat-card .num {{ font-size:32px; font-weight:700; font-family:'JetBrains Mono',monospace; }}
.stat-card .label {{ font-size:11px; color:#8892A6; text-transform:uppercase; letter-spacing:1px; margin-top:4px; }}
.entity-grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(250px,1fr)); gap:12px; margin-bottom:32px; }}
.entity-card {{ background:#131826; border:1px solid #1E2433; border-radius:12px; padding:16px; }}
.entity-card h3 {{ font-size:14px; margin:0 0 8px; color:#E2E8F0; }}
.entity-stats {{ display:flex; gap:8px; flex-wrap:wrap; font-size:12px; color:#8892A6; }}
.risk-badge {{ padding:2px 8px; border-radius:4px; font-weight:600; font-size:11px; font-family:'JetBrains Mono',monospace; }}
.risk-high {{ background:rgba(239,68,68,0.15); color:#EF4444; border:1px solid rgba(239,68,68,0.3); }}
.risk-med {{ background:rgba(245,158,11,0.15); color:#F59E0B; border:1px solid rgba(245,158,11,0.3); }}
.risk-low {{ background:rgba(34,197,94,0.15); color:#22C55E; border:1px solid rgba(34,197,94,0.3); }}
table {{ width:100%; border-collapse:collapse; font-size:12px; margin-bottom:32px; }}
th,td {{ padding:10px 12px; text-align:left; border-bottom:1px solid #1E2433; }}
th {{ color:#8892A6; font-size:10px; text-transform:uppercase; letter-spacing:1px; font-weight:600; background:#0D111E; }}
td {{ color:#E2E8F0; }}
.sev-critical {{ color:#EF4444; font-weight:600; }}
.sev-high {{ color:#F97316; font-weight:600; }}
.sev-medium {{ color:#F59E0B; }}
.sev-low {{ color:#3B82F6; }}
.tool-cell {{ font-size:10px; color:#8892A6; font-family:'JetBrains Mono',monospace; }}
.meta {{ font-size:12px; color:#8892A6; margin-top:32px; padding-top:16px; border-top:1px solid #1E2433; }}
</style></head><body>
<div class="container">
<h1>🔒 SentinelWatch Security Report</h1>
<p class="subtitle">Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M UTC')} — {len(_entities_db)} entities monitored</p>

<div class="stats">
<div class="stat-card"><div class="num" style="color:#22D3EE">{findings_count}</div><div class="label">Total Findings</div></div>
<div class="stat-card"><div class="num" style="color:#EF4444">{critical_count}</div><div class="label">Critical</div></div>
<div class="stat-card"><div class="num" style="color:#F97316">{high_count}</div><div class="label">High</div></div>
<div class="stat-card"><div class="num" style="color:#F59E0B">{medium_count}</div><div class="label">Medium</div></div>
<div class="stat-card"><div class="num" style="color:#3B82F6">{low_count}</div><div class="label">Low</div></div>
<div class="stat-card"><div class="num" style="color:#EF4444">{pending_alerts}</div><div class="label">Active Alerts</div></div>
</div>

<h2>Entities</h2>
<div class="entity-grid">{entities_cards}</div>

<h2>Findings</h2>
<table><thead><tr><th>Severity</th><th>Title</th><th>Entity</th><th>Agent</th><th>Bright Data Tool</th></tr></thead>
<tbody>{findings_rows}</tbody></table>

<div class="meta">
<p>Report generated by SentinelWatch multi-agent pipeline using Bright Data Web Unlocker, SERP API, and Scraping Browser.</p>
<p>Powered by AI/ML API for threat analysis and compliance classification.</p>
</div>
</div></body></html>"""
    return HTMLResponse(content=html)


@router.get("/reports/html/{entity_name}")
async def get_entity_html_report(entity_name: str):
    """Generate a per-entity standalone HTML security report."""
    entity = next((e for e in _entities_db if e["name"].lower() == entity_name.lower()), None)
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")

    entity_findings = [f for f in _findings_db if f.get("entity_id", "").lower() == entity_name.lower()]

    findings_rows = ""
    for f in entity_findings:
        agent = f.get("agent_meta", {})
        compliance_tags = "".join(f'<span class="comp-tag">{c["regulation"]} {c["article"]}</span>' for c in (f.get("compliance") or [])[:4])
        findings_rows += f"""<tr>
            <td class="sev-{f.get('severity', 'info')}">{f.get('severity', 'info').upper()}</td>
            <td>{f.get('title', '')}</td>
            <td class="tool-cell">{agent.get('brightdata_tool', '—')[:50]}</td>
            <td>{compliance_tags}</td>
        </tr>"""

    sev_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for f in entity_findings:
        sev_counts[f.get("severity", "low")] = sev_counts.get(f.get("severity", "low"), 0) + 1

    html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><title>SentinelWatch - {entity_name} Report</title>
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif; background:#0B0F19; color:#E2E8F0; padding:40px; }}
.container {{ max-width:1000px; margin:0 auto; }}
h1 {{ font-size:24px; font-weight:700; margin-bottom:4px; color:#22D3EE; }}
h2 {{ font-size:16px; font-weight:600; margin:24px 0 12px; color:#E2E8F0; border-bottom:1px solid #1E2433; padding-bottom:6px; }}
.subtitle {{ color:#8892A6; font-size:13px; margin-bottom:20px; }}
.stats {{ display:grid; grid-template-columns:repeat(4,1fr); gap:10px; margin-bottom:24px; }}
.stat-card {{ background:#131826; border:1px solid #1E2433; border-radius:10px; padding:16px; text-align:center; }}
.stat-card .num {{ font-size:28px; font-weight:700; font-family:'JetBrains Mono',monospace; }}
.stat-card .label {{ font-size:10px; color:#8892A6; text-transform:uppercase; letter-spacing:1px; margin-top:4px; }}
table {{ width:100%; border-collapse:collapse; font-size:12px; }}
th,td {{ padding:8px 10px; text-align:left; border-bottom:1px solid #1E2433; }}
th {{ color:#8892A6; font-size:10px; text-transform:uppercase; letter-spacing:1px; background:#0D111E; }}
td {{ color:#E2E8F0; }}
.sev-critical {{ color:#EF4444; font-weight:600; }}
.sev-high {{ color:#F97316; font-weight:600; }}
.sev-medium {{ color:#F59E0B; }}
.sev-low {{ color:#3B82F6; }}
.tool-cell {{ font-size:10px; color:#8892A6; font-family:'JetBrains Mono',monospace; }}
.comp-tag {{ display:inline-block; padding:1px 6px; margin:1px; border-radius:3px; font-size:9px; font-weight:500; border:1px solid currentColor; }}
.comp-tag:nth-child(4n+1) {{ color:#60A5FA; background:rgba(96,165,250,0.1); }}
.comp-tag:nth-child(4n+2) {{ color:#22D3EE; background:rgba(34,211,238,0.1); }}
.comp-tag:nth-child(4n+3) {{ color:#EF4444; background:rgba(239,68,68,0.1); }}
.comp-tag:nth-child(4n) {{ color:#F59E0B; background:rgba(245,158,11,0.1); }}
.meta {{ font-size:11px; color:#8892A6; margin-top:24px; padding-top:12px; border-top:1px solid #1E2433; }}
</style></head><body>
<div class="container">
<h1>🔒 {entity_name}</h1>
<p class="subtitle">Risk Score: {entity.get('current_risk_score', 0):.0f}/100 | {entity.get('entity_type', 'N/A')} | {len(entity_findings)} findings</p>

<div class="stats">
<div class="stat-card"><div class="num" style="color:#EF4444">{sev_counts['critical']}</div><div class="label">Critical</div></div>
<div class="stat-card"><div class="num" style="color:#F97316">{sev_counts['high']}</div><div class="label">High</div></div>
<div class="stat-card"><div class="num" style="color:#F59E0B">{sev_counts['medium']}</div><div class="label">Medium</div></div>
<div class="stat-card"><div class="num" style="color:#3B82F6">{sev_counts['low']}</div><div class="label">Low</div></div>
</div>

<h2>Findings & Agent Analysis</h2>
<table><thead><tr><th>Severity</th><th>Finding</th><th>Bright Data Tool</th><th>Compliance</th></tr></thead>
<tbody>{findings_rows}</tbody></table>

<div class="meta">
<p>Generated by SentinelWatch | Bright Data Web Unlocker, SERP API, Scraping Browser | AI/ML API Analysis</p>
</div>
</div></body></html>"""
    return HTMLResponse(content=html)


@router.get("/investigations")
async def list_investigations(
    limit: int = Query(50, le=200),
    verdict: Optional[str] = Query(None),
):
    """List all completed investigations, newest first."""
    results = _investigations_db[:]
    if verdict:
        results = [inv for inv in results if inv.get("verdict") == verdict]
    results.sort(key=lambda i: i.get("timestamp", ""), reverse=True)
    return {
        "total": len(results),
        "limit": limit,
        "results": results[:limit],
    }


@router.post("/investigate")
async def trigger_investigation(request: InvestigationRequest):
    """Trigger an ad-hoc investigation via the InvestigationAgent."""
    from src.intelligence.investigation_agent import InvestigationAgent

    agent = InvestigationAgent()
    result = await agent.investigate(
        indicator=request.indicator,
        indicator_type=request.indicator_type,
        context=request.context,
    )

    inv = result.to_dict()
    inv["id"] = uuid.uuid4().hex[:12]
    _investigations_db.append(inv)
    await db.save_investigation(inv)

    return inv


@router.get("/investigate/{investigation_id}")
async def get_investigation(investigation_id: str):
    for inv in _investigations_db:
        if inv.get("id") == investigation_id:
            return inv
    raise HTTPException(status_code=404,
                        detail="Investigation not found")


# ── Demo Seed Data ────────────────────────────────────────────── #

@router.post("/seed")
async def seed_demo_data():
    """Populate the in-memory store with demo data for UI showcase."""
    import datetime
    now = datetime.datetime.now

    # Clear previous data and re-seed
    _findings_db.clear()
    _alerts_db.clear()
    _investigations_db.clear()

    sample_findings = [
        {"id": "f001", "finding_type": "vulnerability", "source_type": "web_scraper", "source_url": "https://brightdata.com", "title": "Exposed API endpoint with weak authentication", "description": "The Bright Data dashboard exposes an API endpoint that lacks rate limiting and contains a potential SSRF vector.", "severity": "critical", "entity_id": "Bright Data", "status": "new", "risk_score": 8.5, "created_at": (now() - datetime.timedelta(hours=2)).isoformat()},
        {"id": "f002", "finding_type": "vulnerability", "source_type": "web_scraper", "source_url": "https://aimlapi.com", "title": "Insecure direct object reference in user API", "description": "IDOR vulnerability found in the AI/ML API user profile endpoint allowing enumeration of user IDs.", "severity": "high", "entity_id": "AI/ML API", "status": "new", "risk_score": 7.2, "created_at": (now() - datetime.timedelta(hours=5)).isoformat()},
        {"id": "f003", "finding_type": "compliance", "source_type": "serp_news", "source_url": "https://gdpr.eu", "title": "GDPR compliance gap in data retention policy", "description": "Data retention periods exceed GDPR Article 5(1)(e) requirements. Customer logs retained for 18 months without legitimate purpose.", "severity": "high", "entity_id": "Bright Data", "status": "new", "risk_score": 7.8, "created_at": (now() - datetime.timedelta(hours=8)).isoformat()},
        {"id": "f004", "finding_type": "threat_intel", "source_type": "serp_news", "source_url": "https://news.ycombinator.com", "title": "Third-party library with known CVE detected", "description": "lodash 4.17.20 has CVE-2024-23346 with CVSS 7.2. Library is used in the main web application bundle.", "severity": "medium", "entity_id": "Bright Data", "status": "new", "risk_score": 5.0, "created_at": (now() - datetime.timedelta(hours=12)).isoformat()},
        {"id": "f005", "finding_type": "vulnerability", "source_type": "web_scraper", "source_url": "https://docs.aimlapi.com", "title": "Missing Content-Security-Policy header", "description": "AI/ML API documentation portal lacks CSP headers, exposing users to XSS attacks through crafted links.", "severity": "medium", "entity_id": "AI/ML API", "status": "new", "risk_score": 5.5, "created_at": (now() - datetime.timedelta(hours=18)).isoformat()},
        {"id": "f006", "finding_type": "compliance", "source_type": "serp_news", "source_url": "https://brightdata.com", "title": "SOC 2 Type II certification renewal overdue", "description": "SOC 2 Type II report expired 14 days ago. Renewal audit has been scheduled but not completed.", "severity": "medium", "entity_id": "Bright Data", "status": "new", "risk_score": 4.8, "created_at": (now() - datetime.timedelta(hours=24)).isoformat()},
        {"id": "f007", "finding_type": "compliance", "source_type": "serp_news", "source_url": "https://aimlapi.com", "title": "Privacy policy missing data processing disclosure", "description": "AI/ML API privacy policy lacks disclosure about third-party data processing under GDPR Article 28.", "severity": "low", "entity_id": "AI/ML API", "status": "new", "risk_score": 2.5, "created_at": (now() - datetime.timedelta(hours=30)).isoformat()},
        {"id": "f008", "finding_type": "threat_intel", "source_type": "serp_news", "source_url": "https://twitter.com", "title": "Brand impersonation detected on social media", "description": "Twitter account @BrightData_Support impersonates official support. 12 followers, active since last week.", "severity": "medium", "entity_id": "Bright Data", "status": "new", "risk_score": 4.5, "created_at": (now() - datetime.timedelta(hours=36)).isoformat()},
        {"id": "f009", "finding_type": "threat_intel", "source_type": "web_scraper", "source_url": "https://github.com", "title": "Sensitive key exposed in public GitHub repo", "description": "AWS access key found in public repository \"brightdata-sdk-examples\". Key has been rotated.", "severity": "critical", "entity_id": "Bright Data", "status": "new", "risk_score": 9.0, "created_at": (now() - datetime.timedelta(hours=40)).isoformat()},
        {"id": "f010", "finding_type": "vulnerability", "source_type": "web_scraper", "source_url": "https://status.aimlapi.com", "title": "SSL certificate expiring in 7 days", "description": "Wildcard SSL certificate for *.aimlapi.com expires in 7 days. Auto-renewal is configured but untested.", "severity": "high", "entity_id": "AI/ML API", "status": "new", "risk_score": 7.0, "created_at": (now() - datetime.timedelta(hours=48)).isoformat()},
        {"id": "f011", "finding_type": "vulnerability", "source_type": "serp_news", "source_url": "https://brightdata.com", "title": "Open redirect vulnerability on login page", "description": "The redirect_uri parameter on the Bright Data login page does not validate allowed redirect targets.", "severity": "low", "entity_id": "Bright Data", "status": "new", "risk_score": 3.0, "created_at": (now() - datetime.timedelta(hours=52)).isoformat()},
        {"id": "f012", "finding_type": "threat_intel", "source_type": "serp_news", "source_url": "https://reddit.com", "title": "Credentials leaked in pastebin dump", "description": "Credentials associated with AI/ML API test environment found in a pastebin dump. No production impact confirmed.", "severity": "high", "entity_id": "AI/ML API", "status": "new", "risk_score": 7.5, "created_at": (now() - datetime.timedelta(hours=56)).isoformat()},
        {"id": "f013", "finding_type": "compliance", "source_type": "serp_news", "source_url": "https://brightdata.com", "title": "Data residency requirement not met for EU customers", "description": "Customer data for EU-based clients is stored in US-east region, violating GDPR data residency requirements.", "severity": "critical", "entity_id": "Bright Data", "status": "new", "risk_score": 8.8, "created_at": (now() - datetime.timedelta(hours=60)).isoformat()},
        {"id": "f014", "finding_type": "vulnerability", "source_type": "web_scraper", "source_url": "https://docs.brightdata.com", "title": "Documentation exposing internal IP addresses", "description": "Internal IP ranges and network topology visible in Bright Data developer documentation.", "severity": "low", "entity_id": "Bright Data", "status": "new", "risk_score": 2.0, "created_at": (now() - datetime.timedelta(hours=66)).isoformat()},
        {"id": "f015", "finding_type": "threat_intel", "source_type": "serp_news", "source_url": "https://news.ycombinator.com", "title": "DDoS chatter targeting proxy infrastructure", "description": "Dark web forums discussing coordinated DDoS attacks on major proxy providers including Bright Data.", "severity": "high", "entity_id": "Bright Data", "status": "new", "risk_score": 7.3, "created_at": (now() - datetime.timedelta(hours=70)).isoformat()},
    ]
    _findings_db.extend(sample_findings)
    # Add compliance classification tags to seed findings
    from src.compliance.classifier import classify_findings as _cf
    _findings_db[:] = _cf(_findings_db)
    await db.bulk_save("findings", _findings_db)

    sample_alerts = [
        {"id": "a001", "finding_id": "f001", "alert_type": "severity_threshold", "title": "Critical: Exposed API Endpoint", "description": "Bright Data dashboard has an exposed API with weak authentication requiring immediate attention.", "severity": "critical", "channels": ["email", "slack"], "status": "pending", "created_at": (now() - datetime.timedelta(hours=2)).isoformat()},
        {"id": "a002", "finding_id": "f002", "alert_type": "severity_threshold", "title": "High: IDOR Vulnerability", "description": "AI/ML API user profile endpoint allows user ID enumeration. Patch required.", "severity": "high", "channels": ["email"], "status": "pending", "created_at": (now() - datetime.timedelta(hours=5)).isoformat()},
        {"id": "a003", "finding_id": "f009", "alert_type": "severity_threshold", "title": "Critical: AWS Key Exposure", "description": "AWS access key exposed in public GitHub repository. Immediate rotation required.", "severity": "critical", "channels": ["email", "slack", "pagerduty"], "status": "pending", "created_at": (now() - datetime.timedelta(hours=40)).isoformat()},
        {"id": "a004", "finding_id": "f013", "alert_type": "compliance", "title": "Critical: GDPR Data Residency Violation", "description": "EU customer data stored in US region violating GDPR data residency requirements.", "severity": "critical", "channels": ["email", "slack"], "status": "pending", "created_at": (now() - datetime.timedelta(hours=60)).isoformat()},
        {"id": "a005", "finding_id": "f003", "alert_type": "compliance", "title": "High: GDPR Retention Policy Gap", "description": "Customer logs retained for 18 months. Maximum allowed under GDPR is 12 months.", "severity": "high", "channels": ["email"], "status": "pending", "created_at": (now() - datetime.timedelta(hours=8)).isoformat()},
        {"id": "a006", "finding_id": "f010", "alert_type": "severity_threshold", "title": "High: SSL Certificate Expiring", "description": "AI/ML API SSL certificate expires in 7 days. Auto-renewal untested.", "severity": "high", "channels": ["email"], "status": "pending", "created_at": (now() - datetime.timedelta(hours=48)).isoformat()},
        {"id": "a007", "finding_id": "f015", "alert_type": "threat_intel", "title": "High: DDoS Chatter Detected", "description": "Dark web forums discussing DDoS attacks on proxy infrastructure including Bright Data.", "severity": "high", "channels": ["email", "slack"], "status": "pending", "created_at": (now() - datetime.timedelta(hours=70)).isoformat()},
    ]
    _alerts_db.extend(sample_alerts)
    await db.bulk_save("alerts", sample_alerts)

    # Update entity risk scores to reflect findings
    for entity in _entities_db:
        name = entity.get("name", "")
        if name == "Bright Data":
            entity["current_risk_score"] = 72.5
            entity["last_assessed"] = now().isoformat()
        elif name == "AI/ML API":
            entity["current_risk_score"] = 45.0
            entity["last_assessed"] = now().isoformat()
        await db.save_entity(entity)

    # Seed Cognee memory with demo findings (fire-and-forget)
    asyncio.create_task(_seed_cognee_memory(sample_findings, _entities_db))

    return {
        "status": "seeded",
        "findings": len(sample_findings),
        "alerts": len(sample_alerts),
    }


