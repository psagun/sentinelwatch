import { Award, Globe, Search, Eye, Shield, Cpu, CheckCircle, ExternalLink, Server, Zap, Layers, ArrowRight, ArrowDown, Database, BarChart3 } from 'lucide-react';

const BD_PRODUCTS = [
  {
    icon: <Shield size={20} />,
    name: 'Web Unlocker',
    usage: 'Fetches security.txt, robots.txt, paste sites, compliance pages, and abuse check pages — bypasses CAPTCHAs and geo-blocks for reliable data collection. Automatically rotates browser fingerprints, headers, and IP addresses across Bright Data\'s residential proxy pool to evade anti-bot detection. Handles CAPTCHA challenges (reCAPTCHA, hCaptcha, Cloudflare Turnstile) transparently without manual intervention. Enables reliable scraping of security forums (e.g., ZeroDay, Exploit-DB mirrors), paste sites (Pastebin, Ghostbin), and compliance portals that would otherwise block datacenter IPs and headless browser signatures.',
    calls: 'web_unlocker_get() in WebScraper, ThreatCollector, ComplianceCollector, InvestigationAgent',
    color: 'text-accent-cyan',
    bg: 'bg-accent-cyan/10',
  },
  {
    icon: <Search size={20} />,
    name: 'SERP API',
    usage: 'Searches Google for threat intelligence (CVE mentions, leak sites), brand monitoring (impersonation, phishing), compliance news, and vendor reputation. Returns structured JSON results (title, URL, snippet, rich snippets, sitelinks) ready for AI/ML API ingestion — no HTML parsing needed. Supports geotargeting by country and language for region-specific threat intel (e.g., tracking GDPR enforcement news in Germany, phishing campaigns targeted at Japanese financial institutions). Freshness filtering (past hour / day / week) enables real-time alerting on newly published CVEs, data breaches, and brand impersonation pages as they appear in search results.',
    calls: 'serp_search() / serp_news() in BrandMonitor, ThreatCollector, ThirdPartyCollector, InvestigationAgent',
    color: 'text-accent-green',
    bg: 'bg-green-500/10',
  },
  {
    icon: <Eye size={20} />,
    name: 'Scraping Browser',
    usage: 'Full headless browser automation for JS-heavy security analysis. Renders pages, detects third-party scripts, captures visual snapshots, inspects inline JS. Executes JavaScript in a real Chromium environment to uncover client-side threats invisible to HTTP-level scrapers: dynamic content loading, DOM-based obfuscation, injected tracking scripts, cryptominers, and skimming code. Captures full-page PNG screenshots and accessibility tree snapshots for evidence collection and visual verification. Enables detection of Magecart-style attacks, form-jacking scripts, and malicious browser extensions that the Web Unlocker (HTTP-level) cannot see, since these threats only manifest after JS execution in a live browser context.',
    calls: 'scraping_browser_navigate() in WebScraper._check_with_browser(), InvestigationAgent._browser_investigation()',
    color: 'text-accent-purple',
    bg: 'bg-purple-500/10',
  },
];

const PARTNERS = [
  { name: 'AI/ML API', role: 'Threat analysis, severity classification, investigation verdict generation', icon: <Cpu size={18} /> },
  { name: 'Bright Data CLI', role: 'Web Unlocker, SERP, and Scraping Browser infrastructure', icon: <Server size={18} /> },
  { name: 'FastAPI', role: 'Python REST API framework for backend services', icon: <Zap size={18} /> },
  { name: 'React + Vite', role: 'Frontend dashboard with real-time data visualization', icon: <Globe size={18} /> },
];

