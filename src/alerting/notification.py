"""Notification helpers for alert delivery."""

from src.alerting.alert_manager import alert_manager, Alert


async def send_alert(
    finding_type: str,
    findings: list,
) -> list:
    """Convenience function: create and send alerts from findings."""
    alerts = alert_manager.create_alerts(finding_type, findings)
    for alert in alerts:
        await alert_manager.send_alert(alert)
    return [a.to_dict() for a in alerts]
