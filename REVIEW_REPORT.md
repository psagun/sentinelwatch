# SentinelWatch Consolidated Code Review Report

**Generated:** 2026-05-29  
**Scope:** UX/UI, Security, Code Quality, Bright Data Integration

---

## 1. Executive Summary

SentinelWatch shows strong foundational architecture with clean domain separation, a polished dark-theme UI, and thoughtful fallback patterns across data collectors. However, four critical issues demand immediate attention before any production deployment: **no authentication on any API route**, **committed credentials in version control**, **SQL injection risk in database layer**, and a **browser-native multi-select dropdown that silently behaves as single-select** (the latter being a functional bug, not just a code quality concern).

The four review areas scored as follows, with Security being the most urgent area at 3/10:

| Area | Score | Assessment |
|------|-------|-----------|
| UX/UI | 6.5/10 | Polished design, inconsistent filter UX, missing feedback |
| Security | 3/10 | No auth, exposed credentials, multiple OWASP Top 10 violations |
| Code Quality | 6/10 | Good architecture, bloated files, loose types, dead code |
| Bright Data | 6/10 | Good abstraction, no retry/caching, credential leakage via CLI |

**Top 5 Immediate Actions:**
1. Rotate all exposed credentials and add `.env` to `.gitignore` (Security)
2. Add authentication middleware to all API routes (Security)
3. Fix SQL injection vector in `database.py` with table name whitelist (Security)
4. Fix the entity filter bug in `Dashboard.tsx` — single-select state typed as multi-select (UX/UI + Code Quality)
5. Replace sequential batch operations with `Promise.allSettled` in `Alerts.tsx` (UX/UI + Code Quality)

---

## 2. Score Summary

| Category | Score | Key Strengths | Key Weaknesses |
|----------|-------|---------------|----------------|
| **UX/UI** | 6.5 / 10 | Polished dark theme, excellent state coverage, sophisticated multi-step modal | Inconsistent filter UX, no toast system, no error boundary, hardcoded URLs |
| **Security** | 3 / 10 | Pydantic validation, HTTPS for external calls, parameterized queries for values | No auth, committed credentials, SQL injection via table names, CORS misconfig |
| **Code Quality** | 6 / 10 | Domain separation, write-through DB pattern, graceful fallbacks | 1214-line routes.py, `__import__` anti-pattern, loose TypeScript types |
| **Bright Data** | 6 / 10 | 3 products integrated, clean abstraction layer, REST+CLI fallback | No retry, no caching, CLI credential leak, dead `web_unlocker_post` |

---

## 3. Critical Issues

These issues must be addressed before any production deployment or further development. They represent security vulnerabilities, data loss risks, or functional bugs that break core workflows.

### 3.1 No Authentication (Security)
Every API route — including `/seed`, `/scan`, `/delete`, `/entities` — is publicly accessible with no middleware, JWT, or API key check. This makes the entire system trivially exploitable by any network-adjacent attacker.
- **Files:** `routes.py` (all endpoints)
- **Fix:** Add FastAPI `Depends` middleware validating a bearer token signed with `SECRET_KEY` on every route.

### 3.2 Committed Credentials in Version Control (Security + Bright Data)
The `.env` file contains `BRIGHTDATA_API_KEY`, `AIML_API_KEY`, `BRIGHTDATA_USERNAME`, `DATABASE_URL`, and `SECRET_KEY` — all tracked by git. The API key `f5df44b0-c473-41d0-8b17-016137b6ca70` is also passed as a CLI argument (`-k` flag) in `brightdata_client.py`, visible to all processes via `ps`/`wmic`.
- **Files:** `.env`, `brightdata_client.py` (lines 47-48)
- **Fix:** Rotate all keys immediately. Add `.env` to `.gitignore`. Remove from git history with `git filter-branch`. Switch CLI auth to environment variables only.

### 3.3 SQL Injection via Table Names (Security)
`database.py` interpolates table names via f-strings in `INSERT OR REPLACE INTO {table}` queries with no whitelist validation. While data values use parameterized `?` placeholders, the table name interpolation opens the door to injection if any caller passes unsanitized input.
- **Files:** `database.py`
- **Fix:** Add `ALLOWED_TABLES = {'findings', 'alerts', 'entities', 'investigations', 'scans'}` and validate before any f-string interpolation.

