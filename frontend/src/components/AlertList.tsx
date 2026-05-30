import type { Alert } from '../types';
import { Bell, CheckCircle2, Trash2, ChevronDown, ChevronRight, Shield, ExternalLink, Square, CheckSquare } from 'lucide-react';
import { acknowledgeAlert } from '../api/client';
import { useState, useEffect } from 'react';

interface AlertListProps {
  alerts: Alert[];
  onDelete?: (id: string) => void;
  selectedIds?: Set<string>;
  onToggleSelect?: (id: string) => void;
  onToggleSelectAll?: () => void;
}

const severityDot: Record<string, string> = {
  critical: 'bg-accent-red shadow-[0_0_6px_rgba(239,68,68,0.5)]',
  high: 'bg-orange-500 shadow-[0_0_6px_rgba(249,115,22,0.4)]',
  medium: 'bg-accent-amber shadow-[0_0_6px_rgba(245,158,11,0.4)]',
  low: 'bg-blue-400',
  info: 'bg-slate-400',
};

const regColors: Record<string, string> = {
  GDPR: 'text-blue-400 bg-blue-500/10 border-blue-500/20',
  SOC2: 'text-accent-cyan bg-accent-cyan/10 border-accent-cyan/20',
  HIPAA: 'text-accent-red bg-red-500/10 border-red-500/20',
  PCI_DSS: 'text-accent-amber bg-amber-500/10 border-amber-500/20',
};

