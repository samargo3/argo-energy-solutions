# Argo Energy Solutions — Project Context Document

> **Purpose:** This document provides comprehensive context about the Argo Energy Solutions codebase for AI tools, new developers, and collaborators. It covers architecture, data flow, tech stack, database schema, coding conventions, and operational procedures.
>
> **Last updated:** February 12, 2026

---

## 1. What This Project Does

Argo Energy Solutions is a **commercial energy monitoring and analytics platform** that:

1. **Ingests** real-time and historical energy data from **Eniscope** hardware (smart meters/gateways installed at customer sites).
2. **Stores** time-series readings in a cloud **PostgreSQL** database (Neon).
3. **Analyzes** the data to detect anomalies, after-hours energy waste, demand spikes, sensor health issues, electrical health problems, and cost optimization opportunities.
4. **Delivers** automated weekly reports (HTML/JSON), Electrical Health Screening PDFs, Tableau exports, and a React dashboard for customers and internal stakeholders.

The primary customer site is **Wilson Center** (site ID `23271`), with the system designed to scale to multiple sites via a `sites` registry table.

---

## 2. Architecture Overview

### The Four-Stage Data Journey

The codebase is strictly organized by **data lifecycle stage**. No script should span more than two stages. This is the project's core architectural principle.

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   INGEST    │───▶│   GOVERN    │───▶│   ANALYZE   │───▶│   DELIVER   │
│  /ingest    │    │  /govern    │    │  /analyze   │    │  /deliver   │
│             │    │             │    │             │    │             │
│ Eniscope API│    │ Schema,     │    │ Read-Only   │    │ Reports,    │
│ → Postgres  │    │ Views, Data │    │ Stats,      │    │ PDF, HTML,  │
│ (Raw)       │    │ Quality     │    │ Models      │    │ Exports     │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

| Stage | Folder | Responsibility | Key Rule |
|-------|--------|---------------|----------|
| **Ingest** | `backend/python_scripts/ingest/` | Pull raw data from Eniscope API, normalize (Wh→kWh), insert into Postgres | Must use `ON CONFLICT DO NOTHING`; must log to `ingestion_logs` |
| **Govern** | `backend/python_scripts/govern/` | Schema management, materialized view refreshes, data validation, migrations | Must run after every ingest cycle; validations act as circuit breakers |
| **Analyze** | `backend/python_scripts/analyze/` | Business logic — anomaly detection, after-hours waste, electrical health, forecasting | **Read-only** — must NEVER INSERT/UPDATE core tables; consumes Layer 3 views |
| **Deliver** | `backend/python_scripts/deliver/` | Weekly reports, customer HTML reports, Electrical Health PDFs, Tableau CSV exports | Formatter-centric; calls analyze modules for calculations |

### Supporting Folders

| Folder | Purpose |
|--------|---------|
| `backend/python_scripts/operations/` | Cron jobs, daily sync orchestration, health checks, cleanup |
| `backend/python_scripts/lib/` | Shared utilities (date helpers, stats, site registry, Sentry, logging) |
| `backend/python_scripts/config/` | Centralized configuration (report thresholds, TOU rates, business hours, electrical health) |
| `backend/python_reports/scripts/` | PDF report generators (matplotlib charts + fpdf2 assembly) |
| `backend/server/` | FastAPI REST API serving the React frontend |
| `src/` | React + TypeScript frontend (Vite) |
| `backend/scripts/` | **Legacy** Node.js scripts (deprecated; replaced by `py:*` equivalents) |

---

## 3. Tech Stack

### Backend (Data Pipeline)
- **Python 3.9+** — all pipeline scripts
- **psycopg2** — PostgreSQL driver
- **pandas / numpy / scipy** — data analysis
- **Prophet** — time-series forecasting
- **matplotlib** — chart generation for PDF reports
- **fpdf2** — PDF assembly for branded reports
- **python-dotenv** — environment variable management

### Backend (API Server)
- **FastAPI** — REST API framework
- **Uvicorn** — ASGI server
- **httpx** — async HTTP client (Eniscope API proxy)
- **Pydantic** — request/response validation

### Frontend
- **React 18** with **TypeScript**
- **Vite 7** — build tooling and dev server
- **React Router 6** — client-side routing
- **TanStack React Query** — server state management
- **Recharts** — charting library
- **Lucide React** — icon library
- **Axios** — HTTP client
- **date-fns** — date manipulation

### Database
- **Neon PostgreSQL** (cloud-hosted, serverless Postgres)
- Connection via `DATABASE_URL` with SSL required

### External Services
- **Eniscope API** (`https://core.eniscope.com`) — source of energy data
- **Sentry** — error tracking (optional)

### Infrastructure
- **Docker / Docker Compose** — containerized deployment (API + nginx frontend)
- **GitHub Actions** — CI/CD (daily sync, weekly reports, validation, manual backfill)

