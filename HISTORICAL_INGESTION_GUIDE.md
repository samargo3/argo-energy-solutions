# 🔄 Historical Data Ingestion Guide

**Robust Python script for fetching complete historical energy data from Eniscope API**

---

## 🎯 What This Script Does

The **Historical Ingestion Script** (`historical_ingestion.py`) is a production-grade tool that:

✅ Fetches **complete historical data** from Eniscope installation date (2025-05-01) to present  
✅ Enforces **strict data integrity rules** to prevent bad data  
✅ Uses **composite primary key** (meter_id, timestamp) to prevent duplicates  
✅ Logs **every API pull** for gap detection and audit trails  
✅ Implements **safe upsert logic** - can be re-run without creating duplicates  
✅ Includes **1-second rate limiting** to respect API limits  
✅ Validates **all data** before insertion (negative kW rejected, future timestamps rejected)  

---

## 🔐 Data Integrity Rules

### 1. Composite Primary Key
```sql
PRIMARY KEY (channel_id, timestamp)
```
**Benefit:** Physically impossible to have duplicate readings for same meter at same time

### 2. Data Validation
Before any insertion, the script validates:
- ✅ **Power (kW) must not be negative**
- ✅ **Timestamp must be in the past** (no future dates)
- ✅ **All required fields present**

**Rejected readings are logged** but don't stop the ingestion process.

### 3. Ingestion Logs Table
```sql
CREATE TABLE ingestion_logs (
    id SERIAL PRIMARY KEY,
    organization_id TEXT NOT NULL,
    channel_id INTEGER NOT NULL,
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ NOT NULL,
    readings_fetched INTEGER NOT NULL,
    readings_inserted INTEGER NOT NULL,
    readings_rejected INTEGER NOT NULL,
    status TEXT NOT NULL,  -- 'success' or 'failure'
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
)
```

**Purpose:** Track every API pull to detect gaps in your historical data

### 4. Upsert Logic
```sql
INSERT INTO readings (...)
VALUES (...)
ON CONFLICT (channel_id, timestamp) DO NOTHING
```

**Benefit:** Safe to re-run script multiple times without creating duplicates

---

## 🚀 How to Use

### Quick Start (Wilson Center, from installation date)
```bash
npm run py:ingest:historical
```

This fetches data from **2025-05-01** (installation date) to **today**.

### Custom Date Range
```bash
source venv/bin/activate

# From specific start date to today
python backend/python_scripts/historical_ingestion.py \
  --site 23271 \
  --start-date 2025-06-01

# Specific date range
python backend/python_scripts/historical_ingestion.py \
  --site 23271 \
  --start-date 2025-05-01 \
  --end-date 2025-12-31
```

### Custom Site
```bash
npm run py:ingest:historical:custom -- --site YOUR_SITE_ID
```

### Disable Validation (Not Recommended)
```bash
python backend/python_scripts/historical_ingestion.py \
  --site 23271 \
  --no-validate
```

---

## 📊 How It Works

### The Historical Loop

```python
# Start from installation date (2025-05-01)
current_date = start_date

# Loop until today
while current_date < today:
    # Fetch 24 hours of data
    readings = fetch_readings(current_date, current_date + 24h)
    
    # Validate each reading
    for reading in readings:
        if validate(reading):
            insert_reading(reading)  # ON CONFLICT DO NOTHING
        else:
            reject_reading(reading)
    
    # Log this ingestion run
    log_ingestion(start, end, fetched, inserted, rejected)
    
    # Rate limit: wait 1 second
    sleep(1)
    
    # Move to next day
    current_date += 24h
```

### Key Features

1. **24-Hour Increments**
   - Fetches data in manageable chunks
   - Prevents timeout on large requests
   - Makes progress trackable

2. **Rate Limiting**
   - 1 second delay between API calls
   - Respects Eniscope API limits
   - Prevents rate limit errors

3. **Automatic Retry**
   - Errors logged but don't stop process
   - Can re-run to fill gaps
   - Upsert logic prevents duplicates

4. **Progress Tracking**
   - Real-time console output
   - Shows date being processed
   - Displays fetched/inserted/rejected counts

---

## 📋 Sample Output

```
======================================================================
🔄 HISTORICAL ENERGY DATA INGESTION
======================================================================

🎯 Site ID: 23271
📅 Start Date: 2025-05-01
🏁 End Date: 2026-02-03
🔐 Data Validation: ✅ Enabled

✅ Database schema verified

🔑 Authenticating with Eniscope API...
✅ Authenticated as: Wilson Center

📡 Fetching channels...
✅ Found 17 channels

📊 Processing: RTU-1 Main Panel (ID: 67890)
----------------------------------------------------------------------
   📅 2025-05-01 ✅ Fetched: 1440, Inserted: 1440, Rejected: 0
   📅 2025-05-02 ✅ Fetched: 1440, Inserted: 1440, Rejected: 0
   📅 2025-05-03 ✅ Fetched: 1440, Inserted: 1440, Rejected: 0
   ...

📊 Processing: AHU-1A_WCDS (ID: 67891)
----------------------------------------------------------------------
   📅 2025-05-01 ✅ Fetched: 1440, Inserted: 1440, Rejected: 0
   📅 2025-05-02 ✅ Fetched: 1440, Inserted: 1438, Rejected: 2
   ⚠️  Rejected reading: Negative power: -0.5 kW
   ⚠️  Rejected reading: Future timestamp: 2026-02-05 10:30:00
   ...

======================================================================
✅ INGESTION COMPLETE
======================================================================

📊 Summary:
   Channels processed: 17
   API calls made: 4,590
   Readings fetched: 6,609,600
   Readings inserted: 6,609,450
   Readings rejected: 150
   Success rate: 99.998%

🔍 Checking for ingestion gaps...
   ✅ RTU-1 Main Panel: No gaps
   ✅ AHU-1A_WCDS: No gaps
   ✅ A/C Unit 0: No gaps
   ✅ A/C Unit 3: No gaps
   ✅ A/C Unit 6: No gaps

🎉 Historical ingestion complete!
```