### 3.4 Dashboard Entity Filter is Broken (UX/UI + Code Quality)
The entity filter dropdown in `Dashboard.tsx` line 137 is typed as `string[]` (suggesting multi-select) but implements single-select logic: `prev.includes(e) ? [] : [e]`. Users can never select more than one entity, despite the UI implying they can. Meanwhile, the identical dropdown in `Alerts.tsx` uses genuine multi-select (`toggleEntity` adds/removes), creating an inconsistent cross-page experience.
- **Files:** `Dashboard.tsx` (line 137), `Alerts.tsx` (lines 33, 113-169)
- **Fix:** Decide on single vs multi-select semantics, make the type match the behavior, and extract a shared `EntityFilterDropdown` component.

---

## 4. High Priority Recommendations

Important issues that significantly impact security, performance, or maintainability. Organized by area.

### 4.1 Security

- **Full exception leakage to API clients:** `routes.py` lines 858-862 return stack traces and internal paths in error responses. Return generic errors to clients; log full details server-side with `logger.exception()`.
- **SSL verification disabled:** `web_scraper.py` line 210 uses `verify=False` on HTTPS connections, enabling MITM attacks on security header checks. Remove the `verify=False` override.
- **CORS misconfiguration:** `main.py` uses `allow_origins=['*']` with `allow_credentials=True`, which browsers reject. Set explicit origins from an environment variable.
- **No SSRF protection:** User-supplied URLs are passed directly to Bright Data Web Unlocker and direct HTTP connections. Block RFC 1918 private IPs, link-local, and loopback addresses. Restrict schemes to `https://`.
- **No rate limiting:** All API endpoints can be abused without throttling. Add `slowapi` or similar middleware, especially on `/scan` and `/seed`.
- **Docker runs as root:** No `USER` directive in the Dockerfile. Add `adduser sentinel && USER sentinel`.
- **Weak/default secrets:** `config.py` has `SECRET_KEY = 'change-me-in-production'`. Default PostgreSQL password `sentinel` is hardcoded in `docker-compose.yml`.
- **Weak database security:** SQLite file is unencrypted at rest; database path is hardcoded relative path `sentinelwatch.db` with no configurable option.

### 4.2 UX/UI

- **No error boundary:** A render crash in any component collapses the entire application. Wrap the app in `react-error-boundary` with a user-friendly fallback.
- **No 404 catch-all route:** Unrecognized paths silently fall through with no error display. Add `<Route path="*" element={<NotFound />}>` to `App.tsx`.
- **No toast/notification system:** Operations like acknowledging alerts or deleting entities provide zero success feedback. Silent `catch` blocks swallow errors. Add `react-hot-toast` or a custom context provider.
- **`window.confirm()` for destructive actions:** Delete alert/finding/entity uses browser-native dialogs instead of an in-app modal, breaking the dark-theme consistency. Replace with a custom confirmation dialog.
- **Hardcoded `localhost:8000` URLs:** `Reports.tsx` lines 322-323 and 498-499 hardcode the development URL. Replace with `API_BASE` from config or a `VITE_API_URL` env var.
- **No pagination on Findings page:** `Findings.tsx` loads up to 100 results with no page navigation. Add server-side page/size query params and Previous/Next controls.

### 4.3 Code Quality

- **`routes.py` is 1214 lines:** Mixes route definitions, background task orchestration, inline HTML templates, and a seed endpoint. Split into `routes/scans.py`, `routes/findings.py`, `routes/entities.py`, `routes/reports.py`, `routes/dashboard.py`.
- **`__import__` anti-pattern:** At least 8 calls to `__import__("datetime")` and similar for `json` and `uuid` in `routes.py` instead of using the already-imported module at line 4.
- **Batch operations are sequential:** `Alerts.tsx` lines 59-61 and 70-72 use `for ... await` loops, making N sequential HTTP requests. Replace with `Promise.allSettled(...)`.
- **Loose TypeScript types:** `severity`, `status`, `finding_type`, `entity_type` are all `string` instead of union types. `Entity.metadata` uses `Record<string, any>`. Add strict union types throughout.
- **`fetchJSON<any>()` everywhere:** Frontend `client.ts` uses untyped fetches and manually reshapes responses. Backend API shape and frontend types are not aligned — silent breakage risk.
- **Unhandled background task exceptions:** `asyncio.create_task` calls in `routes.py` are fire-and-forget with no error surfacing mechanism. Wrap with a utility that logs and updates scan status on failure.

