# Python Scripts Organization Proposal — Data Governance

**Purpose:** Organize scripts by **data journey stage** so it’s clear what runs when, who owns it, and how it fits into governance (ingest → govern → analyze → deliver).

**Status:** Proposal only. No files have been moved.

---

## 1. Current Scripts Mapped to Data Journey

| Stage | Script(s) | Role |
|-------|-----------|------|
| **Ingest** | `historical_ingestion.py` | Backfill / historical pull from Eniscope API → Postgres (with validation, ingestion_logs). |
| **Ingest** | `ingest_to_postgres.py` | Incremental/daily pull from Eniscope API → Postgres (used by daily sync). |
| **Govern** | `run_create_views.py` | Create layered views (v_clean_readings, mv_hourly_usage, etc.) — schema/views. |
| **Govern** | `run_migration.py` | Run migrations (e.g. TIMESTAMP → TIMESTAMPTZ). |
| **Govern** | `refresh_views.py` | Refresh materialized views after ingestion. |
| **Govern** | `validate_data.py` | Data quality checks (schema, duplicates, gaps, ingestion_logs). |
| **Analyze** | `analytics/*.py` | Sensor health, after-hours waste, anomalies, spikes, quick wins. |
| **Analyze** | `query_energy_data.py` | Ad-hoc query CLI over the database. |
| **Deliver** | `generate_weekly_report.py` | Weekly analytics report (JSON/HTML). |
| **Deliver** | `generate_customer_report.py` | Customer-facing HTML report. |
| **Deliver** | `export_for_tableau.py` | Export to CSV for Tableau. |
| **Operations** | `cleanup_old_files.py` | Archive old reports/exports. |
| **Operations** | `daily_sync.sh`, `setup_cron.sh` | Scheduling and cron setup. |
| **Testing** | `test_analytics.py` | Validates analytics and report generation. |
| **Shared** | `lib/`, `config/` | Utilities and report config used across stages. |

---

## 2. Proposed Folder Layout (Governance-Oriented)

```
backend/python_scripts/
├── README.md
├── requirements.txt
│
├── ingest/                          # STAGE 1: Get data into the system
│   ├── README.md                    # When to run, env, site IDs, backfill vs incremental
│   ├── historical_ingestion.py      # Backfill from API (e.g. --site 23271 --start-date 2025-04-29)
│   └── ingest_to_postgres.py        # Incremental/daily sync from API
│
├── govern/                          # STAGE 2: Schema, views, quality, migrations
│   ├── README.md                    # Order of operations: create views → migrate → validate
│   ├── run_create_views.py         # Create views (one-time or after schema change)
│   ├── run_migration.py            # Run SQL migrations (e.g. TIMESTAMPTZ)
│   ├── refresh_views.py            # Refresh materialized views (after ingest)
│   └── validate_data.py            # Data quality and ingestion health checks
│
├── analyze/                         # STAGE 3: Analytics and ad-hoc query
│   ├── README.md                    # What each module does, inputs/outputs
│   ├── query_energy_data.py        # CLI for querying the DB
│   ├── anomaly_detection.py
│   ├── after_hours_waste.py
│   ├── quick_wins.py
│   ├── sensor_health.py
│   └── spike_detection.py
│
├── deliver/                         # STAGE 4: Reports and exports
│   ├── README.md                    # Report types, outputs, delivery
│   ├── generate_weekly_report.py
│   ├── generate_customer_report.py
│   └── export_for_tableau.py
│
├── operations/                      # Scheduling, cleanup, cron
│   ├── README.md
│   ├── daily_sync.sh
│   ├── setup_cron.sh
│   └── cleanup_old_files.py
│
├── tests/                           # Quality assurance
│   └── test_analytics.py
│
├── lib/                             # Shared (unchanged)
│   ├── __init__.py
│   ├── date_utils.py
│   └── stats_utils.py
│
└── config/                         # Shared config (unchanged)
    ├── __init__.py
    └── report_config.py
```

**Why this helps governance**

- **Ingest** = single place for “how data enters” (API → Postgres). Easy to audit and document retention/backfill.
- **Govern** = all schema, views, migrations, and validation in one place. Clear order: create views → migrate → refresh after ingest → validate.
- **Analyze** = all analytics and ad-hoc query in one place. Clear what reads from the governed layer.
- **Deliver** = all outputs (reports, exports) in one place. Clear what is customer-facing vs internal.
- **Operations** = scheduling and lifecycle only; no business logic.

---

## 3. Suggested Run Order (Data Pipeline)

1. **Ingest**  
   - Backfill (once or rarely): `ingest/historical_ingestion.py --site 23271 --start-date 2025-04-29`  
   - Daily: `ingest/ingest_to_postgres.py --site 23271 --days 2`

2. **Govern (after ingest)**  
   - `govern/refresh_views.py`  
   - Optionally: `govern/validate_data.py` (e.g. in CI or after backfill)

3. **Analyze**  
   - As needed: `analyze/query_energy_data.py` or report scripts that use `analytics/`.

4. **Deliver**  
   - Weekly/customer: `deliver/generate_weekly_report.py`, `deliver/generate_customer_report.py`  
   - Tableau: `deliver/export_for_tableau.py`

5. **Operations**  
   - Cron runs `operations/daily_sync.sh` (which calls ingest + refresh_views).

---

## 4. What Would Need to Change If You Adopt This

- **Imports**  
  - Scripts that do `from analytics.xxx` or `from lib.xxx` may need path fixes or a single top-level package (e.g. run from `backend/python_scripts` with `PYTHONPATH=.` or install as a package) so `ingest/`, `govern/`, `analyze/`, `deliver/` can still import `lib` and `config` and `analyze` modules.

- **Cron / npm**  
  - `daily_sync.sh` and any npm scripts that call these Python scripts would need updated paths (e.g. `backend/python_scripts/ingest/ingest_to_postgres.py` and `backend/python_scripts/govern/refresh_views.py`).

- **README and docs**  
  - Update main README and any setup docs (e.g. DAILY_SYNC_SETUP.md) to point to the new paths and to the stage-specific READMEs.

- **GitHub Actions / CI**  
  - If any workflow runs these scripts, update their paths and document that `govern/validate_data.py` (and optionally ingest) are the governance entry points.

---

## 5. Alternative: Minimal Change (No Folders)

If you prefer not to move files yet, you can still improve governance with:

- **Naming prefix**  
  - e.g. `ingest_historical_ingestion.py`, `ingest_to_postgres.py`, `govern_refresh_views.py`, `govern_validate_data.py`, `deliver_generate_weekly_report.py`.  
  - Makes stage obvious in one flat list.

- **Single README section**  
  - In `README.md`, add a “Data journey and governance” section that lists scripts by stage (as in the table in section 1) and the suggested run order (as in section 3). No file moves.

---

## 6. Recommendation Summary

- **Best for data governance:** Use the **folder layout** (section 2) so “ingest”, “govern”, “analyze”, and “deliver” are explicit and easy to document and audit.
- **Lowest friction:** Keep current layout and add **stage prefixes** and a **README “Data journey”** section (section 5).

If you tell me which option you prefer (folders vs minimal), I can outline exact steps and a checklist for the refactor without changing any code until you’re ready.