---

## ⏱️ Performance Estimates

### Time Calculation
```
Days of data: 270 (May 1, 2025 - Feb 3, 2026)
Channels: 17
API calls: 270 days × 17 channels = 4,590 calls
Rate limit: 1 second per call
Total time: 4,590 seconds = ~76 minutes
```

### Data Volume
```
Readings per day per channel: 1,440 (1-minute resolution)
Total readings: 270 days × 17 channels × 1,440 = 6,609,600 readings
Database size: ~660 MB (estimated)
```

---

## 🔍 Gap Detection

### Check for Gaps
The script automatically checks for gaps after ingestion. You can also query manually:

```sql
-- Find gaps in ingestion history
WITH ingestion_ranges AS (
    SELECT
        channel_id,
        start_time,
        end_time,
        LAG(end_time) OVER (
            PARTITION BY channel_id 
            ORDER BY start_time
        ) as prev_end_time
    FROM ingestion_logs
    WHERE organization_id = '23271'
      AND status = 'success'
)
SELECT
    channel_id,
    prev_end_time as gap_start,
    start_time as gap_end,
    EXTRACT(EPOCH FROM (start_time - prev_end_time))/3600 as gap_hours
FROM ingestion_ranges
WHERE prev_end_time IS NOT NULL
  AND start_time > prev_end_time + INTERVAL '5 minutes'
ORDER BY gap_hours DESC;
```

### Fill Gaps
If gaps are found, re-run with specific date range:

```bash
python backend/python_scripts/historical_ingestion.py \
  --site 23271 \
  --start-date 2025-07-15 \
  --end-date 2025-07-20
```

The upsert logic ensures no duplicates are created.

---

## 🛡️ Error Handling

### Validation Errors
```python
# Example rejected readings:
⚠️  Rejected reading: Negative power: -0.5 kW
⚠️  Rejected reading: Future timestamp: 2026-02-05 10:30:00
⚠️  Rejected reading: Missing timestamp
```

**Action:** Logged but don't stop ingestion. Check logs for patterns.

### API Errors
```python
# Example API error:
❌ 2025-05-15 Error: API rate limit exceeded
```

**Action:** Logged as 'failure' in ingestion_logs. Re-run to retry.

### Database Errors
```python
# Example database error:
❌ Fatal error: Connection to database failed
```

**Action:** Script stops. Fix database connection and re-run.

---

## 📊 Monitoring Ingestion

### View Ingestion Logs
```sql
-- Recent ingestion runs
SELECT
    channel_id,
    start_time,
    end_time,
    readings_fetched,
    readings_inserted,
    readings_rejected,
    status,
    created_at
FROM ingestion_logs
ORDER BY created_at DESC
LIMIT 100;
```

### Success Rate by Channel
```sql
SELECT
    channel_id,
    COUNT(*) as total_runs,
    SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as successful_runs,
    SUM(readings_fetched) as total_fetched,
    SUM(readings_inserted) as total_inserted,
    SUM(readings_rejected) as total_rejected,
    ROUND(100.0 * SUM(readings_inserted) / NULLIF(SUM(readings_fetched), 0), 2) as success_rate
FROM ingestion_logs
WHERE organization_id = '23271'
GROUP BY channel_id
ORDER BY success_rate DESC;
```

### Failed Ingestion Runs
```sql
SELECT
    channel_id,
    start_time,
    end_time,
    error_message,
    created_at
FROM ingestion_logs
WHERE status = 'failure'
  AND organization_id = '23271'
ORDER BY created_at DESC;
```

---

## 🔧 Troubleshooting

### Issue: "Missing required environment variables"

**Solution:** Check your `.env` file has:
```bash
VITE_ENISCOPE_API_KEY=b8006d2d1d257a41ee63ea300fc6b7af
VITE_ENISCOPE_EMAIL=your-email@example.com
VITE_ENISCOPE_PASSWORD=your-password
DATABASE_URL=postgresql://...
```

### Issue: "API rate limit exceeded"

**Solution:** The script already includes 1-second delays. If still hitting limits:
1. Check for other processes calling the API
2. Increase delay in script (change `self.rate_limit_delay = 1.0` to `2.0`)

