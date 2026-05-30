import { useEffect, useState, useMemo } from 'react';
import { getDashboardMetrics } from '../api/client';
import type { DashboardMetrics } from '../types';
import { Shield, CheckCircle, AlertTriangle, ExternalLink, Filter, ChevronDown } from 'lucide-react';
import PageMeta from '../components/PageMeta';

const regColors: Record<string, string> = {
  GDPR: 'border-blue-500/30',
  SOC2: 'border-accent-cyan/30',
  HIPAA: 'border-accent-red/30',
  PCI_DSS: 'border-accent-amber/30',
};

const regLabels: Record<string, string> = {
  GDPR: 'GDPR',
  SOC2: 'SOC 2',
  HIPAA: 'HIPAA',
  PCI_DSS: 'PCI DSS',
};

const sevColor = (s: string) =>
  s === 'critical' ? 'text-accent-red' :
  s === 'high' ? 'text-orange-400' :
  s === 'medium' ? 'text-accent-amber' : 'text-text-secondary';

export default function Compliance() {
  const [data, setData] = useState<DashboardMetrics | null>(null);
  const [unfilteredData, setUnfilteredData] = useState<DashboardMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedEntity, setSelectedEntity] = useState<string>('');
  const [dropdownOpen, setDropdownOpen] = useState(false);

  // Fetch unfiltered data once to get the entity list
  useEffect(() => {
    getDashboardMetrics()
      .then(setUnfilteredData)
      .catch(() => {});
  }, []);

  // Fetch filtered/unfiltered data when selection changes
  useEffect(() => {
    setLoading(true);
    getDashboardMetrics(selectedEntity || undefined)
      .then(setData)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [selectedEntity]);

  // Extract entities from unfiltered recent_findings
  const entities = useMemo(() => {
    const set = new Set<string>();
    for (const f of unfilteredData?.recent_findings ?? []) {
      if (f.entity_id) set.add(f.entity_id);
    }
    return Array.from(set).sort();
  }, [unfilteredData]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-2 border-accent-cyan border-t-transparent rounded-full animate-spin" />
          <p className="text-text-muted text-sm">Loading compliance data...</p>
        </div>
      </div>
    );
  }

  const summary = data?.compliance_summary ?? {};
  const regs = Object.entries(summary);

  return (
    <>
      <PageMeta id="compliance" description="Compliance analysis mapping security findings against regulatory frameworks."
        features={['Per-regulation severity breakdown (critical, high, medium, low)','Coverage by GDPR, SOC 2, HIPAA, and PCI DSS','Article-level finding mapping','Compliance gap analysis','Entity-level compliance filtering']}
        endpoints={['GET /api/v1/dashboard/summary']}
        technicalNotes="Findings auto-classified by ComplianceClassifier against regulatory keywords. Compliance summary computed server-side from all findings with compliance tags." />
      <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col items-center gap-3 text-center">
        <div>
          <h1 className="text-xl font-bold text-text-primary">Compliance Overview</h1>
          <p className="text-sm text-text-muted mt-1">
            Findings mapped to regulatory frameworks — {data?.compliance_tagged ?? 0} tagged findings across {regs.length} regulations
          </p>
        </div>
        {entities.length > 0 && (
          <div className="relative w-full max-w-xs mx-auto">
            <button
              onClick={() => setDropdownOpen(!dropdownOpen)}
              className="w-full flex items-center justify-between gap-2 px-4 h-11 bg-surface-100 border border-border-light rounded-xl
                         text-sm text-text-primary hover:border-accent-cyan/40 transition-all shadow-sm"
            >
              <Filter size={16} className="text-text-muted shrink-0" />
              <span className="flex-1 text-left">
                {!selectedEntity ? 'All Entities' : selectedEntity}
              </span>
              <ChevronDown size={16} className={`text-text-muted transition-transform ${dropdownOpen ? 'rotate-180' : ''}`} />
            </button>
            {dropdownOpen && (
              <>
                <div className="fixed inset-0 z-10" onClick={() => setDropdownOpen(false)} />
                <div className="absolute top-full left-0 right-0 mt-1 z-20 bg-surface-100 border border-border-light rounded-xl shadow-xl shadow-black/30 overflow-hidden">
                  <button
                    onClick={() => { setSelectedEntity(''); setDropdownOpen(false); }}
                    className={`w-full flex items-center gap-3 px-4 h-10 text-sm transition-colors hover:bg-surface-200 ${
                      !selectedEntity ? 'text-accent-cyan font-semibold bg-accent-cyan/5' : 'text-text-secondary'
                    }`}
                  >
                    <span className={`w-4 h-4 rounded border-2 flex items-center justify-center ${
                      !selectedEntity ? 'border-accent-cyan bg-accent-cyan/20' : 'border-border'
                    }`}>
                      {!selectedEntity && <span className="w-2 h-2 rounded-sm bg-accent-cyan" />}
                    </span>
                    All Entities
                  </button>
                  <div className="h-px bg-border mx-2" />
                  {entities.map((e) => (
                    <button
                      key={e}
                      onClick={() => { setSelectedEntity(e); setDropdownOpen(false); }}
                      className={`w-full flex items-center gap-3 px-4 h-10 text-sm transition-colors hover:bg-surface-200 ${
                        selectedEntity === e ? 'text-accent-cyan font-medium' : 'text-text-secondary'
                      }`}
                    >
                      <span className={`w-4 h-4 rounded border-2 flex items-center justify-center transition-colors ${
                        selectedEntity === e ? 'border-accent-cyan bg-accent-cyan/20' : 'border-border'
                      }`}>
                        {selectedEntity === e && <span className="w-2 h-2 rounded-sm bg-accent-cyan" />}
                      </span>
                      {e}
                    </button>
                  ))}
                </div>
              </>
            )}
          </div>
        )}
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {regs.map(([key, reg]) => (
          <div key={key} className={`widget border-l-4 ${regColors[key] || 'border-border'}`}>
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-semibold text-text-muted uppercase tracking-wider">{regLabels[key] || key}</span>
              <Shield size={16} className="text-text-muted/40" />
            </div>
            <p className="stat-value text-text-primary">{reg.total}</p>
            <div className="flex items-center gap-3 mt-1.5 text-[10px] font-mono">
              <span className="text-accent-red">{reg.critical}C</span>
              <span className="text-orange-400">{reg.high}H</span>
              <span className="text-accent-amber">{reg.medium}M</span>
              <span className="text-blue-400">{reg.low}L</span>
            </div>
          </div>
        ))}
      </div>

      {/* Detailed Findings per Regulation */}
      <div className="space-y-4">
        {regs.map(([key, reg]) => (
          <div key={key} className="widget">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-bold text-text-primary">{regLabels[key] || key}</h3>
              <span className="text-xs text-text-muted">{reg.total} findings</span>
            </div>
            {reg.findings.length === 0 ? (
              <p className="text-xs text-text-muted">No findings mapped to this regulation.</p>
            ) : (
              <div className="space-y-1.5">
                {reg.findings.slice(0, 20).map((f: any) => (
                  <div key={f.id} className="flex items-start gap-2 p-2 rounded bg-surface-200/50 text-xs">
                    <AlertTriangle size={12} className={`mt-0.5 shrink-0 ${sevColor(f.severity)}`} />
                    <div className="flex-1 min-w-0">
                      <p className="text-text-primary truncate">{f.title}</p>
                      <p className="text-text-muted/60 text-[10px] font-mono">{f.article}</p>
                    </div>
                    <span className={`text-[10px] font-mono font-semibold shrink-0 ${sevColor(f.severity)}`}>
                      {f.severity}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  </>);
}