### 4.4 Bright Data Integration

- **No retry logic despite config declaring it:** `monitoring_config.yaml` specifies `retry_attempts: 3` and `retry_delay_seconds: 5`, but no Bright Data API call implements retries. Every transient error is a hard failure.
- **No caching layer:** Every SERP search, Web Unlocker fetch, and Scraping Browser launch hits the API fresh. SERP results are prime caching candidates (slow-changing). Redis was documented for this but never wired up.
- **CLI credential leak:** `-k {self.api_key}` in `brightdata_client.py` line 47 leaks the key in process listings. Switch to env-var-only auth and remove the `-k` argument.
- **`web_unlocker_post` is dead code:** It ignores `form_data` and delegates to `web_unlocker_get()`, providing GET semantics despite the POST name. Either implement POST or remove the method.
- **Sequential collection:** `threat_collector.collect()` runs 5 search methods sequentially when all are independent I/O operations. Use `asyncio.gather` to parallelize.
- **Silent error swallowing:** `web_unlocker_get()` returns `''` on failure; `serp_search()` returns `[]`. Callers cannot distinguish "API down" from "no results." Surface health status.

---

## 5. Medium Priority Improvements

Enhancements that improve polish, maintainability, and developer experience but are not blocking.

### 5.1 UX/UI

- **Unacknowledged alert badge on Sidebar:** No count badge on the Alerts nav item, which is a standard security dashboard affordance for quick triage.
- **Pause polling when tab is backgrounded:** `Entities.tsx` (3s polling) and `AddEntityModal.tsx` (2s polling) continue when the tab is hidden. Add `document.hidden` check via a `usePageVisibility` hook.
- **Quick Stats widget missing Critical findings:** Dashboard shows High/Medium/Low progress bars but omits the most important severity tier. Add Critical or consolidate severity info.
- **Misleading stat card label:** Dashboard's "Monitored Entities" card changes title based on filter state, conflating filtering with metric labeling. Always show the true count; move entity name to the filter label.
- **Hardcoded RiskGauge thresholds:** Color thresholds (40/70 for Low/Medium/High) are hardcoded with no explanation of what contributes to the score. Add a tooltip or documentation.
- **No keyboard navigation:** Tab order, arrow keys in lists, Escape to close modals — none implemented. Add focus rings and keyboard handlers.
- **Non-core nav items mixed with product nav:** "Hackathon" and "About" sit alongside core security pages in the sidebar. Move to a secondary section with a divider.
- **No shared state between pages:** Dashboard and Alerts each fetch their own entity lists and maintain independent filter state. Consider a shared data layer (React Context or Zustand).

### 5.2 Security

- **Sensitive findings leaked to PagerDuty:** `alert_manager.py` line 213 sends finding details as unredacted `custom_details`. Sanitize data bound for third-party alerting services.
- **No CSRF protection:** Despite `allow_credentials=True`, there is no CSRF token validation. Add CSRF middleware for cookie-based session support.
- **Redis without password:** `docker-compose.yml` configures Redis with no authentication. Add `requirepass` and update the connection string.
- **No dependency vulnerability scanning:** No `pip-audit` or `safety` in CI/CD or `requirements.txt`.
- **No HTTPS/TLS:** The API server has no TLS configuration. Implement termination via reverse proxy (nginx/Caddy) or uvicorn SSL options.
- **Typo in env variable name:** `BDRIGHT_DATA_API_KEY` vs `BRIGHT_DATA_API_KEY` in `brightdata_client.py` line 54.
- **Unused `psycopg2-binary` dependency:** Listed in requirements but the code uses SQLite via `aiosqlite`. Remove to reduce attack surface.