---

## 4. Database Schema

### Core Tables

```sql
-- Organizations (customer sites)
organizations (
  organization_id TEXT PRIMARY KEY,       -- Eniscope org ID
  organization_name TEXT NOT NULL,
  address TEXT, city TEXT, postcode TEXT, country TEXT,
  timezone TEXT DEFAULT 'America/New_York',
  created_at TIMESTAMP, updated_at TIMESTAMP
)

-- Devices (Eniscope gateways)
devices (
  device_id INTEGER PRIMARY KEY,
  device_name TEXT,
  organization_id TEXT REFERENCES organizations,
  device_type TEXT, serial_number TEXT, firmware_version TEXT,
  last_seen TIMESTAMP
)

-- Channels (meters / monitoring points)
channels (
  channel_id INTEGER PRIMARY KEY,
  channel_name TEXT NOT NULL,
  device_id INTEGER REFERENCES devices,
  organization_id TEXT REFERENCES organizations,
  channel_type TEXT, unit TEXT, description TEXT
)

-- Readings (time-series — largest table)
readings (
  id BIGSERIAL PRIMARY KEY,
  channel_id INTEGER NOT NULL REFERENCES channels,
  timestamp TIMESTAMP NOT NULL,
  -- Core energy fields
  energy_kwh REAL, power_kw REAL,
  voltage_v REAL, current_a REAL, power_factor REAL,
  reactive_power_kvar REAL, temperature_c REAL, relative_humidity REAL,
  -- Electrical health fields (added via add_electrical_health_columns.py)
  frequency_hz REAL, neutral_current_a REAL,
  thd_current REAL, apparent_power_va REAL, cost REAL,
  -- Phase-level measurements (3-phase power)
  voltage_v1 REAL, voltage_v2 REAL, voltage_v3 REAL,
  current_a1 REAL, current_a2 REAL, current_a3 REAL,
  power_w1 REAL, power_w2 REAL, power_w3 REAL,
  power_factor_1 REAL, power_factor_2 REAL, power_factor_3 REAL,
  energy_wh1 REAL, energy_wh2 REAL, energy_wh3 REAL,
  UNIQUE(channel_id, timestamp)           -- prevents duplicate readings
)

-- Data sync tracking
data_sync_status (organization_id, channel_id, last_sync_timestamp, ...)

-- Site registry (multi-site support)
sites (site_id, site_name, is_active, wcds_only, resolution, timezone, notes)

-- Virtual meters (aggregation of physical channels)
virtual_meters / virtual_meter_map
```

### Key Indexes

| Index | Columns | Purpose |
|-------|---------|---------|
| `idx_readings_channel_timestamp` | `(channel_id, timestamp DESC)` | Fast per-meter time queries |
| `idx_readings_timestamp` | `(timestamp DESC)` | Global time-range scans |
| `idx_readings_unique` | `(channel_id, timestamp)` UNIQUE | Deduplication on upsert |
| `idx_channels_org` | `(organization_id)` | Site-level channel lookups |
| `idx_mv_hourly_usage_meter_hour` | `(meter_id, hour)` UNIQUE | MV concurrent refresh support |

### Layered View Architecture

The views are organized in three layers to separate raw data from business logic:

**Layer 1 — Base (filtering)**
| View | Purpose |
|------|---------|
| `v_clean_readings` | Filtered readings — excludes rows with null/zero energy or power; ensures TIMESTAMPTZ; includes all electrical health and phase-level fields |

**Layer 2 — Materialized (performance)**
| View | Purpose |
|------|---------|
| `mv_hourly_usage` | Hourly aggregates per meter: `avg_kw`, `total_kwh`, `reading_count`, plus electrical health aggregates (`avg_frequency_hz`, `avg_neutral_current_a`, `max_neutral_current_a`, `avg_thd_current`, `max_thd_current`, `avg_apparent_power_va`). **Must be refreshed after every ingestion cycle.** |

**Layer 3 — Business (consumption)**
| View | Purpose |
|------|---------|
| `v_sites` | Business alias for `organizations` (site_id, site_name, etc.) |
| `v_meters` | Channels enriched with device and site info |
| `v_readings_enriched` | Clean readings with full context (site, meter, device) — **primary analytics view**. Includes all electrical health and phase-level fields. |
| `v_latest_readings` | Most recent reading per meter (dashboards). Includes frequency, neutral current, THD, apparent power. |
| `v_readings_hourly` | Hourly usage with meter names (wraps `mv_hourly_usage`) |
| `v_readings_daily` | Daily aggregates per meter. Includes electrical health aggregates (`avg/min/max_frequency_hz`, `avg/max_neutral_current_a`, `avg/max_thd_current`, `avg_apparent_power_va`, `peak_current_a`). |
| `v_readings_monthly` | Monthly aggregates per meter |

