import { Shield, Globe, Search, Bell, FlaskConical, ExternalLink, CheckCircle, ArrowRight, Award } from 'lucide-react';

const features = [
  {
    icon: <Search size={20} />,
    title: 'Web Scraper Scanner',
    desc: 'Submit any URL for automated security scanning. Checks security headers, SSL certificates, robots.txt, security.txt, and server info disclosure using Bright Data Web Unlocker.',
    color: 'text-accent-cyan',
    bg: 'bg-accent-cyan/10',
  },
  {
    icon: <Globe size={20} />,
    title: 'Threat Intelligence',
    desc: 'Monitors open web sources, CVE feeds, paste sites, and security blogs for organization-specific threats via Bright Data SERP API.',
    color: 'text-accent-green',
    bg: 'bg-green-500/10',
  },
  {
    icon: <Shield size={20} />,
    title: 'Entity Monitoring',
    desc: 'Add websites or organizations to monitor. Automated background scans collect findings across threat, compliance, brand, and vulnerability domains.',
    color: 'text-accent-amber',
    bg: 'bg-amber-500/10',
  },
  {
    icon: <FlaskConical size={20} />,
    title: 'AI Investigations',
    desc: 'Deep-dive analysis of any IP, domain, URL, or organization. Uses Bright Data search + AI/ML API to gather evidence and generate verdicts.',
    color: 'text-accent-purple',
    bg: 'bg-purple-500/10',
  },
  {
    icon: <Bell size={20} />,
    title: 'Alerting & Dashboard',
    desc: 'Real-time security posture overview with severity distribution, risk scoring, finding trends, and alert management.',
    color: 'text-accent-red',
    bg: 'bg-red-500/10',
  },
  {
    icon: <ExternalLink size={20} />,
    title: 'Bright Data Integration',
    desc: 'Powered by Bright Data Web Unlocker, SERP API, and proxy infrastructure for reliable, unblocked web data collection.',
    color: 'text-accent-cyan',
    bg: 'bg-accent-cyan/10',
  },
];

const howToUse = [
  {
    step: '1',
    title: 'Monitor an Entity',
    desc: 'Go to Entities → "Add Entity" → enter a URL (e.g. https://example.com). SentinelWatch runs automated security checks via Bright Data.',
    action: 'Navigate to Entities',
    path: '/entities',
  },
  {
    step: '2',
    title: 'Review Findings',
    desc: 'Check the Dashboard for an overview or Findings page for detailed results. Filter by severity, type, or entity.',
    action: 'View Dashboard',
    path: '/',
  },
  {
    step: '3',
    title: 'Run a Scan',
    desc: 'Use POST /api/v1/scan or the API to scan any URL directly. Returns security headers, SSL status, and accessibility via Bright Data.',
    action: 'Try API',
    path: '/investigations',
  },
  {
    step: '4',
    title: 'Investigate Threats',
    desc: 'Go to Investigations → enter an IP, domain, or org → click Investigate. AI analyzes Bright Data search results and returns a verdict.',
    action: 'Open Investigations',
    path: '/investigations',
  },
  {
    step: '5',
    title: 'Manage Alerts',
    desc: 'Critical and high-severity findings trigger alerts. Acknowledge or investigate them from the Alerts page.',
    action: 'View Alerts',
    path: '/alerts',
  },
];

const techStack = [
  { name: 'FastAPI', role: 'REST API framework' },
  { name: 'React + Vite', role: 'Frontend UI' },
  { name: 'Bright Data', role: 'Web Unlocker, SERP API, proxy' },
  { name: 'AI/ML API', role: 'Threat analysis & investigation' },
  { name: 'Tailwind CSS', role: 'Dark SOC-themed UI' },
  { name: 'Recharts', role: 'Dashboard visualizations' },
];