export default function AlertList({ alerts, onDelete, selectedIds, onToggleSelect, onToggleSelectAll }: AlertListProps) {
  const [local, setLocal] = useState(alerts);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [acknowledgingId, setAcknowledgingId] = useState<string | null>(null);
  const [notesInput, setNotesInput] = useState('');
  const unacknowledged = local.filter((a) => a.status !== 'acknowledged');

  // Sync local state when alerts prop changes (e.g. filter applied)
  useEffect(() => {
    setLocal(alerts);
    setExpandedId(null);
  }, [alerts]);

  const handleAck = async (id: string) => {
    setAcknowledgingId(id);
    setNotesInput('');
  };

  const submitAck = async () => {
    const id = acknowledgingId;
    if (!id) return;
    try {
      await acknowledgeAlert(id, notesInput || undefined);
      setLocal((prev) => prev.map((a) =>
        a.id === id ? { ...a, status: 'acknowledged', notes: notesInput || undefined } : a
      ));
      setAcknowledgingId(null);
      setNotesInput('');
    } catch {
      // ignore
    }
  };

  const toggleExpand = (id: string) => {
    setExpandedId((prev) => (prev === id ? null : id));
  };

  if (local.length === 0) {
    return (
      <div className="widget">
        <div className="widget-header">
          <h3 className="widget-title">Active Alerts</h3>
        </div>
        <div className="py-10 text-center text-text-muted text-sm">
          <Bell size={32} className="mx-auto mb-2 opacity-30" />
          No active alerts
        </div>
      </div>
    );
  }

  return (
    <div className="widget">
      <div className="widget-header">
        <div className="flex items-center gap-2">
          {onToggleSelect && onToggleSelectAll && (
            <button onClick={onToggleSelectAll} className="text-text-muted hover:text-text-primary transition-colors">
              {selectedIds && selectedIds.size === local.length && local.length > 0 ? <CheckSquare size={16} /> : <Square size={16} />}
            </button>
          )}
          <h3 className="widget-title">Active Alerts</h3>
        </div>
        {unacknowledged.length > 0 && (
          <span className="badge-critical text-[10px]">{unacknowledged.length} unack</span>
        )}
      </div>
      <div className="space-y-2">
        {local.map((alert) => {
          const acknowledged = alert.status === 'acknowledged';
          const isExpanded = expandedId === alert.id;
          const finding = alert.finding;
          const compliance = alert.compliance ?? [];

          return (
            <div key={alert.id}>
              {/* Alert header (always visible, clickable) */}
              <div
                className={`flex items-start gap-2 p-3 rounded-lg border transition-all cursor-pointer ${
                  acknowledged
                    ? 'bg-surface-50 border-border opacity-50'
                    : 'bg-surface-50 border-border-light hover:border-accent-cyan/20'
                } ${isExpanded ? 'rounded-b-none border-b-0' : ''}`}
              >
                {onToggleSelect && (
                  <button
                    onClick={(e) => { e.stopPropagation(); onToggleSelect(alert.id); }}
                    className="mt-1 text-text-muted hover:text-text-primary shrink-0"
                  >
                    {selectedIds?.has(alert.id) ? <CheckSquare size={16} /> : <Square size={16} />}
                  </button>
                )}
                <span className={`w-2 h-2 rounded-full mt-1.5 shrink-0 ${severityDot[alert.severity]}`} />
                <div className="flex-1 min-w-0" onClick={() => toggleExpand(alert.id)}>
                  <p className={`text-sm font-medium ${acknowledged ? 'text-text-muted' : 'text-text-primary'}`}>
                    {alert.title}
                  </p>
                  <p className="text-xs text-text-muted mt-0.5 line-clamp-1">{alert.description}</p>
                  <div className="flex items-center gap-3 mt-1.5">
                    {alert.finding?.entity_id && (
                      <span className="text-[10px] text-accent-cyan font-medium">{alert.finding.entity_id}</span>
                    )}
                    <span className="text-[10px] font-mono text-text-muted/60">
                      {new Date(alert.created_at).toLocaleDateString('en-US', {
                        month: 'short',
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                    </span>
                    <span className="text-[10px] text-text-muted/60">{alert.alert_type}</span>
                  </div>
                </div>
                <div className="flex items-center gap-1 shrink-0">
                  {!acknowledged && acknowledgingId !== alert.id && (
                    <button
                      onClick={(e) => { e.stopPropagation(); handleAck(alert.id); }}
                      className="p-2 rounded-md text-text-muted hover:text-accent-green hover:bg-accent-green/10 transition-colors"
                      title="Mark as fixed"
                    >
                      <CheckCircle2 size={20} />
                    </button>
                  )}
                  {onDelete && (
                    <button
                      onClick={(e) => { e.stopPropagation(); onDelete(alert.id); }}
                      className="p-2 rounded-md text-text-muted hover:text-accent-red hover:bg-red-500/10 transition-colors"
                      title="Delete alert"
                    >
                      <Trash2 size={18} />
                    </button>
                  )}
                  {isExpanded ? <ChevronDown size={16} className="text-text-muted" /> : <ChevronRight size={16} className="text-text-muted" />}
                </div>
              </div>

              {/* Notes popup */}
              {acknowledgingId === alert.id && (
                <div className="p-3 border border-t-0 border-border-light bg-surface-200/50 rounded-b-lg space-y-2">
                  <p className="text-xs font-semibold text-text-muted">Add resolution notes (optional):</p>
                  <textarea
                    value={notesInput}
                    onChange={(e) => setNotesInput(e.target.value)}
                    placeholder="e.g. Fixed by rotating API key, deployed WAF rule..."
                    className="w-full h-20 px-3 py-2 bg-surface-100 border border-border rounded-lg text-xs text-text-primary
                               placeholder:text-text-muted/40 resize-none focus:outline-none focus:border-accent-cyan/40 transition-colors"
                    autoFocus
                  />
                  <div className="flex items-center gap-2 justify-end">
                    <button
                      onClick={() => setAcknowledgingId(null)}
                      className="px-3 h-7 text-xs rounded-md text-text-muted hover:text-text-primary hover:bg-surface-300 transition-colors"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={submitAck}
                      className="px-3 h-7 text-xs rounded-md bg-accent-green/10 text-accent-green border border-accent-green/20
                                 hover:bg-accent-green/20 transition-colors font-medium"
                    >
                      Confirm Fix
                    </button>
                  </div>
                </div>
              )}

              {/* Expanded details */}
              {(isExpanded && acknowledgingId !== alert.id) && (
                <div className="p-3 rounded-b-lg border border-t-0 border-border-light bg-surface-200/50 space-y-3 text-xs">
                  {/* Source Finding */}
                  {finding && (
                    <div>
                      <p className="font-semibold text-text-muted uppercase tracking-wider mb-1.5 flex items-center gap-1">
                        <Shield size={11} /> Source Finding
                      </p>
                      <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-text-secondary">
                        <span>Title: <span className="text-text-primary">{finding.title}</span></span>
                        <span>Entity: <span className="text-text-primary">{finding.entity_id || '—'}</span></span>
                        <span>Source: <span className="text-text-primary">{finding.source_type || '—'}</span></span>
                        <span>Risk Score: <span className="text-text-primary">{finding.risk_score ?? '—'}</span></span>
                        <span>Severity: <span className={`font-semibold ${
                          finding.severity === 'critical' ? 'text-accent-red' :
                          finding.severity === 'high' ? 'text-orange-400' :
                          finding.severity === 'medium' ? 'text-accent-amber' : 'text-text-primary'
                        }`}>{finding.severity}</span></span>
                        <span>Check: <span className="text-text-primary">{finding.check_type || '—'}</span></span>
                      </div>
                    </div>
                  )}

                  {/* Compliance Tags */}
                  {compliance.length > 0 && (
                    <div>
                      <p className="font-semibold text-text-muted uppercase tracking-wider mb-1.5">Compliance Impact</p>
                      <div className="flex flex-wrap gap-1.5">
                        {compliance.map((c, i) => (
                          <span
                            key={i}
                            className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-medium border ${
                              regColors[c.regulation] || 'text-text-secondary bg-surface-200 border-border'
                            }`}
                          >
                            {c.regulation === 'GDPR' ? 'GDPR' :
                             c.regulation === 'SOC2' ? 'SOC 2' :
                             c.regulation === 'HIPAA' ? 'HIPAA' :
                             c.regulation === 'PCI_DSS' ? 'PCI DSS' : c.regulation}
                            {' '}{c.article}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Resolution Notes */}
                  {alert.notes && (
                    <div>
                      <p className="font-semibold text-text-muted uppercase tracking-wider mb-1">Resolution Notes</p>
                      <p className="text-text-secondary bg-surface-100 rounded p-2 leading-relaxed">{alert.notes}</p>
                      {alert.acknowledged_at && (
                        <p className="text-[10px] text-text-muted/60 mt-1">
                          Resolved: {new Date(alert.acknowledged_at).toLocaleString()}
                        </p>
                      )}
                    </div>
                  )}

                  {/* Source Link */}
                  {finding?.source_url && (
                    <div>
                      <p className="font-semibold text-text-muted uppercase tracking-wider mb-1">Source</p>
                      <a
                        href={finding.source_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-xs text-accent-cyan hover:underline flex items-center gap-1 break-all"
                      >
                        <ExternalLink size={11} />
                        {finding.source_url}
                      </a>
                    </div>
                  )}

                  {/* Meta */}
                  <div className="flex items-center gap-3 text-text-muted pt-1">
                    <span>Alert ID: <code className="text-text-secondary font-mono">{alert.id.slice(0, 8)}…</code></span>
                    <span>Finding ID: <code className="text-text-secondary font-mono">{alert.finding_id.slice(0, 8)}…</code></span>
                    <span className="capitalize">Channels: {alert.channels?.join(', ') || '—'}</span>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