**Data Contract Views**
| View | Purpose |
|------|---------|
| `v_data_health_monitor` | Data freshness status per channel (CRITICAL / WARNING / HEALTHY) |
| `v_virtual_readings` | Aggregated readings for virtual meters |


---

## 5. API Endpoints

The FastAPI server (`backend/server/main.py`) exposes these endpoints:

### Auth & Health
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Health check (public) |
| `/api/auth/login` | POST | Simple password-gate authentication |

### Energy Data
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/energy/history` | GET | Hourly-aggregated site energy history |
| `/api/channels` | GET | List all channels/meters |
| `/api/channels/{id}/readings` | GET | Raw readings for a channel |
| `/api/channels/{id}/readings/aggregated` | GET | Aggregated readings |
| `/api/channels/{id}/statistics` | GET | Channel statistics |
| `/api/channels/{id}/readings/latest` | GET | Latest reading |
| `/api/channels/{id}/range` | GET | Data availability date range |
| `/api/organizations/{id}/summary` | GET | Organization-level summary |

### Analytics
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/analytics/forecast/{site_id}` | GET | Prophet usage forecast |
| `/api/analytics/cost-optimization/{site_id}` | GET | TOU + demand charge analysis |
| `/api/analytics/electrical-health/{site_id}` | GET | Electrical health screening data (JSON) |

### Reports
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/reports/weekly/{site_id}/latest` | GET | Latest weekly report JSON |
| `/api/reports/weekly/{site_id}` | GET | List available weekly reports |
| `/api/reports/weekly/{site_id}/{filename}` | GET | Specific report by filename |
| `/api/reports/data-quality/{site_id}` | GET | Live data quality summary |
| `/api/reports/electrical-health/{site_id}` | GET | Generate Electrical Health Screening PDF (returns binary PDF) |

### Eniscope Proxy
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/eniscope/readings/{channelId}` | GET | Eniscope API proxy |
| `/api/eniscope/channels` | GET | Eniscope API proxy |
| `/api/eniscope/devices` | GET | Eniscope API proxy |

Authentication is via a simple password gate (`APP_PASSWORD` env var) for the frontend, and `X-API-Key` header (`API_SECRET_KEY`) for machine clients.

---

## 6. Frontend Structure

The React application at `src/` uses React Router with a password-gate login. All routes are behind authentication.

### Pages
| File | Route | Purpose |
|------|-------|---------|
| `src/pages/Home.tsx` | `/` | Landing page |
| `src/pages/Dashboard.tsx` | `/dashboard` | Main energy dashboard |
| `src/pages/EnergyHistory.tsx` | `/energy-history` | Historical energy data browser |
| `src/pages/Reports.tsx` | `/reports` | Reports hub (links to report types) |
| `src/pages/WilsonCenterReport.tsx` | `/reports/wilson-center` | Wilson Center equipment report |
| `src/pages/WeeklyReport.tsx` | `/reports/weekly` | Weekly analytics brief viewer |
| `src/pages/ElectricalHealthReport.tsx` | `/reports/electrical-health` | Electrical Health Screening report generator (triggers PDF download) |
| `src/pages/CustomerPortal.tsx` | `/customers/:id` | Customer-facing portal |
| `src/pages/Customers.tsx` | `/customers` | Customer list |
| `src/pages/ApiTest.tsx` | `/api-test` | API debugging tool |
| `src/pages/LoginPage.tsx` | — | Password gate login (shown when unauthenticated) |

### Components
| Folder | Contents |
|--------|----------|
| `src/components/charts/` | `LoadProfileChart`, `CostBreakdownChart`, `ForecastChart`, `EnergyHistoryChart`, `EnergyChart` |
| `src/components/layout/` | `Layout` (outlet wrapper), `Navbar`, `Footer` |
| `src/components/common/` | `StatsCard` |
| `src/components/examples/` | `StoredDataExample` |

### Services
| File | Purpose |
|------|---------|
| `src/services/api/apiClient.ts` | Axios instance with auth headers and timeout |
| `src/services/api/storedDataApi.ts` | PostgreSQL-backed data API calls |
| `src/services/api/eniscopeApi.ts` | Direct Eniscope API calls (via proxy) |
| `src/services/api/bestEnergyApi.ts` | Best energy practices API |
| `src/services/analytics/statistics.ts` | Client-side statistical calculations |
| `src/services/analytics/anomalyDetection.ts` | Client-side anomaly detection |

### Build & Dev
- Vite dev server proxies `/api` requests to `http://localhost:8000` (FastAPI)
- Build: `npm run build` (TypeScript compile + Vite production build)
- Docker: nginx serves the built frontend on port 3000, proxying `/api` to the API container

---

## 7. Key Scripts Reference

