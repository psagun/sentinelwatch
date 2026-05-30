# SentinelWatch: Scraping Browser + Hackathon Page Design

## Part 1: Scraping Browser Integration

### Goal
Integrate Bright Data Scraping Browser as the 3rd Bright Data product (alongside Web Unlocker and SERP API).

### A) Web Scraper — `src/data_collection/web_scraper.py`
- Add `_check_with_browser()` method
- Runs after all existing checks (well-known paths, headers, SSL, server info, accessibility)
- Launches `brightdata.scraping_browser_navigate(url)` to get JS-rendered DOM
- Analyzes DOM for:
  - Third-party scripts loaded
  - Inline JavaScript (potential XSS vectors)
  - Mixed content warnings
  - Suspicious redirect chains
- Produces `WebScraperFinding` entries with `check_type: "browser"`

### B) Investigation Agent — `src/intelligence/investigation_agent.py`
- Add 4th investigation step: `_browser_investigation()`
- For `domain` or `url` indicator types, launch Scraping Browser
- Capture screenshot description in evidence
- Check for malicious JS, redirects
- Store as evidence with `source: "scraping_browser"`

### C) Frontend — evidence display
- Scan detail view shows browser-based findings alongside other findings
- Investigation detail shows browser evidence with source type label

## Part 2: Hackathon Rubric Page

### New Frontend Page
- **File:** `frontend/src/pages/Hackathon.tsx`
- **Route:** `/hackathon`
- **Sidebar:** Add "Hackathon" nav item with Award/Trophy icon

### Sections

#### 1. Bright Data Products Used
| Product | Usage in SentinelWatch |
|---------|----------------------|
| **Web Unlocker** | Fetches security.txt, robots.txt, paste sites, compliance pages, abuse check pages — bypasses CAPTCHAs and geo-blocks |
| **SERP API** | Searches Google for threat intel (CVE mentions, leak sites), brand monitoring (impersonation, phishing), compliance news, vendor reputation |
| **Scraping Browser** | Full browser automation for JS-heavy security analysis, screenshot capture, third-party script detection, malicious redirect inspection |

#### 2. Partner Technologies
- **AI/ML API** — Powers threat analysis, severity classification, investigation verdicts
- **FastAPI** — REST API framework
- **React + Vite** — Frontend dashboard
- **Bright Data CLI/SDK** — Web data collection infrastructure

#### 3. Hackathon Track
- **Track 3: Security & Compliance**
- Real-time security posture monitoring
- Automated threat intelligence gathering
- Compliance violation detection (GDPR, SOC 2)
- AI-powered investigation and risk scoring

#### 4. Rubric Checklist
- ✅ 3+ Bright Data products integrated (Web Unlocker, SERP API, Scraping Browser)
- ✅ AI/ML API integration for analysis
- ✅ Real-time monitoring dashboard
- ✅ Interactive UI with filtering and search
- ✅ REST API for programmatic access
- ✅ Background scanning and alerting

## Files to Modify

### Backend
- `src/data_collection/web_scraper.py` — Add `_check_with_browser()`
- `src/data_collection/brightdata_client.py` — (already has `scraping_browser_navigate`)
- `src/intelligence/investigation_agent.py` — Add browser investigation step

### Frontend
- `frontend/src/pages/Hackathon.tsx` — New page
- `frontend/src/pages/About.tsx` — Update to reference hackathon page
- `frontend/src/App.tsx` — Add hackathon route
- `frontend/src/components/Sidebar.tsx` — Add nav item
- `frontend/src/types/index.ts` — Add 'hackathon' to NavPage

## Verification
1. Run `POST /api/v1/scan` on a JS-heavy site → verify browser findings appear
2. Run `POST /api/v1/investigate` on a domain → verify browser evidence included
3. Navigate to `/hackathon` page → verify all 4 sections render
4. Check sidebar has "Hackathon" nav item
