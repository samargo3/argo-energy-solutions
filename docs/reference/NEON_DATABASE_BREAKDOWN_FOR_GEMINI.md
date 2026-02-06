# Neon Database: Complete Breakdown for Gemini

This document describes the **Neon PostgreSQL database** used by Argo Energy Solutions: its structure, how it is built, and how it is maintained. Use it to give an AI (e.g. Gemini) full context about the database.

---

## 1. Neon project overview

- **Project name:** Argo Energy Solutions  
- **Project ID:** `small-hat-99276920`  
- **Provider/region:** AWS US East 1 (`aws-us-east-1`)  
- **PostgreSQL version:** 17  
- **Default database:** `neondb` (or first available)  
- **Branches:**
  - **production** (`br-frosty-sound-ahkj2pl7`) – primary, default  
  - **prod-test** (`br-silent-darkness-ahp7g8qd`) – non-primary, for testing  

Connection is via `DATABASE_URL` in `.env` (and GitHub Actions secrets for CI).

---

## 2. Schema overview

The database has two main schemas:

| Schema      | Purpose |
|------------|---------|
| **public** | Application data: organizations, devices, channels, readings, sync/ingestion metadata, and all analytics views. |
| **neon_auth** | Neon/Stack Auth tables (account, session, user, organization, member, invitation, verification, jwks, project_config). Not used by the application logic described below. |

The rest of this document focuses on the **public** schema.

---

## 3. Base tables (public schema)

### 3.1 Entity relationship (high level)

```
organizations (sites/customers)
    │
    ├── devices (gateway units)  ──► devices.organization_id → organizations.organization_id
    │
    ├── channels (meters)       ──► channels.device_id → devices.device_id
    │                              channels.organization_id → organizations.organization_id
    │
    └── readings (time-series)  ──► readings.channel_id → channels.channel_id
```

### 3.2 organizations

Represents sites/customers.

| Column             | Type      | Nullable | Default           | Description |
|--------------------|-----------|----------|-------------------|-------------|
| organization_id     | text      | NOT NULL | -                 | Primary key (e.g. Eniscope org ID). |
| organization_name   | text      | NOT NULL | -                 | Display name. |
| address             | text      | YES      | -                 | Street address. |
| city                | text      | YES      | -                 | City. |
| postcode            | text      | YES      | -                 | Postal code. |
| country             | text      | YES      | -                 | Country. |
| timezone            | text      | YES      | 'America/New_York'| IANA timezone. |
| created_at          | timestamptz | YES   | CURRENT_TIMESTAMP | Row creation time. |
| updated_at          | timestamptz | YES   | CURRENT_TIMESTAMP | Row update time. |

- **Primary key:** `organization_id`  
- **Indexes:** `organizations_pkey` on `organization_id`  
- **Size (approx.):** ~8 KB table, ~24 KB indexes  

---

### 3.3 devices

Gateway/metering devices belonging to an organization.

| Column           | Type        | Nullable | Default           | Description |
|------------------|-------------|----------|-------------------|-------------|
| device_id        | integer     | NOT NULL | -                 | Primary key (e.g. Eniscope device ID). |
| device_name      | text        | YES      | -                 | Display name. |
| organization_id  | text        | YES      | -                 | FK → organizations.organization_id. |
| device_type      | text        | YES      | -                 | Type of device. |
| serial_number    | text        | YES      | -                 | Serial / UUID. |
| firmware_version | text        | YES      | -                 | Firmware version. |
| last_seen        | timestamptz | YES     | -                 | Last activity timestamp. |
| created_at       | timestamptz | YES     | CURRENT_TIMESTAMP | Row creation. |
| updated_at       | timestamptz | YES     | CURRENT_TIMESTAMP | Row update. |

- **Primary key:** `device_id`  
- **Foreign key:** `organization_id` → `organizations(organization_id)`  
- **Indexes:** `devices_pkey`, `idx_devices_org` on `organization_id`  
- **Size (approx.):** ~8 KB table, ~40 KB indexes  

---

### 3.4 channels

Meters / monitoring points. Each channel belongs to a device and an organization.