### Ingest Scripts
| Script | npm Command | Purpose |
|--------|------------|---------|
| `ingest_to_postgres.py` | `npm run py:ingest -- <site_id>` | Ingest last N days of data for a site (default: 1 day). Fetches all WCDS channels day-by-day. Includes electrical health and phase-level fields. |
| `historical_ingestion.py` | `npm run py:ingest:historical -- <site_id>` | Backfill historical data for a custom date range |
| `diagnostic_report.py` | `npm run py:ingest:diagnostic` | Diagnose ingestion issues |
| `discover_api_endpoints.py` | `npm run py:ingest:discover` | Explore Eniscope API endpoints |

### Govern Scripts
| Script | npm Command | Purpose |
|--------|------------|---------|
| `validate_data.py` | `npm run py:validate` | Data quality circuit breaker |
| `refresh_views.py` | `npm run db:refresh-views` | Refresh `mv_hourly_usage` materialized view |
| `run_create_views.py` | `npm run db:views` | Create/recreate all layered views |
| `data_quality_report.py` | `npm run py:govern:quality` | Detailed data quality report |
| `check_completeness.py` | — | Data completeness checks |
| `add_electrical_health_columns.py` | `npm run db:migrate:electrical-health` | Migration: add 20 electrical health + phase-level columns to readings |
| `create_sites_table.py` | `npm run db:migrate:sites` | Migration: create and seed the sites table |
| `add_meters_table.py` | `npm run db:migrate:meters` | Migration: add meters table |
| `run_migration.py` | `npm run db:migrate:timestamptz` | Migration: convert timestamps to timestamptz |

### Analyze Scripts
| Script | Purpose |
|--------|---------|
| `sensor_health.py` | Detect missing data, stale meters, flatlined sensors |
| `after_hours_waste.py` | Calculate after-hours energy waste vs. baseline |
| `anomaly_detection.py` | Statistical outlier detection (IQR method) |
| `spike_detection.py` | Demand spike and short-cycling detection |
| `quick_wins.py` | Generate prioritized energy savings recommendations |
| `forecast.py` | Prophet-based energy usage forecasting |
| `cost_model.py` | Time-of-Use and demand charge cost analysis |
| `electrical_health.py` | **Electrical Health Screening** — voltage stability, current peaks, frequency excursions, neutral current indicators, THD analysis, and composite health score |
| `query_energy_data.py` | Natural language query interface for energy data |

### Deliver Scripts
| Script | npm Command | Purpose |
|--------|------------|---------|
| `generate_weekly_report.py` | `npm run py:report -- <site_id>` | Weekly analytics JSON report |
| `generate_customer_report.py` | `npm run py:report:customer -- <site_id>` | Customer-ready HTML + JSON report |
| `generate_electrical_health_report.py` | `npm run py:report:electrical-health -- <site_id>` | Electrical Health Screening PDF report (calls analyze module, delegates to python_reports for PDF generation) |
| `export_for_tableau.py` | `npm run py:export:tableau` | Export CSV files for Tableau |

### PDF Report Generators (`backend/python_reports/scripts/`)
| Script | Purpose |
|--------|---------|
| `generate_electrical_health_report.py` | `ElectricalHealthReportGenerator` class — Argo-branded PDF with matplotlib charts (voltage trends, current peaks, frequency, THD) assembled via fpdf2 |

### Operations Scripts
| Script | npm Command | Purpose |
|--------|------------|---------|
| `daily_sync.sh` | `npm run py:sync` | Orchestrates: ingest → refresh views → validate (all active sites) |
| `setup_cron.sh` | `npm run py:setup-cron` | Install cron job for daily sync at 6:00 AM |
| `list_active_sites.py` | `npm run py:sites` | List all active sites from the registry |
| `check_ingestion_health.py` | `npm run py:operations:health` | Check ingestion pipeline health |
| `cleanup_old_files.py` | `npm run py:cleanup` | Archive old reports, exports, and logs |

### Test Suite (`backend/python_scripts/tests/`)
| Script | Purpose |
|--------|---------|
| `test_analytics.py` | End-to-end analytics test harness |
| `test_forecast.py` | Prophet forecast module tests |
| `test_cost_model.py` | TOU/demand cost model tests |
| `test_stats_utils.py` | Stats utility tests |
| `test_site_registry.py` | Site registry tests |
| `test_date_utils.py` | Date utility tests |
| `test_logging_config.py` | Logging setup tests |

---

## 8. Electrical Health Screening Feature

This is a recently added feature spanning Analyze and Deliver stages.

### Architecture

```
analyze/electrical_health.py          →  Pure analytics (read-only)
    ↓ called by
deliver/generate_electrical_health_report.py  →  CLI wrapper
    ↓ delegates to
python_reports/scripts/generate_electrical_health_report.py  →  PDF generator (matplotlib + fpdf2)
```

### Analytics Modules (`analyze/electrical_health.py`)

