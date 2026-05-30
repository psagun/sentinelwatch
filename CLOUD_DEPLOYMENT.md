# SentinelWatch Cloud Deployment Strategy

> **Project**: SentinelWatch — AI-Powered Security & Compliance Monitoring Platform  
> **Stack**: FastAPI (Python 3.11) + React/Vite + SQLite/PostgreSQL  
> **External APIs**: Bright Data Web Unlocker/SERP API, AI/ML API  
> **Context**: Hackathon demo / small-scale deployment  

---

## 1. Executive Summary

**Recommended approach for a hackathon / demo deployment:**

> **Option 4 (split)**: Frontend on **Vercel (free tier)** + Backend on **Railway.app (free tier)**.

This combination gives the best cost-to-capability ratio:

- **Vercel** is the best free hosting for React/Vite apps: instant global CDN, zero-config deploys from GitHub, automatic SSL, and generous free tier (100 GB bandwidth, 6000 build minutes/month). It has zero spin-down time on the frontend.
- **Railway.app** gives you $5/month credit (enough for the backend + a Starter PostgreSQL for several months), native FastAPI support (no Dockerfile required unless you want one), plus built-in secrets management and custom domains.
- Total estimated cost: **$0/month for demo usage** with both free tiers.

If you prefer a single platform for simplicity, **Railway.app alone** (hosting both backend and frontend static files from the same project) is the runner-up.

### Why not the others?

- **Fly.io**: Requires Docker knowledge and a proper multi-stage Dockerfile. Great platform, but more setup effort than a hackathon needs.
- **Render**: Identical concept to Railway but spin-down on inactivity (30-60s cold start) hurts the demo experience.
- **DigitalOcean App Platform**: $5/month minimum with no meaningful free tier.
- **Vercel alone**: Cannot run Python/FastAPI backends natively (serverless functions are possible but require significant adaptation).

---

## 2. Comparison Table

| Criteria | Railway.app | Fly.io | Render | Vercel + Railway.app | DigitalOcean App Platform |
|---|---|---|---|---|---|
| **Setup Complexity** | Low (3-5 steps) | Medium (Dockerfile + config) | Low (3-5 steps) | Medium (2 platforms) | Low |
| **Monthly Cost (demo)** | $0 (uses $5 credit) | $0 (3 shared VMs) | $0 (free web service) | $0 (both have free tiers) | $5 minimum |
| **Monthly Cost (prod)** | ~$5-20 | ~$5-25 | ~$7-15 | ~$5-20 (backend only) | $5-12 |
| **Free PostgreSQL** | Yes (Starter: 1 GB) | Yes (3 GB shared) | Yes (1 GB) | Yes (via Railway) | Yes (1 GB) |
| **Spin-down on idle** | No | No | **Yes** (30 min) | Frontend: No / Backend: No | No |
| **Cold start penalty** | None (always on) | None | ~30-60s on first request | None (both always-on) | None |
| **Custom domain** | Yes (built-in) | Yes (built-in) | Yes (built-in) | Yes (on both) | Yes |
| **SSL** | Automatic | Automatic | Automatic | Automatic | Automatic |
| **Docker required** | Optional | Yes | Optional | Optional (backend) | Optional |
| **Global CDN** | Built-in (fly) | Yes (Fly Anycast) | Built-in | Vercel Edge (frontend) | Built-in |
| **Scaling ceiling** | Low (free tier limited RAM/CPU) | Medium | Low | Medium (frontend scales well) | Medium |
| **Secrets management** | Built-in UI | Env vars / secrets | Built-in UI | Both have built-in | Built-in UI |
| **CI/CD from GitHub** | Auto-deploy | GitHub Actions | Auto-deploy | Auto-deploy on both | Auto-deploy |

---

## 3. Recommended Option: Vercel (Frontend) + Railway (Backend)

### 3.1 Architecture Diagram