| Column           | Type        | Nullable | Default           | Description |
|------------------|-------------|----------|-------------------|-------------|
| channel_id       | integer     | NOT NULL | -                 | Primary key (e.g. Eniscope channel ID). |
| channel_name     | text        | NOT NULL | -                 | Display name. |
| device_id        | integer     | YES      | -                 | FK → devices.device_id. |
| organization_id  | text        | YES      | -                 | FK → organizations.organization_id. |
| channel_type     | text        | YES      | -                 | Type of channel. |
| unit             | text        | YES      | -                 | Unit (e.g. kWh, kW). |
| description      | text        | YES      | -                 | Optional description. |
| created_at       | timestamptz | YES     | CURRENT_TIMESTAMP | Row creation. |
| updated_at       | timestamptz | YES     | CURRENT_TIMESTAMP | Row update. |

- **Primary key:** `channel_id`  
- **Foreign keys:** `device_id` → `devices(device_id)`, `organization_id` → `organizations(organization_id)`  
- **Indexes:** `channels_pkey`, `idx_channels_org` on `organization_id`  
- **Size (approx.):** ~8 KB table, ~72 KB indexes  

---

### 3.5 readings

Time-series energy data: one row per channel per timestamp (15-minute resolution from Eniscope).

| Column               | Type        | Nullable | Default           | Description |
|----------------------|-------------|----------|-------------------|-------------|
| id                   | bigint      | NOT NULL | nextval(...)      | Surrogate primary key. |
| channel_id           | integer     | NOT NULL | -                 | FK → channels.channel_id. |
| timestamp            | timestamptz | NOT NULL | -                 | Reading time (UTC). |
| energy_kwh           | real        | YES      | -                 | Energy (kWh). |
| power_kw             | real        | YES      | -                 | Power (kW). |
| voltage_v            | real        | YES      | -                 | Voltage (V). |
| current_a            | real        | YES      | -                 | Current (A). |
| power_factor         | real        | YES      | -                 | Power factor. |
| reactive_power_kvar  | real        | YES      | -                 | Reactive power (kVAR). |
| temperature_c        | real        | YES      | -                 | Temperature (°C). |
| relative_humidity    | real        | YES      | -                 | Relative humidity. |
| created_at           | timestamptz | YES     | CURRENT_TIMESTAMP | Row creation. |

- **Primary key:** `id` (bigserial).  
- **Unique constraint:** `(channel_id, timestamp)` via `idx_readings_unique` – prevents duplicate readings and enables upsert (ON CONFLICT DO NOTHING).  
- **Foreign key:** `channel_id` → `channels(channel_id)`.  
- **Indexes:**
  - `idx_readings_channel_timestamp` on `(channel_id, timestamp DESC)` – main query pattern.  
  - `idx_readings_timestamp` on `(timestamp DESC)`.  
  - `idx_readings_unique` on `(channel_id, timestamp)`.  
- **Size (approx.):** ~23 MB table, ~32 MB indexes (largest table).  

Data is inserted from the Eniscope API (energy in kWh, power in kW). Validation before insert: no negative power, no future timestamps.

---

### 3.6 data_sync_status

Tracks last sync per organization (and optionally per channel): when data was last synced and status.

| Column                | Type        | Nullable | Default           | Description |
|-----------------------|-------------|----------|-------------------|-------------|
| id                    | integer     | NOT NULL | nextval(...)      | Primary key. |
| organization_id       | text        | NOT NULL | -                 | Organization/site. |
| channel_id            | integer     | YES      | -                 | Optional channel. |
| last_sync_timestamp   | timestamptz | NOT NULL | -                 | Last sync time. |
| last_reading_timestamp| timestamptz | YES     | -                 | Latest reading time in DB. |
| readings_count        | integer     | YES      | -                 | Count of readings (optional). |
| sync_status           | text        | YES      | -                 | e.g. 'success', 'partial', 'failed'. |
| error_message         | text        | YES      | -                 | Error details if failed. |
| created_at            | timestamptz | YES     | CURRENT_TIMESTAMP | Row creation. |