### 5.3 Code Quality

- **Duplicate compliance label logic:** `_reg_label` in `classifier.py` and `get_regulation_label` in `rules.py` are identical. Consolidate.
- **Duplicate severity keyword logic:** `_infer_severity` in `threat_collector.py` duplicates keyword matching from `analysis_agent.py` `SEVERITY_KEYWORDS`. Extract to a shared module.
- **Unstable React list keys:** `FindingsTable` uses `key={f.id ?? i}` falling back to array index, causing unnecessary re-renders when findings are reordered. Use a stable composite key.
- **MCP Server references are misleading:** Documentation and docstrings claim MCP Server integration, but `mcp_client.py` does not exist and `get_mcp_server_config()` just returns credentials. Either implement or update docs.
- **Reports.tsx is 654 lines monolithic:** Hardcoded agent descriptions (`AGENTS_DETAILED`), remediation templates (`REMEDIATION`), rendering, and AI logic all in one component. Extract data/config and split into subcomponents.
- **Custom regex markdown parser:** `utils/markdown.ts` uses `dangerouslySetInnerHTML` with a fragile regex parser. Replace with `react-markdown` or `marked` for spec compliance and safety.
- **Compliance.tsx piggybacks on dashboard endpoint:** Uses `getDashboardMetrics` instead of a dedicated compliance API, coupling compliance data to an endpoint not designed for this purpose.
- **Zone configuration is fragile:** `brightdata_zone` defaults to empty string, and the REST API fallback zone `cli_unlocker` may not exist in the user's account. Validate at startup.

### 5.4 Bright Data Integration

- **REST-then-CLI fallback doubles cost:** On transient REST errors, `web_unlocker_get()` charges for the same URL twice (REST failure + CLI fallback). Use REST-only with retry instead.
- **Excessive SERP calls:** `threat_collector._search_security_blogs()` has a keyword x blog_sources nested loop making up to 6 calls per entity. Consolidate into broader queries.
- **Scraping Browser underutilized:** Only used for basic page rendering. No screenshot capture, network interception, cookie/session handling, or form interaction.
- **No health check method:** No `BrightDataClient.health_check()` to ping BD API and report connectivity/credit status. Surface this in the `/health` endpoint.

---

## 6. Strengths

### 6.1 Architecture & Design
- **Clean domain separation:** `data_collection/`, `intelligence/`, `compliance/`, `alerting/` form clear architectural boundaries with distinct responsibilities. The `memory/` module anticipates long-term persistence needs.
- **Write-through database pattern:** `database.py` combines in-memory lists, SQLite with WAL mode, per-table async locks, and `bulk_save` — pragmatic and performant for this stage.
- **Graceful fallback architecture:** `AnalysisAgent` tries AI/ML API first, falls back to keyword matching; `BrightDataClient.web_unlocker_get` tries REST API, falls back to CLI. System stays functional when paid services are unavailable.
- **Smart compliance classification:** `classifier.py` + `rules.py` use declarative rule tables with separate passes for check_type, title keywords, and finding_type. Dedup via `seen` set prevents redundant tags.
- **Sound risk scoring:** `RiskScorer` accounts for recency, severity weights, and entity aggregation with a 0-100 normalized scale and configurable thresholds.
- **Graceful collector degradation:** Each data collector wraps individual checks in try/except blocks. Bright Data errors are logged at warning level and return empty results rather than crashing pipelines.

### 6.2 UX/UI
- **Polished dark-theme design system:** Consistent color tokens, severity badges, widget cards, and transitions across all pages (`index.css` defines reusable component classes).
- **Excellent state coverage:** Every page handles loading spinners, empty states (with contextual CTAs), and error states. Entities page has distinct empty states for "no entities yet" vs "no search results."
- **Sophisticated modal UX:** `AddEntityModal` has a multi-step flow (form -> scanning -> complete/error) with polling, URL-to-name inference, expandable advanced config, and close prevention during scanning.
- **Thoughtful alert workflow:** Inline resolution notes textarea within the accordion acknowledgment flow reduces context switching.
- **Animated stat cards:** `StatCard` uses IntersectionObserver for progressive number roll-up — premium feel with performance mindfulness.
- **Drill-down pattern:** Action buttons on stat cards navigate to detail pages, providing natural task flow from summary to detail.