| Function | Purpose |
|----------|---------|
| `analyze_voltage_stability()` | Per-meter voltage sag/swell detection against nominal ±5% band. Uses `v_readings_enriched` and `v_readings_daily`. |
| `analyze_current_peaks()` | Peak current events per meter, top-N events, daily peak trend |
| `analyze_frequency_excursions()` | Frequency deviations outside 59.95–60.05 Hz band |
| `analyze_neutral_current()` | Neutral current elevated vs. phase current baseline |
| `analyze_thd()` | Current THD analysis against IEEE 519 limit (5%) |
| `compute_health_score()` | Weighted composite score: voltage (35%), current (25%), frequency (20%), THD (20%). Grades: Good/Fair/Poor |
| `generate_electrical_health_data()` | **Main entry point** — orchestrates all analyses, returns combined dict |

### Thresholds (`config/report_config.py` → `electricalHealth`)

| Parameter | Default | Purpose |
|-----------|---------|---------|
| `voltageTolerancePct` | 5% | Nominal ±band for sag/swell detection |
| `frequencyBand` | (59.95, 60.05) Hz | Acceptable frequency range |
| `thdCurrentLimitPct` | 5.0% | IEEE 519 current THD limit |
| `neutralCurrentElevatedPct` | 20% | Elevated threshold as % of avg phase current |
| `healthScoreWeights` | V:0.35, I:0.25, F:0.20, THD:0.20 | Composite score weights |

### Database Requirements

The electrical health feature requires:
1. **20 additional columns** on the `readings` table (added via `npm run db:migrate:electrical-health`)
2. **Updated views** that include the new columns in `v_clean_readings`, `mv_hourly_usage`, `v_readings_enriched`, `v_latest_readings`, and `v_readings_daily`
3. **Ingestion script** updated to fetch expanded Eniscope API fields (frequency, neutral current, THD, apparent power, cost, phase-level V/I/P/PF/E)

---

## 9. Configuration

### Environment Variables (`.env`)

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | Neon PostgreSQL connection string (`postgresql://...?sslmode=require`) |
| `ENISCOPE_API_URL` | Yes | Eniscope API base URL (`https://core.eniscope.com`) |
| `ENISCOPE_API_KEY` | Yes | Eniscope API key |
| `ENISCOPE_EMAIL` | Yes | Eniscope login email |
| `ENISCOPE_PASSWORD` | Yes | Eniscope login password |
| `API_SECRET_KEY` | Yes | Shared secret for API authentication (X-API-Key header) |
| `APP_PASSWORD` | Yes | Simple password for frontend access gate |
| `SENTRY_DSN` | No | Sentry error tracking DSN |
| `VITE_API_TIMEOUT` | No | Frontend API timeout in ms (default: 30000) |
| `VITE_API_BASE_URL` | No | Frontend API base URL (empty = same-origin) |
| `CORS_ORIGIN` | No | Production frontend URL for CORS |
| `ENISCOPE_RESOLUTION` | No | Data resolution in seconds (default: 3600 = hourly) |

### Report Configuration (`config/report_config.py`)

Centralized thresholds for all analytics modules:

- **Business hours:** Mon–Fri 7:00–18:00 ET; weekends are fully after-hours
- **Sensor health:** 2× gap multiplier, 2h stale threshold, 10% missing data threshold, 6h flatline detection
- **After-hours waste:** 5th percentile baseline, 0.1 kW minimum, 10 kWh significance threshold
- **Anomaly detection:** 3× IQR multiplier, z-score threshold of 3, minimum 3 consecutive intervals
- **Spike detection:** 95th percentile baseline, 1.5× multiplier
- **Tariff:** Default $0.12/kWh; TOU schedule with off-peak ($0.06), mid-peak ($0.10), on-peak ($0.20)
- **Demand charges:** $12.00/kW per billing period, 80% ratchet rule
- **Forecasting:** 90-day lookback, 7-day default horizon, 80% confidence interval
- **Electrical health:** ±5% voltage tolerance, 59.95–60.05 Hz frequency band, 5% THD limit, 20% neutral current threshold, weighted composite score

---

## 10. CI/CD & Automation

### GitHub Actions Workflows

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `daily-sync.yml` | Daily at 02:00 UTC | Ingest last 3 days for all active sites |
| `weekly-report.yml` | Mondays at 08:00 UTC | Generate customer HTML + JSON reports |
| `data-validation.yml` | After daily sync | Run test suite + data validation |
| `historical-backfill.yml` | Manual dispatch | Historical data backfill for a date range |
| `debug-probe.yml` | Manual dispatch | Eniscope API debug/diagnostic probe |

### Operational Flow (daily_sync.sh)

```
1. Ingest   → Pull data from Eniscope API (last 3 days, all active sites)
2. Govern   → Refresh mv_hourly_usage materialized view
3. Govern   → Run data validation (circuit breaker)
4. Analyze  → Trigger scheduled reports (if validation passes)
```