```
User's Browser
      |
      |  HTTPS
      v
+-------------+          /api/*          +------------------+
|   Vercel    |  ------------------->   |   Railway.app    |
|  (CDN Edge) |                         |                  |
|             |                         |  FastAPI uvicorn |
|  static/    |   (no CORS needed —     |  (port 8000)     |
|  index.html |    Vite proxy handled   |                  |
|  assets/*   |    by Vercel rewrites)  |  PostgreSQL      |
+-------------+                         |  (Starter plan)  |
                                         |                  |
                                         |  Redis (optional)|
                                         +------------------+
                                                  |
                                                  |  HTTPS
                                                  v
                                         +------------------+
                                         |  Bright Data     |
                                         |  AI/ML API       |
                                         |  (external)      |
                                         +------------------+
```

Traffic flow:
1. User visits `https://sentinelwatch.vercel.app`
2. React app loads from Vercel's global CDN (instant, no cold start)
3. API calls to `/api/*` are proxied by Vercel rewrites to Railway backend
4. Railway backend handles requests, queries PostgreSQL, calls Bright Data / AI/ML APIs
5. Backend returns JSON responses through Vercel's proxy

### 3.2 Prerequisites

- GitHub account (for auto-deploy)
- Vercel account (sign up with GitHub)
- Railway.app account (sign up with GitHub)
- Bright Data account (with API keys)
- AI/ML API account (with API keys)

### 3.3 Step-by-Step Deployment

#### Step 1: Prepare the Frontend for Vercel

The frontend is already set up with Vite. Add a `vercel.json` configuration file to the `frontend/` directory:

**`frontend/vercel.json`:**
```json
{
  "rewrites": [
    {
      "source": "/api/(.*)",
      "destination": "https://your-railway-app.up.railway.app/api/$1"
    },
    {
      "source": "/(.*)",
      "destination": "/index.html"
    }
  ]
}
```

**IMPORTANT:** Replace `your-railway-app.up.railway.app` with the actual Railway URL once deployed (step 2).

Also add the Vercel adapter as a dev dependency:

```bash
cd frontend
npm install -D @vercel/analytics
```

The Vite build command (`npm run build`) already produces static files in `frontend/dist/` — Vercel detects this automatically.

#### Step 2: Deploy Backend to Railway.app

**2a. Create a new Railway project**

