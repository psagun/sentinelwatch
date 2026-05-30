import { useEffect, useState, useRef, useCallback } from 'react';
import { getEntities, rescanEntity, deleteEntity } from '../api/client';
import type { Entity } from '../types';
import { Globe, Search, Plus, RotateCw, ExternalLink, AlertTriangle, Shield, Trash2 } from 'lucide-react';
import AddEntityModal from '../components/AddEntityModal';

const riskColor = (score: number) =>
  score >= 70 ? 'text-accent-red' : score >= 40 ? 'text-accent-amber' : 'text-accent-green';

const riskBg = (score: number) =>
  score >= 70 ? 'bg-red-500/10 border-red-500/20' : score >= 40
    ? 'bg-amber-500/10 border-amber-500/20'
    : 'bg-green-500/10 border-green-500/20';

const riskLabel = (score: number) =>
  score >= 70 ? 'High Risk' : score >= 40 ? 'Medium Risk' : 'Low Risk';

const scanBadge: Record<string, { label: string; class: string }> = {
  pending:   { label: 'Pending',   class: 'bg-slate-500/10 text-text-secondary border-slate-500/20' },
  scanning:  { label: 'Scanning',  class: 'bg-amber-500/10 text-accent-amber border-accent-amber/20' },
  completed: { label: 'Completed', class: 'bg-green-500/10 text-accent-green border-green-500/20' },
  failed:    { label: 'Failed',    class: 'bg-red-500/10 text-accent-red border-red-500/20' },
};

