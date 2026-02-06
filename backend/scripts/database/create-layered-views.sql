-- =============================================================================
-- Layered View Architecture + Option A Analytics Views
-- Neon / PostgreSQL
-- Run once: see run_create_views.py or npm run db:views
-- =============================================================================
-- Layer 1: Clean readings (raw table is "readings" in this schema)
-- Layer 2: Materialized hourly usage (refresh after ingestion)
-- Layer 3: Option A views (sites, meters, enriched, latest, daily, monthly)
-- =============================================================================

-- -----------------------------------------------------------------------------
-- LAYER 1: Clean readings
-- Source: readings (your raw table, conceptually energy_readings_raw)
-- Ensures TIMESTAMPTZ and excludes rows with null/zero energy or power.
-- -----------------------------------------------------------------------------
CREATE OR REPLACE VIEW v_clean_readings AS
SELECT
    id,
    channel_id,
    (timestamp AT TIME ZONE 'UTC')::timestamptz AS timestamp,
    energy_kwh,
    power_kw,
    voltage_v,
    current_a,
    power_factor,
    reactive_power_kvar,
    temperature_c,
    relative_humidity,
    created_at
FROM readings
WHERE energy_kwh IS NOT NULL AND energy_kwh <> 0
  AND power_kw IS NOT NULL AND power_kw <> 0;

COMMENT ON VIEW v_clean_readings IS 'Clean readings: TIMESTAMPTZ, no null/zero energy or power. Source: readings (raw).';


-- -----------------------------------------------------------------------------
-- LAYER 2: Materialized hourly usage (supports REFRESH CONCURRENTLY)
-- Groups v_clean_readings by hour and meter (channel_id).
-- -----------------------------------------------------------------------------
DROP MATERIALIZED VIEW IF EXISTS mv_hourly_usage CASCADE;

CREATE MATERIALIZED VIEW mv_hourly_usage AS
SELECT
    channel_id AS meter_id,
    date_trunc('hour', timestamp) AS hour,
    AVG(power_kw)   AS avg_kw,
    SUM(energy_kwh) AS total_kwh,
    COUNT(*)        AS reading_count
FROM v_clean_readings
GROUP BY channel_id, date_trunc('hour', timestamp);

COMMENT ON MATERIALIZED VIEW mv_hourly_usage IS 'Hourly aggregates from v_clean_readings. Refresh after ingestion.';

-- Required for REFRESH MATERIALIZED VIEW CONCURRENTLY
CREATE UNIQUE INDEX idx_mv_hourly_usage_meter_hour ON mv_hourly_usage (meter_id, hour);


-- -----------------------------------------------------------------------------
-- OPTION A: Business-friendly aliases
-- -----------------------------------------------------------------------------

-- v_sites: alias for organizations (business terminology)
CREATE OR REPLACE VIEW v_sites AS
SELECT
    organization_id AS site_id,
    organization_name AS site_name,
    address,
    city,
    postcode,
    country,
    timezone,
    created_at,
    updated_at
FROM organizations;

COMMENT ON VIEW v_sites IS 'Sites (organizations). Business-friendly alias.';


-- v_meters: enriched channels with device and site info
CREATE OR REPLACE VIEW v_meters AS
SELECT
    c.channel_id AS meter_id,
    c.channel_name AS meter_name,
    c.organization_id AS site_id,
    o.organization_name AS site_name,
    c.device_id,
    d.device_name,
    d.device_type,
    d.serial_number AS device_uuid,
    c.channel_type,
    c.unit,
    c.created_at,
    c.updated_at
FROM channels c
LEFT JOIN devices d ON c.device_id = d.device_id
JOIN organizations o ON c.organization_id = o.organization_id;

COMMENT ON VIEW v_meters IS 'Meters (channels) with device and site. Business-friendly alias.';


-- v_readings_enriched: clean readings with full context (site, meter, device)
CREATE OR REPLACE VIEW v_readings_enriched AS
SELECT
    r.id,
    r.channel_id AS meter_id,
    c.channel_name AS meter_name,
    c.organization_id AS site_id,
    o.organization_name AS site_name,
    c.device_id,
    d.device_name,
    d.device_type,
    d.serial_number AS device_uuid,
    r.timestamp,
    r.energy_kwh,
    r.power_kw,
    r.voltage_v,
    r.current_a,
    r.power_factor,
    r.reactive_power_kvar,
    r.temperature_c,
    r.relative_humidity,
    r.created_at
