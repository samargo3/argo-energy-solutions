# Neon PostgreSQL Setup Guide for Argo Energy Solutions

## Step 1: Create Neon Account (5 minutes)

### A. Sign Up
1. Go to **https://neon.tech**
2. Click "Sign Up"
3. Choose "Continue with GitHub" (recommended - easiest)
4. Authorize Neon to access your GitHub account

### B. Create Your Project
1. After login, click "Create a project"
2. **Project name:** `argo-energy-production`
3. **Region:** Choose closest to you:
   - `US East (Ohio)` - us-east-2
   - `US West (Oregon)` - us-west-2
   - (Choose US East if unsure)
4. **PostgreSQL version:** 16 (default, latest)
5. Click "Create Project"

### C. Get Your Connection String
After project creation, you'll see a connection string like:

```
postgresql://neondb_owner:npg_ABC123xyz@ep-cool-breeze-a1b2c3d4.us-east-2.aws.neon.tech/neondb?sslmode=require
```

**Save this!** You'll need it in the next step.

---

## Step 2: Add Connection String to .env

```bash
# Open your .env file
nano /Users/sargo/cursor-repo/projects/argo-energy-solutions/.env
```

Add these lines:

```bash
# Neon PostgreSQL Database
DATABASE_URL=postgresql://neondb_owner:YOUR_PASSWORD@ep-xxx.us-east-2.aws.neon.tech/neondb?sslmode=require

# For backwards compatibility (keep SQLite too during transition)
SQLITE_DB_PATH=./backend/data/eniscope.db
```

