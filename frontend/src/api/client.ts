import type { DashboardMetrics, Finding, Alert, Entity, InvestigationResult, MonitorRequest } from '../types';

export const API_BASE = '/api/v1';

async function fetchJSON<T>(url: string, opts?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${url}`, {
    headers: { 'Content-Type': 'application/json' },
    ...opts,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => 'Unknown error');
    throw new Error(`${res.status}: ${text}`);
  }
  return res.json();
}

export async function getDashboardMetrics(entityId?: string): Promise<DashboardMetrics> {
  const q = entityId ? `?entity_id=${encodeURIComponent(entityId)}` : '';
  const data = await fetchJSON<any>(`/dashboard/summary${q}`);

  const bySeverity = data.findings_by_severity ?? {};
  const risk = data.overall_risk ?? {};

  const metrics: DashboardMetrics = {
    total_findings: data.total_findings ?? 0,
    critical_findings: bySeverity.critical ?? 0,
    high_findings: bySeverity.high ?? 0,
    medium_findings: bySeverity.medium ?? 0,
    low_findings: bySeverity.low ?? 0,
    active_alerts: data.pending_alerts ?? 0,
    total_entities: data.monitored_entities ?? 0,
    avg_risk_score: risk.overall_score ?? 0,
    severity_breakdown: [
      { name: 'Critical', value: bySeverity.critical ?? 0, color: '#EF4444' },
      { name: 'High', value: bySeverity.high ?? 0, color: '#F97316' },
      { name: 'Medium', value: bySeverity.medium ?? 0, color: '#F59E0B' },
      { name: 'Low', value: bySeverity.low ?? 0, color: '#3B82F6' },
    ],
    recent_findings: (data.recent_findings ?? []).reverse().slice(0, 6),
    timeline_data: data.timeline_data ?? [],
    compliance_tagged: data.compliance_tagged ?? 0,
    compliance_summary: data.compliance_summary ?? {},
  };

  return metrics;
}

export async function getFindings(params?: {
  severity?: string;
  entity_id?: string;
  limit?: number;
}): Promise<Finding[]> {
  const q = new URLSearchParams();
  if (params?.severity) q.set('severity', params.severity);
  if (params?.entity_id) q.set('entity_id', params.entity_id);
  if (params?.limit) q.set('limit', String(params.limit));
  const data = await fetchJSON<any>(`/findings${q.toString() ? '?' + q.toString() : ''}`);
  return (data.results ?? []).slice(0, params?.limit ?? 100);
}

export async function getAlerts(): Promise<Alert[]> {
  const data = await fetchJSON<any>('/alerts');
  return data.results ?? [];
}

export async function acknowledgeAlert(id: string, notes?: string): Promise<void> {
  await fetchJSON(`/alerts/${id}/acknowledge`, {
    method: 'POST',
    body: JSON.stringify({ notes: notes || '' }),
  });
}

export async function getEntities(): Promise<Entity[]> {
  const data = await fetchJSON<any>('/entities');
  return data.results ?? [];
}

export async function runInvestigation(indicator: string, indicatorType: string = 'ip'): Promise<InvestigationResult> {
  return fetchJSON<InvestigationResult>('/investigate', {
    method: 'POST',
    body: JSON.stringify({ indicator, indicator_type: indicatorType }),
  });
}

export async function getInvestigation(id: string): Promise<InvestigationResult> {
  return fetchJSON<InvestigationResult>(`/investigate/${id}`);
}

export async function listCompletedInvestigations(): Promise<InvestigationResult[]> {
  const data = await fetchJSON<any>('/investigations');
  return data.results ?? [];
}

// ── Self-Service Monitoring ──────────────────────────────────── #

export async function monitorEntity(request: MonitorRequest): Promise<Entity> {
  return fetchJSON<Entity>('/entities/monitor', {
    method: 'POST',
    body: JSON.stringify(request),
  });
}

export async function getEntity(id: string): Promise<Entity> {
  return fetchJSON<Entity>(`/entities/${id}`);
}

export async function rescanEntity(id: string): Promise<{ status: string; entity_id: string }> {
  return fetchJSON(`/entities/${id}/rescan`, { method: 'POST' });
}

export async function generateAiReport(): Promise<{ status: string; report?: string; error?: string }> {
  return fetchJSON('/reports/generate', { method: 'POST' });
}

export async function generateEntityAiReport(entityName: string): Promise<{ status: string; report?: string; error?: string }> {
  return fetchJSON(`/reports/generate/${encodeURIComponent(entityName)}`, { method: 'POST' });
}

export async function deleteEntity(id: string): Promise<{ status: string }> {
  return fetchJSON(`/entities/${id}`, { method: 'DELETE' });
}

export async function deleteFinding(id: string): Promise<{ status: string }> {
  return fetchJSON(`/findings/${id}`, { method: 'DELETE' });
}

export async function deleteAlert(id: string): Promise<{ status: string }> {
  return fetchJSON(`/alerts/${id}`, { method: 'DELETE' });
}
