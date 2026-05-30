import { useEffect, useState, useMemo } from 'react';
import { getEntities, getFindings, getAlerts, getDashboardMetrics, generateAiReport, generateEntityAiReport, API_BASE } from '../api/client';
import type { Entity, Finding, Alert, DashboardMetrics } from '../types';
import {
  FileText, ChevronDown, ChevronRight, Shield, Globe, Search, Bell,
  AlertTriangle, CheckCircle, Activity, ExternalLink, Download, Bug, Eye, Server,
  Terminal, ShieldCheck, AlertOctagon, Lightbulb, ArrowRight, Info, Sparkles, Loader2, FileCode2
} from 'lucide-react';
import PageMeta from '../components/PageMeta';
import { mdToHtml } from '../utils/markdown';

const sevColor = (s: string) =>
  s === 'critical' ? 'text-accent-red' : s === 'high' ? 'text-orange-400' : s === 'medium' ? 'text-accent-amber' : s === 'low' ? 'text-blue-400' : 'text-text-secondary';

const sevBg = (s: string) =>
  s === 'critical' ? 'bg-red-500/10 border-red-500/20' : s === 'high' ? 'bg-orange-500/10 border-orange-500/20' : s === 'medium' ? 'bg-amber-500/10 border-amber-500/20' : 'bg-blue-500/10 border-blue-500/20';

const regColors: Record<string, string> = {
  GDPR: 'text-blue-400 bg-blue-500/10 border-blue-500/20',
  SOC2: 'text-accent-cyan bg-accent-cyan/10 border-accent-cyan/20',
  HIPAA: 'text-accent-red bg-red-500/10 border-red-500/20',
  PCI_DSS: 'text-accent-amber bg-amber-500/10 border-amber-500/20',
};

const AGENTS_DETAILED = [
  {
    step: '1', name: 'Threat Intelligence Agent', icon: <Search size={16} />, color: 'text-accent-cyan',
    description: 'Searches Google via Bright Data SERP API for CVE mentions, leak sites, and dark web chatter.',
    methodology: 'For each entity, the agent runs Google searches using the SERP API with queries like "{entity} vulnerability", "{entity} data breach", "{entity} CVE". It parses structured JSON results (title, URL, snippet) and classifies results by keyword matching for severity.',
    tool: 'Bright Data SERP API — Google Search',
    remediation: 'Investigate each threat mention. For confirmed CVEs, patch within vendor timeline. For leak mentions, verify if credentials are active and rotate immediately.',
  },
  {
    step: '2', name: 'Web Scraper Agent', icon: <Globe size={16} />, color: 'text-accent-green',
    description: 'Fetches security.txt, robots.txt, checks SSL certs, security headers, and server info via Bright Data Web Unlocker.',
    methodology: 'Uses Bright Data Web Unlocker REST API to fetch /.well-known/security.txt, /robots.txt, and the homepage. Checks HTTP response headers for CSP, HSTS, X-Frame-Options, X-Content-Type-Options. Inspects SSL certificate expiry and issuer via socket-level connection. Checks Server and X-Powered-By headers for info disclosure.',
    tool: 'Bright Data Web Unlocker — HTTP/HTTPS Fetch + SSL Socket Inspection',
    remediation: 'Add missing security headers in reverse proxy/WAF config. Renew expiring SSL certificates. Remove or obfuscate server version headers. Publish security.txt for vulnerability disclosure.',
  },
  {
    step: '3', name: 'Scraping Browser Agent', icon: <Eye size={16} />, color: 'text-accent-purple',
    description: 'Launches Bright Data Scraping Browser to detect third-party scripts, inline JS, mixed content, and client-side threats.',
    methodology: 'Opens a headless Chromium browser via Bright Data Scraping Browser (`bdata browser open`). Captures the full accessibility tree. Analyzes rendered DOM for: third-party script domains (cross-origin script loads), inline JavaScript blocks with executable code, HTTP resource references in HTTPS pages. These client-side threats are invisible to HTTP-level scrapers.',
    tool: 'Bright Data Scraping Browser — Headless Chromium + DOM Analysis',
    remediation: 'Remove unnecessary third-party scripts. Implement strict CSP with script-src restrictions. Migrate all mixed content to HTTPS. Audit inline scripts for XSS vectors.',
  },
  {
    step: '4', name: 'Compliance Classifier', icon: <ShieldCheck size={16} />, color: 'text-accent-amber',
    description: 'Tags all findings against GDPR, SOC 2, HIPAA, and PCI DSS regulations with article-level mappings.',
    methodology: 'Uses a rule-based engine mapping each check_type to regulation articles: headers→PCI DSS 6.5/SOC 2 CC6.1, SSL→PCI DSS 4.1/HIPAA 164.312(a)(2)(iv), credential leaks→GDPR Art. 32/SOC 2 CC6.1/HIPAA 164.312(a)(1)/PCI DSS 8.0. Also matches finding titles against keyword patterns for more specific classifications.',
    tool: 'SentinelWatch Compliance Rule Engine (500+ rules across 4 frameworks)',
    remediation: 'Address findings per regulation priority. Critical compliance violations (data residency, credential exposure) require immediate legal + engineering response. Schedule medium-severity items for next sprint.',
  },
  {
    step: '5', name: 'AI Investigation Agent', icon: <Bell size={16} />, color: 'text-accent-red',
    description: 'Uses AI/ML API to generate verdicts, confidence scores, and remediation recommendations.',
    methodology: 'Collects all evidence from previous agents (SERP results, web scraper findings, browser analysis, compliance tags). Sends a structured prompt to AI/ML API requesting: severity classification (critical/high/medium/low/info), risk score (0-10), remediation steps, and executive summary. Falls back to rule-based classification if AI/ML API is unavailable.',
    tool: 'AI/ML API — LLM-based Threat Analysis (Claude/GPT-4o)',
    remediation: 'AI-generated recommendations are finding-specific. Prioritize critical/high items. Review AI confidence scores — low confidence findings may need manual investigation.',
  },
  {
    step: '6', name: 'Alert Manager', icon: <AlertOctagon size={16} />, color: 'text-orange-400',
    description: 'Creates alerts for critical/high findings, tracks acknowledgment status and resolution notes.',
    methodology: 'Monitors the findings pipeline for severity thresholds. Automatically creates alerts when findings are classified as critical or high severity. Supports acknowledgment workflow with resolution notes. Tracks alert age for escalation. Integrates with notification channels (email, Slack, PagerDuty).',
    tool: 'SentinelWatch Alert Engine — Severity-based + Notification Routing',
    remediation: 'Acknowledge alerts promptly with resolution notes. Critical alerts: respond within 24h. High alerts: respond within 72h. Use the "Mark as fixed" button to document remediation steps.',
  },
];