---

## 11. Development Setup

### Prerequisites
- Node.js 18+
- Python 3.9+ with `venv`
- Access to Neon PostgreSQL database
- Eniscope API credentials

### Quick Start

```bash
# 1. Clone and install
git clone <repo-url>
cd argo-energy-solutions
npm install

# 2. Set up Python environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env with your credentials

# 4. Set up database (first time)
npm run legacy:db:setup            # Create core tables
npm run db:migrate:electrical-health  # Add electrical health columns
npm run db:views                   # Create layered views

# 5. Run development servers
npm start                          # Starts both frontend + API
# Or individually:
npm run dev                        # Frontend at http://localhost:5173
npm run py:api                     # API at http://localhost:8000
```

### Docker

```bash
docker compose up --build
# Frontend: http://localhost:3000
# API:      http://localhost:8000
```

---

## 12. Coding Conventions

### Python Standards

1. **Absolute imports** — Always use package-level imports:
   ```python
   from lib.date_utils import get_date_range
   from config.report_config import DEFAULT_CONFIG
   from analyze.electrical_health import generate_electrical_health_data
   ```

2. **Path resolution** — Use the `_PKG_ROOT` / `_PROJECT_ROOT` pattern:
   ```python
   from pathlib import Path
   from dotenv import load_dotenv

   _PKG_ROOT = Path(__file__).resolve().parent.parent
   _PROJECT_ROOT = _PKG_ROOT.parent.parent
   load_dotenv(_PROJECT_ROOT / '.env')
   ```

3. **npm interface** — Every production script has a corresponding `npm run py:*` command in `package.json`.

4. **No credentials in code** — All secrets via `.env` at the project root.

5. **Stage discipline** — Analyze scripts are read-only; Ingest scripts don't contain business logic; Govern scripts own the schema.

6. **Governance views** — Analyze and Deliver scripts must consume data from Layer 3 business views (`v_readings_enriched`, `v_readings_daily`, etc.), never from raw tables.

### Shared Libraries (`lib/`)

| Module | Purpose |
|--------|---------|
| `site_registry.py` | Query `sites` table for active sites; fallback to Wilson Center default (site 23271) |
| `date_utils.py` | Date range helpers, timezone conversions |
| `stats_utils.py` | Statistical utility functions |
| `logging_config.py` | Standardized logging setup (`configure_logging`, `get_logger`) |
| `sentry_client.py` | Sentry error tracking initialization (`init_sentry`, `capture_exception`) |

---

## 13. Eniscope API Integration

### Authentication
- **Basic Auth** header using email/password credentials
- API key also required for some endpoints

### Data Fields Ingested
The ingestion script fetches expanded fields from the Eniscope API:

| Category | Fields |
|----------|--------|
| Core | energy (Wh→kWh), power (kW), voltage (V), current (A), power factor |
| Reactive | reactive power (kVAR) |
| Environmental | temperature (°C), relative humidity |
| Electrical Health | frequency (Hz), neutral current (A), THD current, apparent power (VA), cost |
| Phase-Level | voltage V1–V3, current A1–A3, power W1–W3, power factor PF1–PF3, energy Wh1–Wh3 |

### Wilson Center Channels (WCDS)
The primary site has 8 hardware channels installed 2025-04-29:

| Channel ID | Name |
|------------|------|
| 162119 | RTU-2 |
| 162120 | RTU-3 |
| 162121 | AHU-2 |
| 162122 | AHU-1A |
| 162123 | AHU-1B |
| 162285 | Kitchen Main Panel(s) |
| 162319 | Kitchen Panel (small) |
| 162320 | RTU-1 |

---

## 14. Key Domain Concepts

| Term | Meaning |
|------|---------|
| **Organization / Site** | A customer location with Eniscope hardware installed |
| **Device / Gateway** | An Eniscope hardware unit that connects to multiple meters |
| **Channel / Meter** | A single monitoring point (e.g., one electrical circuit) |
| **WCDS** | Wilson Center Data Source — the 8 active channels at Wilson Center |
| **Reading** | A single time-series data point (energy, power, voltage, current, power factor, plus optional electrical health and phase-level fields) |
| **Materialized View** | Pre-computed hourly aggregates (`mv_hourly_usage`) for query performance |
| **Business Hours** | Mon–Fri 7:00–18:00 ET (configurable per site) |
| **After-Hours Waste** | Energy consumed outside business hours above the baseline |
| **Flatline** | A sensor reporting near-zero variance for 6+ hours (likely malfunction) |
| **Quick Wins** | Prioritized energy savings recommendations ranked by impact |
| **TOU** | Time-of-Use pricing — rates vary by time of day |
| **Demand Charge** | Per-kW charge based on peak demand in a billing period |
| **Voltage Sag/Swell** | Voltage dipping below or rising above nominal ±5% band |
| **THD (Current)** | Total Harmonic Distortion — measure of waveform quality; IEEE 519 limit is typically 5% |
| **Neutral Current** | Current on the neutral conductor; elevated levels indicate load imbalance |
| **Frequency Excursion** | Grid frequency deviating outside the 59.95–60.05 Hz acceptable range |
| **Health Score** | Weighted composite of voltage (35%), current (25%), frequency (20%), and THD (20%) |