FROM v_clean_readings r
JOIN channels c ON r.channel_id = c.channel_id
LEFT JOIN devices d ON c.device_id = d.device_id
JOIN organizations o ON c.organization_id = o.organization_id;

COMMENT ON VIEW v_readings_enriched IS 'Clean readings with site, meter, device. Use for analytics.';


-- v_latest_readings: most recent reading per meter (for dashboards)
CREATE OR REPLACE VIEW v_latest_readings AS
SELECT DISTINCT ON (r.channel_id)
    r.channel_id AS meter_id,
    c.channel_name AS meter_name,
    c.organization_id AS site_id,
    o.organization_name AS site_name,
    r.timestamp,
    r.energy_kwh,
    r.power_kw,
    r.voltage_v,
    r.current_a,
    r.power_factor
FROM v_clean_readings r
JOIN channels c ON r.channel_id = c.channel_id
JOIN organizations o ON c.organization_id = o.organization_id
ORDER BY r.channel_id, r.timestamp DESC;

COMMENT ON VIEW v_latest_readings IS 'Latest reading per meter. For real-time dashboards.';


-- -----------------------------------------------------------------------------
-- OPTION A: Time aggregations (hourly uses materialized view)
-- -----------------------------------------------------------------------------

-- v_readings_hourly: hourly with names (wraps mv_hourly_usage)
CREATE OR REPLACE VIEW v_readings_hourly AS
SELECT
    h.meter_id,
    m.meter_name,
    m.site_id,
    m.site_name,
    m.device_id,
    m.device_name,
    h.hour,
    h.avg_kw,
    h.total_kwh,
    h.reading_count
FROM mv_hourly_usage h
JOIN v_meters m ON h.meter_id = m.meter_id;

COMMENT ON VIEW v_readings_hourly IS 'Hourly usage with meter/site names. Backed by mv_hourly_usage.';


-- v_readings_daily: daily aggregates from clean readings
CREATE OR REPLACE VIEW v_readings_daily AS
SELECT
    r.channel_id AS meter_id,
    c.channel_name AS meter_name,
    c.organization_id AS site_id,
    o.organization_name AS site_name,
    date_trunc('day', r.timestamp)::date AS reading_date,
    SUM(r.energy_kwh)   AS total_energy_kwh,
    AVG(r.power_kw)     AS avg_power_kw,
    MAX(r.power_kw)     AS peak_power_kw,
    AVG(r.voltage_v)    AS avg_voltage_v,
    AVG(r.power_factor) AS avg_power_factor,
    COUNT(*)            AS reading_count
FROM v_clean_readings r
JOIN channels c ON r.channel_id = c.channel_id
JOIN organizations o ON c.organization_id = o.organization_id
GROUP BY r.channel_id, c.channel_name, c.organization_id, o.organization_name,
         date_trunc('day', r.timestamp);

COMMENT ON VIEW v_readings_daily IS 'Daily aggregates per meter. For trends and billing.';


-- v_readings_monthly: monthly aggregates from clean readings
CREATE OR REPLACE VIEW v_readings_monthly AS
SELECT
    r.channel_id AS meter_id,
    c.channel_name AS meter_name,
    c.organization_id AS site_id,
    o.organization_name AS site_name,
    date_trunc('month', r.timestamp)::date AS reading_month,
    SUM(r.energy_kwh)   AS total_energy_kwh,
    AVG(r.power_kw)     AS avg_power_kw,
    MAX(r.power_kw)     AS peak_power_kw,
    COUNT(*)            AS reading_count
FROM v_clean_readings r
JOIN channels c ON r.channel_id = c.channel_id
JOIN organizations o ON c.organization_id = o.organization_id
GROUP BY r.channel_id, c.channel_name, c.organization_id, o.organization_name,
         date_trunc('month', r.timestamp);

COMMENT ON VIEW v_readings_monthly IS 'Monthly aggregates per meter. For budgets and trends.';
