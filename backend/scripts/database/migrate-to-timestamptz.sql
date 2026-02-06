-- Migration Script: Convert TIMESTAMP to TIMESTAMPTZ
-- 
-- This script converts all timestamp columns to timezone-aware TIMESTAMPTZ
-- Safe to run on existing data - preserves all values
--
-- Run with: psql $DATABASE_URL -f migrate-to-timestamptz.sql
-- Or via: npm run db:migrate:timestamptz

BEGIN;

-- Backup recommendations:
-- 1. Take a snapshot of your Neon database first
-- 2. Test on a copy before running on production
-- 3. Run during low-usage period

-- readings table (most important - 151K+ rows)
ALTER TABLE readings 
ALTER COLUMN timestamp TYPE TIMESTAMPTZ 
USING timestamp AT TIME ZONE 'America/New_York';

ALTER TABLE readings 
ALTER COLUMN created_at TYPE TIMESTAMPTZ 
USING created_at AT TIME ZONE 'America/New_York';

-- channels table
ALTER TABLE channels 
ALTER COLUMN created_at TYPE TIMESTAMPTZ 
USING created_at AT TIME ZONE 'America/New_York';

ALTER TABLE channels 
ALTER COLUMN updated_at TYPE TIMESTAMPTZ 
USING updated_at AT TIME ZONE 'America/New_York';

-- devices table
ALTER TABLE devices 
ALTER COLUMN last_seen TYPE TIMESTAMPTZ 
USING last_seen AT TIME ZONE 'America/New_York';

ALTER TABLE devices 
ALTER COLUMN created_at TYPE TIMESTAMPTZ 
USING created_at AT TIME ZONE 'America/New_York';

ALTER TABLE devices 
ALTER COLUMN updated_at TYPE TIMESTAMPTZ 
USING updated_at AT TIME ZONE 'America/New_York';

-- organizations table
ALTER TABLE organizations 
ALTER COLUMN created_at TYPE TIMESTAMPTZ 
USING created_at AT TIME ZONE 'America/New_York';

ALTER TABLE organizations 
ALTER COLUMN updated_at TYPE TIMESTAMPTZ 
USING updated_at AT TIME ZONE 'America/New_York';

-- data_sync_status table
ALTER TABLE data_sync_status 
ALTER COLUMN last_sync_timestamp TYPE TIMESTAMPTZ 
USING last_sync_timestamp AT TIME ZONE 'America/New_York';

ALTER TABLE data_sync_status 
ALTER COLUMN last_reading_timestamp TYPE TIMESTAMPTZ 
USING last_reading_timestamp AT TIME ZONE 'America/New_York';

ALTER TABLE data_sync_status 
ALTER COLUMN created_at TYPE TIMESTAMPTZ 
USING created_at AT TIME ZONE 'America/New_York';

-- Verify migration
DO $$
DECLARE
    timestamp_count INTEGER;
    timestamptz_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO timestamp_count
    FROM information_schema.columns
    WHERE table_schema = 'public'
      AND data_type = 'timestamp without time zone';
    
    SELECT COUNT(*) INTO timestamptz_count
    FROM information_schema.columns
    WHERE table_schema = 'public'
      AND data_type = 'timestamp with time zone';
    
    RAISE NOTICE 'Migration complete:';
    RAISE NOTICE '  Remaining TIMESTAMP columns: %', timestamp_count;
    RAISE NOTICE '  TIMESTAMPTZ columns: %', timestamptz_count;
    
    IF timestamp_count > 0 THEN
        RAISE WARNING 'Some TIMESTAMP columns remain - review manually';
    END IF;
END $$;

COMMIT;

-- Verify the migration
SELECT 
    table_name,
    column_name,
    data_type
FROM information_schema.columns
WHERE table_schema = 'public'
  AND (data_type LIKE '%timestamp%')
ORDER BY table_name, column_name;