1. Log in to [Railway.app](https://railway.app) with GitHub
2. Click "New Project" -> "Deploy from GitHub repo"
3. Select your SentinelWatch repository
4. Railway auto-detects the Python project and `requirements.txt`

**2b. Configure the service**

Railway will create a service and attempt to run it. You need to configure it:

- **Start command**: `uvicorn src.main:app --host 0.0.0.0 --port $PORT`
  - Railway injects the `$PORT` environment variable automatically
- **Root directory**: `/` (the project root where `src/` lives)

**2c. Add a PostgreSQL database**

1. In the same Railway project, click "New" -> "Database" -> "Add PostgreSQL"
2. Railway automatically creates a PostgreSQL instance and sets a `DATABASE_URL` environment variable
3. The database is accessible within the Railway network — no public port needed

**2d. Set environment variables**

In the Railway dashboard for your service, add these variables:

| Variable | Value | Notes |
|---|---|---|
| `BRIGHTDATA_API_KEY` | (your key) | Required |
| `BRIGHTDATA_USERNAME` | (your username) | Required |
| `AIML_API_KEY` | (your key) | Required |
| `SECRET_KEY` | `openssl rand -hex 32` | Generate a random key |
| `DATABASE_URL` | (auto-set by Railway Postgres) | Railway sets this automatically |
| `LOG_LEVEL` | `INFO` | Optional |
| `CORS_ORIGINS` | `https://sentinelwatch.vercel.app` | Your Vercel domain |
| `REDIS_URL` | (leave blank if not using Redis) | Optional |

**2e. Update database.py for PostgreSQL**

The current `database.py` uses SQLite. For Railway deployment with PostgreSQL, you have two options:

**Option A (Recommended for demo): Keep SQLite** — Railway's ephemeral filesystem works fine for SQLite. Data persists as long as the service runs but will be lost on service restart (Railway restarts occasionally). This is acceptable for a demo.

**Option B (Production-ready): Switch to PostgreSQL** — See Section 5 below for the migration guide.

For Option A, no code changes are needed. The SQLite database file will be created at `/app/sentinelwatch.db` inside the container.

**2f. Deploy**

1. Connect your GitHub repo to Railway
2. Railway auto-deploys on every push to the main branch
3. Monitor the deployment logs in the Railway dashboard

**2g. Get your Railway URL**

Once deployed, Railway provides a URL like:
```
https://sentinelwatch-backend.up.railway.app
```
Note this for the Vercel configuration.

#### Step 3: Deploy Frontend to Vercel

1. Push the repository to GitHub
2. Go to [vercel.com](https://vercel.com) -> "Add New" -> "Project"
3. Import your SentinelWatch GitHub repo
4. Configure:
   - **Framework Preset**: Vite
   - **Root Directory**: `frontend/`
   - **Build Command**: `npm run build` (default)
   - **Output Directory**: `dist` (default)
5. Add environment variable:
   - `VITE_API_BASE_URL`: `https://sentinelwatch-backend.up.railway.app`
6. Deploy

**Important**: Update `frontend/vercel.json` with the actual Railway backend URL before deploying.

#### Step 4: Configure Proxy

Update `frontend/vercel.json` with your actual Railway backend URL:

```json
{
  "rewrites": [
    {
      "source": "/api/(.*)",
      "destination": "https://sentinelwatch-backend.up.railway.app/api/$1"
    },
    {
      "source": "/(.*)",
      "destination": "/index.html"
    }
  ]
}
```

This eliminates CORS issues entirely — the browser sees all requests going to the same Vercel domain, and Vercel proxies `/api/*` to Railway.

#### Step 5: Verify

1. Visit your Vercel URL (e.g., `https://sentinelwatch.vercel.app`)
2. The React app should load
3. API calls to `/api/*` should reach the Railway backend
4. Test the health endpoint: `https://sentinelwatch.vercel.app/api/v1/health`

---

## 4. Cost Estimates

### Demo / Hackathon Usage (0-100 users/month)

| Component | Service | Monthly Cost |
|---|---|---|
| Backend (FastAPI) | Railway.app free tier ($5 credit) | $0 |
| PostgreSQL | Railway.app Starter ($5 credit covers it) | $0 |
| Frontend (React/Vite) | Vercel free tier | $0 |
| Custom domain (optional) | Vercel/Railway built-in | $0 |
| **Total** | | **$0/month** |

### Low-Traffic Production (100-1000 users/month)

| Component | Service | Monthly Cost |
|---|---|---|
| Backend (FastAPI, 1 CPU, 1 GB RAM) | Railway.app Starter ($5) | $5 |
| PostgreSQL (1 GB storage) | Railway.app built-in | $0 (included) |
| Frontend | Vercel Pro ($20) | $0 (free still works) |
| Custom domain | Included | $0 |
| Redis (optional) | Railway.app ($5) | $0-5 |
| **Total** | | **~$5-10/month** |

### Moderate Usage (1000-10000 users/month)

| Component | Service | Monthly Cost |
|---|---|---|
| Backend (2 CPU, 2 GB RAM) | Railway.app Developer ($20) | $20 |
| PostgreSQL (10 GB) | Railway.app ($5) | $5 |
| Frontend (larger bandwidth) | Vercel Pro ($20) | $20 |
| Redis | Railway.app ($5) | $5 |
| **Total** | | **~$50/month** |

### Cost Notes

- Bright Data API costs are separate and usage-dependent (hackathon provides $250 credit with code `unlocked`)
- AI/ML API costs are usage-based (check their pricing for inference)
- Railway free tier gives $5/month credit — no credit card required to start
- Vercel free tier: 100 GB bandwidth, 6000 build minutes/month, unlimited sites

---

## 5. SQLite to PostgreSQL Migration Guide

### 5.1 Do You Need to Migrate?

**For a hackathon demo: No.** SQLite is perfectly adequate. The current implementation uses an in-memory store with SQLite write-through, which works well for single-server deployments. Railway's filesystem persists SQLite between service restarts (but not rebuilds).

**When to migrate:**
- You expect multiple concurrent API server instances (horizontal scaling)
- You need data durability across deployments/rebuilds
- You want the managed PostgreSQL backup/restore features
- You add more than one worker process (SQLite has write-contention issues)

### 5.2 Migration Effort Assessment

The current `database.py` uses a **hybrid approach**: in-memory Python lists for fast reads, with write-through to an aiosqlite-backed SQLite file. The migration to PostgreSQL involves:

| Component | Effort | Notes |
|---|---|---|
| Database config | Low | Already in config.py (`DATABASE_URL`) |
| Persistence layer | Medium | Replace aiosqlite with asyncpg/psycopg |
| Schema definitions | Medium | Move from raw SQL to SQLAlchemy or a migration tool |
| Data migration | Low | Single export/import script for SQLite -> PostgreSQL |
| Queries | Low | Current queries are simple CRUD |

### 5.3 Migration Implementation

#### Option A: SQLAlchemy with Alembic (Recommended for production)

Add dependencies to `requirements.txt`:
```
sqlalchemy[asyncio]==2.0.35
asyncpg==0.29.0
alembic==1.13.2
```

Create a database models file `src/models.py`:
```python
"""SQLAlchemy models for PostgreSQL persistence."""

from sqlalchemy import Column, String, Float, DateTime, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class FindingModel(Base):
    __tablename__ = "findings"
    id = Column(String, primary_key=True)
    data = Column(JSON)
    created_at = Column(DateTime)

class AlertModel(Base):
    __tablename__ = "alerts"
    id = Column(String, primary_key=True)
    data = Column(JSON)
    created_at = Column(DateTime)

# Create engine using DATABASE_URL from settings
# (convert postgresql:// to postgresql+asyncpg://)
from src.config import settings

DATABASE_URL = settings.database_url.replace(
    "postgresql://", "postgresql+asyncpg://"
)
engine = create_async_engine(DATABASE_URL, echo=False)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def init_models():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
```

Then update `database.py` to use SQLAlchemy models instead of aiosqlite. This is a significant refactor — the write-through pattern stays the same, but the underlying storage changes.

#### Option B: Minimal asyncpg adapter (Lighter lift)

Add to `requirements.txt`:
```
asyncpg==0.29.0
```

Create a thin adapter that mirrors the current write-through pattern but uses asyncpg:
```python
import asyncpg
import json
from src.config import settings

class PostgresStorage:
    def __init__(self):
        self.pool = None

    async def connect(self):
        self.pool = await asyncpg.create_pool(
            settings.database_url, min_size=2, max_size=5
        )
        # Create tables
        async with self.pool.acquire() as conn:
            for table in ["findings", "alerts", "entities", "investigations", "scans"]:
                await conn.execute(f"""
                    CREATE TABLE IF NOT EXISTS {table} (
                        id TEXT PRIMARY KEY,
                        data JSONB NOT NULL,
                        created_at TIMESTAMPTZ DEFAULT NOW()
                    )
                """)

    async def upsert(self, table: str, record: dict):
        async with self.pool.acquire() as conn:
            await conn.execute(
                f"INSERT INTO {table} (id, data) VALUES ($1, $2) "
                f"ON CONFLICT (id) DO UPDATE SET data = $2",
                record["id"], json.dumps(record, default=str)
            )

    async def close(self):
        if self.pool:
            await self.pool.close()
```

### 5.4 Data Export/Import Script

For migrating existing SQLite data to PostgreSQL:

```python
"""One-time migration: SQLite -> PostgreSQL."""
import aiosqlite
import asyncpg
import json
import asyncio
from src.config import settings

TABLES = ["findings", "alerts", "entities", "investigations", "scans"]

async def migrate():
    # Read from SQLite
    sqlite = await aiosqlite.connect("sentinelwatch.db")
    sqlite.row_factory = aiosqlite.Row

    # Connect to PostgreSQL
    pg = await asyncpg.connect(settings.database_url)

    for table in TABLES:
        rows = await sqlite.execute_fetchall(f"SELECT * FROM {table}")
        for row in rows:
            data = json.loads(row["data"])
            await pg.execute(
                f"INSERT INTO {table} (id, data) VALUES ($1, $2) "
                f"ON CONFLICT (id) DO NOTHING",
                row["id"], json.dumps(data)
            )
        print(f"Migrated {len(rows)} rows to {table}")

    await sqlite.close()
    await pg.close()

if __name__ == "__main__":
    asyncio.run(migrate())
```

---

## 6. Environment Variables and Secrets Management

### 6.1 Required Variables

| Variable | Required | Description |
|---|---|---|
| `BRIGHTDATA_API_KEY` | Yes | Bright Data account API key |
| `BRIGHTDATA_USERNAME` | Yes | Bright Data account username |
| `AIML_API_KEY` | Yes | AI/ML API key for AI analysis |
| `SECRET_KEY` | Yes | App secret (run `openssl rand -hex 32`) |
| `DATABASE_URL` | Yes* | PostgreSQL connection string (*Railway sets this automatically when you add a Postgres DB) |

### 6.2 Optional Variables

| Variable | Default | Description |
|---|---|---|
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG/INFO/WARNING/ERROR) |
| `AIML_API_BASE` | `https://api.aimlapi.com` | AI/ML API base URL |
| `AIML_DEFAULT_MODEL` | `claude-opus-4-8` | AI model for analysis |
| `COGNEE_API_KEY` | (none) | Cognee agent memory |
| `COGNEE_API_BASE` | `https://api.cognee.ai/v1` | Cognee API URL |
| `REDIS_URL` | (none) | Redis connection URL |
| `SLACK_WEBHOOK_URL` | (none) | Slack alert webhook |
| `PAGERDUTY_API_KEY` | (none) | PagerDuty integration |
| `SMTP_HOST` / `SMTP_PORT` / `SMTP_USER` / `SMTP_PASSWORD` | (none) | Email alerts |
| `CORS_ORIGINS` | `*` | CORS allowed origins (set to Vercel domain in production) |

### 6.3 Best Practices

**Railway Secrets Management:**
- Use Railway's built-in **Variables** UI (not `.env` files in the repo)
- Variables set in Railway override any `.env` file
- All secret values are encrypted at rest and masked in logs

**Vercel Environment Variables:**
- Set `VITE_API_BASE_URL` in Vercel project settings
- Vite variables must be prefixed with `VITE_` to be exposed to the browser
- These are injected at build time, so a rebuild is needed on change

**Prevent `.env` from being committed:**
The `.gitignore` already includes `.env` — verify this is present:
```
.env
.env.local
```

---

## 7. CI/CD Recommendations

### 7.1 Recommended Setup: GitHub Auto-Deploy

Both Vercel and Railway support auto-deploy from GitHub branches. This is the simplest approach.

```
main branch push
    |
    +---> Railway: auto-deploys backend
    |
    +---> Vercel: auto-deploys frontend
```

**No additional configuration needed** — both platforms detect changes and deploy automatically.

### 7.2 GitHub Actions (Optional Enhancement)

For validation before deployment, add `.github/workflows/ci.yml`:

```yaml
name: CI

on:
  pull_request:
    branches: [main]
  push:
    branches: [main]

jobs:
  test-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: pytest

  build-frontend:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: frontend
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
      - name: Install dependencies
        run: npm ci
      - name: Build
        run: npm run build
```

### 7.3 Railway + Vercel Deploy Hooks (For manual deployments)

Both platforms provide deploy hooks:

1. **Railway**: Settings -> Deploy -> Generate Deploy Hook URL
2. **Vercel**: Project Settings -> Git -> Deploy Hooks

These can be triggered via `curl` from any CI/CD system:
```bash
curl -X POST https://railway.app/api/deploy/your-hook
curl -X POST https://api.vercel.com/v1/integrations/deploy/your-hook
```

---

## 8. Dockerfile Update (For Railway/Fly.io Deployments)

The current `Dockerfile` only builds the Python backend. For Railway, this is fine — the frontend is deployed separately to Vercel. But if you want a single-container deployment (e.g., for Fly.io), use a multi-stage build:

```dockerfile
# ========== Stage 1: Build frontend ==========
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build

# ========== Stage 2: Build backend ==========
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --from=frontend-builder /app/frontend/dist /app/frontend/dist
COPY . .

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

With this Dockerfile, the frontend static files are baked into the Python container and can be served by FastAPI using `StaticFiles`:

```python
from fastapi.staticfiles import StaticFiles

# Serve frontend from FastAPI
app.mount("/", StaticFiles(directory="frontend/dist", html=True), name="frontend")
```

---

## 9. Platform-Specific Notes

### 9.1 Railway.app Notes

- **Free tier**: $5 one-time credit, then pay-as-you-go. No card required to start.
- **Port**: Railway injects `$PORT` env var automatically. The app MUST listen on this port.
- **SQLite persistence**: Railway uses ephemeral storage. Data survives restarts but NOT rebuilds (when the service definition changes). For demo data, this is fine — use the `/api/v1/seed` endpoint to re-populate.
- **PostgreSQL**: When you add PostgreSQL to a Railway project, the connection URL is automatically set as `DATABASE_URL` in all linked services.
- **Custom domain**: Railway provides `*.up.railway.app` for free. Custom domains need the $5 Starter plan.
- **Logs**: Built-in log viewer in the Railway dashboard.

### 9.2 Vercel Notes

- **Framework detection**: Vercel auto-detects Vite. Just set root directory to `frontend/`.
- **Build command**: `npm run build` (produces `frontend/dist/`).
- **Rewrites**: The `vercel.json` rewrites must point to the Railway backend URL. Update this when the backend URL changes.
- **Environment variables**: Only `VITE_*` variables are available to client-side code.
- **Preview deployments**: Vercel creates preview URLs for every PR branch — useful for testing.

### 9.3 Fly.io Notes (Alternative)

If you prefer Fly.io (e.g., for Docker experience or global regions):

1. Create `fly.toml`:
```toml
app = "sentinelwatch"
primary_region = "iad"

[build]
  dockerfile = "Dockerfile"

[env]
  LOG_LEVEL = "INFO"

[[services]]
  internal_port = 8000
  protocol = "tcp"
  [[services.ports]]
    handlers = ["http"]
    port = 80
  [[services.ports]]
    handlers = ["tls"]
    port = 443
```

2. Deploy:
```bash
flyctl launch
flyctl secrets set BRIGHTDATA_API_KEY=... AIML_API_KEY=... SECRET_KEY=...
flyctl deploy
```

3. Add PostgreSQL:
```bash
flyctl postgres create
flyctl postgres attach sentinelwatch
```

### 9.4 Render Notes

If using Render:
- **Spin-down**: Free web services spin down after 15 minutes of inactivity. First request after idle takes 30-60 seconds (cold start). This is the main downside for demo.
- **Health pings**: You can use a free uptime monitor (e.g., UptimeRobot) to ping every 5 minutes to keep the service awake.
- **Cron job**: Use Render's Cron Jobs or an external service like cron-job.org to call `/api/v1/collect` periodically.

---

## 10. Deployment Checklist

Use this checklist for first-time deployment:

### Pre-Deployment

- [ ] Repository pushed to GitHub
- [ ] Bright Data API keys obtained (use promo `unlocked` for $250 credit)
- [ ] AI/ML API key obtained
- [ ] `SECRET_KEY` generated (`openssl rand -hex 32`)
- [ ] `frontend/.env` or Vercel env vars: `VITE_API_BASE_URL` set
- [ ] `frontend/vercel.json` created with Railway URL
- [ ] `requirements.txt` includes all dependencies
- [ ] Frontend builds locally (`cd frontend && npm run build`)

### Railway Deployment

- [ ] Railway project created
- [ ] GitHub repo connected
- [ ] Start command configured: `uvicorn src.main:app --host 0.0.0.0 --port $PORT`
- [ ] PostgreSQL database added (auto-sets `DATABASE_URL`)
- [ ] All environment variables set in Railway dashboard
- [ ] Deploy initiated and logs show no errors
- [ ] Health check: `curl https://sentinelwatch-backend.up.railway.app/api/v1/health`
- [ ] Seed data: `POST https://sentinelwatch-backend.up.railway.app/api/v1/seed`

### Vercel Deployment

- [ ] Vercel project created, linked to GitHub
- [ ] Root directory set to `frontend/`
- [ ] Framework preset: Vite
- [ ] Build command: `npm run build`
- [ ] Output directory: `dist`
- [ ] Environment variable `VITE_API_BASE_URL` set
- [ ] Deploy initiated and build succeeds
- [ ] Site loads at Vercel URL
- [ ] API proxy working: page makes API calls without CORS errors
- [ ] Dashboard renders with seed data

### Post-Deployment

- [ ] Custom domain configured (optional)
- [ ] Deployment badge added to README (optional)
- [ ] Uptime monitoring configured (optional)

---

## 11. Quick-Reference Comparison: SQLite vs PostgreSQL

| Factor | SQLite | PostgreSQL |
|---|---|---|
| **Setup effort** | Zero (file-based) | Requires separate service |
| **Data durability** | Low (ephemeral on Railway) | High (managed backups) |
| **Concurrent reads** | Good (WAL mode) | Excellent |
| **Concurrent writes** | Poor (single writer) | Excellent |
| **Horizontal scaling** | Impossible | Possible (read replicas) |
| **Storage limit** | ~281 TB (practical: a few GB) | Unlimited (practical: TB+) |
| **Backup/restore** | Manual file copy | Built-in (pg_dump/pg_restore) |
| **Cost** | Free | Free on Railway (Starter) |
| **Verdict for demo** | **Acceptable** | Better but not required |

The current SQLite-based approach is **fine for demo purposes**. The in-memory store pattern provides fast reads, and the SQLite write-through gives basic persistence. Only migrate to PostgreSQL when you need:
- Multiple API workers (horizontal scaling)
- Persistent data across deployments
- Managed backups
- Concurrent write workloads

---

## 12. Summary: Decision Flowchart

```
Is this a hackathon/demo? 
    |--- YES ---> Do I want the simplest setup?
    |                 |--- YES ---> Railway.app only (backend + serve frontend static)
    |                 |--- NO  ---> Vercel (frontend) + Railway (backend) [RECOMMENDED]
    |
    |--- NO (production) ---> Do I have Docker experience?
                                  |--- YES ---> Fly.io (more control, global regions)
                                  |--- NO  ---> Railway.app (easiest, still production-capable)
```

**Bottom line for SentinelWatch**: Deploy the backend to Railway.app, deploy the frontend to Vercel, keep SQLite for the demo, and spend zero dollars. This setup takes under 30 minutes and requires no ongoing maintenance.