---

## 15. File Tree (Key Files Only)

```
argo-energy-solutions/
├── .env.example                           # Environment template
├── .cursor/rules/argo-governance.mdc      # AI governance rules (always applied)
├── package.json                           # npm scripts interface
├── vite.config.ts                         # Vite + API proxy config
├── docker-compose.yml                     # Docker services (api + web)
├── tsconfig.json                          # TypeScript config
│
├── .github/workflows/
│   ├── daily-sync.yml                     # Daily ingestion (02:00 UTC)
│   ├── weekly-report.yml                  # Monday reports (08:00 UTC)
│   ├── data-validation.yml                # Post-sync validation
│   ├── historical-backfill.yml            # Manual backfill
│   └── debug-probe.yml                    # API debug probe
│
├── backend/
│   ├── server/
│   │   └── main.py                        # FastAPI server (all endpoints)
│   │
│   ├── python_scripts/
│   │   ├── ingest/
│   │   │   ├── ingest_to_postgres.py      # Primary ingestion (expanded fields)
│   │   │   └── historical_ingestion.py    # Historical backfill
│   │   ├── govern/
│   │   │   ├── validate_data.py           # Data quality validation
│   │   │   ├── refresh_views.py           # Materialized view refresh
│   │   │   ├── run_create_views.py        # Create layered views
│   │   │   ├── data_quality_report.py     # Quality reporting
│   │   │   ├── check_completeness.py      # Completeness checks
│   │   │   ├── add_electrical_health_columns.py  # Migration: +20 columns
│   │   │   ├── create_sites_table.py      # Migration: sites table
│   │   │   ├── add_meters_table.py        # Migration: meters table
│   │   │   └── run_migration.py           # Migration: timestamptz
│   │   ├── analyze/
│   │   │   ├── sensor_health.py           # Sensor health checks
│   │   │   ├── after_hours_waste.py       # After-hours waste detection
│   │   │   ├── anomaly_detection.py       # Statistical anomaly detection
│   │   │   ├── spike_detection.py         # Demand spike detection
│   │   │   ├── quick_wins.py              # Savings recommendations
│   │   │   ├── forecast.py                # Prophet forecasting
│   │   │   ├── cost_model.py              # TOU/demand cost analysis
│   │   │   ├── electrical_health.py       # Electrical health screening
│   │   │   └── query_energy_data.py       # Natural language query
│   │   ├── deliver/
│   │   │   ├── generate_weekly_report.py  # Weekly JSON report
│   │   │   ├── generate_customer_report.py # Customer HTML report
│   │   │   ├── generate_electrical_health_report.py  # Electrical Health PDF (CLI)
│   │   │   └── export_for_tableau.py      # Tableau CSV export
│   │   ├── operations/
│   │   │   ├── daily_sync.sh              # Daily orchestration script
│   │   │   ├── setup_cron.sh              # Cron installation
│   │   │   ├── list_active_sites.py       # Site discovery
│   │   │   ├── check_ingestion_health.py  # Pipeline health check
│   │   │   └── cleanup_old_files.py       # File archival
│   │   ├── tests/                         # Test suite
│   │   │   ├── test_analytics.py          # End-to-end analytics tests
│   │   │   ├── test_forecast.py           # Forecast tests
│   │   │   ├── test_cost_model.py         # Cost model tests
│   │   │   ├── test_stats_utils.py        # Stats utility tests
│   │   │   ├── test_site_registry.py      # Site registry tests
│   │   │   ├── test_date_utils.py         # Date utility tests
│   │   │   └── test_logging_config.py     # Logging tests
│   │   ├── lib/                           # Shared utilities
│   │   │   ├── site_registry.py           # Site lookup with fallback
│   │   │   ├── date_utils.py              # Date helpers
│   │   │   ├── stats_utils.py             # Statistics helpers
│   │   │   ├── logging_config.py          # Logging setup
│   │   │   └── sentry_client.py           # Sentry initialization
│   │   └── config/
│   │       └── report_config.py           # Centralized thresholds
│   │
│   ├── python_reports/scripts/
│   │   └── generate_electrical_health_report.py  # PDF generator (matplotlib + fpdf2)
│   │
│   └── scripts/                           # [LEGACY] Node.js scripts (deprecated)
│       └── database/
│           ├── setup-postgres-schema.js    # Schema creation (reference)
│           └── create-layered-views.sql    # View definitions (canonical SQL)
│
├── src/                                   # React frontend
│   ├── App.tsx                            # Routes and layout
│   ├── main.tsx                           # Entry point
│   ├── contexts/AuthContext.tsx            # Auth state
│   ├── pages/
│   │   ├── Dashboard.tsx                  # Energy dashboard
│   │   ├── EnergyHistory.tsx              # Historical data browser
│   │   ├── Reports.tsx                    # Reports hub
│   │   ├── WeeklyReport.tsx               # Weekly analytics viewer
│   │   ├── WilsonCenterReport.tsx         # Wilson Center report
│   │   ├── ElectricalHealthReport.tsx     # Electrical Health report page
│   │   ├── ElectricalHealthReport.css     # Electrical Health styles
│   │   ├── CustomerPortal.tsx             # Customer portal
│   │   ├── Customers.tsx                  # Customer list
│   │   ├── LoginPage.tsx                  # Password gate
│   │   └── ApiTest.tsx                    # API testing tool
│   ├── components/
│   │   ├── charts/                        # Recharts visualizations
│   │   │   ├── LoadProfileChart.tsx
│   │   │   ├── CostBreakdownChart.tsx
│   │   │   ├── ForecastChart.tsx
│   │   │   ├── EnergyHistoryChart.tsx
│   │   │   └── EnergyChart.tsx
│   │   ├── layout/                        # Navbar, Footer, Layout
│   │   ├── common/                        # StatsCard
│   │   └── examples/                      # StoredDataExample
│   └── services/
│       ├── api/
│       │   ├── apiClient.ts               # Axios instance
│       │   ├── storedDataApi.ts            # PostgreSQL data API
│       │   ├── eniscopeApi.ts             # Eniscope proxy API
│       │   └── bestEnergyApi.ts           # Best energy practices
│       └── analytics/
│           ├── statistics.ts              # Client-side statistics
│           └── anomalyDetection.ts        # Client-side anomaly detection
│
├── reports/                               # Generated report output (PDFs, JSON)
├── exports/                               # Tableau export output
└── docs/                                  # Documentation
    └── PROJECT_CONTEXT.md                 # This file
```

