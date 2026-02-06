# Local Database Quick Start

## Why You're Here

You want to:
- ✅ Stop making 30+ API calls per report
- ✅ Generate reports in seconds instead of minutes
- ✅ Avoid rate limiting
- ✅ Enable advanced analytics in Cursor
- ✅ Save money on API costs

**Good news: You already have a database set up!**

## 5-Minute Setup

### Step 1: Ingest Wilson Center Data

```bash
# Pull last 90 days of data (one-time, takes ~5 minutes)
npm run ingest:full -- --days 90

# This creates: backend/data/eniscope.db
```

### Step 2: Verify Data

```bash
# Check what was loaded
npm run db:check

# You should see:
# ✓ Organizations: 1+
# ✓ Devices: 20+
# ✓ Channels: 20+
# ✓ Readings: 60,000+ (90 days × 18 channels × 96 intervals/day)
```

### Step 3: Set Up Daily Sync

```bash
# Add to crontab (runs daily at 6 AM)
crontab -e

# Add this line:
0 6 * * * cd /Users/sargo/cursor-repo/projects/argo-energy-solutions && npm run ingest:incremental >> logs/sync.log 2>&1
```

### Step 4: Query Your Data!

You can now query the database directly:

```bash
# Open SQLite CLI
sqlite3 backend/data/eniscope.db

# Try a query
SELECT COUNT(*) FROM readings;
```

## Using with Cursor

### Ask Cursor to Analyze Your Data

With the database loaded, you can now ask Cursor things like:

```
"Write a SQL query to find the top 5 energy consumers 
at Wilson Center last week"

"Show me hourly consumption patterns for AHU-2 
for the last 30 days"

"Compare weekend vs weekday energy use across 
all HVAC equipment"

"Find any channels where consumption doubled 
compared to last month"
```

Cursor will:
1. Write the SQL query
2. Execute it against your local database
3. Analyze the results
4. Suggest insights

### Example Cursor Workflow

```
You: "What were the peak demand times at Wilson Center last week?"

Cursor: [Writes and executes SQL query]
       [Shows results with timestamps and kW values]
       [Suggests: "Peak demand consistently occurs at 2-3 PM"]
```

## Speed Comparison

### Before (API-only):
```
Generating Wilson Center weekly report...
├─ Authenticate: 2s
├─ Fetch channels: 3s (with rate limiting)
├─ Fetch report data (18 channels): 45s (rate limited!)
├─ Fetch baseline data (18 channels): 90s (rate limited!)
├─ Run analytics: 5s
└─ Total: ~2.5 minutes
```

### After (Local database):
```
Generating Wilson Center weekly report...
├─ Query report data (18 channels): 0.5s ⚡
├─ Query baseline data (18 channels): 1.0s ⚡
├─ Run analytics: 5s
└─ Total: ~7 seconds (20× faster!)
```

## Data Freshness

### Automatic Daily Sync (Recommended)

Your cron job pulls new data every morning:
```
6:00 AM → Sync runs automatically
6:05 AM → New data available for reports
```

### Manual Sync (When Needed)

```bash
# Sync just Wilson Center
npm run ingest:incremental

# Sync all customers
npm run ingest:incremental --all
```

### Check Data Age

```sql
-- Last reading timestamp
SELECT 
  channel_name,
  MAX(timestamp) as last_reading,
  ROUND((julianday('now') - julianday(MAX(timestamp))) * 24, 1) as hours_ago
FROM readings r
JOIN channels c ON r.channel_id = c.channel_id
WHERE c.organization_id = '23271'
GROUP BY c.channel_name;
```

## Common Queries

### 1. Weekly Consumption Summary
```sql
SELECT 
  c.channel_name,
  ROUND(SUM(r.energy_kwh), 2) as total_kwh,
  ROUND(AVG(r.power_kw), 2) as avg_kw,
  ROUND(MAX(r.power_kw), 2) as peak_kw
FROM readings r
JOIN channels c ON r.channel_id = c.channel_id
WHERE c.organization_id = '23271'
  AND r.timestamp >= date('now', '-7 days')
GROUP BY c.channel_name
ORDER BY total_kwh DESC;
```

