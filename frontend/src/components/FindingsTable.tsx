import type { Finding } from '../types';
import { Search, Filter, ChevronDown, Trash2 } from 'lucide-react';
import { useState } from 'react';

interface FindingsTableProps {
  findings: Finding[];
  compact?: boolean;
  onViewAll?: () => void;
  onDelete?: (id: string) => void;
}

const severityBadge: Record<string, string> = {
  critical: 'badge-critical',
  high: 'badge-high',
  medium: 'badge-medium',
  low: 'badge-low',
  info: 'badge-info',
};

export default function FindingsTable({ findings, compact, onViewAll, onDelete }: FindingsTableProps) {
  const [filter, setFilter] = useState<string>('all');
  const [search, setSearch] = useState('');

  const filtered = findings.filter((f) => {
    if (filter !== 'all' && f.severity !== filter) return false;
    if (search && !f.title.toLowerCase().includes(search.toLowerCase())) return false;
    return true;
  });

  const displayFindings = compact ? filtered.slice(0, 5) : filtered;

  return (
    <div className={`widget ${compact ? '' : 'h-full'}`}>
      <div className="widget-header">
        <h3 className="widget-title">Findings</h3>
        {onViewAll && (
          <button onClick={onViewAll} className="text-xs text-accent-cyan hover:underline font-medium">
            View All
          </button>
        )}
      </div>

      {!compact && (
        <div className="flex items-center gap-2 mb-4">
          <div className="relative flex-1">
            <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted" />
            <input
              type="text"
              placeholder="Search findings..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full h-9 pl-9 pr-3 bg-surface-200 border border-border rounded-lg text-sm text-text-primary
                         placeholder:text-text-muted focus:outline-none focus:border-accent-cyan/40 transition-colors"
            />
          </div>
          <div className="relative">
            <select
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              className="h-9 pl-3 pr-8 bg-surface-200 border border-border rounded-lg text-sm text-text-primary
                         appearance-none cursor-pointer focus:outline-none focus:border-accent-cyan/40 transition-colors"
            >
              <option value="all">All Severities</option>
              <option value="critical">Critical</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
              <option value="info">Info</option>
            </select>
            <ChevronDown size={14} className="absolute right-2.5 top-1/2 -translate-y-1/2 text-text-muted pointer-events-none" />
          </div>
        </div>
      )}

      <div className="space-y-2">
        {displayFindings.length === 0 && (
          <div className="py-8 text-center text-text-muted text-sm">
            No findings match your filter.
          </div>
        )}
        {displayFindings.map((f, i) => (
          <div
            key={`${f.id}-${i}`}
            className="flex items-start gap-3 p-3 rounded-lg bg-surface-50 border border-border
                       hover:border-border-light transition-colors group"
          >
            <span className={`${severityBadge[f.severity]} mt-0.5 shrink-0`}>
              {f.severity}
            </span>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-text-primary truncate">{f.title}</p>
              {!compact && (
                <p className="text-xs text-text-muted mt-0.5">
                  {f.entity_id || ''}
                  <span className="ml-2 text-text-muted/60">via {f.source_type}</span>
                </p>
              )}
            </div>
            <time className="text-[11px] text-text-muted shrink-0 mt-0.5 font-mono">
              {f.created_at
                ? new Date(f.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
                : '—'}
            </time>
            {onDelete && !compact && (
              <button
                onClick={() => onDelete(f.id)}
                className="shrink-0 p-1 rounded-md text-text-muted hover:text-accent-red hover:bg-red-500/10
                           transition-colors opacity-0 group-hover:opacity-100"
                title="Delete finding"
              >
                <Trash2 size={16} />
              </button>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
