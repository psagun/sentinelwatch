import { useEffect, useState, useMemo, useCallback } from 'react';
import { getAlerts, deleteAlert, acknowledgeAlert } from '../api/client';
import type { Alert } from '../types';
import AlertList from '../components/AlertList';
import { Filter, ChevronDown, CheckSquare, Square, Trash2, CheckCircle2 } from 'lucide-react';

export default function Alerts() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedEntities, setSelectedEntities] = useState<string[]>([]);
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [batchLoading, setBatchLoading] = useState(false);

  useEffect(() => {
    getAlerts()
      .then(setAlerts)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const entities = useMemo(() => {
    const set = new Set<string>();
    for (const a of alerts) {
      if (a.finding?.entity_id) set.add(a.finding.entity_id);
    }
    return Array.from(set).sort();
  }, [alerts]);

  const toggleEntity = (entity: string) => {
    setSelectedEntities((prev) =>
      prev.includes(entity) ? prev.filter((e) => e !== entity) : [...prev, entity]
    );
  };

  const filtered = useMemo(() => {
    if (selectedEntities.length === 0) return alerts;
    return alerts.filter((a) => a.finding?.entity_id && selectedEntities.includes(a.finding.entity_id));
  }, [alerts, selectedEntities]);

  const toggleSelect = useCallback((id: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id); else next.add(id);
      return next;
    });
  }, []);

  const toggleSelectAll = useCallback(() => {
    setSelectedIds((prev) => {
      if (prev.size === filtered.length) return new Set();
      return new Set(filtered.map((a) => a.id));
    });
  }, [filtered]);

  const handleBatchAcknowledge = async () => {
    if (selectedIds.size === 0) return;
    setBatchLoading(true);
    for (const id of selectedIds) {
      try { await acknowledgeAlert(id); } catch { /* ignore */ }
    }
    setAlerts((prev) => prev.map((a) => selectedIds.has(a.id) ? { ...a, status: 'acknowledged' } : a));
    setSelectedIds(new Set());
    setBatchLoading(false);
  };

  const handleBatchDelete = async () => {
    if (selectedIds.size === 0 || !window.confirm(`Delete ${selectedIds.size} alert(s)?`)) return;
    setBatchLoading(true);
    for (const id of selectedIds) {
      try { await deleteAlert(id); } catch { /* ignore */ }
    }
    setAlerts((prev) => prev.filter((a) => !selectedIds.has(a.id)));
    setSelectedIds(new Set());
    setBatchLoading(false);
  };

  const handleDelete = async (id: string) => {
    if (!window.confirm('Delete this alert?')) return;
    try {
      await deleteAlert(id);
      setAlerts((prev) => prev.filter((a) => a.id !== id));
    } catch {
      // ignore
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-2 border-accent-cyan border-t-transparent rounded-full animate-spin" />
          <p className="text-text-muted text-sm">Loading alerts...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col items-center gap-3 text-center">
        <div>
          <h1 className="text-xl font-bold text-text-primary">Alerts</h1>
          <p className="text-sm text-text-muted mt-1">
            Security alerts requiring attention
            {alerts.length > 0 && (
              <span className="ml-2 text-text-muted/60">
                ({alerts.length} total, {alerts.filter((a) => a.status !== 'acknowledged').length} unacknowledged)
              </span>
            )}
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
                {selectedEntities.length === 0
                  ? 'All Entities'
                  : `${selectedEntities.length} entity${selectedEntities.length > 1 ? 'ies' : ''} selected`}
              </span>
              <span className="text-xs text-text-muted font-medium">
                {selectedEntities.length > 0 ? `(${selectedEntities.length})` : ''}
              </span>
              <ChevronDown size={16} className={`text-text-muted transition-transform ${dropdownOpen ? 'rotate-180' : ''}`} />
            </button>

            {dropdownOpen && (
              <>
                <div className="fixed inset-0 z-10" onClick={() => setDropdownOpen(false)} />
                <div className="absolute top-full left-0 right-0 mt-1 z-20 bg-surface-100 border border-border-light rounded-xl shadow-xl shadow-black/30 overflow-hidden">
                  <button
                    onClick={() => { setSelectedEntities([]); setDropdownOpen(false); }}
                    className={`w-full flex items-center gap-3 px-4 h-10 text-sm transition-colors hover:bg-surface-200 ${
                      selectedEntities.length === 0 ? 'text-accent-cyan font-semibold bg-accent-cyan/5' : 'text-text-secondary'
                    }`}
                  >
                    <span className={`w-4 h-4 rounded border-2 flex items-center justify-center ${
                      selectedEntities.length === 0 ? 'border-accent-cyan bg-accent-cyan/20' : 'border-border'
                    }`}>
                      {selectedEntities.length === 0 && <span className="w-2 h-2 rounded-sm bg-accent-cyan" />}
                    </span>
                    All Entities
                  </button>
                  <div className="h-px bg-border mx-2" />
                  {entities.map((e) => (
                    <button
                      key={e}
                      onClick={() => toggleEntity(e)}
                      className={`w-full flex items-center gap-3 px-4 h-10 text-sm transition-colors hover:bg-surface-200 ${
                        selectedEntities.includes(e) ? 'text-accent-cyan font-medium' : 'text-text-secondary'
                      }`}
                    >
                      <span className={`w-4 h-4 rounded border-2 flex items-center justify-center transition-colors ${
                        selectedEntities.includes(e) ? 'border-accent-cyan bg-accent-cyan/20' : 'border-border'
                      }`}>
                        {selectedEntities.includes(e) && <span className="w-2 h-2 rounded-sm bg-accent-cyan" />}
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
      {/* Batch Actions Bar */}
      {selectedIds.size > 0 && (
        <div className="flex items-center justify-between p-3 bg-accent-cyan/5 border border-accent-cyan/20 rounded-xl">
          <div className="flex items-center gap-3">
            <button onClick={toggleSelectAll} className="text-text-muted hover:text-text-primary transition-colors">
              <CheckSquare size={18} />
            </button>
            <span className="text-sm font-medium text-text-primary">{selectedIds.size} selected</span>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handleBatchAcknowledge}
              disabled={batchLoading}
              className="flex items-center gap-1.5 px-3 h-8 rounded-lg text-xs font-medium bg-accent-green/10 text-accent-green border border-accent-green/20
                         hover:bg-accent-green/20 transition-all disabled:opacity-40"
            >
              <CheckCircle2 size={14} />
              Acknowledge All
            </button>
            <button
              onClick={handleBatchDelete}
              disabled={batchLoading}
              className="flex items-center gap-1.5 px-3 h-8 rounded-lg text-xs font-medium bg-accent-red/10 text-accent-red border border-accent-red/20
                         hover:bg-accent-red/20 transition-all disabled:opacity-40"
            >
              <Trash2 size={14} />
              Delete All
            </button>
          </div>
        </div>
      )}

      <AlertList
        alerts={filtered}
        onDelete={handleDelete}
        selectedIds={selectedIds}
        onToggleSelect={toggleSelect}
        onToggleSelectAll={toggleSelectAll}
      />
    </div>
  );
}
