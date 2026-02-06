# Data Storage Strategy for Argo Energy Solutions

## Overview

This guide outlines the recommended approach for storing and managing energy data to enable fast, flexible analytics while minimizing API costs and rate limiting issues.

## Current State

### What You Have
✅ SQLite database schema (`backend/scripts/data-collection/ingest-eniscope-data.js`)
✅ Data ingestion script (working)
✅ Database structure for:
- Organizations (sites/customers)
- Devices
- Channels (meters)
- Readings (time-series interval data)

### What's Missing
⚠️ Automated daily sync
⚠️ Data freshness monitoring
⚠️ Weekly reports using local database
⚠️ Query optimization

## Recommended Architecture

### Phase 1: Use SQLite (Current - Next 6 months)
**Best for:** 1-50 customers, getting started

**Database location:** `backend/data/eniscope.db`

**Advantages:**
- Already partially implemented
- Zero infrastructure costs
- Fast enough for your scale
- Perfect for development and analysis
- Great integration with Cursor AI

**Limitations:**
- Single writer at a time
- Max ~1TB data (you'll hit 1-10GB first)
- Not ideal for 24/7 web app

### Phase 2: Migrate to PostgreSQL (When needed)
**Upgrade when:** 50+ customers OR multiple team members OR customer portal

**Advantages:**
- Concurrent access
- Better performance at scale
- Richer analytics capabilities
- Production-ready

## Data Sync Strategy

### 1. Initial Data Load (One-time)
Pull historical data for each customer:

```bash
# Full ingestion for Wilson Center
npm run ingest:full -- --site 23271 --days 180

# This creates/updates backend/data/eniscope.db
```

**Recommendation:** Start with 90-180 days of history

### 2. Daily Incremental Sync (Automated)
Run every morning to get yesterday's data:

```bash
# Incremental (only new data)
npm run ingest:incremental -- --site 23271
```

**Setup cron job:**
```bash
# Run daily at 6 AM
0 6 * * * cd /path/to/project && npm run ingest:incremental
```

### 3. Weekly Report Generation
Reports now use **local database** instead of API:

```bash
# Fast! Uses local data
npm run report:weekly -- --site 23271 --source local
```

**Benefits:**
- ⚡ 10-100× faster
- 💰 Zero API calls
- 🔄 No rate limiting
- 📊 Can query any time range

## Database Schema

### Current Tables

```sql
-- Sites/Customers
organizations (
  organization_id TEXT PRIMARY KEY,
  organization_name TEXT,
  address, city, country,
  created_at, updated_at
)

-- Meters/Monitoring Points
channels (
  channel_id INTEGER PRIMARY KEY,
  channel_name TEXT,
  device_id INTEGER,
  organization_id INTEGER
)

-- Time-Series Data (The Big Table)
readings (
  id INTEGER PRIMARY KEY,
  channel_id INTEGER,
  timestamp TEXT,
  energy_kwh REAL,    -- kWh per interval
  power_kw REAL,      -- Average kW
  voltage_v REAL,
  current_a REAL,
  power_factor REAL,
  temperature_c REAL
)
```

### Indexes (Already Created)
```sql
-- Fast lookups
CREATE INDEX idx_readings_channel_timestamp ON readings(channel_id, timestamp);
CREATE INDEX idx_readings_timestamp ON readings(timestamp);
```

## Storage Estimates

### Data Size Projections

**Per Channel:**
- 15-min intervals = 96 readings/day = 35,040/year
- ~100 bytes per reading
- **1 year = ~3.5 MB per channel**

**Wilson Center (18 channels):**
- 1 year = 63 MB
- 2 years = 126 MB

**50 Customers (average 15 channels each):**
- 1 year = 2.6 GB
- 2 years = 5.2 GB

**Conclusion:** SQLite handles this easily (can go to ~1TB)

## Query Performance

### SQLite Performance Benchmarks

With proper indexes:
- Point query (single reading): <1ms
- Time range (1 week): 10-50ms
- Aggregation (1 month): 50-200ms
- Complex analytics (1 year): 200ms-1s

**This is 100-1000× faster than API calls!**

### Example Queries

```sql
-- Weekly consumption by channel
SELECT 
  c.channel_name,
  SUM(r.energy_kwh) as total_kwh,
  AVG(r.power_kw) as avg_kw
FROM readings r
JOIN channels c ON r.channel_id = c.channel_id
WHERE r.timestamp BETWEEN '2026-01-18' AND '2026-01-24'
GROUP BY c.channel_name
ORDER BY total_kwh DESC;

-- After-hours consumption (fast!)
SELECT 
  c.channel_name,
  SUM(CASE 
    WHEN CAST(strftime('%w', r.timestamp) AS INTEGER) IN (0,6) 
    THEN r.energy_kwh 
    ELSE 0 
  END) as weekend_kwh,
  SUM(r.energy_kwh) as total_kwh
FROM readings r
JOIN channels c ON r.channel_id = c.channel_id
WHERE c.organization_id = '23271'
GROUP BY c.channel_name;

-- Year-over-year comparison (impossible with API!)
SELECT 
  strftime('%Y-%m', timestamp) as month,
  SUM(energy_kwh) as monthly_kwh
FROM readings
WHERE channel_id = 162119
GROUP BY month
ORDER BY month;
```

## Using Local Data in Reports

### Update Weekly Report Script

Modify `weekly-exceptions-brief.js` to use local database:

```javascript
// Instead of:
const reportData = await dataFetcher.fetchReportData(...);

// Use:
const reportData = await db.getReportData(siteId, startDate, endDate);
```

### Benefits

**Speed comparison:**
- API approach: 2-3 minutes (rate limited)
- Database approach: 2-3 seconds ⚡

**Cost comparison:**
- API: ~30 calls per report × $0.001 = $0.03/report
- Database: ~$0.00/report (already stored)
- **Savings: $1.50/customer/year at weekly reports**

## Advanced Analytics with Cursor

### AI-Powered Queries

With local database, you can ask Cursor:

```
"Show me all channels at Wilson Center where 
consumption increased >20% month-over-month"

"Find correlations between outdoor temperature 
and HVAC energy use"

"Identify equipment that shows unusual patterns 
on weekends vs weekdays"
```

Cursor can:
1. Write complex SQL queries
2. Analyze results
3. Generate visualizations
4. Suggest optimizations

### Statistical Analysis

Local data enables:
- **Regression analysis** (usage vs temperature, occupancy)
- **Anomaly detection** (ML models)
- **Forecasting** (predict future consumption)
- **Clustering** (group similar usage patterns)
- **Correlation** (find relationships between meters)

**Example:** Train ML model to predict HVAC energy use based on weather

## Data Freshness Strategy

### Monitoring Data Age

Add to daily sync script:

```javascript
// Check last reading timestamp
const lastReading = await db.get(`
  SELECT MAX(timestamp) as last_ts
  FROM readings
  WHERE channel_id = ?
`);

const hoursSinceUpdate = (Date.now() - new Date(lastReading.last_ts)) / 3600000;

if (hoursSinceUpdate > 48) {
  console.warn(`⚠️  Channel ${channelId} is ${hoursSinceUpdate}h behind`);
  // Send alert, trigger manual sync, etc.
}
```

### Update Indicators

Show data freshness in reports:

```json
{
  "dataQuality": {
    "lastUpdated": "2026-02-01T06:00:00Z",
    "dataAge": "12 hours",
    "completeness": "99.9%"
  }
}
```

## Migration Path

### Today: Start Using What You Have

1. **Run initial ingestion:**
   ```bash
   npm run ingest:full -- --site 23271 --days 90
   ```

2. **Set up daily sync:**
   ```bash
   crontab -e
   # Add: 0 6 * * * cd /path && npm run ingest:incremental
   ```

3. **Update weekly report to use local DB** (we can do this next)

### Next Month: Optimize

1. Add data freshness monitoring
2. Create helper SQL views for common queries
3. Set up backup strategy
4. Document query patterns

### In 6-12 Months: Evaluate PostgreSQL

**Upgrade triggers:**
- More than 50 customers
- Need real-time dashboard
- Multiple team members querying
- Database > 10 GB

**Migration:** Easy (export SQLite → import PostgreSQL)

## Backup Strategy

### SQLite Backup
```bash
# Daily backup (simple file copy)
cp backend/data/eniscope.db backend/data/backups/eniscope-$(date +%Y%m%d).db

# Weekly rotation (keep 4 weeks)
find backend/data/backups/ -name "*.db" -mtime +28 -delete
```

### Cloud Backup
```bash
# Upload to S3, Dropbox, etc.
aws s3 cp backend/data/eniscope.db s3://argo-energy-backups/
```

## Cost Analysis

### API-Only Approach (Current)
- Wilson Center weekly report: ~40 API calls
- 52 weeks/year = 2,080 API calls
- At typical API pricing: ~$2-5/year per customer
- **50 customers = $100-250/year**
- **Plus**: Slow performance, rate limits

### Local Database Approach (Recommended)
- Initial sync: 40 API calls (one-time)
- Daily sync: 1 API call/day = 365/year
- **50 customers = $25-50/year**
- **Plus**: Fast queries, no limits, advanced analytics

**Savings: $75-200/year + much better performance**

## Best Practices

### 1. Don't Store API Credentials in Database
✅ Use environment variables
❌ Never commit `.env` with credentials

### 2. Index Time-Range Queries
```sql
-- Already done in your schema!
CREATE INDEX idx_readings_timestamp ON readings(timestamp);
```

### 3. Partition by Time (PostgreSQL only)
When you migrate:
```sql
-- Partition by month for faster queries
CREATE TABLE readings_2026_01 PARTITION OF readings
FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');
```

### 4. Regular Maintenance
```sql
-- SQLite: Optimize (monthly)
VACUUM;
ANALYZE;
```

### 5. Query Optimization
- Always filter by `timestamp` first
- Use `channel_id` index
- Limit results when exploring

## Example Use Cases

### 1. Trend Analysis
```sql
-- 12-month trend for customer
SELECT 
  strftime('%Y-%m', timestamp) as month,
  channel_name,
  SUM(energy_kwh) as monthly_kwh
FROM readings r
JOIN channels c ON r.channel_id = c.channel_id
WHERE c.organization_id = '23271'
  AND timestamp >= date('now', '-12 months')
GROUP BY month, channel_name
ORDER BY month;
```

### 2. Peak Demand Analysis
```sql
-- Find daily peak demand
SELECT 
  date(timestamp) as day,
  MAX(power_kw) as peak_kw,
  time(timestamp) as peak_time
FROM readings
WHERE channel_id = 162119
  AND timestamp >= date('now', '-30 days')
GROUP BY day
ORDER BY peak_kw DESC
LIMIT 10;
```

### 3. Efficiency Benchmarking
```sql
-- Compare customers
SELECT 
  o.organization_name,
  SUM(r.energy_kwh) / COUNT(DISTINCT date(r.timestamp)) as avg_kwh_per_day
FROM readings r
JOIN channels c ON r.channel_id = c.channel_id
JOIN organizations o ON c.organization_id = o.organization_id
WHERE r.timestamp >= date('now', '-30 days')
GROUP BY o.organization_name
ORDER BY avg_kwh_per_day DESC;
```

## Next Steps

1. **This week:**
   - Run full ingestion for Wilson Center
   - Test queries in SQLite
   - Set up daily sync cron job

2. **Next week:**
   - Update weekly report to use local DB
   - Document common queries
   - Set up backup automation

3. **This month:**
   - Add data freshness monitoring
   - Create SQL views for common patterns
   - Expand to 2-3 more customers

4. **Ongoing:**
   - Monitor database size
   - Optimize slow queries
   - Plan PostgreSQL migration (when needed)

## Summary

✅ **Use SQLite now** - Perfect for your current scale  
✅ **Sync daily** - Pull new data automatically  
✅ **Query locally** - 100× faster than API  
✅ **Save money** - Fewer API calls  
✅ **Enable advanced analytics** - Complex queries, ML, trends  
✅ **Plan to scale** - Migrate to PostgreSQL when needed  

**The database is already set up - you just need to use it more systematically!**
