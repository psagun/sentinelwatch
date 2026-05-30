import { useState, useEffect, useRef } from 'react';
import { X, Plus, Globe, Loader2, CheckCircle2, AlertTriangle, ExternalLink, RefreshCw, Shield, Search, Eye, Bug, FileText } from 'lucide-react';
import { monitorEntity, getEntity } from '../api/client';
import type { Entity } from '../types';

interface AddEntityModalProps {
  open: boolean;
  onClose: () => void;
  onComplete: () => void;
}

type ModalView = 'form' | 'scanning' | 'complete' | 'error';

function inferNameFromUrl(url: string): string {
  try {
    const parsed = new URL(url);
    const hostname = parsed.hostname.replace(/^www\./, '');
    const parts = hostname.split('.');
    const stem = parts.length >= 2 ? parts[parts.length - 2] : parts[0];
    return stem
      .split(/[-_]/)
      .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
      .join(' ');
  } catch {
    return '';
  }
}

const SCAN_OPTIONS = [
  { key: 'web_unlocker', label: 'Web Unlocker', icon: <Globe size={14} />, desc: 'Fetches security.txt, headers, SSL certs' },
  { key: 'serp', label: 'SERP Search', icon: <Search size={14} />, desc: 'Threat intel via Google search' },
  { key: 'scraping_browser', label: 'Scraping Browser', icon: <Eye size={14} />, desc: 'JS rendering & client-side analysis' },
];

const COMPLIANCE_OPTIONS = [
  { key: 'GDPR', label: 'GDPR', color: 'text-blue-400 border-blue-500/30' },
  { key: 'SOC2', label: 'SOC 2', color: 'text-accent-cyan border-accent-cyan/30' },
  { key: 'HIPAA', label: 'HIPAA', color: 'text-accent-red border-red-500/30' },
  { key: 'PCI_DSS', label: 'PCI DSS', color: 'text-accent-amber border-amber-500/30' },
];

const CHECK_OPTIONS = [
  { key: 'headers', label: 'Security Headers' },
  { key: 'ssl', label: 'SSL Certificate' },
  { key: 'server_info', label: 'Server Info' },
  { key: 'well_known', label: 'Well-Known Paths' },
  { key: 'browser', label: 'Browser Analysis' },
];