const WHY_BRIGHT_DATA = [
  {
    title: 'Reliable Data Access — No CAPTCHAs, No Blocks',
    desc: 'Bright Data\'s Web Unlocker and proxy infrastructure handle anti-bot detection, CAPTCHA challenges (reCAPTCHA, hCaptcha, Cloudflare), IP rate-limiting, and fingerprint rotation automatically. This means SentinelWatch can collect data from security forums, paste sites, government compliance portals, and dark-web-adjacent sources without ever hitting a block page — a requirement for any serious security monitoring platform.',
  },
  {
    title: 'Multiple Data Collection Methods for Different Threat Vectors',
    desc: 'No single data collection method covers all security use cases. SentinelWatch uses all three Bright Data products strategically: Web Unlocker for direct page fetching of known URLs, SERP API for discovering new threats via search, and Scraping Browser for client-side threat detection. This layered approach ensures broad coverage across known and unknown threat surfaces.',
  },
  {
    title: 'Enterprise-Grade Proxy Infrastructure at Developer-Friendly Pricing',
    desc: 'Bright Data\'s residential and datacenter proxy network spans millions of IPs across every country, with automatic failover, session persistence, and bandwidth scaling. The pay-as-you-go pricing model and generous free tier made it accessible for a hackathon project while still being the same infrastructure used by Fortune 500 companies for web-scale data collection.',
  },
  {
    title: 'Easy Integration via CLI and REST API',
    desc: 'The Bright Data CLI (`bdata`) provides a unified interface for all three products — Web Unlocker, SERP API, and Scraping Browser — with consistent authentication, output formatting, and error handling. The REST API enables programmatic control for automated pipelines. This simplicity allowed the SentinelWatch backend to integrate all three products in under 500 lines of Python code.',
  },
];

const RUBRIC_ITEMS = [
  { label: '3+ Bright Data Products', detail: 'Web Unlocker, SERP API, Scraping Browser', done: true },
  { label: 'AI/ML Integration', detail: 'AI/ML API for analysis, classification, and verdicts', done: true },
  { label: 'Real-Time Monitoring', detail: 'Background entity scans with live dashboard updates', done: true },
  { label: 'Interactive Dashboard', detail: 'Filterable findings, severity charts, risk scoring, trends', done: true },
  { label: 'REST API', detail: 'Full REST API for programmatic access and integration', done: true },
  { label: 'Alerting System', detail: 'Critical/high severity alerts with acknowledge workflow', done: true },
  { label: 'Web Scraper Scanner', detail: 'Dedicated endpoint for URL security scanning', done: true },
  { label: 'AI Investigations', detail: 'Autonomous deep-dive investigation with evidence gathering', done: true },
];

const ARCHITECTURE_LAYERS = [
  {
    layer: 'Data Collection Layer (Bright Data)',
    color: 'text-accent-cyan',
    items: [
      'Web Unlocker fetches raw HTML from security.txt, paste sites, compliance portals',
      'SERP API searches Google for CVE mentions, phishing sites, brand impersonation',
      'Scraping Browser renders JS-heavy pages, captures screenshots and accessibility trees',
    ],
  },
  {
    layer: 'Intelligence Layer (AI/ML API + Compliance)',
    color: 'text-accent-purple',
    items: [
      'Analyzes collected data for threats, suspicious patterns, and compliance violations',
      'Classifies findings by severity (critical / high / medium / low / info)',
      'Tags findings with GDPR, SOC 2, HIPAA, and PCI DSS compliance mappings',
      'Auto-generates remediation recommendations per regulation requirement',
      'Generates autonomous investigation verdicts with evidence citations',
    ],
  },
  {
    layer: 'Storage Layer (SQLite)',
    color: 'text-accent-amber',
    items: [
      'Persists findings, entity state, scan history, and investigation reports',
      'Enables historical trend analysis and audit trail for compliance reporting',
    ],
  },
  {
    layer: 'Presentation Layer (React + Vite)',
    color: 'text-accent-green',
    items: [
      'Live dashboard with severity charts, risk scoring, and entity overview',
      'Interactive filters, alert acknowledge workflow, and investigation viewer',
    ],
  },
];