### 6.3 Bright Data Integration
- **Three products integrated:** Web Unlocker, SERP API, and Scraping Browser are meaningfully used across threat intelligence, compliance monitoring, and third-party risk — meeting the hackathon minimum requirement.
- **Clean abstraction layer:** `BrightDataClient` isolates all BD logic behind typed methods. All 5 collectors import from this single client, not from BD APIs directly.
- **Smart SERP parsing:** `_parse_search_output()` handles NDJSON output, normalizes organic and news results consistently, and respects `max_results` limits.
- **Proper async subprocess management:** `_run_cli()` uses `asyncio.create_subprocess_exec` with `wait_for` timeout, `communicate()` for pipe handling, and decoded stdout for parsing.

---

## 7. Action Plan

Prioritized list of changes grouped by implementation effort.

### Quick Wins (1-2 hours each)

| Priority | Task | Area | Files |
|----------|------|------|-------|
| 1 | Add `.env` to `.gitignore` and rotate all exposed credentials | Security | `.env`, repo root |
| 2 | Fix Dashboard entity filter — make type match single-select behavior | UX/UI, Code Quality | `Dashboard.tsx` line 137 |
| 3 | Replace `for await` batch loops with `Promise.allSettled` | UX/UI, Code Quality | `Alerts.tsx` lines 59-61, 70-72 |
| 4 | Fix `__import__` calls to use top-level imports | Code Quality | `routes.py` lines 289, 352-354, 451, etc. |
| 5 | Hardcode `localhost:8000` -> config constant | UX/UI | `Reports.tsx` lines 322-323, 498-499 |
| 6 | Fix env var typo `BDRIGHT_DATA_API_KEY` | Security, Bright Data | `brightdata_client.py` line 54 |
| 7 | Remove unused `psycopg2-binary` dependency | Security | `requirements.txt` |
| 8 | Add `USER` directive to Dockerfile | Security | `Dockerfile` |
| 9 | Add `<Route path="*">` 404 catch-all | UX/UI | `App.tsx` |
| 10 | Remove `verify=False` from httpx calls | Security | `web_scraper.py` line 210 |

### Medium Effort (half day each)

| Priority | Task | Area | Files |
|----------|------|------|-------|
| 11 | Add table name whitelist to `database.py` | Security | `database.py` |
| 12 | Wrap app in `ErrorBoundary` | UX/UI | `App.tsx` |
| 13 | Implement retry with exponential backoff on BD API calls | Bright Data | `brightdata_client.py` |
| 14 | Add Redis-backed caching for SERP results | Bright Data | `brightdata_client.py`, config |
| 15 | Replace `window.confirm()` with custom modal | UX/UI | Throughout |
| 16 | Add toast notification system | UX/UI | New file, update all routes |
| 17 | Parallelize `threat_collector.collect()` with `asyncio.gather` | Bright Data | `threat_collector.py` |
| 18 | Create shared `EntityFilterDropdown` component | UX/UI, Code Quality | New file, update Dashboard + Alerts |
| 19 | Strip `-k` CLI arg, use env var only for BD auth | Security, Bright Data | `brightdata_client.py` |
| 20 | Add rate limiting middleware | Security | `main.py` |
| 21 | Add pagination to Findings page | UX/UI | `Findings.tsx`, `client.ts` |
| 22 | Replace regex markdown parser with `react-markdown` | UX/UI, Code Quality | `utils/markdown.ts` |
| 23 | Upgrade TypeScript types to strict unions | Code Quality | `types/index.ts`, throughout |
| 24 | Consolidate duplicate `_reg_label` / `get_regulation_label` | Code Quality | `classifier.py`, `rules.py` |
| 25 | Extract severity keywords into shared module | Code Quality | `analysis_agent.py`, `threat_collector.py`, new file |
| 26 | Fix `web_unlocker_post` (implement POST or remove) | Code Quality, Bright Data | `brightdata_client.py` |