- **Primary key:** `id`.  
- **Index:** `idx_sync_status_org` on `(organization_id, last_sync_timestamp DESC)`.  
- **Size (approx.):** minimal table, ~24 KB indexes.  

---

### 3.7 ingestion_logs

Created by the historical ingestion script. One row per API pull (per channel per time range) for gap analysis and auditing.

| Column            | Type        | Nullable | Default           | Description |
|-------------------|-------------|----------|-------------------|-------------|
| id                | integer     | NOT NULL | nextval(...)      | Primary key. |
| organization_id   | text        | NOT NULL | -                 | Organization. |
| channel_id        | integer     | NOT NULL | -                 | Channel. |
| start_time        | timestamptz | NOT NULL | -                 | Start of requested range. |
| end_time          | timestamptz | NOT NULL | -                 | End of requested range. |
| readings_fetched  | integer     | NOT NULL | 0                 | Count from API. |
| readings_inserted | integer     | NOT NULL | 0                 | Count inserted. |
| readings_rejected | integer     | NOT NULL | 0                 | Count rejected (validation). |
| status            | text        | NOT NULL | 'success'         | 'success' or 'failure'. |
| error_message     | text        | YES      | -                 | Error if status = 'failure'. |
| created_at        | timestamptz | YES     | CURRENT_TIMESTAMP | Row creation. |

- **Primary key:** `id`.  
- **Index:** `idx_ingestion_logs_time` on `(organization_id, channel_id, start_time, end_time)` for gap queries.  
- **Size (approx.):** ~232 KB table, ~240 KB indexes.  

The table is created by `historical_ingestion.py` (`DatabaseManager.ensure_schema()`) if it does not exist.

---

### 3.8 Other tables in public

- **playing_with_neon** – legacy/test table; can be ignored for application logic.

---

## 4. Views and materialized views (layered architecture)

Analytics use a layered view design: raw → clean → materialized hourly → business views.

### 4.1 Layer 1: Clean readings

- **View:** `v_clean_readings`  
- **Source:** `readings`.  
- **Logic:**
  - Cast `timestamp` to `timestamptz` (UTC).
  - Filter out rows where `energy_kwh` or `power_kw` is NULL or zero.  
- **Purpose:** Single place for “valid” readings for all downstream views.

### 4.2 Layer 2: Materialized hourly

- **Materialized view:** `mv_hourly_usage`  
- **Source:** `v_clean_readings`.  
- **Columns:** `meter_id` (channel_id), `hour` (date_trunc hour), `avg_kw`, `total_kwh`, `reading_count`.  
- **Unique index:** `(meter_id, hour)` – required for `REFRESH MATERIALIZED VIEW CONCURRENTLY`.  
- **Refresh:** After ingestion (see “Maintenance” below). Refreshed via `refresh_views.py` (CONCURRENTLY when possible).

### 4.3 Layer 3: Business views (Option A)

All in **public** schema; they use business-friendly names (sites, meters).

| View                  | Purpose |
|-----------------------|--------|
| **v_sites**           | Alias for `organizations`: site_id, site_name, address, city, postcode, country, timezone, created_at, updated_at. |
| **v_meters**          | Channels joined to devices and organizations: meter_id, meter_name, site_id, site_name, device_id, device_name, device_type, device_uuid (serial_number), channel_type, unit, created_at, updated_at. |
| **v_readings_enriched**| Rows from `v_clean_readings` with site, meter, and device context (ids and names). Main view for analytics. |
| **v_latest_readings** | Latest reading per meter (DISTINCT ON channel_id, ordered by timestamp DESC): meter_id, meter_name, site_id, site_name, timestamp, energy_kwh, power_kw, voltage_v, current_a, power_factor. For dashboards. |
| **v_readings_hourly** | Wraps `mv_hourly_usage` and joins `v_meters`: hourly aggregates with meter/site names. |
| **v_readings_daily**  | From `v_clean_readings`: daily aggregates per meter (total_energy_kwh, avg/peak power, etc.) with meter/site names. |
| **v_readings_monthly**| From `v_clean_readings`: monthly aggregates per meter with meter/site names. |

