import { useEffect, useState, useMemo, useCallback } from 'react';
import { getDashboardMetrics } from '../api/client';
import type { DashboardMetrics } from '../types';
import StatCard from '../components/StatCard';
import SeverityChart from '../components/SeverityChart';
import FindingsTable from '../components/FindingsTable';
import TimelineChart from '../components/TimelineChart';
import AlertList from '../components/AlertList';
import RiskGauge from '../components/RiskGauge';
import { getAlerts } from '../api/client';
import type { Alert } from '../types';
import { Shield, AlertTriangle, Globe, Activity, CheckCircle, Filter, Bug, ChevronDown } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export default function Dashboard() {
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedEntities, setSelectedEntities] = useState<string[]>([]);
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const navigate = useNavigate();

  // Fetch data — re-fetches from backend when entity selection changes
  const fetchData = useCallback(async (entities: string[]) => {
    setLoading(true);
    try {
      // When a single entity is selected, pass entity_id to backend for server-side filter
      const entityParam = entities.length === 1 ? entities[0] : undefined;
      const [m, a] = await Promise.all([
        getDashboardMetrics(entityParam),
        getAlerts(),
      ]);
      setMetrics(m);
      setAlerts(a);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData(selectedEntities);
  }, [selectedEntities, fetchData]);

  // Extract entity names from metrics findings for the filter dropdown
  const entities = useMemo(() => {
    const set = new Set<string>();
    for (const f of metrics?.recent_findings ?? []) {
      if (f.entity_id) set.add(f.entity_id);
    }
    return Array.from(set).sort();
  }, [metrics]);

  // Filter alerts locally based on selected entities
  const filteredAlerts = useMemo(() => {
    if (selectedEntities.length === 0) return alerts;
    return alerts.filter((a) => {
      if (!a.finding?.entity_id) return false;
      return selectedEntities.some((e) => e.trim() === a.finding!.entity_id!.trim());
    });
  }, [alerts, selectedEntities]);

  const toggleEntity = (entity: string) => {
    setSelectedEntities((prev) =>
      prev.includes(entity) ? prev.filter((e) => e !== entity) : [...prev, entity]
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-2 border-accent-cyan border-t-transparent rounded-full animate-spin" />
          <p className="text-text-muted text-sm">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  if (!metrics) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-text-muted text-sm">Failed to load dashboard data.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header with entity filter */}
      <div className="flex flex-col items-center gap-3 text-center">
        <div>
          <h1 className="text-xl font-bold text-text-primary">Security Dashboard</h1>
          <p className="text-sm text-text-muted mt-1">
            Real-time security posture overview for your monitored entities
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
                  : `${entities.find(e => selectedEntities.includes(e)) || selectedEntities.length + ' selected'}`}
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
                      onClick={() => {
                        // Single select: select only this entity
                        setSelectedEntities(prev =>
                          prev.includes(e) ? [] : [e]
                        );
                        setDropdownOpen(false);
                      }}
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

      {/* Stat Cards — all data is already filtered by backend */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        <StatCard
          title="Security Findings"
          value={metrics.security_only ?? 0}
          icon={<Bug size={18} />}
          color="#22D3EE"
          delay={0.05}
          subtitle="Vulnerabilities & threat intel"
          onClick={() => navigate('/findings')}
        />
        <StatCard
          title="Compliance Findings"
          value={metrics.compliance_tagged ?? 0}
          icon={<CheckCircle size={18} />}
          color="#22C55E"
          delay={0.1}
          subtitle="Mapped to regulations"
          onClick={() => navigate('/compliance')}
        />
        <StatCard
          title="Critical"
          value={metrics.critical_findings}
          icon={<AlertTriangle size={18} />}
          color="#EF4444"
          delay={0.12}
          onClick={() => navigate('/findings?severity=critical')}
        />
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <StatCard
          title={selectedEntities.length === 1 ? selectedEntities[0] : "Monitored Entities"}
          value={selectedEntities.length > 0 ? selectedEntities.length : (metrics?.total_entities ?? 0)}
          icon={<Globe size={18} />}
          color="#A78BFA"
          delay={0.15}
          onClick={() => navigate('/entities')}
        />
        <StatCard
          title="Active Alerts"
          value={filteredAlerts.filter(a => a.status !== 'acknowledged').length}
          icon={<Shield size={18} />}
          color="#F59E0B"
          delay={0.18}
          onClick={() => navigate('/alerts')}
        />
        <StatCard
          title="Total Findings"
          value={metrics.total_findings}
          icon={<Activity size={18} />}
          color="#8892A6"
          delay={0.2}
          onClick={() => navigate('/findings')}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-1">
          <SeverityChart data={metrics.severity_breakdown} />
        </div>
        <div className="lg:col-span-1">
          <RiskGauge score={metrics.avg_risk_score} />
        </div>
        <div className="lg:col-span-1">
          <div className="widget h-full">
            <div className="widget-header">
              <h3 className="widget-title">Quick Stats</h3>
            </div>
            <div className="space-y-4">
              {[
                { label: 'High Findings', value: metrics.high_findings, color: '#F97316' },
                { label: 'Medium Findings', value: metrics.medium_findings, color: '#F59E0B' },
                { label: 'Low Findings', value: metrics.low_findings, color: '#3B82F6' },
              ].map((s) => (
                <div key={s.label}>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-text-secondary">{s.label}</span>
                    <span className="font-mono font-semibold text-text-primary">{s.value}</span>
                  </div>
                  <div className="h-2 rounded-full bg-surface-200 overflow-hidden">
                    <div
                      className="h-full rounded-full transition-all duration-700"
                      style={{
                        width: `${metrics.total_findings > 0 ? (s.value / metrics.total_findings) * 100 : 0}%`,
                        backgroundColor: s.color,
                      }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      <TimelineChart data={metrics.timeline_data} />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <FindingsTable
          findings={metrics.recent_findings}
          compact
          onViewAll={() => navigate('/findings')}
        />
        <AlertList alerts={filteredAlerts.slice(0, 5)} />
      </div>
    </div>
  );
}