### Large Effort (1-2 days each)

| Priority | Task | Area | Files |
|----------|------|------|-------|
| 27 | Add authentication middleware to all API routes | Security | `routes.py`, `main.py` |
| 28 | Split `routes.py` into domain modules | Code Quality | `routes/` directory |
| 29 | Decompose `Reports.tsx` into subcomponents | UX/UI, Code Quality | `Reports.tsx` |
| 30 | Align backend API responses with frontend types | Code Quality | `client.ts`, `types/index.ts`, routes |
| 31 | Implement or remove MCP Server references | Bright Data, Code Quality | Throughout |
| 32 | Add unacknowledged alert count badge to Sidebar | UX/UI | `Sidebar.tsx`, new state |
| 33 | Implement shared state layer (Context/Zustand) | UX/UI | New file, update consumers |
| 34 | Add `health_check()` to Bright Data client | Bright Data | `brightdata_client.py`, health endpoint |
| 35 | Add document.hidden pause to polling | UX/UI | `Entities.tsx`, `AddEntityModal.tsx` |
| 36 | Implement keyboard navigation | UX/UI | Throughout |
| 37 | Refactor Compliance.tsx to use dedicated endpoint | UX/UI, Code Quality | `Compliance.tsx`, routes |
| 38 | Add CSRF protection | Security | `main.py` |
| 39 | Implement TLS termination | Security | nginx config or uvicorn options |
| 40 | Validate zone configuration at startup | Bright Data | `brightdata_client.py` |
| 41 | Add SSRF protection for user-supplied URLs | Security | URL validation helper |
| 42 | Sanitize finding data for PagerDuty/Slack | Security | `alert_manager.py` |
| 43 | Add dependency vulnerability scanning | Security | CI/CD config |

---

## File Index

Key files referenced throughout this report:

| File | Path | Relevance |
|------|------|-----------|
| Main API routes | `src/api/routes.py` | Security, Code Quality (bloat) |
| Database layer | `src/api/database.py` | Security (SQL injection) |
| Bright Data client | `src/data_collection/brightdata_client.py` | Security (credential leak), Bright Data |
| Web scraper | `src/data_collection/web_scraper.py` | Security (SSL verify=False) |
| Threat collector | `src/data_collection/threat_collector.py` | Code Quality, Bright Data |
| Alert manager | `src/alerting/alert_manager.py` | Security (data leak) |
| Dashboard page | `src/api/frontend/src/pages/Dashboard.tsx` | UX/UI (filter bug, stat cards) |
| Alerts page | `src/api/frontend/src/pages/Alerts.tsx` | UX/UI (batch ops, filter inconsistency) |
| Reports page | `src/api/frontend/src/pages/Reports.tsx` | UX/UI (monolithic, hardcoded URLs) |
| Findings table | `src/api/frontend/src/pages/FindingsTable.tsx` | UX/UI (unstable keys) |
| Markdown utils | `src/api/frontend/src/utils/markdown.ts` | UX/UI (fragile parser) |
| API client | `src/api/frontend/src/client.ts` | Code Quality (loose types) |
| TypeScript types | `src/api/frontend/src/types/index.ts` | Code Quality (string instead of union) |
| Config | `src/api/config.py` | Security (weak secret) |
| Sidebar | `src/api/frontend/src/components/Sidebar.tsx` | UX/UI (no badge, non-core nav) |
| Risk gauge | `src/api/frontend/src/components/RiskGauge.tsx` | UX/UI (hardcoded thresholds) |
| Entity modal | `src/api/frontend/src/components/AddEntityModal.tsx` | UX/UI (no tab-background pause) |
| Classifier | `src/intelligence/classifier.py` | Code Quality (duplicate logic) |
| Rules | `src/compliance/rules.py` | Code Quality (duplicate labels) |
| Analysis agent | `src/intelligence/analysis_agent.py` | Code Quality (duplicate keywords) |
| Dockerfile | `Dockerfile` | Security (root user) |
| Docker Compose | `docker-compose.yml` | Security (no Redis password) |
| Monitoring config | `monitoring_config.yaml` | Bright Data (declared but unused retry config) |
