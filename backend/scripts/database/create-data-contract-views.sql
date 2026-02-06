-- ============================================================
-- Data Contract Views for Argo Energy Solutions
-- - Data Health Monitoring (gap detection)
-- - Virtual Metering (aggregated / synthetic meters)
-- ============================================================

-- ============================================================
-- A. Data Health View: v_data_health_monitor
-- ------------------------------------------------------------
-- Purpose:
--   Surface the latest reading per channel, compute how long
--   it has been since the last reading, and classify health.
--
-- Columns:
--   channel_id
--   channel_name
--   organization_id
--   last_reading_at        (TIMESTAMPTZ)
--   minutes_since_last_reading (NUMERIC)
--   status                 ('CRITICAL' | 'WARNING' | 'HEALTHY')
--
-- Notes:
--   - Uses CURRENT_TIMESTAMP AT TIME ZONE 'UTC' as reference.
--   - Channels with no readings are treated as CRITICAL.
-- ============================================================

CREATE OR REPLACE VIEW v_data_health_monitor AS
WITH latest AS (
    SELECT
        r.channel_id,
        MAX(r.timestamp) AS last_reading_at
    FROM readings r
    GROUP BY r.channel_id
)
SELECT
    c.channel_id,
    c.channel_name,
    c.organization_id,
    l.last_reading_at,
    CASE
        WHEN l.last_reading_at IS NULL THEN NULL
        ELSE EXTRACT(
            EPOCH FROM (
                (CURRENT_TIMESTAMP AT TIME ZONE 'UTC') - l.last_reading_at
            )
        ) / 60.0
    END AS minutes_since_last_reading,
    CASE
        WHEN l.last_reading_at IS NULL THEN 'CRITICAL'
        WHEN (CURRENT_TIMESTAMP AT TIME ZONE 'UTC') - l.last_reading_at > INTERVAL '120 minutes'
            THEN 'CRITICAL'
        WHEN (CURRENT_TIMESTAMP AT TIME ZONE 'UTC') - l.last_reading_at > INTERVAL '60 minutes'
            THEN 'WARNING'
        ELSE 'HEALTHY'
    END AS status
FROM channels c
LEFT JOIN latest l ON l.channel_id = c.channel_id;


-- ============================================================
-- B. Virtual Metering Schema
-- ------------------------------------------------------------
-- Purpose:
--   Define virtual meters as weighted combinations of physical
--   channels (meters) and expose a virtual readings view that
--   behaves like a physical meter for querying.
--
-- Tables:
--   virtual_meters:
--     - id              (PK)
--     - name            (TEXT)
--     - organization_id (TEXT)
--     - unit            (TEXT, e.g. 'kWh')
--     - description     (TEXT)
--
--   virtual_meter_map:
--     - virtual_meter_id (FK → virtual_meters.id)
--     - channel_id       (FK → channels.channel_id)
--     - weight           (NUMERIC, e.g. 1.0 or -1.0)
--
-- View:
--   v_virtual_readings:
--     - Aggregates readings by virtual_meter_id and timestamp,
--       weighting each channel's contribution by `weight`.
-- ============================================================

CREATE TABLE IF NOT EXISTS virtual_meters (
    id              SERIAL PRIMARY KEY,
    name            TEXT NOT NULL,
    organization_id TEXT NOT NULL,
    unit            TEXT NOT NULL DEFAULT 'kWh',
    description     TEXT
);


CREATE TABLE IF NOT EXISTS virtual_meter_map (
    virtual_meter_id INTEGER NOT NULL REFERENCES virtual_meters(id) ON DELETE CASCADE,
    channel_id       INTEGER NOT NULL REFERENCES channels(channel_id) ON DELETE CASCADE,
    weight           NUMERIC NOT NULL DEFAULT 1.0,
    PRIMARY KEY (virtual_meter_id, channel_id)
);


CREATE OR REPLACE VIEW v_virtual_readings AS
SELECT
    vm.id              AS virtual_meter_id,
    vm.name            AS virtual_meter_name,
    vm.organization_id,
    vm.unit,
    r.timestamp,
    SUM(r.energy_kwh * COALESCE(vmm.weight, 1.0)) AS energy_kwh,
    SUM(r.power_kw   * COALESCE(vmm.weight, 1.0)) AS power_kw
FROM virtual_meters vm
JOIN virtual_meter_map vmm
    ON vmm.virtual_meter_id = vm.id
JOIN readings r
    ON r.channel_id = vmm.channel_id
GROUP BY
    vm.id,
    vm.name,
    vm.organization_id,
    vm.unit,
    r.timestamp;


-- ============================================================
-- C. Example Test Data (Wilson Center - Site 23271)
-- ------------------------------------------------------------
-- NOTE:
--   This is commented-out example data to help validate the
--   virtual metering logic. Replace the channel_id values
--   with real Wilson Center channel IDs from your environment
--   before running.
--   To use it, copy/paste into psql or a migration and
--   remove the leading `--` markers.
-- ============================================================
-- INSERT INTO virtual_meters (name, organization_id, unit, description)
-- VALUES (
--     'Wilson Center - Total Building Load',
--     '23271',
--     'kWh',
--     'Virtual meter combining two Wilson Center feeds'
-- )
-- -- Example: after getting id = 1, map two physical channels into it
-- INSERT INTO virtual_meter_map (virtual_meter_id, channel_id, weight)
-- VALUES
--     (1, 12345, 1.0),  -- TODO: replace 12345 with a real channel_id for Site 23271
--     (1, 23456, 1.0);  -- TODO: replace 23456 with a different channel_id for Site 23271

