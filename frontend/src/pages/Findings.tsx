import { useEffect, useState } from 'react';
import { getFindings, deleteFinding } from '../api/client';
import type { Finding } from '../types';
import FindingsTable from '../components/FindingsTable';
import PageMeta from '../components/PageMeta';

export default function Findings() {
  const [findings, setFindings] = useState<Finding[]>([]);
  const [loading, setLoading] = useState(true);
  const [displayCount, setDisplayCount] = useState(20);

  useEffect(() => {
    getFindings({ limit: 100 })
      .then(setFindings)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const handleDelete = async (id: string) => {
    if (!window.confirm('Delete this finding?')) return;
    try {
      await deleteFinding(id);
      setFindings((prev) => prev.filter((f) => f.id !== id));
    } catch {
      // ignore
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-2 border-accent-cyan border-t-transparent rounded-full animate-spin" />
          <p className="text-text-muted text-sm">Loading findings...</p>
        </div>
      </div>
    );
  }

  return (
    <>
      <PageMeta id="findings" description="All security findings across monitored entities with severity classification, compliance tags, and AI analysis."
        features={['Severity filtering (critical, high, medium, low, info)','Entity filtering','Paginated list with Load More','Individual finding deletion','Compliance classification tags','Source type identification']}
        endpoints={['GET /api/v1/findings','DELETE /api/v1/findings/{id}']}
        technicalNotes="Findings come from Bright Data collectors (Web Unlocker, SERP, Scraping Browser) and are enriched by AnalysisAgent (AI/ML API). Supports query params: severity, entity_id, finding_type, limit, offset." />
      <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-xl font-bold text-text-primary">Findings</h1>
        <p className="text-sm text-text-muted mt-1">
          All security findings across monitored entities
          {findings.length > 0 && (
            <span className="ml-2 text-text-muted/60">
              ({findings.length} total)
            </span>
          )}
        </p>
      </div>
      <FindingsTable findings={findings.slice(0, displayCount)} onDelete={handleDelete} />
      {findings.length > displayCount && (
        <div className="flex justify-center pt-2">
          <button
            onClick={() => setDisplayCount((prev) => prev + 20)}
            className="px-6 h-10 bg-surface-200 border border-border rounded-lg text-sm font-medium
                       text-text-secondary hover:text-text-primary hover:border-accent-cyan/30
                       transition-all"
          >
            Load More ({findings.length - displayCount} remaining)
          </button>
        </div>
      )}
    </div>
  </>);
}
