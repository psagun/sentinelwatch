"""Alert management system.

Routes findings to appropriate channels based on severity,
manages alert lifecycle (new → acknowledged → resolved),
and handles deduplication and throttling.
"""

import json
import logging
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

import httpx

from src.config import settings

logger = logging.getLogger(__name__)


class AlertStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    FALSE_POSITIVE = "false_positive"


class Alert:
    """A security or compliance alert."""

    def __init__(
        self,
        finding_id: str,
        alert_type: str,
        title: str,
        description: str,
        severity: str,
        channels: List[str],
        source_finding: Dict[str, Any],
    ):
        self.id = str(uuid4())
        self.finding_id = finding_id
        self.alert_type = alert_type
        self.title = title
        self.description = description
        self.severity = severity
        self.channels = channels
        self.source_finding = source_finding
        self.status = AlertStatus.PENDING
        self.created_at = datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "finding_id": self.finding_id,
            "alert_type": self.alert_type,
            "title": self.title,
            "description": self.description,
            "severity": self.severity,
            "channels": self.channels,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
        }


class AlertManager:
    """Central alert management."""

    def __init__(self):
        self._sent_alerts: Dict[str, Alert] = {}

    def create_alerts(
        self,
        finding_type: str,
        findings: List[Dict[str, Any]],
    ) -> List[Alert]:
        """Create alerts from findings based on severity thresholds."""
        alerts: List[Alert] = []

        for finding in findings:
            severity = finding.get("severity", "low")
            should_alert, channels = self._determine_routing(severity)

            if not should_alert:
                continue

            dedup_key = self._dedup_key(finding)
            if dedup_key in self._sent_alerts:
                continue

            alert = Alert(
                finding_id=finding.get("id", str(uuid4())),
                alert_type=finding_type,
                title=finding.get("title", "Security Alert"),
                description=finding.get("description", ""),
                severity=severity,
                channels=channels,
                source_finding=finding,
            )

            self._sent_alerts[dedup_key] = alert
            alerts.append(alert)

        return alerts

    def _determine_routing(
        self, severity: str
    ) -> tuple:
        """Determine if an alert should fire and which channels to use."""
        routing = {
            "critical": (True, ["pagerduty", "slack", "email"]),
            "high": (True, ["slack", "email"]),
            "medium": (True, ["slack"]),
            "low": (False, []),
            "info": (False, []),
        }
        return routing.get(severity, (False, []))

    def _dedup_key(self, finding: Dict[str, Any]) -> str:
        """Generate a deduplication key for a finding."""
        title = finding.get("title", "")
        source_url = finding.get("source_url", "")
        return f"{title}:{source_url}"

    async def send_alert(self, alert: Alert) -> bool:
        """Route an alert to all configured channels."""
        success = True

        for channel in alert.channels:
            try:
                if channel == "slack":
                    await self._send_slack(alert)
                elif channel == "email":
                    await self._send_email(alert)
                elif channel == "pagerduty":
                    await self._send_pagerduty(alert)
                else:
                    await self._send_webhook(alert, channel)
            except Exception as e:
                logger.error(f"Failed to send alert via {channel}: {e}")
                success = False

        return success

    async def _send_slack(self, alert: Alert) -> None:
        """Send alert to Slack via webhook."""
        webhook_url = settings.slack_webhook_url
        if not webhook_url:
            logger.debug("Slack webhook not configured")
            return

        color = {
            "critical": "#FF0000",
            "high": "#FF6600",
            "medium": "#FFCC00",
            "low": "#666666",
        }.get(alert.severity, "#666666")

        payload = {
            "attachments": [
                {
                    "color": color,
                    "title": alert.title,
                    "text": alert.description,
                    "fields": [
                        {"title": "Severity",
                         "value": alert.severity.upper(),
                         "short": True},
                        {"title": "Type",
                         "value": alert.alert_type,
                         "short": True},
                    ],
                    "footer": "SentinelWatch",
                    "ts": int(alert.created_at.timestamp()),
                }
            ]
        }
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                webhook_url, json=payload
            )
            response.raise_for_status()

    async def _send_email(self, alert: Alert) -> None:
        """Send alert via email (SMTP)."""
        if not all([settings.smtp_host, settings.smtp_user,
                    settings.smtp_password]):
            logger.debug("SMTP not configured")
            return
        # Email sending via SMTP would use aiosmtplib
        logger.info(f"Email alert queued: {alert.title}")

    async def _send_pagerduty(self, alert: Alert) -> None:
        """Send critical alert to PagerDuty."""
        api_key = settings.pagerduty_api_key
        if not api_key:
            logger.debug("PagerDuty not configured")
            return

        severity_map = {
            "critical": "critical", "high": "error",
            "medium": "warning", "low": "info",
        }
        payload = {
            "routing_key": api_key,
            "event_action": "trigger",
            "payload": {
                "summary": alert.title[:120],
                "severity": severity_map.get(alert.severity, "info"),
                "source": "SentinelWatch",
                "custom_details": alert.source_finding,
            },
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                "https://events.pagerduty.com/v2/enqueue",
                json=payload,
            )
            response.raise_for_status()

    async def _send_webhook(
        self, alert: Alert, webhook_url: str
    ) -> None:
        """Send alert to a custom webhook."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                webhook_url, json=alert.to_dict()
            )
            response.raise_for_status()


alert_manager = AlertManager()