export default function AddEntityModal({ open, onClose, onComplete }: AddEntityModalProps) {
  const [url, setUrl] = useState('');
  const [name, setName] = useState('');
  const [entityId, setEntityId] = useState<string | null>(null);
  const [scannedEntity, setScannedEntity] = useState<Entity | null>(null);
  const [error, setError] = useState('');
  const [view, setView] = useState<ModalView>('form');
  const [showConfig, setShowConfig] = useState(false);
  const [scanConfig, setScanConfig] = useState({
    scans: ['web_unlocker', 'serp', 'scraping_browser'],
    compliance: ['GDPR', 'SOC2', 'HIPAA', 'PCI_DSS'],
    checks: ['headers', 'ssl', 'server_info', 'well_known', 'browser'],
  });
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const inferredName = inferNameFromUrl(url);
  const displayName = name || inferredName;

  const toggleConfigArray = (arr: string[], key: string): string[] =>
    arr.includes(key) ? arr.filter(k => k !== key) : [...arr, key];

  useEffect(() => {
    if (!open) {
      setUrl('');
      setName('');
      setEntityId(null);
      setScannedEntity(null);
      setError('');
      setView('form');
      setShowConfig(false);
      setScanConfig({
        scans: ['web_unlocker', 'serp', 'scraping_browser'],
        compliance: ['GDPR', 'SOC2', 'HIPAA', 'PCI_DSS'],
        checks: ['headers', 'ssl', 'server_info', 'well_known', 'browser'],
      });
      if (pollingRef.current) clearInterval(pollingRef.current);
    }
  }, [open]);

  useEffect(() => {
    if (view === 'scanning' && entityId) {
      pollingRef.current = setInterval(async () => {
        try {
          const entity = await getEntity(entityId);
          if (entity.scan_status === 'completed' || entity.scan_status === 'failed') {
            setScannedEntity(entity);
            setView(entity.scan_status === 'completed' ? 'complete' : 'error');
            if (entity.scan_status === 'completed') setError('');
            else setError('Scan failed to complete. Some data may be unavailable.');
            if (pollingRef.current) clearInterval(pollingRef.current);
            if (entity.scan_status === 'completed') onComplete();
          }
        } catch {
          // keep polling
        }
      }, 2000);
      return () => {
        if (pollingRef.current) clearInterval(pollingRef.current);
      };
    }
  }, [view, entityId, onComplete]);

  const handleSubmit = async () => {
    if (!url.trim()) return;
    setError('');
    setView('scanning');
    try {
      const entity = await monitorEntity({
        url: url.trim(),
        name: name || undefined,
        scan_config: scanConfig,
      });
      setEntityId(entity.id);
    } catch (e: any) {
      setError(e.message || 'Failed to start monitoring');
      setView('error');
    }
  };

  const handleRetry = () => {
    setError('');
    setView('form');
    setEntityId(null);
    setScannedEntity(null);
  };

  const handleClose = () => {
    if (view === 'scanning') return; // don't close while scanning
    onClose();
  };

  const riskColor = (score: number) =>
    score >= 70 ? 'text-accent-red' : score >= 40 ? 'text-accent-amber' : 'text-accent-green';

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={handleClose} />
      <div className="relative w-full max-w-lg mx-4">
        {/* Form View */}
        {view === 'form' && (
          <div className="widget border-accent-cyan/20">
            <div className="flex items-center justify-between mb-5">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-lg bg-accent-cyan/15 flex items-center justify-center">
                  <Plus size={18} className="text-accent-cyan" />
                </div>
                <div>
                  <h2 className="text-base font-bold text-text-primary">Add Website to Monitor</h2>
                  <p className="text-xs text-text-muted">SentinelWatch will scan this URL for threats</p>
                </div>
              </div>
              <button
                onClick={handleClose}
                className="p-1.5 rounded-md text-text-muted hover:text-text-primary hover:bg-surface-200 transition-colors"
              >
                <X size={16} />
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-text-secondary mb-1.5 tracking-wide uppercase">
                  Website URL
                </label>
                <div className="relative">
                  <Globe size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted" />
                  <input
                    type="url"
                    placeholder="https://example.com"
                    value={url}
                    onChange={(e) => {
                      setUrl(e.target.value);
                      if (!name) setName('');
                    }}
                    className="w-full h-10 pl-9 pr-3 bg-surface-200 border border-border rounded-lg text-sm text-text-primary
                               placeholder:text-text-muted/50 focus:outline-none focus:border-accent-cyan/40 transition-colors font-mono"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-text-secondary mb-1.5 tracking-wide uppercase">
                  Display Name <span className="text-text-muted/50 font-normal normal-case tracking-normal">(optional)</span>
                </label>
                <input
                  type="text"
                  placeholder={inferredName || 'My Website'}
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full h-10 px-3 bg-surface-200 border border-border rounded-lg text-sm text-text-primary
                             placeholder:text-text-muted/50 focus:outline-none focus:border-accent-cyan/40 transition-colors"
                />
              </div>

              {url && (
                <div className="bg-surface-200/50 border border-border rounded-lg p-3 space-y-1.5">
                  <p className="text-[11px] font-semibold uppercase tracking-wider text-text-muted">Inferred Configuration</p>
                  <div className="flex items-center gap-2 text-xs">
                    <span className="text-text-muted">Name:</span>
                    <span className="text-text-primary font-medium">{displayName}</span>
                  </div>
                  <div className="flex items-center gap-2 text-xs">
                    <span className="text-text-muted">Domain:</span>
                    <span className="text-text-primary font-mono text-[11px]">
                      {(() => { try { return new URL(url).hostname.replace(/^www\./, ''); } catch { return '—'; } })()}
                    </span>
                  </div>
                </div>
              )}

              {/* Scan Configuration Toggle */}
              <button
                onClick={() => setShowConfig(!showConfig)}
                className="w-full flex items-center justify-between p-3 rounded-lg bg-surface-200/50 border border-border text-xs text-text-muted hover:text-text-primary transition-colors"
              >
                <span className="font-semibold uppercase tracking-wider">Scan Configuration</span>
                <span className="text-[10px]">{showConfig ? 'Hide' : 'Show'} advanced settings</span>
              </button>

              {showConfig && (
                <div className="space-y-4 p-3 rounded-lg bg-surface-200/30 border border-border">
                  {/* Scan Types */}
                  <div>
                    <p className="text-[10px] font-semibold text-text-muted uppercase tracking-wider mb-2">Bright Data Scans</p>
                    <div className="flex flex-wrap gap-1.5">
                      {SCAN_OPTIONS.map((opt) => (
                        <button
                          key={opt.key}
                          onClick={() => setScanConfig(prev => ({ ...prev, scans: toggleConfigArray(prev.scans, opt.key) }))}
                          className={`inline-flex items-center gap-1.5 px-2.5 h-7 rounded-md text-[11px] font-medium border transition-all ${
                            scanConfig.scans.includes(opt.key)
                              ? 'bg-accent-cyan/15 text-accent-cyan border-accent-cyan/30'
                              : 'bg-surface-200 text-text-muted border-border hover:border-border-light'
                          }`}
                        >
                          {opt.icon}
                          {opt.label}
                        </button>
                      ))}
                    </div>
                    <p className="text-[10px] text-text-muted/60 mt-1">Choose which Bright Data products to use for scanning</p>
                  </div>

                  {/* Compliance Frameworks */}
                  <div>
                    <p className="text-[10px] font-semibold text-text-muted uppercase tracking-wider mb-2">Compliance Frameworks</p>
                    <div className="flex flex-wrap gap-1.5">
                      {COMPLIANCE_OPTIONS.map((opt) => (
                        <button
                          key={opt.key}
                          onClick={() => setScanConfig(prev => ({ ...prev, compliance: toggleConfigArray(prev.compliance, opt.key) }))}
                          className={`inline-flex items-center gap-1 px-2.5 h-7 rounded-md text-[11px] font-medium border transition-all ${
                            scanConfig.compliance.includes(opt.key)
                              ? `${opt.color} bg-opacity-10`
                              : 'bg-surface-200 text-text-muted border-border hover:border-border-light'
                          }`}
                        >
                          {opt.label}
                        </button>
                      ))}
                    </div>
                    <p className="text-[10px] text-text-muted/60 mt-1">Select regulations to check findings against</p>
                  </div>

                  {/* Security Checks */}
                  <div>
                    <p className="text-[10px] font-semibold text-text-muted uppercase tracking-wider mb-2">Security Checks</p>
                    <div className="flex flex-wrap gap-1.5">
                      {CHECK_OPTIONS.map((opt) => (
                        <button
                          key={opt.key}
                          onClick={() => setScanConfig(prev => ({ ...prev, checks: toggleConfigArray(prev.checks, opt.key) }))}
                          className={`inline-flex items-center gap-1 px-2.5 h-7 rounded-md text-[11px] font-medium border transition-all ${
                            scanConfig.checks.includes(opt.key)
                              ? 'bg-accent-cyan/15 text-accent-cyan border-accent-cyan/30'
                              : 'bg-surface-200 text-text-muted border-border hover:border-border-light'
                          }`}
                        >
                          {opt.label}
                        </button>
                      ))}
                    </div>
                    <p className="text-[10px] text-text-muted/60 mt-1">Select which security checks to perform</p>
                  </div>
                </div>
              )}

              {error && (
                <div className="flex items-center gap-2 p-3 rounded-lg bg-accent-red/10 border border-accent-red/20 text-xs text-accent-red">
                  <AlertTriangle size={14} className="shrink-0" />
                  {error}
                </div>
              )}

              <button
                onClick={handleSubmit}
                disabled={!url.trim()}
                className="w-full h-10 flex items-center justify-center gap-2 rounded-lg font-semibold text-sm
                           bg-accent-cyan text-surface hover:bg-accent-cyan/90 transition-all
                           disabled:opacity-40 disabled:cursor-not-allowed"
              >
                <Plus size={16} />
                Start Monitoring
              </button>
            </div>
          </div>
        )}

        {/* Scanning View */}
        {view === 'scanning' && (
          <div className="widget border-accent-cyan/30">
            <div className="text-center py-6">
              <div className="relative w-16 h-16 mx-auto mb-4">
                <div className="absolute inset-0 rounded-full border-2 border-accent-cyan/20" />
                <div className="absolute inset-0 rounded-full border-2 border-accent-cyan border-t-transparent animate-spin" />
                <Loader2 size={24} className="absolute inset-0 m-auto text-accent-cyan animate-pulse" />
              </div>
              <h2 className="text-base font-bold text-text-primary mb-1">Scanning in Progress</h2>
              <p className="text-sm text-text-muted mb-2">
                Running security analysis on <span className="text-accent-cyan font-medium">{displayName}</span>
              </p>
              <div className="flex items-center justify-center gap-2 text-xs text-text-muted">
                <span className="w-1.5 h-1.5 rounded-full bg-accent-amber animate-pulse" />
                Collecting threat intelligence
              </div>
              <div className="mt-4 flex items-center justify-center gap-2 text-[11px] text-text-muted/60">
                <RefreshCw size={12} className="animate-spin" />
                Auto-refreshing every 2s
              </div>
            </div>
          </div>
        )}

        {/* Complete View */}
        {view === 'complete' && scannedEntity && (
          <div className="widget border-accent-green/20">
            <div className="flex items-center justify-between mb-5">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-lg bg-accent-green/15 flex items-center justify-center">
                  <CheckCircle2 size={18} className="text-accent-green" />
                </div>
                <div>
                  <h2 className="text-base font-bold text-text-primary">Scan Complete</h2>
                  <p className="text-xs text-text-muted">{displayName}</p>
                </div>
              </div>
              <button
                onClick={handleClose}
                className="p-1.5 rounded-md text-text-muted hover:text-text-primary hover:bg-surface-200 transition-colors"
              >
                <X size={16} />
              </button>
            </div>

            <div className="grid grid-cols-2 gap-3 mb-5">
              <div className="bg-surface-200/50 border border-border rounded-lg p-3 text-center">
                <p className="text-2xl font-bold font-mono text-text-primary">
                  {scannedEntity.finding_count}
                </p>
                <p className="text-[11px] text-text-muted mt-0.5">Findings</p>
              </div>
              <div className="bg-surface-200/50 border border-border rounded-lg p-3 text-center">
                <p className={`text-2xl font-bold font-mono ${riskColor(scannedEntity.current_risk_score)}`}>
                  {scannedEntity.current_risk_score.toFixed(0)}
                </p>
                <p className="text-[11px] text-text-muted mt-0.5">Risk Score</p>
              </div>
            </div>

            <div className="flex gap-2">
              <button
                onClick={handleClose}
                className="flex-1 h-10 rounded-lg border border-border text-sm font-semibold text-text-primary
                           hover:bg-surface-200 transition-colors"
              >
                Close
              </button>
              <button
                onClick={() => {
                  onClose();
                  window.location.hash = '#/';
                }}
                className="flex-1 h-10 flex items-center justify-center gap-2 rounded-lg font-semibold text-sm
                           bg-accent-cyan text-surface hover:bg-accent-cyan/90 transition-colors"
              >
                <ExternalLink size={14} />
                View Dashboard
              </button>
            </div>
          </div>
        )}

        {/* Error View */}
        {view === 'error' && (
          <div className="widget border-accent-red/20">
            <div className="flex items-center justify-between mb-5">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-lg bg-accent-red/15 flex items-center justify-center">
                  <AlertTriangle size={18} className="text-accent-red" />
                </div>
                <div>
                  <h2 className="text-base font-bold text-text-primary">Scan Failed</h2>
                  <p className="text-xs text-text-muted">{displayName}</p>
                </div>
              </div>
              <button
                onClick={handleClose}
                className="p-1.5 rounded-md text-text-muted hover:text-text-primary hover:bg-surface-200 transition-colors"
              >
                <X size={16} />
              </button>
            </div>

            <div className="p-3 rounded-lg bg-accent-red/10 border border-accent-red/20 text-sm text-accent-red mb-5">
              {error || 'An unexpected error occurred during the scan.'}
            </div>

            <div className="flex gap-2">
              <button
                onClick={handleClose}
                className="flex-1 h-10 rounded-lg border border-border text-sm font-semibold text-text-primary
                           hover:bg-surface-200 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleRetry}
                className="flex-1 h-10 flex items-center justify-center gap-2 rounded-lg font-semibold text-sm
                           bg-accent-cyan text-surface hover:bg-accent-cyan/90 transition-colors"
              >
                <RefreshCw size={14} />
                Retry
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
