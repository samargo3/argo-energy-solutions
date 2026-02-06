# Argo Energy Solutions — Full Project Context for Gemini

This document gives an AI (e.g. Gemini) complete, detailed context on the **Argo Energy Solutions** project: what it is, how the repo is structured, how data flows, and how to work in the codebase. Use it together with `NEON_DATABASE_BREAKDOWN_FOR_GEMINI.md` for full database detail.

---

## 1. Project overview

### 1.1 What it is

**Argo Energy Solutions** is a full-stack application for:

- **Ingesting** energy meter data from the **Eniscope** (Best.Energy) API into a **Neon PostgreSQL** database.
- **Storing and governing** that data (schema, views, migrations, validation).
- **Analyzing** it (sensor health, after-hours waste, anomalies, spikes, quick wins).
- **Delivering** reports (weekly analytics, customer HTML/JSON reports) and exports (e.g. for Tableau).
- **Surfacing** it in a **React** dashboard (customers, channels, readings, charts) and via a **Node/Express API** for stored data and Eniscope proxy.

Primary use case: **Wilson Center** (organization/site ID **23271**) — Eniscope meters, 15‑minute resolution, data in Neon, reports and exports for internal and customer use.

### 1.2 Tech stack (high level)

| Layer | Technology |
|-------|------------|
| **Frontend** | React 18, TypeScript, Vite, React Router, TanStack Query, Recharts, Axios, date-fns |
| **Backend API** | Node.js, Express, CORS; Eniscope proxy + stored-data endpoints (intended: query service over Neon) |
| **Database** | Neon (PostgreSQL 17); see `NEON_DATABASE_BREAKDOWN_FOR_GEMINI.md` |
| **Ingestion & analytics** | Python 3.9+ (psycopg2, requests, pandas, numpy, scipy, pytz, python-dotenv) |
| **CI/CD** | GitHub Actions (daily sync, data validation, weekly report) |
| **Integrations** | Eniscope API, Tableau (CSV/ODBC), optional Salesforce (documented) |

### 1.3 Repository root layout

```
argo-energy-solutions/
├── .env.example              # Env template (Best.Energy; real usage adds Eniscope + DATABASE_URL)
├── .github/workflows/        # CI: daily-sync, data-validation, weekly-report
├── backend/
│   ├── python_scripts/       # Python ingest, govern, analyze, deliver, operations, tests
│   ├── python_reports/       # Separate Python report pipeline (VEM/demo reports)
│   ├── scripts/              # Node: analysis, data-collection, database, diagnostics, reports, utilities
│   └── server/               # Express API server (api-server.js)
├── docs/                     # All documentation (api, guides, reference, setup, troubleshooting)
├── exports/                  # Tableau exports, workbooks
├── public/                   # Static assets, index.html
├── reports/                  # Generated report outputs (HTML, JSON)
├── src/                      # Frontend (React/TypeScript)
├── package.json
├── vite.config.ts
├── tsconfig.json
└── README.md
```

---

## 2. Frontend (React / Vite)

### 2.1 Entry and routing

- **Entry:** `src/main.tsx` → `App.tsx`.
- **Router:** React Router 6; all routes wrapped in `<Layout />` (navbar + footer).
- **Base URL:** Dev server typically `http://localhost:5173`; Vite proxies `/api` to `http://localhost:3001` (Express server).

### 2.2 Routes (pages)

| Path | Component | Purpose |
|------|-----------|---------|
| `/` | `Home` | Landing / home |
| `/dashboard` | `Dashboard` | Energy dashboard (charts, stats) |
| `/customers` | `Customers` | Customer list |
| `/customers/:id` | `CustomerPortal` | Single customer/site view |
| `/reports` | `Reports` | Reports index |
| `/reports/wilson-center` | `WilsonCenterReport` | Wilson Center–specific report |
| `/api-test` | `ApiTest` | API testing UI |

### 2.3 Key directories under `src/`