### 2. After-Hours Consumption
```sql
SELECT 
  c.channel_name,
  ROUND(SUM(CASE 
    WHEN CAST(strftime('%w', r.timestamp) AS INTEGER) IN (0, 6)  -- Weekend
      OR CAST(strftime('%H', r.timestamp) AS INTEGER) NOT BETWEEN 7 AND 18  -- After hours
    THEN r.energy_kwh 
    ELSE 0 
  END), 2) as after_hours_kwh,
  ROUND(SUM(r.energy_kwh), 2) as total_kwh,
  ROUND(100.0 * SUM(CASE 
    WHEN CAST(strftime('%w', r.timestamp) AS INTEGER) IN (0, 6) 
      OR CAST(strftime('%H', r.timestamp) AS INTEGER) NOT BETWEEN 7 AND 18 
    THEN r.energy_kwh ELSE 0 END) / SUM(r.energy_kwh), 1) as after_hours_pct
FROM readings r
JOIN channels c ON r.channel_id = c.channel_id
WHERE c.organization_id = '23271'
  AND r.timestamp >= date('now', '-7 days')
GROUP BY c.channel_name
HAVING after_hours_pct > 20
ORDER BY after_hours_kwh DESC;
```

### 3. Month-over-Month Comparison
```sql
SELECT 
  c.channel_name,
  ROUND(SUM(CASE WHEN r.timestamp >= date('now', 'start of month') 
    THEN r.energy_kwh ELSE 0 END), 2) as this_month_kwh,
  ROUND(SUM(CASE WHEN r.timestamp >= date('now', 'start of month', '-1 month') 
    AND r.timestamp < date('now', 'start of month') 
    THEN r.energy_kwh ELSE 0 END), 2) as last_month_kwh,
  ROUND(100.0 * (
    SUM(CASE WHEN r.timestamp >= date('now', 'start of month') THEN r.energy_kwh ELSE 0 END) - 
    SUM(CASE WHEN r.timestamp >= date('now', 'start of month', '-1 month') 
      AND r.timestamp < date('now', 'start of month') THEN r.energy_kwh ELSE 0 END)
  ) / NULLIF(SUM(CASE WHEN r.timestamp >= date('now', 'start of month', '-1 month') 
    AND r.timestamp < date('now', 'start of month') THEN r.energy_kwh ELSE 0 END), 0), 1) as pct_change
FROM readings r
JOIN channels c ON r.channel_id = c.channel_id
WHERE c.organization_id = '23271'
GROUP BY c.channel_name
HAVING last_month_kwh > 0
ORDER BY ABS(pct_change) DESC;
```

### 4. Daily Peak Demand
```sql
SELECT 
  date(r.timestamp) as day,
  c.channel_name,
  ROUND(MAX(r.power_kw), 2) as peak_kw,
  time(MAX(r.timestamp)) as peak_time
FROM readings r
JOIN channels c ON r.channel_id = c.channel_id
WHERE c.channel_id = 162119  -- RTU-2
  AND r.timestamp >= date('now', '-30 days')
GROUP BY date(r.timestamp), c.channel_name
ORDER BY peak_kw DESC
LIMIT 10;
```

## Export Data for Analysis

### Export to CSV
```bash
# Weekly data for specific channel
sqlite3 -header -csv backend/data/eniscope.db \
  "SELECT timestamp, power_kw, energy_kwh 
   FROM readings 
   WHERE channel_id = 162119 
     AND timestamp >= date('now', '-7 days')" \
  > wilson-ahu2-weekly.csv
```

