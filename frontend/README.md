# SentinelWatch Frontend

A Grafana/Kibana-inspired security monitoring dashboard for **SentinelWatch** — an AI-powered security and compliance platform.

Built for the **Web Data UNLOCKED AI Hackathon** by Bright Data × lablab.ai.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Framework | React 18 + TypeScript |
| Build | Vite 5 |
| Styling | Tailwind CSS 3 |
| Charts | Recharts |
| Icons | Lucide React |
| Routing | React Router v6 |
| Backend | FastAPI (Python) |
| Data | Bright Data (Web Unlocker, SERP API) |

---

## Design

**Dark SOC/NOC aesthetic** inspired by Grafana, Kibana, and GitHub:

- Background: `#0B0F19` (deep navy)
- Cards: `#131826` with `#1E2433` borders
- Accent: `#22D3EE` cyan (primary), `#EF4444` red (critical)
- Fonts: **Plus Jakarta Sans** (UI) + **JetBrains Mono** (data/metrics)
- Components: custom `.widget`, `.badge-*`, `.nav-item` CSS utility classes
- Glow effects for severity indicators (critical/high)

---

## Pages

### Dashboard (`/`)
- 4 animated stat cards: Total Findings, Critical, Monitored Entities, Active Alerts
- Severity Distribution donut chart with color-coded bar breakdown
- Risk Score gauge (arc visualization, color-coded green/amber/red)
- Quick Stats with progress bars (High/Medium/Low)
- 14-day Finding Trends area chart (4 severity traces with gradient fills)
- Recent Findings compact table (last 6)
- Active Alerts widget with acknowledge buttons

### Findings (`/findings`)
- Filterable table with all 15 findings
- Severity filter dropdown (All / Critical / High / Medium / Low / Info)
- Live search by title
- Color-coded severity badges (critical=red, high=orange, medium=amber, low=blue, info=slate)

### Alerts (`/alerts`)
- 7 active alerts with severity indicator dots
- Acknowledge button per alert (calls `POST /api/v1/alerts/{id}/acknowledge`)
- Unacknowledged count badge

### Entities (`/entities`)
- Entity cards showing name, type, risk score, domains, last assessed date
- Risk score: 0-39 green, 40-69 amber, 70+ red
- Live search by entity name
- Currently tracking: Bright Data (risk 73), AI/ML API (risk 45)

### Investigations (`/investigations`)
- "Run Investigation" button triggers `POST /api/v1/investigate`
- Shows investigation results with confidence score, evidence sources, recommendations
- Empty state when no investigations have been run

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/dashboard/summary` | Dashboard metrics, severity breakdown, timeline, recent findings |
| GET | `/api/v1/findings` | Paginated findings list with optional severity/entity filters |
| GET | `/api/v1/alerts` | All alerts |
| POST | `/api/v1/alerts/{id}/acknowledge` | Acknowledge an alert |
| GET | `/api/v1/entities` | All monitored entities |
| POST | `/api/v1/investigate` | Run AI investigation on an entity |
| POST | `/api/v1/seed` | Seed 15 demo findings + 7 alerts |

---

## Getting Started

```bash
# Install dependencies
cd frontend && npm install

# Start development server (runs on :5173, proxies /api to :8000)
npm run dev

# Production build
npm run build
```

The Vite dev server proxies `/api/*` requests to `http://127.0.0.1:8000`, so both servers must be running:

```bash
# Backend (from project root)
python -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

# Seed demo data (15 findings, 7 alerts)
curl -X POST http://localhost:8000/api/v1/seed

# Add entities
curl -X POST http://localhost:8000/api/v1/entities \
  -H "Content-Type: application/json" \
  -d '{"name":"Bright Data","entity_type":"organization","metadata":{"domains":["brightdata.com"]}}'

curl -X POST http://localhost:8000/api/v1/entities \
  -H "Content-Type: application/json" \
  -d '{"name":"AI/ML API","entity_type":"organization","metadata":{"domains":["aimlapi.com"]}}'
```

---

## Project Structure

```
frontend/
├── index.html              # HTML shell with Google Fonts
├── vite.config.ts          # Vite config + API proxy
├── tailwind.config.js      # Custom theme (colors, fonts, animations)
├── postcss.config.js
├── tsconfig.json
├── package.json
├── public/
│   └── favicon.svg         # Shield icon
└── src/
    ├── main.tsx            # React entry + BrowserRouter
    ├── index.css           # Tailwind layers + .widget/.badge/.nav-item classes
    ├── App.tsx             # Router configuration
    ├── types/
    │   └── index.ts        # TypeScript interfaces
    ├── api/
    │   └── client.ts       # API fetch wrapper
    ├── hooks/
    │   └── useSSE.ts       # Server-Sent Events hook
    ├── components/
    │   ├── Layout.tsx       # Sidebar + main area shell
    │   ├── Sidebar.tsx      # Collapsible navigation
    │   ├── StatCard.tsx     # Animated metric counter
    │   ├── SeverityChart.tsx # Donut chart
    │   ├── FindingsTable.tsx # Searchable findings list
    │   ├── AlertList.tsx    # Alert feed with acknowledge
    │   ├── TimelineChart.tsx # Area chart
    │   └── RiskGauge.tsx    # Arc gauge
    └── pages/
        ├── Dashboard.tsx
        ├── Findings.tsx
        ├── Alerts.tsx
        ├── Entities.tsx
        └── Investigations.tsx
```