// Remediation templates per finding type
const REMEDIATION: Record<string, { action: string; effort: string; priority: string; details: string }> = {
  'headers': {
    action: 'Add missing security headers via reverse proxy/WAF',
    effort: 'Low — config change only',
    priority: 'Medium',
    details: 'Add the following headers to your nginx/Apache/CDN config:\n- Content-Security-Policy: default-src \'self\'\n- Strict-Transport-Security: max-age=31536000\n- X-Frame-Options: DENY\n- X-Content-Type-Options: nosniff\n- Referrer-Policy: strict-origin-when-cross-origin',
  },
  'ssl': {
    action: 'Renew SSL certificate and fix configuration',
    effort: 'Low-Medium — cert renewal + config',
    priority: 'Critical/High based on expiry',
    details: '1. Run certbot or use your CA dashboard to renew\n2. Verify auto-renewal is configured\n3. Ensure TLS 1.2+ is enforced\n4. Use strong ciphers (e.g. ECDHE-RSA-AES256-GCM)',
  },
  'server_info': {
    action: 'Obfuscate or remove server version headers',
    effort: 'Low — config change',
    priority: 'Low',
    details: 'Edit server config to suppress Server and X-Powered-By headers:\n- nginx: server_tokens off;\n- Apache: ServerSignature Off\n- Express: app.set("x-powered-by", false)',
  },
  'well-known': {
    action: 'Publish security.txt and review robots.txt',
    effort: 'Low — create text files',
    priority: 'Medium',
    details: 'Create /.well-known/security.txt with contact and disclosure policy. Review robots.txt for sensitive path exposure (admin, config, backup). Remove sensitive paths from robots.txt — use proper auth instead.',
  },
  'browser': {
    action: 'Audit third-party scripts and implement CSP',
    effort: 'Medium — audit + config changes',
    priority: 'Medium',
    details: '1. Inventory all third-party scripts from the browser analysis\n2. Remove unused/unnecessary scripts\n3. Implement strict CSP with script-src hashes\n4. Use Subresource Integrity (SRI) tags\n5. Monitor for script injection via integrity checks',
  },
  'accessibility': {
    action: 'Fix accessibility and mixed content issues',
    effort: 'Low-Medium',
    priority: 'Medium',
    details: '1. Ensure site is reachable via standard browsers\n2. Fix mixed content warnings — serve all resources over HTTPS\n3. Remove any "not secure" warnings from pages\n4. Verify CDN/WAF is not blocking legitimate traffic',
  },
};