Definitions live in `backend/scripts/database/create-layered-views.sql`.

---

## 5. How the database is built

### 5.1 Initial schema (tables)

- **Script:** `backend/scripts/database/setup-postgres-schema.js`  
- **Command:** `npm run db:setup`  
- **Actions:**
  - Creates (IF NOT EXISTS): `organizations`, `devices`, `channels`, `readings`, `data_sync_status`.  
  - Creates indexes on readings (`channel_id`+timestamp, timestamp, unique on channel_id+timestamp), and on channels/devices/sync_status by org.  
- **Note:** `ingestion_logs` is **not** in this script; it is created by `historical_ingestion.py` when that script runs (see below).

### 5.2 Migrations

- **TIMESTAMPTZ migration**  
  - **Script:** `backend/scripts/database/migrate-to-timestamptz.sql` and `backend/python_scripts/run_migration.py`.  
  - **Command:** `npm run db:migrate:timestamptz` (or run the SQL file).  
  - **Actions:** Converts timestamp columns to `timestamptz` in `readings`, `channels`, `devices`, `organizations`, `data_sync_status`, using `America/New_York` for existing naive timestamps.  

- **SQLite → Postgres (legacy):** `backend/scripts/database/migrate-sqlite-to-postgres.js` – one-time migration from an older SQLite DB; not part of normal Neon build.

### 5.3 Views and materialized view

- **Script:** `backend/scripts/database/create-layered-views.sql`.  
- **Runner:** `backend/python_scripts/run_create_views.py`.  
- **Command:** `npm run db:views`.  
- **Actions:** Creates/replaces `v_clean_readings`, drops and recreates `mv_hourly_usage` (and its unique index), then creates/replaces all Option A views above.  

Order of operations for a **new** Neon DB is typically:

1. `npm run db:setup`  
2. (Optional) `npm run db:migrate:timestamptz` if starting from old schema  
3. Run ingestion at least once so `readings` (and optionally `ingestion_logs`) exist  
4. `npm run db:views`  
5. Then use `npm run db:refresh-views` after each ingestion (see below)

---

## 6. How the database is maintained

### 6.1 Data ingestion (source: Eniscope API)

Two Python entrypoints populate **organizations**, **devices**, **channels**, and **readings** (and optionally **ingestion_logs**).

- **Daily / rolling sync (last N days)**  
  - **Script:** `backend/python_scripts/ingest_to_postgres.py`.  
  - **Example:** `python backend/python_scripts/ingest_to_postgres.py --site 23271 --days 7`.  
  - **Flow:** Authenticate to Eniscope → fetch orgs/channels → for each channel fetch readings in 15-min resolution (E, P, V, I, PF) → normalize (Wh→kWh, W→kW) → insert into `organizations`, `devices`, `channels`, `readings` (with conflict handling). After a successful run it can call `refresh_views.refresh_materialized_views()` to refresh `mv_hourly_usage`.  
  - **npm:** `npm run py:ingest` (1 day), `npm run py:ingest:full` (e.g. 90 days).

- **Historical backfill (with logging and validation)**  
  - **Script:** `backend/python_scripts/historical_ingestion.py`.  
  - **Example:** `python backend/python_scripts/historical_ingestion.py --site 23271 --start-date 2025-05-01 [--end-date 2025-12-31]`.  
  - **Flow:**  
    - Ensures schema: creates `ingestion_logs` (and index) if missing; does not change `readings` PK (relies on unique index on `(channel_id, timestamp)`).  
    - Fetches readings in 24-hour windows; validates (no negative power, no future timestamps); upserts into `readings` with `ON CONFLICT (channel_id, timestamp) DO NOTHING`.  
    - For each pull, inserts one row into `ingestion_logs` (org, channel, start/end time, fetched/inserted/rejected counts, status, error_message).  
  - **npm:** `npm run py:ingest:historical` (default dates), `npm run py:ingest:historical:custom` (with args).

### 6.2 Materialized view refresh