export default function Entities() {
  const [entities, setEntities] = useState<Entity[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [showAddModal, setShowAddModal] = useState(false);
  const [deleting, setDeleting] = useState<string | null>(null);
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const fetchEntities = useCallback(async () => {
    try {
      const data = await getEntities();
      setEntities(data);
    } catch {
      // keep current state on error
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchEntities();
  }, [fetchEntities]);

  // Auto-poll every 3s when any entity is scanning
  useEffect(() => {
    const hasScanning = entities.some((e) => e.scan_status === 'pending' || e.scan_status === 'scanning');
    if (hasScanning) {
      pollingRef.current = setInterval(fetchEntities, 3000);
      return () => {
        if (pollingRef.current) clearInterval(pollingRef.current);
      };
    }
  }, [entities, fetchEntities]);

  const handleRescan = async (id: string) => {
    try {
      await rescanEntity(id);
      setEntities((prev) =>
        prev.map((e) => (e.id === id ? { ...e, scan_status: 'scanning' as const } : e)),
      );
    } catch {
      // ignore
    }
  };

  const handleDelete = async (id: string) => {
    setDeleting(id);
    try {
      await deleteEntity(id);
      setEntities((prev) => prev.filter((e) => e.id !== id));
    } catch {
      // ignore
    } finally {
      setDeleting(null);
    }
  };

  const filtered = entities.filter((e) =>
    e.name.toLowerCase().includes(search.toLowerCase()),
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-2 border-accent-cyan border-t-transparent rounded-full animate-spin" />
          <p className="text-text-muted text-sm">Loading entities...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-text-primary">Monitored Entities</h1>
          <p className="text-sm text-text-muted mt-1">
            Websites and services under security monitoring
          </p>
        </div>
        <button
          onClick={() => setShowAddModal(true)}
          className="shrink-0 h-10 flex items-center gap-2 px-4 rounded-lg font-semibold text-sm
                     bg-accent-cyan text-surface hover:bg-accent-cyan/90 transition-all shadow-lg shadow-accent-cyan/10"
        >
          <Plus size={16} />
          Add Website
        </button>
      </div>

      <div className="relative max-w-md">
        <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted" />
        <input
          type="text"
          placeholder="Search entities..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full h-10 pl-9 pr-3 bg-surface-100 border border-border rounded-lg text-sm text-text-primary
                     placeholder:text-text-muted focus:outline-none focus:border-accent-cyan/40 transition-colors"
        />
      </div>

      {/* Empty state: no entities at all */}
      {entities.length === 0 && (
        <div className="widget py-16 text-center">
          <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-surface-200 border border-border flex items-center justify-center">
            <Shield size={32} className="text-text-muted/30" />
          </div>
          <h3 className="text-base font-bold text-text-primary mb-1">No websites monitored yet</h3>
          <p className="text-sm text-text-muted mb-5 max-w-sm mx-auto">
            Add your first website to start monitoring for security threats, vulnerabilities, and compliance issues.
          </p>
          <button
            onClick={() => setShowAddModal(true)}
            className="inline-flex h-10 items-center gap-2 px-5 rounded-lg font-semibold text-sm
                       bg-accent-cyan text-surface hover:bg-accent-cyan/90 transition-all"
          >
            <Plus size={16} />
            Add Your First Website
          </button>
        </div>
      )}

      {/* Empty state: filter no results */}
      {entities.length > 0 && filtered.length === 0 && (
        <div className="py-16 text-center">
          <Globe size={40} className="mx-auto mb-3 text-text-muted/30" />
          <p className="text-text-muted text-sm">No entities match your search.</p>
        </div>
      )}

      {/* Entity grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filtered.map((entity) => {
          const isScanning = entity.scan_status === 'pending' || entity.scan_status === 'scanning';
          const badge = scanBadge[entity.scan_status] ?? scanBadge.pending;

          return (
            <div
              key={entity.id}
              className="widget group hover:border-accent-cyan/20 transition-all relative pt-4 pb-4"
            >
              {/* Top row: icon + name + scan status */}
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-accent-purple/15 flex items-center justify-center">
                    <Globe size={18} className="text-accent-purple" />
                  </div>
                  <div>
                    <h3 className="text-sm font-semibold text-text-primary">{entity.name}</h3>
                    <p className="text-[11px] text-text-muted capitalize">{entity.entity_type}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span
                    className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded text-[10px] font-semibold border ${badge.class} ${
                      entity.scan_status === 'scanning' ? 'animate-pulse' : ''
                    }`}
                  >
                    {entity.scan_status === 'scanning' && (
                      <span className="w-1.5 h-1.5 rounded-full bg-accent-amber" />
                    )}
                    {entity.scan_status === 'failed' && (
                      <AlertTriangle size={10} />
                    )}
                    {badge.label}
                  </span>
                  <div className={`px-2.5 py-1 rounded-md text-xs font-bold font-mono border ${riskBg(entity.current_risk_score)} ${riskColor(entity.current_risk_score)}`}>
                    {entity.current_risk_score.toFixed(0)}
                  </div>
                </div>
              </div>

              {/* Risk label */}
              <div className="flex items-center gap-2 mb-3">
                <span className={`text-[11px] font-semibold ${riskColor(entity.current_risk_score)}`}>
                  {riskLabel(entity.current_risk_score)}
                </span>
                {entity.finding_count > 0 && (
                  <>
                    <span className="text-text-muted/30">·</span>
                    <span className="font-mono text-[11px] text-text-secondary">
                      {entity.finding_count} finding{entity.finding_count !== 1 ? 's' : ''}
                    </span>
                  </>
                )}
              </div>

              {/* Bottom info bar */}
              <div className="flex items-center justify-between text-xs text-text-muted border-t border-border pt-3">
                <div className="flex items-center gap-2">
                  <span className="font-mono text-[11px] text-text-muted/70">
                    {(() => {
                      const u = entity.metadata?.url || '';
                      try { return new URL(u.startsWith('http') ? u : 'https://' + u).hostname.replace(/^www\./, ''); }
                      catch { return entity.metadata?.domains?.join(', ') || u || '—'; }
                    })()}
                  </span>
                  {entity.finding_count > 0 && (
                    <>
                      <span className="text-text-muted/30">·</span>
                      <span className="font-mono text-[11px] text-text-secondary">
                        {entity.finding_count} finding{entity.finding_count !== 1 ? 's' : ''}
                      </span>
                    </>
                  )}
                </div>
                <div className="flex items-center gap-1.5">
                  <button
                    onClick={() => handleRescan(entity.id)}
                    disabled={isScanning}
                    className="p-1.5 rounded-md text-text-muted hover:text-accent-cyan hover:bg-accent-cyan/10
                               transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
                    title={isScanning ? 'Already scanning' : 'Rescan'}
                  >
                    <RotateCw size={14} className={isScanning ? 'animate-spin' : ''} />
                  </button>
                  <button
                    onClick={() => {
                      if (window.confirm(`Remove "${entity.name}" and all its findings?`)) {
                        handleDelete(entity.id);
                      }
                    }}
                    disabled={deleting === entity.id}
                    className="p-1.5 rounded-md text-text-muted hover:text-accent-red hover:bg-red-500/10
                               transition-colors disabled:opacity-30"
                    title="Delete entity"
                  >
                    <Trash2 size={18} />
                  </button>
                  <span>
                    {entity.last_assessed
                      ? new Date(entity.last_assessed).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
                      : '—'}
                  </span>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      <AddEntityModal
        open={showAddModal}
        onClose={() => setShowAddModal(false)}
        onComplete={() => fetchEntities()}
      />
    </div>
  );
}
