import { useEffect, useState } from 'react';
import { listCompletedInvestigations, runInvestigation } from '../api/client';
import type { InvestigationResult } from '../types';
import { FlaskConical, ExternalLink, AlertCircle, Play, Search } from 'lucide-react';

const confColor = (c: number) =>
  c >= 0.7 ? 'text-accent-green' : c >= 0.4 ? 'text-accent-amber' : 'text-accent-red';

const confBg = (c: number) =>
  c >= 0.7 ? 'bg-green-500/10 border-green-500/20' : c >= 0.4
    ? 'bg-amber-500/10 border-amber-500/20'
    : 'bg-red-500/10 border-red-500/20';

const INDICATOR_TYPES = [
  { value: 'ip', label: 'IP Address' },
  { value: 'domain', label: 'Domain' },
  { value: 'url', label: 'URL' },
  { value: 'hash', label: 'File Hash' },
  { value: 'organization', label: 'Organization' },
  { value: 'email', label: 'Email' },
];

export default function Investigations() {
  const [investigations, setInvestigations] = useState<InvestigationResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [target, setTarget] = useState('');
  const [indicatorType, setIndicatorType] = useState('ip');

  const load = () =>
    listCompletedInvestigations()
      .then(setInvestigations)
      .catch(console.error)
      .finally(() => setLoading(false));

  useEffect(() => {
    load();
  }, []);

  const handleRun = async () => {
    const indicator = target.trim() || 'Bright Data';
    const iType = target.trim() ? indicatorType : 'organization';
    setRunning(true);
    try {
      const result = await runInvestigation(indicator, iType);
      setInvestigations((prev) => [result, ...prev]);
      setTarget('');
    } catch (e) {
      console.error(e);
    } finally {
      setRunning(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') handleRun();
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-2 border-accent-cyan border-t-transparent rounded-full animate-spin" />
          <p className="text-text-muted text-sm">Loading investigations...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-text-primary">AI Investigations</h1>
          <p className="text-sm text-text-muted mt-1">
            AI-powered deep-dive analysis results using Bright Data intelligence
          </p>
        </div>
      </div>

      {/* Investigation input bar */}
      <div className="widget">
        <div className="flex items-center gap-3">
          <div className="relative flex-1">
            <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted" />
            <input
              type="text"
              value={target}
              onChange={(e) => setTarget(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Enter IP, domain, URL, hash, or organization to investigate..."
              className="w-full h-10 pl-9 pr-3 bg-surface-200 border border-border rounded-lg
                         text-sm text-text-primary placeholder:text-text-muted/40
                         focus:outline-none focus:border-accent-cyan/50 transition-colors"
            />
          </div>
          <select
            value={indicatorType}
            onChange={(e) => setIndicatorType(e.target.value)}
            className="h-10 px-3 bg-surface-200 border border-border rounded-lg
                       text-sm text-text-primary focus:outline-none focus:border-accent-cyan/50"
          >
            {INDICATOR_TYPES.map((t) => (
              <option key={t.value} value={t.value}>{t.label}</option>
            ))}
          </select>
          <button
            onClick={handleRun}
            disabled={running}
            className="flex items-center gap-2 px-5 h-10 bg-accent-cyan/10 border border-accent-cyan/20 rounded-lg
                       text-sm font-medium text-accent-cyan hover:bg-accent-cyan/20 transition-all
                       disabled:opacity-40 shrink-0"
          >
            <Play size={14} />
            {running ? 'Running...' : 'Investigate'}
          </button>
        </div>
        <p className="text-xs text-text-muted/60 mt-2">
          {target.trim()
            ? `Will investigate "${target.trim()}" as a ${INDICATOR_TYPES.find(t => t.value === indicatorType)?.label || indicatorType}`
            : 'Default: investigates "Bright Data" as an organization'}
        </p>
      </div>

      {investigations.length === 0 && (
        <div className="py-16 text-center">
          <FlaskConical size={40} className="mx-auto mb-3 text-text-muted/30" />
          <p className="text-text-muted text-sm">No investigations have been run yet.</p>
          <p className="text-text-muted/60 text-xs mt-1">
            Type a target above and click "Investigate" to begin.
          </p>
        </div>
      )}

      <div className="space-y-4">
        {investigations.map((inv, i) => (
          <div
            key={inv.id ?? i}
            className="widget animate-fade-in"
            style={{ animationDelay: `${i * 0.1}s` }}
          >
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-lg bg-accent-cyan/15 flex items-center justify-center">
                  <FlaskConical size={16} className="text-accent-cyan" />
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-text-primary">{inv.indicator}</h3>
                  <p className="text-xs text-text-muted capitalize">
                    {inv.indicator_type} &middot; {inv.verdict}
                  </p>
                </div>
              </div>
              <div
                className={`px-2.5 py-1 rounded-md text-xs font-bold font-mono border ${confBg(inv.confidence)} ${confColor(inv.confidence)}`}
              >
                {Math.round(inv.confidence * 100)}% confidence
              </div>
            </div>

            {inv.evidence && inv.evidence.length > 0 && (
              <div className="mb-4">
                <p className="text-xs font-semibold text-text-muted uppercase tracking-wider mb-2">
                  Evidence ({inv.evidence.length} items)
                </p>
                <div className="flex flex-wrap gap-2">
                  {inv.evidence.map((ev, j) => (
                    <span
                      key={j}
                      className="inline-flex items-center gap-1 px-2 py-1 text-xs rounded-md
                                 bg-surface-200 text-text-secondary border border-border"
                    >
                      <ExternalLink size={10} />
                      {ev.source}: {ev.data_preview || 'No data'}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {inv.recommended_actions && inv.recommended_actions.length > 0 && (
              <div>
                <p className="text-xs font-semibold text-text-muted uppercase tracking-wider mb-2">
                  Recommendations
                </p>
                <ul className="space-y-1">
                  {inv.recommended_actions.map((rec, j) => (
                    <li key={j} className="flex items-start gap-2 text-xs text-text-secondary">
                      <AlertCircle size={12} className="mt-0.5 shrink-0 text-accent-cyan" />
                      {rec}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