| Directory | Purpose |
|-----------|---------|
| **components/** | Reusable UI: `charts/` (EnergyChart), `common/` (StatsCard), `examples/` (StoredDataExample), `layout/` (Layout, Navbar, Footer) |
| **hooks/** | `useCustomerData`, `useEnergyData`, `useEniscopeChannel`, `useStoredEnergyData` — data fetching and state for dashboard/customers |
| **pages/** | One component per route; co-located `*.css` (e.g. Dashboard.css, CustomerPortal.css) |
| **services/** | **api/** — apiClient, bestEnergyApi, eniscopeApi, storedDataApi; **analytics/** — anomalyDetection, statistics |
| **types/** | TypeScript types: api.ts, energy.ts, insights.ts, index.ts (EnergyConsumption, Site, Customer, TimeSeriesDataPoint, etc.) |
| **lib/** | queryClient.ts (TanStack Query client) |
| **utils/** | dateUtils.ts |

### 2.4 Data flow (frontend)

- **Stored data (Neon):** Frontend calls Express at `VITE_STORED_DATA_API_URL` (default `http://localhost:3001`). `storedDataApi.ts` defines methods for channels, readings, aggregated readings, statistics, organization summary, latest reading, data range. Types: `Reading`, `AggregatedReading`, `EnergyStatistics`, `ChannelInfo`.
- **Live Eniscope:** Via Express proxy or direct Eniscope API (bestEnergyApi / eniscopeApi) for real-time or on-demand API data.
- **Build:** `npm run build` → `dist/`; `npm run preview` to preview production build.

---

## 3. Backend — Node.js

### 3.1 Express API server

- **File:** `backend/server/api-server.js`.
- **Port:** `process.env.API_PORT || 3001`.
- **Role:**
  - **Stored data API:** Channels, channel readings, aggregated readings, statistics, organization summary, latest reading, data range. Implementations delegate to a **data query service** (intended to query Neon). The server imports `dataQueryService` from `../src/services/data/queryService.js` (path relative to `backend/server/`); if that module is missing, those endpoints may fail until the service is implemented or path fixed.
  - **Eniscope proxy:** Authenticates to Eniscope (Basic + API key, session token), proxies requests (e.g. readings by channel) with retries and rate-limit handling.
- **Env:** `VITE_ENISCOPE_API_URL`, `VITE_ENISCOPE_API_KEY`, `VITE_ENISCOPE_EMAIL`, `VITE_ENISCOPE_PASSWORD`; optionally `API_PORT`, `DATABASE_URL` for the query service.
- **Commands:** `npm run api:server`, `npm run api:dev` (nodemon), `npm run dev:all` (API + Vite).

### 3.2 Node scripts (`backend/scripts/`)

| Directory | Purpose | Notable files |
|-----------|---------|----------------|
| **analysis/** | Energy and Wilson Center analysis | analyze-energy-data.js, wilson-center-analysis.js |
| **data-collection/** | Eniscope fetch & ingest (legacy/alternative to Python) | ingest-eniscope-data.js, ingest-to-postgres.js, explore-channels.js, export-wilson-raw-monthly.js |
| **database/** | Schema, migrations, views, Neon | setup-postgres-schema.js, create-layered-views.sql, migrate-to-timestamptz.sql, migrate-sqlite-to-postgres.js, check-database.js, test-neon-connection.js |
| **diagnostics/** | Data access and unit health | diagnose-data-access.js, unit-health-report.js |
| **reports/** | Weekly analytics (Node path) | weekly-exceptions-brief.js, generate-html-from-json.js, analytics/ (after-hours-waste, anomaly-detection, quick-wins, sensor-health, spike-detection), lib/, config/ |
| **utilities/** | CSV export, daily check, env setup | export-to-csv.js, check-data-daily.sh, setup-env.sh |

The project’s **primary ingestion and reporting** path is **Python** (see below); Node scripts remain for compatibility, exploration, and some reports.

---

## 4. Backend — Python (primary data pipeline)

Python lives under `backend/python_scripts/`. Scripts are organized by **data journey**: ingest → govern → analyze → deliver → operations; shared code in `lib/` and `config/`.

### 4.1 Directory layout (reorganized)

```
backend/python_scripts/
├── requirements.txt
├── README.md
├── ingest/                    # Get data from Eniscope into Neon
│   ├── ingest_to_postgres.py  # Incremental/daily sync (e.g. --site 23271 --days 7)
│   └── historical_ingestion.py # Backfill with validation and ingestion_logs
├── govern/                    # Schema, views, migrations, validation
│   ├── run_create_views.py    # Create layered views (v_clean_readings, mv_*, v_sites, etc.)
│   ├── run_migration.py       # TIMESTAMP → TIMESTAMPTZ migration
│   ├── refresh_views.py       # REFRESH MATERIALIZED VIEW CONCURRENTLY mv_hourly_usage
│   └── validate_data.py       # Data quality and ingestion health
├── analyze/                   # Analytics and ad-hoc query
│   ├── query_energy_data.py  # CLI query over DB
│   ├── anomaly_detection.py, after_hours_waste.py, quick_wins.py, sensor_health.py, spike_detection.py
├── deliver/                   # Reports and exports
│   ├── generate_weekly_report.py   # Weekly analytics (JSON/HTML)
│   ├── generate_customer_report.py  # Customer-facing HTML/JSON report
│   └── export_for_tableau.py       # CSV for Tableau
├── operations/                # Scheduling and lifecycle
│   ├── daily_sync.sh          # Runs ingest (e.g. last 2 days), logs to logs/daily_sync.log
│   ├── setup_cron.sh          # Cron setup for daily sync
│   └── cleanup_old_files.py   # Archive old reports/exports
├── tests/
│   └── test_analytics.py      # Validates analytics and report generation
├── lib/                       # Shared utilities
│   ├── date_utils.py
│   └── stats_utils.py
└── config/
    └── report_config.py       # Report configuration
```

**Path note:** `package.json` and local scripts use the paths above (e.g. `ingest/ingest_to_postgres.py`, `govern/validate_data.py`). Some GitHub Actions may still reference the old flat paths (e.g. `backend/python_scripts/ingest_to_postgres.py`); those workflows may need updating to the new paths.

### 4.2 Ingest

- **ingest_to_postgres.py:** Authenticates to Eniscope, fetches orgs/channels/readings, normalizes (Wh→kWh, W→kW), inserts into Neon (organizations, devices, channels, readings). Can refresh materialized views after run. Args: e.g. `--site 23271 --days 7`.
- **historical_ingestion.py:** Backfill in 24‑hour windows; validates (no negative power, no future timestamps); upserts with `ON CONFLICT (channel_id, timestamp) DO NOTHING`; writes **ingestion_logs** for each pull; ensures **ingestion_logs** table exists. Args: e.g. `--site 23271 --start-date 2025-05-01 [--end-date ...]`.

### 4.3 Govern

- **run_create_views.py:** Executes `backend/scripts/database/create-layered-views.sql` (v_clean_readings, mv_hourly_usage, v_sites, v_meters, v_readings_*, etc.).
- **run_migration.py:** Runs TIMESTAMPTZ migration (all timestamp columns in public tables).
- **refresh_views.py:** Refreshes `mv_hourly_usage` (CONCURRENTLY when possible).
- **validate_data.py:** Checks tables exist, basic integrity, and optional ingestion/gap checks using `ingestion_logs`.

### 4.4 Analyze

- **analyze/** modules: sensor health, after-hours waste, anomaly detection, spike detection, quick wins. Used by weekly and customer reports.
- **query_energy_data.py:** CLI to run queries against the database.

### 4.5 Deliver

- **generate_weekly_report.py:** Fetches data from Neon, runs analytics, outputs JSON (and optionally HTML) for a given site and date range.
- **generate_customer_report.py:** Customer-facing report (HTML and/or JSON), e.g. `--site 23271`.
- **export_for_tableau.py:** Exports data (e.g. CSV) for Tableau.

### 4.6 Operations

- **daily_sync.sh:** Activates venv, runs `ingest/ingest_to_postgres.py --site 23271 --days 2`, logs to `logs/daily_sync.log`.
- **setup_cron.sh:** Helps configure a daily cron job for sync.
- **cleanup_old_files.py:** Cleans or archives old report/export files (optional `--execute`).

### 4.7 Python reports (separate area)

- **backend/python_reports/:** Contains its own scripts (e.g. demo_report, generate_vem_report, fetch_bestenergy_data) and outputs (reports/, charts/). Used for VEM-style and demo reports; separate from the main `python_scripts` pipeline.

---

## 5. Data flow and integrations

### 5.1 End-to-end pipeline

```
Eniscope API (organizations, channels, readings 15‑min)
    │
    ├─► Python: ingest/ingest_to_postgres.py  or  ingest/historical_ingestion.py
    │       │
    │       └─► Neon PostgreSQL (organizations, devices, channels, readings [, ingestion_logs])
    │
    ├─► Govern: run_create_views.py → views; after ingest → refresh_views.py → mv_hourly_usage
    │
    ├─► Validate: validate_data.py
    │
    ├─► Analyze: analyze/* + deliver/generate_weekly_report.py, generate_customer_report.py
    │
    └─► Deliver: Reports (HTML/JSON), export_for_tableau.py (CSV), exports/tableau/
```

### 5.2 Eniscope API

- **Base URL:** `VITE_ENISCOPE_API_URL` (e.g. `https://core.eniscope.com`).
- **Auth:** Basic (email + MD5 password) + header `X-Eniscope-API` (API key); session token in response header (`x-eniscope-token`).
- **Usage:** Organizations list, channels by organization, readings by channel (e.g. `action=summarize`, `res=900`, `daterange[]`, `fields[]`: E, P, V, I, PF). Units from API: Wh, W; app converts to kWh, kW.
- **Docs:** `docs/api/` (API_ACCESS_GUIDE, API_ENDPOINTS_SUMMARY, etc.); `docs/reference/` (Core API v1).

### 5.3 Neon PostgreSQL

- **Role:** Single source of truth for stored meter data and analytics views. Full schema and maintenance are in **docs/reference/NEON_DATABASE_BREAKDOWN_FOR_GEMINI.md** (tables, views, build order, ingestion, validation, refresh).

### 5.4 Tableau

- **Export:** Python `deliver/export_for_tableau.py`; Node utilities for CSV/export.
- **Docs:** `docs/guides/integrations/TABLEAU_INTEGRATION_GUIDE.md`, `NEON_TABLEAU_DIRECT_CONNECT.md`, `TABLEAU_JOINING_GUIDE.md`; `exports/tableau/` (workbooks, README).

### 5.5 Salesforce

- Documented in `docs/guides/integrations/SALESFORCE_INTEGRATION_GUIDE.md`; integration architecture only, not implemented in repo.

---

## 6. Configuration and environment

### 6.1 Environment variables (consolidated)

| Variable | Used by | Purpose |
|----------|---------|---------|
| **DATABASE_URL** | Python, Node DB scripts, CI | Neon PostgreSQL connection string |
| **VITE_ENISCOPE_API_URL** | Python ingest, Express | Eniscope API base URL (e.g. https://core.eniscope.com) |
| **VITE_ENISCOPE_API_KEY** | Python ingest, Express | Eniscope API key |
| **VITE_ENISCOPE_EMAIL** | Python ingest, Express | Eniscope login email |
| **VITE_ENISCOPE_PASSWORD** | Python ingest, Express | Eniscope login password |
| **VITE_STORED_DATA_API_URL** | Frontend | Stored-data API base (default http://localhost:3001) |
| **VITE_BEST_ENERGY_API_URL** | Frontend (Best.Energy) | Best.Energy API URL (legacy) |
| **VITE_BEST_ENERGY_API_KEY** | Frontend | Best.Energy API key (legacy) |
| **VITE_API_TIMEOUT** | Frontend | Request timeout (ms) |
| **API_PORT** | Express | API server port (default 3001) |

- **.env:** Root; not committed. Copy from `.env.example` and add Eniscope + DATABASE_URL (see docs/setup/CREATE_ENV_FILE.md, ENV_SETUP_HELP.md).
- **GitHub Actions:** Use repository secrets (e.g. DATABASE_URL, VITE_ENISCOPE_*) for CI.

### 6.2 Key site/organization ID

- **23271** — Wilson Center; used in examples, npm scripts, and CI (e.g. `--site 23271`).

---

## 7. CI/CD (GitHub Actions)

| Workflow | File | Schedule | Purpose |
|----------|------|----------|---------|
| **Daily sync** | `.github/workflows/daily-sync.yml` | 02:00 UTC daily + manual | Run ingestion (e.g. `ingest_to_postgres.py --site 23271 --days 7`), then validate. Uses DATABASE_URL and VITE_ENISCOPE_* secrets. **Note:** Workflow may still use old path `backend/python_scripts/ingest_to_postgres.py`; should be `backend/python_scripts/ingest/ingest_to_postgres.py` if repo uses reorganized layout. |
| **Data validation** | `.github/workflows/data-validation.yml` | Every 6 hours + push to main (python_scripts/**) + manual | Run `validate_data.py`. On failure, can create a GitHub issue. |
| **Weekly report** | `.github/workflows/weekly-report.yml` | Mondays 08:00 UTC + manual | Run `generate_customer_report.py --site 23271`, upload HTML and JSON artifacts. **Note:** Workflow may reference `backend/python_scripts/generate_customer_report.py`; reorganized path is `backend/python_scripts/deliver/generate_customer_report.py`. |

---

## 8. Documentation map

| Area | Path | Contents |
|------|------|----------|
| **API** | docs/api/ | API_ACCESS_GUIDE, API_CONFIGURATION, API_CONNECTION_GUIDE, API_ENDPOINTS_SUMMARY, API_RATE_LIMITS, Core_API_v1.txt |
| **Guides** | docs/guides/ | ADVANCED_ANALYTICS_GUIDE, DATA_EXPORT_OVERVIEW, DATA_STORAGE_STRATEGY, LOCAL_DATABASE_QUICKSTART, WILSON_RAW_EXPORT_QUICKSTART; integrations/ (Tableau, Neon–Tableau, Salesforce); reports/ (Gemini, Wilson Center, Unit Health, etc.) |
| **Reference** | docs/reference/ | NEON_DATABASE_BREAKDOWN_FOR_GEMINI.md, ARGO_ENERGY_SOLUTIONS_PROJECT_CONTEXT_FOR_GEMINI.md (this file), Core API v1.pdf, Generic ingress instructions |
| **Setup** | docs/setup/ | CREATE_ENV_FILE, DAILY_SYNC_SETUP, ENV_SETUP_HELP, NEON_QUICKSTART, NEON_SETUP_GUIDE, LAYERED_VIEWS, RUN_SETUP, SETUP_CHECKLIST, SETUP_STATUS, OPTION_2_*, EXPORT_SETUP_CHECKLIST |
| **Troubleshooting** | docs/troubleshooting/ | FIX_CORS_ERROR, FIXES_APPLIED, NEON_MCP_TROUBLESHOOTING |
| **Project status** | docs/ | CURRENT_STATUS.md, NEXT_STEPS.md, QUICK_REFERENCE.md |

Root-level markdown files (README, QUICK_START, HISTORICAL_INGESTION_GUIDE, CUSTOMER_REPORTS_GUIDE, TABLEAU_*, PYTHON_*, etc.) are feature or completion notes; primary structured docs live under `docs/`.

---

## 9. NPM scripts quick reference

### 9.1 Development

- `npm run dev` — Vite dev server (frontend).
- `npm run api:server` — Express API server.
- `npm run dev:all` / `npm start` — Frontend + API (concurrently).

### 9.2 Build and lint

- `npm run build` — TypeScript + Vite build → dist/.
- `npm run preview` — Preview production build.
- `npm run lint` — ESLint (ts, tsx).

### 9.3 Python (data pipeline)

- **Ingest:** `py:ingest` (1 day), `py:ingest:full` (90 days), `py:ingest:historical`, `py:ingest:historical:custom`.
- **Reports:** `py:report`, `py:report:custom`, `py:report:customer`, `py:report:customer:json`.
- **Export:** `py:export:tableau`, `py:export:tableau:custom`.
- **Govern:** `py:validate`; **DB:** `db:views`, `db:refresh-views`, `db:migrate:timestamptz`, `db:check-schema`.
- **Operations:** `py:sync`, `py:setup-cron`, `py:logs`; `py:cleanup`, `py:cleanup:dry-run`.
- **Query/test:** `py:query`, `py:test`, `py:test:verbose`.

### 9.4 Database (Node + Python)

- `db:setup` — Create base tables (Node).
- `db:views` — Create layered views (Python run_create_views).
- `db:refresh-views` — Refresh materialized views (Python refresh_views).
- `db:migrate:timestamptz` — Run TIMESTAMPTZ migration (Python run_migration).
- `db:check`, `db:test-neon` — Check DB and test Neon connection (Node).

### 9.5 Node scripts (analysis, ingest, reports)

- `analyze:energy`, `analyze:wilson`, `explore:channels`, `diagnose:data`, `unit:health`, `check:daily`.
- `ingest:data`, `ingest:full`, `ingest:incremental`, `ingest:postgres`.
- `export:csv`, `export:wilson:raw`.
- `report:weekly`, `report:test`, `report:html`.

---

## 10. Conventions and notes

### 10.1 Paths

- **Reorganized Python:** Scripts under `backend/python_scripts/{ingest,govern,analyze,deliver,operations,tests}`; `package.json` and local scripts use these. Update any CI or docs that still point to flat paths (e.g. `backend/python_scripts/ingest_to_postgres.py` → `backend/python_scripts/ingest/ingest_to_postgres.py`).
- **API server:** Runs from project root; import `../src/services/data/queryService.js` is relative to `backend/server/`, i.e. `backend/src/services/data/queryService.js`. That file does not exist in the repo; stored-data endpoints depend on it (or an equivalent) being implemented or the import path fixed.

### 10.2 Naming

- **Sites = organizations** in DB; **meters = channels**. Views use business names: v_sites, v_meters.
- **Wilson Center** = organization/site ID **23271** in examples and scripts.

### 10.3 Database

- All substantive DB structure and maintenance are in **docs/reference/NEON_DATABASE_BREAKDOWN_FOR_GEMINI.md**. This doc only summarizes how the app and scripts use the DB.

### 10.4 Dual ingest paths

- **Python** is the main path (ingest/, historical_ingestion); **Node** has `ingest-to-postgres.js` and related scripts for legacy/alternative use. Prefer Python for new ingestion logic.

---

This file plus **NEON_DATABASE_BREAKDOWN_FOR_GEMINI.md** give Gemini (or any AI) full context on the Argo Energy Solutions project and its Neon database.