export default function Reports() {
  const [entities, setEntities] = useState<Entity[]>([]);
  const [findings, setFindings] = useState<Finding[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [expandedEntity, setExpandedEntity] = useState<string | null>(null);
  const [expandedSection, setExpandedSection] = useState<string | null>('workflow');
  const [expandedAgent, setExpandedAgent] = useState<string | null>(null);
  const [expandedFinding, setExpandedFinding] = useState<string | null>(null);
  const [aiReport, setAiReport] = useState<string | null>(null);
  const [aiReportLoading, setAiReportLoading] = useState(false);
  const [aiReportError, setAiReportError] = useState<string | null>(null);
  const [aiReportSection, setAiReportSection] = useState(false);
  const [entityAiReports, setEntityAiReports] = useState<Record<string, { report: string; loading: boolean; error?: string }>>({});

  useEffect(() => {
    Promise.all([
      getEntities(),
      getFindings({ limit: 200 }),
      getAlerts(),
      getDashboardMetrics(),
    ])
      .then(([e, f, a, m]) => {
        setEntities(e);
        setFindings(f);
        setAlerts(a);
        setMetrics(m);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const findingsByEntity = useMemo(() => {
    const map: Record<string, Finding[]> = {};
    for (const f of findings) {
      const key = f.entity_id || 'Unassigned';
      if (!map[key]) map[key] = [];
      map[key].push(f);
    }
    return map;
  }, [findings]);

  const alertsByEntity = useMemo(() => {
    const map: Record<string, Alert[]> = {};
    for (const a of alerts) {
      const key = a.finding?.entity_id || 'Unassigned';
      if (!map[key]) map[key] = [];
      map[key].push(a);
    }
    return map;
  }, [alerts]);

  const toggleEntity = (name: string) => {
    setExpandedEntity((prev) => prev === name ? null : name);
  };

  const toggleSection = (section: string) => {
    setExpandedSection((prev) => prev === section ? null : section);
  };

  const getFindingRemediation = (f: Finding) => {
    const checkType = (f as any).check_type || '';
    return REMEDIATION[checkType] || {
      action: 'Review and assess',
      effort: 'Variable',
      priority: f.severity,
      details: 'Investigate this finding and apply appropriate remediation based on severity and context.',
    };
  };

  const getAgentExplanation = (f: Finding): { agent: string; how: string; brightdata: string } => {
    const sourceType = f.source_type || '';
    const checkType = (f as any).check_type || '';
    const title = f.title.toLowerCase();

    if (sourceType === 'serp_news' || sourceType === 'serp_search' || title.includes('cve') || title.includes('leak') || title.includes('chatter') || title.includes('impersonation')) {
      return {
        agent: 'Threat Intelligence Agent (Step 1)',
        how: 'Searched Google via Bright Data SERP API for security mentions. Found this result by matching keywords against search snippets and classifying by threat relevance.',
        brightdata: 'Bright Data SERP API — Google Search with geo-targeting and freshness filtering',
      };
    }
    if (checkType === 'headers' || checkType === 'ssl' || checkType === 'server_info' || checkType === 'well-known') {
      return {
        agent: 'Web Scraper Agent (Step 2)',
        how: checkType === 'headers' ? 'Sent HTTP request via Bright Data Web Unlocker and inspected response headers for security standards compliance.'
          : checkType === 'ssl' ? 'Established SSL connection to the server and inspected certificate chain, expiry date, and issuer.'
          : checkType === 'server_info' ? 'Analyzed HTTP response headers for information disclosure via Server and X-Powered-By fields.'
          : 'Fetched /.well-known/security.txt and /robots.txt via Bright Data Web Unlocker to check for security disclosure policy and sensitive path exposure.',
        brightdata: 'Bright Data Web Unlocker — CAPTCHA-bypassing HTTP fetch + SSL socket inspection',
      };
    }
    if (checkType === 'browser' || title.includes('script') || title.includes('browser')) {
      return {
        agent: 'Scraping Browser Agent (Step 3)',
        how: 'Launched a headless Chromium browser via Bright Data Scraping Browser. Rendered the full page with JavaScript execution and analyzed the accessibility tree for third-party resources, inline scripts, and mixed content.',
        brightdata: 'Bright Data Scraping Browser — Headless Chromium with full JS execution',
      };
    }
    return {
      agent: 'AI Investigation Agent (Step 5)',
      how: 'Collected evidence from all previous agents and analyzed via AI/ML API to classify severity, assign risk score, and generate remediation recommendations.',
      brightdata: 'AI/ML API — LLM-powered threat analysis',
    };
  };

  const generateMarkdown = () => {
    let md = '# SentinelWatch Security Report\n\n';
    md += `**Generated:** ${new Date().toLocaleString()}\n`;
    md += `**Entities Monitored:** ${entities.length}\n`;
    md += `**Total Findings:** ${findings.length}\n`;
    md += `**Active Alerts:** ${alerts.filter(a => a.status !== 'acknowledged').length}\n\n`;
    md += `---\n\n`;
    md += '## Agent Pipeline\n\n';
    for (const agent of AGENTS_DETAILED) {
      md += `### Step ${agent.step}: ${agent.name}\n`;
      md += `${agent.description}\n\n`;
      md += `**Methodology:** ${agent.methodology}\n\n`;
      md += `**Bright Data Tool:** ${agent.tool}\n\n`;
    }
    md += `---\n\n`;
    for (const entity of entities) {
      const entityFindings = findingsByEntity[entity.name] || [];
      if (entityFindings.length === 0) continue;
      md += `## ${entity.name}\n\n`;
      md += `- **Risk Score:** ${entity.current_risk_score?.toFixed(1) ?? 'N/A'}/100\n`;
      md += `- **Total Findings:** ${entityFindings.length}\n`;
      md += `- **Alerts:** ${(alertsByEntity[entity.name] || []).length}\n\n`;
      for (const f of entityFindings.slice(0, 10)) {
        const exp = getAgentExplanation(f);
        const rem = getFindingRemediation(f);
        md += `### ${f.title}\n`;
        md += `- **Severity:** ${f.severity}\n`;
        md += `- **Discovered by:** ${exp.agent}\n`;
        md += `- **How:** ${exp.how}\n`;
        md += `- **Bright Data Tool Used:** ${exp.brightdata}\n`;
        md += `- **Remediation:** ${rem.action}\n`;
        md += `- **Effort:** ${rem.effort}\n`;
        md += `- **Details:** ${rem.details}\n\n`;
      }
    }
    md += `---\n\n*Report generated by SentinelWatch multi-agent pipeline using Bright Data Web Unlocker, SERP API, and Scraping Browser*\n`;
    return md;
  };

  const handleGenerateEntityReport = async (entityName: string) => {
    setEntityAiReports(prev => ({ ...prev, [entityName]: { report: '', loading: true } }));
    try {
      const result = await generateEntityAiReport(entityName);
      if (result.status === 'success' && result.report) {
        const report: string = result.report;
        setEntityAiReports(prev => ({ ...prev, [entityName]: { report, loading: false } }));
      } else {
        setEntityAiReports(prev => ({ ...prev, [entityName]: { report: '', loading: false, error: result.error || 'Failed' } }));
      }
    } catch (e: any) {
      setEntityAiReports(prev => ({ ...prev, [entityName]: { report: '', loading: false, error: e.message } }));
    }
  };

  const handleGenerateAiReport = async () => {
    setAiReportLoading(true);
    setAiReportError(null);
    setAiReport(null);
    setAiReportSection(true);
    try {
      const result = await generateAiReport();
      if (result.status === 'success' && result.report) {
        setAiReport(result.report);
      } else {
        setAiReportError(result.error || 'Failed to generate report');
      }
    } catch (e: any) {
      setAiReportError(e.message || 'Failed to generate AI report');
    } finally {
      setAiReportLoading(false);
    }
  };

  const downloadReport = () => {
    const md = generateMarkdown();
    const blob = new Blob([md], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `sentinelwatch-report-${new Date().toISOString().slice(0, 10)}.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-2 border-accent-cyan border-t-transparent rounded-full animate-spin" />
          <p className="text-text-muted text-sm">Generating detailed reports...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in max-w-5xl">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-text-primary">Detailed Security Reports</h1>
          <p className="text-sm text-text-muted mt-1">
            Per-entity reports with agent methodology, findings analysis, and remediation steps
          </p>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <a
            href={`${API_BASE}/reports/html`}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 px-4 h-10 bg-accent-cyan/10 border border-accent-cyan/20 rounded-lg
                       text-sm font-medium text-accent-cyan hover:bg-accent-cyan/20 transition-all"
          >
            <FileCode2 size={16} />
            HTML Report
          </a>
          <button
            onClick={downloadReport}
            className="flex items-center gap-2 px-3 h-10 bg-surface-200 border border-border rounded-lg
                       text-xs font-medium text-text-secondary hover:text-text-primary transition-all"
            title="Download Markdown"
          >
            <Download size={14} />
          </button>
        </div>
      </div>

      {/* Summary */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <div className="widget text-center"><p className="text-xs text-text-muted uppercase tracking-wider">Entities</p><p className="text-2xl font-bold text-accent-cyan mt-1">{entities.length}</p></div>
        <div className="widget text-center"><p className="text-xs text-text-muted uppercase tracking-wider">Findings</p><p className="text-2xl font-bold text-accent-amber mt-1">{findings.length}</p></div>
        <div className="widget text-center"><p className="text-xs text-text-muted uppercase tracking-wider">Compliance Tags</p><p className="text-2xl font-bold text-accent-green mt-1">{metrics?.compliance_tagged ?? 0}</p></div>
        <div className="widget text-center"><p className="text-xs text-text-muted uppercase tracking-wider">Active Alerts</p><p className="text-2xl font-bold text-accent-red mt-1">{alerts.filter(a => a.status !== 'acknowledged').length}</p></div>
      </div>

      {/* AI-Generated Narrative Report */}
      <div className="widget border-l-4 border-l-accent-purple">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <Sparkles size={16} className="text-accent-purple" />
            <h2 className="text-sm font-bold text-text-primary">AI-Generated Security Report</h2>
          </div>
          <button
            onClick={handleGenerateAiReport}
            disabled={aiReportLoading}
            className="flex items-center gap-2 px-4 h-9 bg-accent-purple/10 border border-accent-purple/20 rounded-lg
                       text-xs font-medium text-accent-purple hover:bg-accent-purple/20 transition-all disabled:opacity-40"
          >
            {aiReportLoading ? <Loader2 size={14} className="animate-spin" /> : <Sparkles size={14} />}
            {aiReportLoading ? 'Generating...' : 'Generate AI Report'}
          </button>
        </div>
        <p className="text-xs text-text-muted mb-1">
          Uses AI/ML API to analyze all findings, alerts, and entity data into a professional narrative security report with executive summary, risk analysis, compliance impact, and prioritized remediation plan.
        </p>

        {aiReportError && (
          <div className="flex items-center gap-2 p-3 rounded-lg bg-accent-red/10 border border-accent-red/20 text-xs text-accent-red mt-3">
            <AlertTriangle size={14} />
            {aiReportError}
          </div>
        )}

        {aiReportLoading && (
          <div className="flex flex-col items-center gap-3 py-8">
            <div className="relative w-12 h-12">
              <div className="absolute inset-0 rounded-full border-2 border-accent-purple/20" />
              <div className="absolute inset-0 rounded-full border-2 border-accent-purple border-t-transparent animate-spin" />
              <Sparkles size={20} className="absolute inset-0 m-auto text-accent-purple animate-pulse" />
            </div>
            <p className="text-sm text-text-muted">AI/ML API is analyzing findings and generating your report...</p>
            <p className="text-xs text-text-muted/60">This may take 30-60 seconds</p>
          </div>
        )}

        {aiReport && !aiReportLoading && (
          <div className="mt-3">
            <button
              onClick={() => setAiReportSection(!aiReportSection)}
              className="flex items-center gap-2 text-xs text-text-muted hover:text-text-primary mb-2"
            >
              {aiReportSection ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
              {aiReportSection ? 'Hide full report' : 'Show full report'}
            </button>
            {aiReportSection && (
              <div className="bg-surface-200/50 border border-border rounded-lg p-4 max-h-[600px] overflow-y-auto report-markdown"
                dangerouslySetInnerHTML={{ __html: mdToHtml(aiReport) }} />
            )}
          </div>
        )}
      </div>

      {/* Agent Pipeline — Detailed */}
      <div className="widget">
        <button onClick={() => toggleSection('workflow')} className="w-full flex items-center justify-between">
          <h2 className="text-sm font-bold text-text-primary uppercase tracking-wider flex items-center gap-2">
            <Activity size={14} className="text-accent-cyan" />
            Agent Pipeline — How Each Finding Was Discovered
          </h2>
          {expandedSection === 'workflow' ? <ChevronDown size={16} className="text-text-muted" /> : <ChevronRight size={16} className="text-text-muted" />}
        </button>
        {expandedSection === 'workflow' && (
          <div className="mt-4 space-y-3">
            {AGENTS_DETAILED.map((agent) => (
              <div key={agent.step} className="border border-border rounded-lg overflow-hidden">
                <button
                  onClick={() => setExpandedAgent(expandedAgent === agent.step ? null : agent.step)}
                  className="w-full flex items-center gap-3 p-3 bg-surface-200/50 hover:bg-surface-200 transition-colors text-left"
                >
                  <span className={`w-7 h-7 rounded-full bg-surface-200 border border-border flex items-center justify-center shrink-0 ${agent.color}`}>{agent.icon}</span>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-semibold text-text-primary">Step {agent.step}: {agent.name}</p>
                    <p className="text-xs text-text-muted">{agent.description}</p>
                  </div>
                  {expandedAgent === agent.step ? <ChevronDown size={14} className="text-text-muted shrink-0" /> : <ChevronRight size={14} className="text-text-muted shrink-0" />}
                </button>
                {expandedAgent === agent.step && (
                  <div className="p-3 border-t border-border space-y-3 text-xs">
                    <div>
                      <p className="font-semibold text-text-muted uppercase tracking-wider mb-1 flex items-center gap-1"><Terminal size={11} /> Methodology</p>
                      <p className="text-text-secondary leading-relaxed">{agent.methodology}</p>
                    </div>
                    <div>
                      <p className="font-semibold text-text-muted uppercase tracking-wider mb-1 flex items-center gap-1"><Server size={11} /> Bright Data Tool</p>
                      <p className="text-accent-cyan font-medium">{agent.tool}</p>
                    </div>
                    <div>
                      <p className="font-semibold text-text-muted uppercase tracking-wider mb-1 flex items-center gap-1"><Lightbulb size={11} /> Remediation Guidance</p>
                      <p className="text-text-secondary leading-relaxed">{agent.remediation}</p>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Per-Entity Reports */}
      <div className="space-y-4">
        {entities.map((entity) => {
          const entityFindings = findingsByEntity[entity.name] || [];
          const entityAlerts = alertsByEntity[entity.name] || [];
          const isOpen = expandedEntity === entity.name;
          const criticalCount = entityFindings.filter(f => f.severity === 'critical').length;
          const highCount = entityFindings.filter(f => f.severity === 'high').length;
          const pendingAlerts = entityAlerts.filter(a => a.status !== 'acknowledged').length;

          return (
            <div key={entity.id} className="widget">
              <button onClick={() => toggleEntity(entity.name)} className="w-full flex items-center justify-between gap-4">
                <div className="flex items-center gap-3 flex-1 min-w-0">
                  <div className={`w-10 h-10 rounded-lg flex items-center justify-center shrink-0 ${
                    criticalCount > 0 ? 'bg-accent-red/15' : highCount > 0 ? 'bg-orange-500/15' : 'bg-accent-cyan/15'
                  }`}>
                    <Shield size={18} className={criticalCount > 0 ? 'text-accent-red' : highCount > 0 ? 'text-orange-400' : 'text-accent-cyan'} />
                  </div>
                  <div className="flex-1 min-w-0 text-left">
                    <h3 className="text-sm font-bold text-text-primary">{entity.name}</h3>
                    <p className="text-xs text-text-muted capitalize">{entity.entity_type} &middot; Risk Score: {entity.current_risk_score?.toFixed(0) ?? 'N/A'}/100</p>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    {criticalCount > 0 && <span className="text-[10px] font-mono font-bold text-accent-red bg-red-500/10 px-1.5 py-0.5 rounded border border-red-500/20">{criticalCount} Critical</span>}
                    {highCount > 0 && <span className="text-[10px] font-mono font-bold text-orange-400 bg-orange-500/10 px-1.5 py-0.5 rounded border border-orange-500/20">{highCount} High</span>}
                    {pendingAlerts > 0 && <span className="text-[10px] font-mono font-bold text-accent-amber bg-amber-500/10 px-1.5 py-0.5 rounded border border-amber-500/20">{pendingAlerts} Alerts</span>}
                  </div>
                </div>
                {isOpen ? <ChevronDown size={16} className="text-text-muted shrink-0" /> : <ChevronRight size={16} className="text-text-muted shrink-0" />}
              </button>

              {/* Per-Entity AI Report button */}
              <div className="mt-3 flex items-center gap-2">
                <button
                  onClick={() => handleGenerateEntityReport(entity.name)}
                  disabled={entityAiReports[entity.name]?.loading}
                  className="flex items-center gap-1.5 px-3 h-7 rounded-md text-[10px] font-medium
                             bg-accent-purple/10 text-accent-purple border border-accent-purple/20
                             hover:bg-accent-purple/20 transition-all disabled:opacity-40"
                >
                  {entityAiReports[entity.name]?.loading ? <Loader2 size={12} className="animate-spin" /> : <Sparkles size={12} />}
                  {entityAiReports[entity.name]?.loading ? 'Generating...' : 'Generate AI Report'}
                </button>
                <a
                  href={`${API_BASE}/reports/html/${encodeURIComponent(entity.name)}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-1 px-3 h-7 rounded-md text-[10px] font-medium
                             bg-accent-cyan/10 text-accent-cyan border border-accent-cyan/20
                             hover:bg-accent-cyan/20 transition-all"
                >
                  <FileCode2 size={12} />
                  HTML Report
                </a>
              </div>

              {/* Entity AI Report display */}
              {entityAiReports[entity.name]?.report && (
                <div className="mt-3 bg-surface-200/50 border border-border rounded-lg p-3 max-h-[400px] overflow-y-auto report-markdown"
                  dangerouslySetInnerHTML={{ __html: mdToHtml(entityAiReports[entity.name].report) }} />
              )}
              {entityAiReports[entity.name]?.error && (
                <p className="mt-2 text-xs text-accent-red">{entityAiReports[entity.name].error}</p>
              )}

              {isOpen && (
                <div className="mt-4 pt-4 border-t border-border space-y-4">
                  {/* Detection Summary per Agent */}
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                    {AGENTS_DETAILED.slice(0, 3).map((agent) => {
                      const count = entityFindings.filter(f => {
                        const exp = getAgentExplanation(f);
                        return exp.agent.includes(agent.step);
                      }).length;
                      return (
                        <div key={agent.step} className="bg-surface-200/50 rounded-lg p-2.5 text-center">
                          <span className={agent.color}>{agent.icon}</span>
                          <p className="text-xs font-semibold text-text-primary mt-1">{agent.name.split('(')[0].trim()}</p>
                          <p className="text-lg font-bold font-mono text-text-primary">{count}</p>
                          <p className="text-[10px] text-text-muted">findings</p>
                        </div>
                      );
                    })}
                  </div>

                  {/* Detailed Findings */}
                  {entityFindings.length > 0 && (
                    <div>
                      <p className="text-xs font-semibold text-text-muted uppercase tracking-wider mb-2 flex items-center gap-1">
                        <Bug size={12} /> Detailed Findings & Remediation ({entityFindings.length})
                      </p>
                      <div className="space-y-2">
                        {entityFindings.slice(0, 15).map((f) => {
                          const exp = getAgentExplanation(f);
                          const rem = getFindingRemediation(f);
                          const isFindingOpen = expandedFinding === f.id;
                          const compliance = (f as any).compliance || [];

                          return (
                            <div key={f.id} className="border border-border rounded-lg overflow-hidden">
                              <button
                                onClick={() => setExpandedFinding(isFindingOpen ? null : f.id)}
                                className="w-full flex items-center gap-2 p-2.5 bg-surface-200/30 hover:bg-surface-200/50 transition-colors text-left"
                              >
                                <AlertTriangle size={12} className={`shrink-0 ${sevColor(f.severity)}`} />
                                <span className="flex-1 text-xs font-medium text-text-primary truncate">{f.title}</span>
                                <span className={`text-[10px] font-mono font-semibold px-1.5 py-0.5 rounded ${sevBg(f.severity)} ${sevColor(f.severity)}`}>{f.severity}</span>
                                {isFindingOpen ? <ChevronDown size={12} className="text-text-muted shrink-0" /> : <ChevronRight size={12} className="text-text-muted shrink-0" />}
                              </button>
                              {isFindingOpen && (
                                <div className="p-3 border-t border-border space-y-3 text-xs bg-surface-100/50">
                                  {/* Agent Explanation */}
                                  <div className="space-y-1.5">
                                    <p className="font-semibold text-text-muted uppercase tracking-wider flex items-center gap-1"><Search size={11} /> Discovery Method</p>
                                    <div className="bg-surface-200/70 rounded p-2 space-y-1">
                                      <p><span className="text-text-muted">Agent:</span> <span className="text-accent-cyan font-medium">{exp.agent}</span></p>
                                      <p><span className="text-text-muted">How:</span> <span className="text-text-secondary">{exp.how}</span></p>
                                      <p><span className="text-text-muted">Bright Data Tool:</span> <span className="text-accent-green font-medium">{exp.brightdata}</span></p>
                                    </div>
                                  </div>

                                  {/* Remediation */}
                                  <div className="space-y-1.5">
                                    <p className="font-semibold text-text-muted uppercase tracking-wider flex items-center gap-1"><Lightbulb size={11} /> Remediation</p>
                                    <div className="bg-surface-200/70 rounded p-2 space-y-1">
                                      <p><span className="text-text-muted">Action:</span> <span className="text-text-primary font-medium">{rem.action}</span></p>
                                      <p><span className="text-text-muted">Effort:</span> <span className="text-text-secondary">{rem.effort}</span></p>
                                      <p><span className="text-text-muted">Priority:</span> <span className={sevColor(f.severity)}>{rem.priority}</span></p>
                                      <div className="mt-1.5 pt-1.5 border-t border-border">
                                        <p className="text-text-muted mb-0.5">Details:</p>
                                        <pre className="text-text-secondary font-mono text-[10px] leading-relaxed whitespace-pre-wrap">{rem.details}</pre>
                                      </div>
                                    </div>
                                  </div>

                                  {/* Compliance Impact */}
                                  {compliance.length > 0 && (
                                    <div className="space-y-1">
                                      <p className="font-semibold text-text-muted uppercase tracking-wider">Compliance Impact</p>
                                      <div className="flex flex-wrap gap-1">
                                        {compliance.map((c: any, i: number) => (
                                          <span key={i} className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-medium border ${regColors[c.regulation] || 'text-text-secondary bg-surface-200 border-border'}`}>
                                            {c.regulation === 'SOC2' ? 'SOC 2' : c.regulation} {c.article}
                                          </span>
                                        ))}
                                      </div>
                                    </div>
                                  )}

                                  {/* Source */}
                                  {(f as any).source_url && (
                                    <div>
                                      <p className="font-semibold text-text-muted uppercase tracking-wider mb-1">Source</p>
                                      <a href={(f as any).source_url} target="_blank" rel="noopener noreferrer"
                                        className="text-accent-cyan hover:underline flex items-center gap-1 break-all">
                                        <ExternalLink size={11} /> {(f as any).source_url}
                                      </a>
                                    </div>
                                  )}
                                </div>
                              )}
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )}

                  {/* Alerts */}
                  {entityAlerts.length > 0 && (
                    <div>
                      <p className="text-xs font-semibold text-text-muted uppercase tracking-wider mb-2 flex items-center gap-1"><Bell size={12} /> Active Alerts ({entityAlerts.length})</p>
                      <div className="space-y-1">
                        {entityAlerts.map((a) => (
                          <div key={a.id} className="flex items-center gap-2 p-2 rounded bg-surface-200/50 text-xs">
                            <AlertTriangle size={12} className={a.status === 'acknowledged' ? 'text-text-muted' : 'text-accent-red'} />
                            <span className="flex-1 text-text-primary truncate">{a.title}</span>
                            {a.notes && <span className="text-[10px] text-accent-green font-medium">Fixed: {a.notes}</span>}
                            <span className={`text-[10px] font-mono ${a.status === 'acknowledged' ? 'text-accent-green' : 'text-accent-amber'}`}>{a.status}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}

        {entities.length === 0 && (
          <div className="widget py-12 text-center">
            <FileText size={40} className="mx-auto mb-3 text-text-muted/30" />
            <p className="text-text-muted text-sm">No entities to report on.</p>
          </div>
        )}
      </div>
    </div>
  );
}