export default function Hackathon() {
  return (
    <div className="space-y-8 animate-fade-in max-w-4xl">
      {/* Hero */}
      <div className="widget border-l-4 border-l-accent-amber">
        <div className="flex items-start gap-4">
          <div className="w-12 h-12 rounded-xl bg-accent-amber/15 flex items-center justify-center shrink-0">
            <Award size={24} className="text-accent-amber" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-text-primary">Hackathon Submission</h1>
            <p className="text-sm text-text-muted mt-1 leading-relaxed">
              Web Data UNLOCKED AI Hackathon — Bright Data × lablab.ai<br />
              <strong>Track 3: Security & Compliance</strong> &middot; Team: SentinelWatch
            </p>
          </div>
        </div>
      </div>

      {/* Track Info */}
      <div className="widget">
        <h2 className="text-sm font-bold text-text-primary uppercase tracking-wider mb-3">
          <span className="text-accent-amber">Track 3:</span> Security & Compliance
        </h2>
        <p className="text-sm text-text-secondary leading-relaxed">
          SentinelWatch addresses the Security & Compliance track by providing continuous,
          automated monitoring of the open web for security threats, regulatory changes,
          third-party risks, and brand exposure. The platform combines Bright Data's web
          data infrastructure with AI-powered analysis to deliver actionable security
          intelligence through a professional-grade dashboard.
        </p>
        <div className="mt-4 grid grid-cols-2 gap-3">
          {[
            { label: 'Real-Time Monitoring', desc: 'Continuous background scanning of monitored entities' },
            { label: 'Threat Intelligence', desc: 'SERP-powered threat detection across web sources' },
            { label: 'Compliance Checking', desc: 'GDPR, SOC 2, and regulatory compliance tracking' },
            { label: 'AI Investigation', desc: 'Autonomous deep-dive analysis with evidence gathering' },
          ].map((t) => (
            <div key={t.label} className="bg-surface-200 rounded-lg p-3 flex items-start gap-2">
              <CheckCircle size={14} className="text-accent-green shrink-0 mt-0.5" />
              <div>
                <p className="text-xs font-semibold text-text-primary">{t.label}</p>
                <p className="text-[10px] text-text-muted mt-0.5">{t.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Bright Data Products */}
      <div>
        <h2 className="text-sm font-bold text-text-primary uppercase tracking-wider mb-3">
          Bright Data Products Used
        </h2>
        <div className="space-y-3">
          {BD_PRODUCTS.map((p) => (
            <div key={p.name} className="widget flex items-start gap-3">
              <div className={`w-9 h-9 rounded-lg ${p.bg} flex items-center justify-center shrink-0`}>
                <span className={p.color}>{p.icon}</span>
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <h3 className="text-sm font-semibold text-text-primary">{p.name}</h3>
                  <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-accent-green/10 text-accent-green font-medium">
                    INTEGRATED
                  </span>
                </div>
                <p className="text-xs text-text-secondary mt-1 leading-relaxed">{p.usage}</p>
                <p className="text-[10px] text-text-muted/60 mt-1 font-mono">{p.calls}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Partner Technologies */}
      <div className="widget">
        <h2 className="text-sm font-bold text-text-primary uppercase tracking-wider mb-3">Partner Technologies</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {PARTNERS.map((p) => (
            <div key={p.name} className="bg-surface-200 rounded-lg p-3 text-center">
              <div className="w-8 h-8 rounded-lg bg-accent-cyan/10 flex items-center justify-center mx-auto mb-2">
                <span className="text-accent-cyan">{p.icon}</span>
              </div>
              <p className="text-xs font-semibold text-text-primary">{p.name}</p>
              <p className="text-[10px] text-text-muted mt-1 leading-relaxed">{p.role}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Why Bright Data */}
      <div className="widget">
        <h2 className="text-sm font-bold text-text-primary uppercase tracking-wider mb-3">
          Why Bright Data
        </h2>
        <div className="space-y-3">
          {WHY_BRIGHT_DATA.map((item) => (
            <div key={item.title} className="flex items-start gap-3">
              <div className="w-5 h-5 rounded-full bg-accent-cyan/15 flex items-center justify-center shrink-0 mt-0.5">
                <CheckCircle size={12} className="text-accent-cyan" />
              </div>
              <div>
                <p className="text-sm font-semibold text-text-primary">{item.title}</p>
                <p className="text-xs text-text-secondary mt-0.5 leading-relaxed">{item.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Rubric Checklist */}
      <div className="widget">
        <h2 className="text-sm font-bold text-text-primary uppercase tracking-wider mb-3">Rubric Checklist</h2>
        <div className="space-y-2">
          {RUBRIC_ITEMS.map((item) => (
            <div key={item.label} className="flex items-center gap-3">
              <div className={`w-5 h-5 rounded-full flex items-center justify-center ${
                item.done ? 'bg-accent-green/20' : 'bg-surface-200'
              }`}>
                {item.done ? (
                  <CheckCircle size={14} className="text-accent-green" />
                ) : (
                  <span className="text-xs text-text-muted">?</span>
                )}
              </div>
              <div>
                <p className="text-sm font-medium text-text-primary">{item.label}</p>
                <p className="text-xs text-text-muted">{item.detail}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Architecture Deep Dive */}
      <div className="widget">
        <h2 className="text-sm font-bold text-text-primary uppercase tracking-wider mb-3">
          Architecture Deep Dive
        </h2>

        {/* Data Flow Diagram */}
        <div className="bg-surface-200 rounded-lg p-4 font-mono text-xs text-text-secondary leading-relaxed overflow-x-auto mb-4">
          <pre>{`
   Data Flow: URL Submission to Dashboard Visualization

   ┌──────────────────────────────────────────────────────────────────────┐
   │  User submits URL                                                    │
   │  (via Dashboard UI or REST API)                                      │
   └─────────────────┬────────────────────┬───────────────┬──────────────-┘
                     │                    │               │
                     ▼                    ▼               ▼
   ┌──────────────────────────────────────────────────────────────────────┐
   │                   FastAPI Backend (Port 8000)                        │
   │                                                                      │
   │  ┌────────────────┐  ┌──────────────────────┐  ┌──────────────────┐  │
   │  │  WebScraper    │  │  Collectors           │  │ Investigation   │  │
   │  │  Scanner       │  │  (Threat / Brand /    │  │ Agent           │  │
   │  │  (/api/scan)   │  │   Compliance / Third) │  │ (Deep Dive)     │  │
   │  └───────┬────────┘  └──────────┬───────────┘  └────────┬─────────┘  │
   └──────────┼──────────────────────┼───────────────────────┼────────────-┘
              │                      │                       │
              ▼                      ▼                       ▼
   ┌──────────────────────────────────────────────────────────────────────┐
   │                   Bright Data Products                               │
   │                                                                      │
   │  ┌─────────────────┐  ┌──────────────────┐  ┌────────────────────┐  │
   │  │  Web Unlocker   │  │   SERP API       │  │ Scraping Browser   │  │
   │  │                  │  │                  │  │                    │  │
   │  │ - HTTP fetches   │  │ - Google search  │  │ - JS rendering     │  │
   │  │ - CAPTCHA bypass │  │ - Geo-targeting  │  │ - Screenshots      │  │
   │  │ - Fingerprint    │  │ - Freshness      │  │ - A11y tree        │  │
   │  │   rotation       │  │   filtering      │  │ - Client-side      │  │
   │  │ - IP rotation    │  │ - Structured     │  │   threat detection │  │
   │  │                  │  │   JSON results   │  │                    │  │
   │  └────────┬─────────┘  └────────┬─────────┘  └─────────┬──────────┘  │
   └───────────┼─────────────────────┼──────────────────────┼────────────-┘
               │                     │                      │
               ▼                     ▼                      ▼
   ┌──────────────────────────────────────────────────────────────────────┐
   │                   AI/ML API Intelligence Layer                        │
   │                                                                      │
   │  ┌──────────────────────┐  ┌──────────────────┐  ┌────────────────┐  │
   │  │ Threat Analysis      │  │ Severity         │  │ Investigation  │  │
   │  │ (entity extraction,  │  │ Classification   │  │ Verdict        │  │
   │  │  pattern matching)   │  │ (critical/high/   │  │ Generation     │  │
   │  │                      │  │  medium/low/info) │  │ + Evidence     │  │
   │  └──────────┬───────────┘  └────────┬─────────┘  └───────┬────────┘  │
   └─────────────┼───────────────────────┼────────────────────┼──────────-┘
                 │                       │                    │
                 ▼                       ▼                    ▼
   ┌──────────────────────────────────────────────────────────────────────┐
   │                   SQLite Storage Layer                               │
   │  findings, entities, scan_history, investigations, alerts            │
   └──────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
   ┌──────────────────────────────────────────────────────────────────────┐
   │            Frontend Dashboard (React + Vite — Port 5173)             │
   │                                                                      │
   │  ┌──────────────┐  ┌────────────────┐  ┌─────────────────────────┐  │
   │  │ Entity View   │  │ Findings Table │  │ Investigation Viewer   │  │
   │  │ (overview,    │  │ (filterable,   │  │ (evidence timeline,    │  │
   │  │  risk score)  │  │  sortable)     │  │  verdict, screenshots) │  │
   │  └──────────────┘  └────────────────┘  └─────────────────────────┘  │
   │  ┌──────────────┐  ┌────────────────┐  ┌─────────────────────────┐  │
   │  │ Severity     │  │ Alert Panel    │  │ Web Scraper             │  │
   │  │ Charts       │  │ (acknowledge   │  │ Scanner UI              │  │
   │  │ (donut/bar)  │  │  workflow)     │  │ (submit URL, view raw)  │  │
   │  └──────────────┘  └────────────────┘  └─────────────────────────┘  │
   └──────────────────────────────────────────────────────────────────────┘
          `}</pre>
        </div>

        {/* Architecture Layer Explanations */}
        <div className="space-y-4">
          {ARCHITECTURE_LAYERS.map((layer) => (
            <div key={layer.layer}>
              <h3 className="text-sm font-semibold text-text-primary mb-2 flex items-center gap-2">
                <Layers size={14} className={layer.color} />
                <span>{layer.layer}</span>
              </h3>
              <ul className="space-y-1 ml-5">
                {layer.items.map((item, i) => (
                  <li key={i} className="text-xs text-text-secondary flex items-start gap-2">
                    <ArrowRight size={10} className="text-text-muted shrink-0 mt-1" />
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* How Bright Data Forms the Data Collection Backbone */}
        <div className="mt-4 pt-4 border-t border-surface-300">
          <h3 className="text-sm font-semibold text-text-primary mb-2 flex items-center gap-2">
            <Database size={14} className="text-accent-cyan" />
            <span>How Bright Data Forms the Data Collection Backbone</span>
          </h3>
          <p className="text-xs text-text-secondary leading-relaxed">
            Every piece of external data in SentinelWatch flows through Bright Data. The <strong className="text-text-primary">Web Unlocker</strong> handles
            direct page fetches — security.txt files, robots.txt, paste site content, compliance portal pages —
            and its anti-detection infrastructure ensures SentinelWatch can access these sources reliably
            without getting blocked or CAPTCHA-challenged. The <strong className="text-text-primary">SERP API</strong> provides the discovery
            layer: it searches Google for CVE mentions, phishing domains, data breach disclosures, and brand
            impersonation pages, delivering structured results that bypass HTML parsing entirely. The{' '}
            <strong className="text-text-primary">Scraping Browser</strong> handles the most complex case: JS-heavy pages where threats
            only manifest after JavaScript execution (cryptominers, form-jacking scripts, injected trackers).
            All three products are accessed through a unified <strong className="text-text-primary">Bright Data CLI</strong> interface,
            which the Python backend calls via subprocess with consistent authentication and output parsing.
            This three-pronged approach means SentinelWatch can collect data from any publicly accessible web
            source — no matter how aggressively protected or how heavily dependent on client-side JavaScript.
          </p>
        </div>

        {/* How AI/ML API Powers the Intelligence Layer */}
        <div className="mt-4 pt-4 border-t border-surface-300">
          <h3 className="text-sm font-semibold text-text-primary mb-2 flex items-center gap-2">
            <Cpu size={14} className="text-accent-purple" />
            <span>How AI/ML API Powers the Intelligence Layer</span>
          </h3>
          <p className="text-xs text-text-secondary leading-relaxed">
            Raw web data is noisy. AI/ML API transforms Bright Data's collected data into structured,
            actionable security intelligence through three stages. First, <strong className="text-text-primary">threat analysis</strong>:
            each collected page is analyzed for security-relevant content — exposed credentials, vulnerability
            mentions, compliance violations, phishing indicators — with entity extraction to identify the
            affected organizations, domains, and systems. Second, <strong className="text-text-primary">severity classification</strong>: every
            finding is classified on a five-tier scale (critical, high, medium, low, info) based on the nature
            of the threat, the sensitivity of exposed data, and the response time required. Third,{' '}
            <strong className="text-text-primary">investigation verdict generation</strong>: for critical and high-severity findings, the
            Investigation Agent autonomously performs deep-dive analysis — conducting follow-up searches via
            SERP API, fetching related pages via Web Unlocker, and capturing screenshots via Scraping Browser —
            then synthesizes an evidence-backed verdict with a severity assessment, affected entities, and
            recommended actions. This AI-driven pipeline turns gigabytes of scraped web data into a concise,
            prioritized security dashboard in real time.
          </p>
        </div>

        {/* How the Frontend Visualizes Everything */}
        <div className="mt-4 pt-4 border-t border-surface-300">
          <h3 className="text-sm font-semibold text-text-primary mb-2 flex items-center gap-2">
            <BarChart3 size={14} className="text-accent-green" />
            <span>How the Frontend Visualizes Everything</span>
          </h3>
          <p className="text-xs text-text-secondary leading-relaxed">
            The React + Vite frontend consumes the FastAPI REST API and renders a professional SOC-style
            dashboard. The <strong className="text-text-primary">Entity Overview</strong> page shows each monitored organization or domain
            with its risk score, recent findings count, and quick status at a glance. The{' '}
            <strong className="text-text-primary">Findings Table</strong> provides filterable, sortable access to every detected
            threat — filtered by severity, entity, source, date range, or keyword — with expandable rows
            for full detail. <strong className="text-text-primary">Severity Charts</strong> (donut and bar) give an at-a-glance view
            of the threat landscape across all monitored entities. The <strong className="text-text-primary">Alert Panel</strong> tracks
            critical and high-severity findings with an acknowledge workflow to ensure nothing is missed.
            The <strong className="text-text-primary">Investigation Viewer</strong> presents autonomous investigation results with an
            evidence timeline, screenshots captured by Scraping Browser, and the AI-generated verdict.
            And the <strong className="text-text-primary">Web Scraper Scanner UI</strong> lets users submit arbitrary URLs for on-demand
            security scanning, with results streamed back in real time. Every visualization updates
            automatically as background collectors discover new threats, providing a live security
            monitoring experience.
          </p>
        </div>
      </div>

      {/* Footer */}
      <div className="text-center py-4">
        <p className="text-xs text-text-muted/50">
          Built for Bright Data × lablab.ai — Web Data UNLOCKED AI Hackathon 2025
        </p>
      </div>
    </div>
  );
}
