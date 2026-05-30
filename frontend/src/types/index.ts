export interface Entity {
  id: string;
  name: string;
  entity_type: string;
  metadata: Record<string, any>;
  current_risk_score: number;
  last_assessed: string | null;
  scan_status: 'pending' | 'scanning' | 'completed' | 'failed';
  finding_count: number;
}

export interface MonitorRequest {
  url: string;
  name?: string;
  scan_config?: {
    scans: string[];
    compliance: string[];
    checks: string[];
  };
}

export interface Finding {
  id: string;
  finding_type: string;
  source_type: string;
  source_url: string;
  title: string;
  description: string;
  severity: string;
  entity_id?: string;
  status: string;
  risk_score: number;
  created_at: string;
  updated_at?: string;
  compliance?: { regulation: string; article: string; severity: string; description: string }[];
  check_type?: string;
  agent_meta?: { agent: string; step: number; method: string; brightdata_tool: string; classification: string };
}

export interface Alert {
  id: string;
  finding_id: string;
  alert_type: string;
  title: string;
  description: string;
  severity: string;
  channels: string[];
  status: string;
  created_at: string;
  notes?: string;
  acknowledged_at?: string;
  finding?: Finding;
  compliance?: { regulation: string; article: string; severity: string; description: string }[];
}

export interface InvestigationResult {
  id: string;
  indicator: string;
  indicator_type: string;
  verdict: string;
  confidence: number;
  evidence: { source: string; data_preview: string }[];
  affected_entities: string[];
  recommended_actions: string[];
  finding_type?: string;
  investigation_steps?: number;
  timestamp?: string;
}

export interface DashboardMetrics {
  total_findings: number;
  critical_findings: number;
  high_findings: number;
  medium_findings: number;
  low_findings: number;
  active_alerts: number;
  total_entities: number;
  avg_risk_score: number;
  severity_breakdown: { name: string; value: number; color: string }[];
  recent_findings: Finding[];
  timeline_data: { date: string; critical: number; high: number; medium: number; low: number }[];
  compliance_tagged?: number;
  security_only?: number;
  compliance_summary?: Record<string, {
    label: string;
    total: number;
    critical: number;
    high: number;
    medium: number;
    low: number;
    findings: { id: string; title: string; severity: string; article: string }[];
  }>;
}

export type NavPage = 'dashboard' | 'findings' | 'alerts' | 'entities' |  'compliance' | 'reports' | 'about' | 'hackathon';