export default function About() {
  return (
    <div className="space-y-8 animate-fade-in max-w-4xl">
      {/* Hero */}
      <div className="widget border-l-4 border-l-accent-cyan">
        <div className="flex items-start gap-4">
          <div className="w-12 h-12 rounded-xl bg-accent-cyan/15 flex items-center justify-center shrink-0">
            <Shield size={24} className="text-accent-cyan" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-text-primary">SentinelWatch</h1>
            <p className="text-sm text-text-muted mt-1 leading-relaxed">
              AI-powered security & compliance monitoring platform built for the
              {' '}<span className="text-accent-cyan">Bright Data × lablab.ai Web Data UNLOCKED Hackathon</span>.
              Track&nbsp;3 — Security & Compliance.
            </p>
          </div>
        </div>
      </div>

      {/* Overview */}
      <div className="widget">
        <h2 className="text-sm font-bold text-text-primary uppercase tracking-wider mb-3">Overview</h2>
        <p className="text-sm text-text-secondary leading-relaxed">
          SentinelWatch continuously monitors the open web for security threats, regulatory changes,
          third-party risks, and brand exposure. It combines{' '}
          <strong className="text-text-primary">Bright Data</strong>'s web unblocking and search
          infrastructure with <strong className="text-text-primary">AI/ML API</strong> analysis
          to deliver structured, actionable intelligence — all from a Grafana/Kibana-inspired
          dark dashboard.
        </p>
        <div className="mt-4 grid grid-cols-3 gap-4">
          {[
            { label: 'Hackathon Track', value: 'Security & Compliance' },
            { label: 'Bright Data Tools', value: 'Web Unlocker, SERP, Proxy' },
            { label: 'AI Analysis', value: 'AI/ML API powered' },
          ].map((s) => (
            <div key={s.label} className="bg-surface-200 rounded-lg p-3 text-center">
              <p className="text-[10px] text-text-muted uppercase tracking-wider">{s.label}</p>
              <p className="text-sm font-semibold text-text-primary mt-1">{s.value}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Hackathon Banner */}
      <div className="widget bg-accent-amber/5 border border-accent-amber/10">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Award size={20} className="text-accent-amber" />
            <div>
              <p className="text-sm font-semibold text-text-primary">Hackathon Submission</p>
              <p className="text-xs text-text-muted">Track 3: Security & Compliance — Bright Data × lablab.ai</p>
            </div>
          </div>
          <button
            onClick={() => window.location.href = '/hackathon'}
            className="flex items-center gap-1.5 px-3 h-8 rounded-lg bg-accent-amber/10 border border-accent-amber/20
                       text-xs font-medium text-accent-amber hover:bg-accent-amber/20 transition-all shrink-0"
          >
            View Submission <ExternalLink size={12} />
          </button>
        </div>
      </div>

      {/* Features */}
      <div>
        <h2 className="text-sm font-bold text-text-primary uppercase tracking-wider mb-3">Features</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {features.map((f) => (
            <div key={f.title} className="widget flex items-start gap-3">
              <div className={`w-9 h-9 rounded-lg ${f.bg} flex items-center justify-center shrink-0`}>
                <span className={f.color}>{f.icon}</span>
              </div>
              <div>
                <h3 className="text-sm font-semibold text-text-primary">{f.title}</h3>
                <p className="text-xs text-text-secondary mt-1 leading-relaxed">{f.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* How to Use */}
      <div>
        <h2 className="text-sm font-bold text-text-primary uppercase tracking-wider mb-3">How to Use</h2>
        <div className="space-y-3">
          {howToUse.map((item) => (
            <div key={item.step} className="widget flex items-start gap-4">
              <div className="w-8 h-8 rounded-full bg-accent-cyan/15 flex items-center justify-center shrink-0">
                <span className="text-xs font-bold text-accent-cyan">{item.step}</span>
              </div>
              <div className="flex-1 min-w-0">
                <h3 className="text-sm font-semibold text-text-primary">{item.title}</h3>
                <p className="text-xs text-text-secondary mt-1 leading-relaxed">{item.desc}</p>
              </div>
              <button
                onClick={() => window.location.href = item.path}
                className="flex items-center gap-1.5 px-3 h-8 rounded-lg bg-accent-cyan/10 border border-accent-cyan/20
                           text-xs font-medium text-accent-cyan hover:bg-accent-cyan/20 transition-all shrink-0"
              >
                {item.action}
                <ArrowRight size={12} />
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* API Endpoints */}
      <div className="widget">
        <h2 className="text-sm font-bold text-text-primary uppercase tracking-wider mb-3">API Endpoints</h2>
        <div className="space-y-1.5">
          {[
            { method: 'GET', path: '/api/v1/health', desc: 'Health check' },
            { method: 'GET', path: '/api/v1/dashboard/summary', desc: 'Dashboard metrics' },
            { method: 'GET', path: '/api/v1/findings', desc: 'List findings (filterable)' },
            { method: 'GET', path: '/api/v1/alerts', desc: 'List alerts' },
            { method: 'GET', path: '/api/v1/entities', desc: 'List monitored entities' },
            { method: 'POST', path: '/api/v1/entities/monitor', desc: 'Add URL to monitor + scan' },
            { method: 'POST', path: '/api/v1/scan', desc: 'Scan a URL with WebScraper' },
            { method: 'GET', path: '/api/v1/scan/{id}', desc: 'Get scan results' },
            { method: 'POST', path: '/api/v1/investigate', desc: 'Investigate a threat indicator' },
            { method: 'GET', path: '/api/v1/investigations', desc: 'List past investigations' },
          ].map((ep) => (
            <div key={ep.path} className="flex items-center gap-3 text-xs">
              <span className={`px-1.5 py-0.5 rounded font-mono font-bold ${
                ep.method === 'GET'
                  ? 'bg-accent-cyan/10 text-accent-cyan'
                  : 'bg-accent-amber/10 text-accent-amber'
              }`}>
                {ep.method}
              </span>
              <code className="text-text-secondary font-mono">{ep.path}</code>
              <span className="text-text-muted ml-auto">{ep.desc}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Tech Stack */}
      <div className="widget">
        <h2 className="text-sm font-bold text-text-primary uppercase tracking-wider mb-3">Tech Stack</h2>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          {techStack.map((t) => (
            <div key={t.name} className="bg-surface-200 rounded-lg p-3">
              <p className="text-sm font-semibold text-text-primary">{t.name}</p>
              <p className="text-[10px] text-text-muted mt-0.5">{t.role}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Footer */}
      <div className="text-center py-4">
        <p className="text-xs text-text-muted/50">
          Built for Bright Data × lablab.ai — Web Data UNLOCKED Hackathon 2025
        </p>
      </div>
    </div>
  );
}