- **Script:** `backend/python_scripts/refresh_views.py`.  
- **Command:** `npm run db:refresh-views`.  
- **Actions:** Refreshes `mv_hourly_usage` using `REFRESH MATERIALIZED VIEW CONCURRENTLY` (so reads are not blocked).  
- **When:** After ingestion; `ingest_to_postgres.py` can call it automatically after a successful run.

### 6.3 Data validation

- **Script:** `backend/python_scripts/validate_data.py`.  
- **Command:** `npm run py:validate`.  
- **Actions:** Checks presence and basic integrity of `organizations`, `channels`, `readings`, `ingestion_logs`; can check for gaps or anomalies in ingestion (e.g. using `ingestion_logs`). Used in CI and after daily sync.

### 6.4 Scheduled / CI maintenance (GitHub Actions)

- **Daily sync** (`.github/workflows/daily-sync.yml`):  
  - Schedule: 02:00 UTC daily (and manual dispatch).  
  - Steps: checkout → Python 3.9 → install deps (psycopg2-binary, python-dotenv, requests, pytz) → run `ingest_to_postgres.py --site 23271 --days 7` → run `validate_data.py`.  
  - Secrets: `DATABASE_URL`, `VITE_ENISCOPE_*` (API key, email, password).  
  - Does **not** run `db:refresh-views` in the workflow; that can be added or run separately.

- **Data validation** (`.github/workflows/data-validation.yml`):  
  - Schedule: every 6 hours; also on push to `main` when `backend/python_scripts/**` or the workflow file change; manual dispatch.  
  - Runs `validate_data.py`; on failure can open a GitHub issue (e.g. “Data Validation Failed”).

- **Weekly report** (`.github/workflows/weekly-report.yml`):  
  - Uses the same DB (read-only for reports); does not change schema or ingestion.

---

## 7. Data flow summary

```
Eniscope API (organizations, channels, readings)
        │
        ▼
ingest_to_postgres.py  OR  historical_ingestion.py
        │
        ├── organizations, devices, channels (upserted/inserted)
        ├── readings (inserted with ON CONFLICT DO NOTHING)
        └── ingestion_logs (historical_ingestion only)
        │
        ▼
refresh_views.py  →  REFRESH MATERIALIZED VIEW CONCURRENTLY mv_hourly_usage
        │
        ▼
Applications / Tableau / reports query:
  v_sites, v_meters, v_readings_enriched, v_latest_readings,
  v_readings_hourly, v_readings_daily, v_readings_monthly
```

---

## 8. Important file reference

| Purpose              | Location |
|----------------------|----------|
| Schema (tables)       | `backend/scripts/database/setup-postgres-schema.js` |
| Views + mv           | `backend/scripts/database/create-layered-views.sql` |
| TIMESTAMPTZ migration| `backend/scripts/database/migrate-to-timestamptz.sql`, `backend/python_scripts/run_migration.py` |
| Create views         | `backend/python_scripts/run_create_views.py` |
| Refresh mv           | `backend/python_scripts/refresh_views.py` |
| Daily ingestion      | `backend/python_scripts/ingest_to_postgres.py` |
| Historical ingestion | `backend/python_scripts/historical_ingestion.py` |
| Validation           | `backend/python_scripts/validate_data.py` |
| Daily sync workflow  | `.github/workflows/daily-sync.yml` |
| Validation workflow  | `.github/workflows/data-validation.yml` |

---

## 9. NPM / CLI quick reference

```bash
# Schema & migrations
npm run db:setup                  # Create base tables
npm run db:migrate:timestamptz    # TIMESTAMP → TIMESTAMPTZ
npm run db:views                  # Create/recreate all views and mv
npm run db:refresh-views          # Refresh mv_hourly_usage

# Ingestion
npm run py:ingest                 # Ingest last 1 day (site 23271)
npm run py:ingest:full            # Ingest last 90 days
npm run py:ingest:historical      # Historical backfill (default range)
npm run py:validate               # Run data validation
```

---

This file is the single source of truth for “how the Neon database is structured and how it’s built and maintained” for use by Gemini or similar AI context.