**Important:** 
- Replace with YOUR actual connection string from Neon
- Keep your Eniscope API credentials (don't delete them)
- Add the SQLite path so you can switch back if needed

---

## Step 3: Install PostgreSQL Client Library

```bash
cd /Users/sargo/cursor-repo/projects/argo-energy-solutions

# Install pg (PostgreSQL client for Node.js)
npm install pg

# Install dotenv if not already installed
npm install dotenv
```

---

## Step 4: Test Connection

Create a test script:

```bash
# This will be created for you in the next step
node backend/scripts/database/test-neon-connection.js
```

You should see:
```
✓ Connected to Neon PostgreSQL!
✓ Server time: 2026-02-01 12:34:56
✓ PostgreSQL version: 16.x
✓ Database: neondb
```

---

## Step 5: Create Database Schema

Run the schema creation script:

```bash
npm run db:setup
```

This creates all the tables:
- ✓ organizations
- ✓ devices  
- ✓ channels
- ✓ readings (with optimized indexes)

---

## Step 6: Migrate Data from SQLite (Optional)

If you already have data in SQLite:

```bash
# Migrate all data from SQLite to Neon
npm run db:migrate:sqlite-to-postgres

# This will:
# - Read all data from backend/data/eniscope.db
# - Transfer to Neon PostgreSQL
# - Show progress
# - Verify counts match
```

---

## Step 7: Ingest Fresh Data

Pull fresh data from Eniscope API directly to Neon:

```bash
# Pull last 90 days for Wilson Center
npm run ingest:full -- --db postgres --days 90

# This now writes to Neon instead of SQLite!
```

---

## Step 8: Verify Data

Check what was loaded:

```bash
npm run db:check -- --db postgres

# You should see:
# ✓ Organizations: 1+
# ✓ Devices: 20+
# ✓ Channels: 18+
# ✓ Readings: 60,000+
```

---

## Step 9: Enable TimescaleDB (Optional, Recommended)

TimescaleDB is a PostgreSQL extension optimized for time-series data.

### In Neon Console:
1. Go to your project dashboard
2. Click "SQL Editor" tab
3. Run this SQL:

```sql
-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Convert readings table to hypertable (time-series optimized)
SELECT create_hypertable('readings', 'timestamp', 
  chunk_time_interval => INTERVAL '7 days',
  if_not_exists => TRUE
);

-- Add compression policy (save storage, improve query speed)
ALTER TABLE readings SET (
  timescaledb.compress,
  timescaledb.compress_segmentby = 'channel_id'
);

-- Auto-compress data older than 30 days
SELECT add_compression_policy('readings', INTERVAL '30 days');

-- Create continuous aggregate for hourly data (pre-computed, super fast)
CREATE MATERIALIZED VIEW readings_hourly
WITH (timescaledb.continuous) AS
SELECT 
  time_bucket('1 hour', timestamp) AS hour,
  channel_id,
  AVG(power_kw) as avg_power_kw,
  MAX(power_kw) as max_power_kw,
  SUM(energy_kwh) as total_energy_kwh,
  COUNT(*) as reading_count
FROM readings
GROUP BY hour, channel_id
WITH NO DATA;

-- Refresh policy (keep aggregate up to date)
SELECT add_continuous_aggregate_policy('readings_hourly',
  start_offset => INTERVAL '3 days',
  end_offset => INTERVAL '1 hour',
  schedule_interval => INTERVAL '1 hour'
);
```

**Benefits:**
- ⚡ 10-100× faster queries on large datasets
- 💾 90% storage reduction with compression
- 🚀 Instant hourly/daily aggregates

---

## Step 10: Update Daily Sync

Update your cron job to use PostgreSQL:

```bash
crontab -e

# Change from:
# 0 6 * * * cd /path && npm run ingest:incremental

# To:
0 6 * * * cd /Users/sargo/cursor-repo/projects/argo-energy-solutions && npm run ingest:incremental -- --db postgres >> logs/sync.log 2>&1
```

---

## Connection String Format

### What Each Part Means

```
postgresql://USER:PASSWORD@HOST:PORT/DATABASE?OPTIONS
           │     │         │     │     │        │
           │     │         │     │     │        └─ SSL mode, etc.
           │     │         │     │     └────────── Database name
           │     │         │     └──────────────── Port (usually 5432)
           │     │         └────────────────────── Neon host
           │     └──────────────────────────────── Your password
           └────────────────────────────────────── Username
```

### Neon-Specific Features

Your connection string includes:
- **Pooler:** For connection pooling (better performance)
- **SSL:** Required for security
- **Region:** Your database location

---

## Neon Dashboard Features

### SQL Editor
- Write and run queries directly
- Save favorite queries
- Export results to CSV

### Monitoring
- Query performance
- Storage usage
- Connection count
- CPU/Memory metrics

### Branches
- Create dev/staging copies
- Test changes safely
- Merge when ready

### Backups
- Automatic daily backups
- Point-in-time recovery (restore to any moment)
- Retention: 7 days (free tier)

---

## Performance Tips

### 1. Use Connection Pooling
```javascript
// In your database client
import pg from 'pg';
const pool = new pg.Pool({
  connectionString: process.env.DATABASE_URL,
  max: 20, // Maximum connections
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 2000,
});
```

### 2. Create Indexes for Common Queries
```sql
-- Already created in schema, but here for reference
CREATE INDEX idx_readings_channel_timestamp 
  ON readings(channel_id, timestamp DESC);

CREATE INDEX idx_readings_timestamp 
  ON readings(timestamp DESC);

CREATE INDEX idx_channels_org 
  ON channels(organization_id);
```

### 3. Use Prepared Statements
```javascript
// Faster for repeated queries
const result = await pool.query(
  'SELECT * FROM readings WHERE channel_id = $1 AND timestamp >= $2',
  [channelId, startDate]
);
```

### 4. Batch Inserts
```javascript
// Insert multiple readings at once
const values = readings.map((r, i) => 
  `($${i*4+1}, $${i*4+2}, $${i*4+3}, $${i*4+4})`
).join(',');

await pool.query(
  `INSERT INTO readings (channel_id, timestamp, power_kw, energy_kwh) 
   VALUES ${values}`,
  readings.flatMap(r => [r.channel_id, r.timestamp, r.power_kw, r.energy_kwh])
);
```

---

## Troubleshooting

### "Connection timeout"
```bash
# Check your connection string
echo $DATABASE_URL

# Make sure SSL mode is set
# Should end with: ?sslmode=require
```

### "Database does not exist"
```bash
# Use the default database: neondb
# Don't create a new one (not needed)
```

### "Too many connections"
```bash
# Use connection pooling (see above)
# Free tier allows 100 simultaneous connections
```

### "Queries are slow"
```bash
# Check if indexes exist
psql $DATABASE_URL -c "\d readings"

# Enable TimescaleDB (see Step 9)
```

### "Out of storage" (unlikely on free tier)
```bash
# Check usage in Neon dashboard
# Free tier: 3 GB storage

# Compress old data with TimescaleDB
# Or delete very old readings
DELETE FROM readings WHERE timestamp < NOW() - INTERVAL '2 years';
```

---

## Data Retention Strategy

### Recommended Approach

```sql
-- Keep detailed data for 1 year
-- Keep hourly aggregates for 3 years
-- Keep daily aggregates forever

-- Create daily aggregate table
CREATE MATERIALIZED VIEW readings_daily AS
SELECT 
  DATE(timestamp) as date,
  channel_id,
  AVG(power_kw) as avg_power_kw,
  MAX(power_kw) as max_power_kw,
  MIN(power_kw) as min_power_kw,
  SUM(energy_kwh) as total_energy_kwh
FROM readings
GROUP BY date, channel_id;

-- Automatic cleanup (run monthly)
DELETE FROM readings 
WHERE timestamp < NOW() - INTERVAL '1 year'
  AND DATE(timestamp) IN (
    SELECT date FROM readings_daily
  );
```

**This keeps your database size under control while preserving historical trends.**

---

## Backup Strategy

### Neon Automatic Backups
- ✅ Daily backups (free tier)
- ✅ 7-day retention
- ✅ Point-in-time recovery

### Manual Backup (Optional)
```bash
# Export full database
pg_dump $DATABASE_URL > backup-$(date +%Y%m%d).sql

# Export just readings table
pg_dump $DATABASE_URL -t readings > readings-backup.sql

# Restore if needed
psql $DATABASE_URL < backup-20260201.sql
```

---

## Cost Monitoring

### Free Tier Limits
- **Storage:** 3 GB
- **Compute:** 191.9 hours/month
- **Data transfer:** 5 GB/month
- **Branches:** 10

### Check Usage
1. Go to Neon dashboard
2. Click "Usage" tab
3. Monitor:
   - Storage (aim for <2.5 GB to stay safe)
   - Compute hours (should be plenty)
   - Data transfer

### If You Approach Limits
- **Storage:** Delete old data or upgrade to Launch ($19/mo)
- **Compute:** Enable auto-suspend (already default)
- **Transfer:** Cache queries in application

---

## Next Steps After Setup

1. ✅ **Test weekly report with Neon:**
   ```bash
   npm run report:weekly -- --site 23271 --db postgres
   ```

2. ✅ **Set up daily sync:**
   ```bash
   # Add to crontab
   0 6 * * * cd /path && npm run ingest:incremental -- --db postgres
   ```

3. ✅ **Enable TimescaleDB** (see Step 9)

4. ✅ **Create monitoring dashboard** (Neon console)

5. ✅ **Add more customers:**
   ```bash
   npm run ingest:full -- --site <NEW_SITE_ID> --db postgres
   ```

---

## Summary Checklist

- [ ] Created Neon account
- [ ] Created project: `argo-energy-production`
- [ ] Saved connection string to `.env`
- [ ] Installed `pg` package
- [ ] Tested connection
- [ ] Created database schema
- [ ] Ingested Wilson Center data
- [ ] Verified data loaded correctly
- [ ] (Optional) Enabled TimescaleDB
- [ ] Updated cron job for daily sync
- [ ] Generated test report

**You're now running on cloud PostgreSQL!** 🚀

---

## Getting Help

- **Neon Docs:** https://neon.tech/docs
- **Neon Discord:** https://discord.gg/neon
- **PostgreSQL Docs:** https://postgresql.org/docs
- **TimescaleDB Docs:** https://docs.timescale.com

---

## Useful SQL Queries for Neon

### Check Database Size
```sql
SELECT 
  pg_size_pretty(pg_database_size('neondb')) as database_size;
```

### Check Table Sizes
```sql
SELECT 
  schemaname,
  tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### Check Active Connections
```sql
SELECT count(*) as active_connections
FROM pg_stat_activity
WHERE state = 'active';
```

### Check Query Performance
```sql
-- Show slow queries
SELECT 
  query,
  calls,
  total_exec_time / 1000 as total_seconds,
  mean_exec_time / 1000 as avg_seconds
FROM pg_stat_statements
ORDER BY total_exec_time DESC
LIMIT 10;
```