### Issue: "Many readings rejected"

**Solution:** Check validation errors:
```bash
# Run with verbose output
python backend/python_scripts/historical_ingestion.py \
  --site 23271 \
  --start-date 2025-05-01 2>&1 | tee ingestion.log

# Search for rejection patterns
grep "Rejected" ingestion.log
```

### Issue: "Script is too slow"

**Current:** ~76 minutes for 270 days × 17 channels

**Options to speed up:**
1. **Parallel processing** (not recommended - may hit rate limits)
2. **Larger time windows** (change from 24h to 7 days)
3. **Reduce rate limit delay** (risky - may get blocked)

### Issue: "Gaps in data"

**Solution:** Re-run for specific date ranges:
```bash
# Check gaps first
npm run py:query "SELECT * FROM ingestion_logs WHERE status='failure'"

# Fill gaps
python backend/python_scripts/historical_ingestion.py \
  --site 23271 \
  --start-date YYYY-MM-DD \
  --end-date YYYY-MM-DD
```

---

## 🎯 Best Practices

### 1. Run During Off-Hours
Historical ingestion can take 1-2 hours. Run overnight or during low-usage periods.

### 2. Monitor Progress
```bash
# Run with output to file
npm run py:ingest:historical 2>&1 | tee historical-ingestion.log

# In another terminal, monitor progress
tail -f historical-ingestion.log
```

### 3. Verify After Completion
```bash
# Check total readings
npm run py:query "show me total energy"

# Check for gaps
npm run py:query "SELECT COUNT(*) FROM ingestion_logs WHERE status='failure'"
```

### 4. Keep Logs
```bash
# Save logs with timestamp
npm run py:ingest:historical 2>&1 | tee "logs/historical-$(date +%Y%m%d-%H%M%S).log"
```

### 5. Test First
```bash
# Test with small date range first
python backend/python_scripts/historical_ingestion.py \
  --site 23271 \
  --start-date 2025-05-01 \
  --end-date 2025-05-03
```

---

## 📚 Database Schema

### Readings Table (Existing)
```sql
CREATE TABLE readings (
    id BIGSERIAL PRIMARY KEY,
    channel_id INTEGER NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    energy_kwh REAL,
    power_kw REAL,
    voltage_v REAL,
    current_a REAL,
    power_factor REAL,
    reactive_power_kvar REAL,
    temperature_c REAL,
    relative_humidity REAL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    -- Composite unique constraint (prevents duplicates)
    CONSTRAINT readings_unique UNIQUE (channel_id, timestamp)
);

-- Indexes for performance
CREATE INDEX idx_readings_channel_timestamp 
ON readings(channel_id, timestamp DESC);

CREATE INDEX idx_readings_timestamp 
ON readings(timestamp DESC);
```

### Ingestion Logs Table (New)
```sql
CREATE TABLE ingestion_logs (
    id SERIAL PRIMARY KEY,
    organization_id TEXT NOT NULL,
    channel_id INTEGER NOT NULL,
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ NOT NULL,
    readings_fetched INTEGER NOT NULL DEFAULT 0,
    readings_inserted INTEGER NOT NULL DEFAULT 0,
    readings_rejected INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'success',
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Index for gap analysis
CREATE INDEX idx_ingestion_logs_time
ON ingestion_logs(organization_id, channel_id, start_time, end_time);
```

---

## 🎉 Summary

### What You Get

✅ **Robust historical data ingestion** from installation date to present  
✅ **Data integrity guarantees** (no duplicates, no bad data)  
✅ **Complete audit trail** (every API call logged)  
✅ **Gap detection** (find missing data automatically)  
✅ **Safe re-runs** (upsert logic prevents duplicates)  
✅ **Validation** (negative kW rejected, future timestamps rejected)  
✅ **Rate limiting** (1 second between calls)  
✅ **Progress tracking** (real-time console output)  

### Quick Commands

```bash
# Run historical ingestion (from 2025-05-01 to today)
npm run py:ingest:historical

# Custom date range
python backend/python_scripts/historical_ingestion.py \
  --site 23271 \
  --start-date 2025-06-01 \
  --end-date 2025-12-31

# Check for gaps
npm run py:query "SELECT * FROM ingestion_logs WHERE status='failure'"
```

---

## 📖 Related Documentation

- **historical_ingestion.py** - Source code
- **PYTHON_MIGRATION_COMPLETE.md** - Complete platform overview
- **NEON_SETUP_GUIDE.md** - Database setup
- **DAILY_SYNC_READY.md** - Ongoing sync automation

---

## 🎯 Next Steps

1. **Run historical ingestion:**
   ```bash
   npm run py:ingest:historical
   ```

2. **Monitor progress** (will take ~76 minutes for full history)

3. **Verify completion:**
   ```bash
   npm run py:query "show me total energy"
   ```

4. **Check for gaps:**
   ```sql
   SELECT COUNT(*) FROM ingestion_logs WHERE status='failure';
   ```

5. **Set up daily sync** (if not already done):
   ```bash
   npm run py:setup-cron
   ```

---

**🎉 You now have a production-grade historical data ingestion system with complete data integrity guarantees!**
