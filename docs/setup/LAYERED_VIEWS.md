# Layered View Architecture

**Status:** Implemented  
**Database:** Neon PostgreSQL

---

## Deploy views to your Neon database

**1. Set your Neon connection string**

In the project root, ensure `.env` contains your Neon connection string:

```bash
# .env
DATABASE_URL=postgresql://USER:PASSWORD@ep-xxx.region.aws.neon.tech/neondb?sslmode=require
```

Get this from the Neon dashboard: **Project → Connection string → Copy**.

**2. Activate the virtual environment and run the view creation**

From the **project root** (`argo-energy-solutions/`):

```bash
npm run db:views
```

This connects to Neon using `DATABASE_URL`, runs `create-layered-views.sql`, and creates all views and the materialized view (including the unique index). You should see:

```
📐 Creating layered views and Option A analytics views...
✅ All views created successfully.
```

**3. (Optional) Refresh the materialized view**

After the first deploy, the materialized view is already populated. To refresh it later (e.g. after new data is loaded):

```bash
npm run db:refresh-views
```

**That’s it.** The views now exist in your Neon database. Use them in SQL, Tableau, or your app (e.g. `SELECT * FROM v_readings_daily`).

---

## Overview

Analytics use a **layered view** design:

1. **Layer 1 – Clean:** `v_clean_readings` (standard view)  
   - Source: `readings` (raw table).  
   - Casts timestamps to `TIMESTAMPTZ`, filters out rows with null or zero `energy_kwh` / `power_kw`.

2. **Layer 2 – Hourly (materialized):** `mv_hourly_usage`  
   - Built from `v_clean_readings`.  
   - Groups by hour and `meter_id` (channel_id), with `avg_kw` and `total_kwh`.  
   - Has a **unique index** on `(meter_id, hour)` so you can run `REFRESH MATERIALIZED VIEW CONCURRENTLY`.

3. **Option A – Analytics:**  
   - `v_sites`, `v_meters`, `v_readings_enriched`, `v_latest_readings`,  
   - `v_readings_hourly` (uses `mv_hourly_usage`), `v_readings_daily`, `v_readings_monthly`.

---

## Create Views (one-time)

```bash
npm run db:views
```

Runs `backend/scripts/database/create-layered-views.sql` via `backend/python_scripts/run_create_views.py`.

---

## Refresh Materialized View (after new data)

**Automatic:** The ingestion script calls the refresh at the end of each run:

```bash
python backend/python_scripts/ingest_to_postgres.py --site 23271 --days 90
# … at the end: "Refreshing materialized views..." then "Refreshed mv_hourly_usage"
```

**Manual:**

```bash
npm run db:refresh-views
```

Or in Python after loading data:

```python
from refresh_views import refresh_materialized_views
refresh_materialized_views()  # REFRESH MATERIALIZED VIEW CONCURRENTLY mv_hourly_usage
```

---

## Views Reference

| View | Type | Purpose |
|------|------|--------|
| `v_clean_readings` | View | Clean readings: TIMESTAMPTZ, no null/zero energy or power |
| `mv_hourly_usage` | Materialized | Hourly avg kW and total kWh per meter |
| `v_sites` | View | Sites (organizations) |
| `v_meters` | View | Meters (channels) with device/site |
| `v_readings_enriched` | View | Clean readings + site, meter, device |
| `v_latest_readings` | View | Latest reading per meter |
| `v_readings_hourly` | View | Hourly usage with meter/site names (from `mv_hourly_usage`) |
| `v_readings_daily` | View | Daily aggregates per meter |
| `v_readings_monthly` | View | Monthly aggregates per meter |

---

## Concurrency

`REFRESH MATERIALIZED VIEW CONCURRENTLY` is used so that:

- Reads can continue against the existing snapshot while the refresh runs.  
- The unique index on `(meter_id, hour)` is required for this; it is created by `create-layered-views.sql`.

---

## Raw table name

The prompt referred to `energy_readings_raw`. In this project the raw table is **`readings`**.  
`v_clean_readings` selects from `readings` and applies the cleaning rules above.