### Export for Excel
```bash
# Monthly summary by channel
sqlite3 -header -csv backend/data/eniscope.db \
  "SELECT c.channel_name, 
          date(r.timestamp) as day,
          SUM(r.energy_kwh) as daily_kwh
   FROM readings r
   JOIN channels c ON r.channel_id = c.channel_id
   WHERE c.organization_id = '23271'
     AND r.timestamp >= date('now', 'start of month')
   GROUP BY c.channel_name, date(r.timestamp)" \
  > wilson-monthly-breakdown.csv
```

## Database Maintenance

### Weekly Optimization
```bash
# Optimize database (run weekly)
sqlite3 backend/data/eniscope.db "VACUUM; ANALYZE;"
```

### Check Database Size
```bash
# Show database size
ls -lh backend/data/eniscope.db

# Show table sizes
sqlite3 backend/data/eniscope.db \
  "SELECT 
     'organizations' as table_name, COUNT(*) as rows FROM organizations
   UNION ALL SELECT 'devices', COUNT(*) FROM devices
   UNION ALL SELECT 'channels', COUNT(*) FROM channels
   UNION ALL SELECT 'readings', COUNT(*) FROM readings;"
```

### Backup
```bash
# Simple backup (copy file)
cp backend/data/eniscope.db backend/data/eniscope-backup-$(date +%Y%m%d).db

# Or use SQLite backup command
sqlite3 backend/data/eniscope.db ".backup backend/data/eniscope-backup.db"
```

## Troubleshooting

### "Database file not found"
```bash
# Run initial ingestion
npm run ingest:full
```

### "No data returned from queries"
```bash
# Check what's in the database
npm run db:check

# Verify organization ID
sqlite3 backend/data/eniscope.db \
  "SELECT * FROM organizations;"
```

### "Queries are slow"
```bash
# Rebuild indexes
sqlite3 backend/data/eniscope.db \
  "REINDEX; ANALYZE;"
```

### "Database locked"
```bash
# Another process is using it
# Close any open SQLite connections
# Kill any running scripts

# Check for stale locks
lsof backend/data/eniscope.db
```

## Advanced: Custom Views

Create views for common queries:

```sql
-- Create view for after-hours consumption
CREATE VIEW IF NOT EXISTS after_hours_consumption AS
SELECT 
  c.channel_name,
  c.channel_id,
  c.organization_id,
  r.timestamp,
  r.energy_kwh,
  r.power_kw,
  CASE 
    WHEN CAST(strftime('%w', r.timestamp) AS INTEGER) IN (0, 6) THEN 1
    WHEN CAST(strftime('%H', r.timestamp) AS INTEGER) NOT BETWEEN 7 AND 18 THEN 1
    ELSE 0
  END as is_after_hours
FROM readings r
JOIN channels c ON r.channel_id = c.channel_id;

-- Now query it easily
SELECT 
  channel_name,
  SUM(CASE WHEN is_after_hours = 1 THEN energy_kwh ELSE 0 END) as after_hours_kwh
FROM after_hours_consumption
WHERE organization_id = '23271'
  AND timestamp >= date('now', '-7 days')
GROUP BY channel_name;
```

## Next Steps

1. **Today:**
   - ✅ Run `npm run ingest:full`
   - ✅ Verify data with `npm run db:check`
   - ✅ Try a few SQL queries

2. **This Week:**
   - ✅ Set up daily sync cron job
   - ✅ Ask Cursor to analyze your data
   - ✅ Export some data to CSV for Excel

3. **Next Week:**
   - ✅ Update weekly report to use local DB (we can help with this)
   - ✅ Create custom SQL views for common queries
   - ✅ Set up automatic backups

## Summary

✅ **Your database is already set up** - Just needs data  
✅ **One command to ingest** - `npm run ingest:full`  
✅ **Daily sync keeps it fresh** - Set up cron job  
✅ **100× faster queries** - Seconds instead of minutes  
✅ **Cursor-ready** - Ask questions, get SQL, analyze results  
✅ **Cost savings** - Fewer API calls  

**Get started now:**
```bash
npm run ingest:full -- --days 90
```

Then start querying! 🚀