---

## 16. Common Operations

| Task | Command |
|------|---------|
| Start full dev environment | `npm start` |
| Ingest yesterday's data | `npm run py:ingest -- 23271` |
| Ingest last 90 days | `npm run py:ingest:full -- 23271` |
| Refresh materialized views | `npm run db:refresh-views` |
| Validate data quality | `npm run py:validate` |
| Generate weekly report | `npm run py:report -- 23271` |
| Generate customer HTML report | `npm run py:report:customer -- 23271` |
| Generate Electrical Health PDF | `npm run py:report:electrical-health -- 23271` |
| Export for Tableau | `npm run py:export:tableau` |
| Run daily sync pipeline | `npm run py:sync` |
| List active sites | `npm run py:sites` |
| Check ingestion health | `npm run py:operations:health` |
| Create/update database views | `npm run db:views` |
| Add electrical health columns | `npm run db:migrate:electrical-health` |
| Run analytics tests | `npm run py:test` |
| Run forecast + cost model tests | `npm run py:test:analytics` |
| Data quality report (7 days) | `npm run py:govern:quality` |
| Data quality report (30 days) | `npm run py:govern:quality:30d` |
| Cleanup old files (dry run) | `npm run py:cleanup:dry-run` |

---

## 17. Recent Changes (as of Feb 2026)

### Electrical Health Screening (In Progress)
- **New analyze module:** `electrical_health.py` — voltage stability, current peaks, frequency excursions, neutral current, THD, composite health score
- **New deliver wrapper:** `generate_electrical_health_report.py` — CLI that generates PDF reports
- **New PDF generator:** `python_reports/scripts/generate_electrical_health_report.py` — Argo-branded PDF with matplotlib charts via fpdf2
- **New frontend page:** `ElectricalHealthReport.tsx` at `/reports/electrical-health` — triggers PDF download via API
- **New API endpoints:** `/api/reports/electrical-health/{site_id}` (PDF), `/api/analytics/electrical-health/{site_id}` (JSON)
- **Schema migration:** `add_electrical_health_columns.py` adds 20 columns (frequency, neutral current, THD, apparent power, cost, 3-phase V/I/P/PF/E)
- **Updated ingestion:** `ingest_to_postgres.py` now fetches expanded Eniscope API fields
- **Updated config:** `report_config.py` now includes `electricalHealth` thresholds
- **Updated views SQL:** `create-layered-views.sql` includes electrical health fields in all view layers
- **Pending fix:** `npm run db:views` fails due to column rename conflict (see Section 4, "Known Issue")

---

*Last updated: February 12, 2026*
