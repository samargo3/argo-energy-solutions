# 🏗️ Data Foundation Plan
## Building Trustworthy, Consistent Energy Data

**Date**: February 8, 2026
**Status**: Foundation Assessment Complete
**Goal**: Establish reliable data pipeline from Eniscope API → Neon Database

---

## 📊 Current State Assessment

### ✅ What You Have (Strong Foundation)

| Component | Status | Details |
|-----------|--------|---------|
| **Database Schema** | ✅ Excellent | 19 tables (7 core + 12 views) |
| **Data Volume** | ✅ Good | 303,484 readings |
| **Date Coverage** | ✅ Good | 96 days (Nov 5 - Feb 9) |
| **Active Channels** | ✅ Active | 17/20 channels reporting |
| **Organizations** | ✅ Setup | 1 org (23271) |
| **Devices** | ✅ Mapped | 17 devices |
| **API Authentication** | ✅ FIXED | Working as of today |

### ⚠️ What Needs Attention

| Issue | Priority | Impact |
|-------|----------|--------|
| **3 inactive channels** | Medium | Missing data streams |
| **Optional fields not captured** | Low | Temperature, humidity missing |
| **No data validation layer** | HIGH | Can't detect bad data |
| **Missing API endpoint discovery** | Medium | May not be using all available data |
| **No alerting on failures** | HIGH | Silent failures possible |

---

## 🎯 Foundation Building Roadmap

### Phase 1: Discover & Document (Today - Day 1)

#### 1.1 API Endpoint Discovery
**Goal**: Know what data is available from Eniscope API

**Actions**:
- [ ] Test all known API endpoints
- [ ] Document response structures
- [ ] Identify unused endpoints
- [ ] Map endpoint → database table relationships

**Script to Create**:
```bash
# Create: backend/python_scripts/ingest/discover_api_endpoints.py
npm run py:ingest:discover
```

**Expected Output**:
- `/organizations` ✅ → organizations table
- `/devices` ✅ → devices table
- `/channels` ✅ → channels table
- `/readings/{id}` ✅ → readings table
- `/sites` ? → Unknown
- `/meters` ? → Unknown
- Other endpoints ? → To discover

---

#### 1.2 Data Field Inventory
**Goal**: Know what fields you're capturing vs what's available

**Current Capture** (readings table):
```sql
✅ channel_id          -- Which sensor
✅ timestamp           -- When
✅ energy_kwh          -- Energy consumption
✅ power_kw            -- Power demand
✅ voltage_v           -- Voltage
✅ current_a           -- Current
✅ power_factor        -- Power factor
⚠️ reactive_power_kvar -- (nullable, rarely populated)
⚠️ temperature_c       -- (nullable, rarely populated)
⚠️ relative_humidity   -- (nullable, rarely populated)
```

**Questions to Answer**:
1. What fields does the API return that you're not storing?
2. Are there additional endpoints for environmental data?
3. Do different device types return different fields?

---

### Phase 2: Validation & Quality Gates (Days 2-3)

#### 2.1 Implement Data Validation Circuit Breakers
**Goal**: Catch bad data before it reaches analytics

**Validation Checks to Implement**:

```python
# backend/python_scripts/govern/validate_ingestion.py

class DataValidator:
    """Circuit breaker for data quality"""

    def validate_reading(self, reading):
        """Validate a single reading"""
        checks = [
            self.check_timestamp_valid(reading),
            self.check_values_in_range(reading),
            self.check_no_impossible_values(reading),
            self.check_channel_exists(reading),
        ]
        return all(checks)

    def check_values_in_range(self, reading):
        """Electrical values should be in realistic ranges"""
        rules = {
            'power_kw': (0, 1000),        # 0-1MW
            'voltage_v': (100, 500),      # Typical ranges
            'current_a': (0, 5000),       # Max current
            'power_factor': (-1, 1),      # Valid range
            'energy_kwh': (0, 10000)      # Reasonable daily max
        }

        for field, (min_val, max_val) in rules.items():
            value = reading.get(field)
            if value is not None:
                if not (min_val <= value <= max_val):
                    return False
        return True

    def check_no_impossible_values(self, reading):
        """Check for impossible combinations"""
        # Power factor should exist if power and voltage exist
        if reading.get('power_kw') and reading.get('voltage_v'):
            if reading.get('power_factor') is None:
                return False
        return True
```

**npm Command**:
```bash
npm run py:govern:validate-ingestion
```

---

#### 2.2 Real-Time Quality Monitoring
**Goal**: Alert on quality issues immediately

**Metrics to Track**:
```sql
-- Create: v_ingestion_quality (materialized view)
CREATE MATERIALIZED VIEW v_ingestion_quality AS
SELECT
    channel_id,
    DATE(timestamp) as date,
    COUNT(*) as readings_count,
    COUNT(*) FILTER (WHERE energy_kwh IS NULL) as null_energy_count,
    COUNT(*) FILTER (WHERE power_kw IS NULL) as null_power_count,
    COUNT(*) FILTER (WHERE power_kw < 0) as negative_power_count,
    COUNT(*) FILTER (WHERE power_kw > 1000) as extreme_power_count,
    MIN(timestamp) as first_reading,
    MAX(timestamp) as last_reading,
    EXTRACT(EPOCH FROM (MAX(timestamp) - MIN(timestamp))) / 3600 as hours_covered
FROM readings
WHERE timestamp >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY channel_id, DATE(timestamp);
```

**Quality Thresholds**:
- Expected readings/day: 96 (15-min intervals)
- Null values: <5%
- Out-of-range values: <1%
- Data gaps: <1 hour

---

### Phase 3: Complete the Pipeline (Days 4-7)

#### 3.1 Handle Missing Data
**Goal**: No silent failures

**Missing Data Strategy**:

1. **Backfill Historical Gaps**
```bash
# Identify gaps
npm run py:govern:find-gaps

# Backfill specific date range
npm run py:ingest -- --start-date 2025-11-01 --end-date 2025-11-04
```

2. **Forward-Fill for Short Gaps**
```sql
-- Option: Fill short gaps with last known value
CREATE OR REPLACE FUNCTION fill_short_gaps()
RETURNS void AS $$
BEGIN
    -- Fill gaps <1 hour with interpolation
    -- Implementation here
END;
$$ LANGUAGE plpgsql;
```

3. **Mark Unfillable Gaps**
```sql
-- Track known gaps
CREATE TABLE data_gaps (
    gap_id serial PRIMARY KEY,
    channel_id integer,
    gap_start timestamptz,
    gap_end timestamptz,
    reason text,
    fillable boolean,
    filled_at timestamptz
);
```

---

#### 3.2 Capture All Available Fields
**Goal**: Don't leave data on the table

**Enhanced Reading Capture**:
```python
# Update ingest_to_postgres.py to capture ALL fields from API response

def normalize_reading(api_reading):
    """Capture all available fields"""
    return {
        # Core energy metrics
        'timestamp': api_reading.get('ts') or api_reading.get('t'),
        'energy_kwh': safe_convert(api_reading.get('E'), 1000),
        'power_kw': safe_convert(api_reading.get('P'), 1000),

        # Electrical metrics
        'voltage_v': api_reading.get('V'),
        'current_a': api_reading.get('I'),
        'power_factor': api_reading.get('PF'),
        'reactive_power_kvar': safe_convert(api_reading.get('Q'), 1000),

        # Environmental (if available)
        'temperature_c': api_reading.get('T'),
        'relative_humidity': api_reading.get('RH'),

        # NEW: Capture metadata
        'frequency_hz': api_reading.get('F'),
        'thd_voltage': api_reading.get('THDV'),
        'thd_current': api_reading.get('THDI'),

        # Quality indicators
        'data_quality': api_reading.get('Q'),
        'signal_strength': api_reading.get('RSSI'),
    }
```

**Database Migration**:
```sql
-- Add new columns if API provides them
ALTER TABLE readings ADD COLUMN IF NOT EXISTS frequency_hz real;
ALTER TABLE readings ADD COLUMN IF NOT EXISTS thd_voltage real;
ALTER TABLE readings ADD COLUMN IF NOT EXISTS thd_current real;
ALTER TABLE readings ADD COLUMN IF NOT EXISTS data_quality text;
ALTER TABLE readings ADD COLUMN IF NOT EXISTS signal_strength integer;
```

---

### Phase 4: Automation & Monitoring (Week 2)

#### 4.1 Continuous Data Quality Monitoring

**Quality Dashboard Views**:
```sql
-- 1. Channel Health Score
CREATE OR REPLACE VIEW v_channel_health AS
SELECT
    c.channel_id,
    c.channel_name,
    COUNT(r.id) as readings_last_7d,
    ROUND(100.0 * COUNT(r.id) / (7 * 96), 1) as completeness_pct,
    MAX(r.timestamp) as last_reading,
    EXTRACT(HOUR FROM NOW() - MAX(r.timestamp)) as hours_since_last,
    CASE
        WHEN MAX(r.timestamp) > NOW() - INTERVAL '1 hour' THEN 'healthy'
        WHEN MAX(r.timestamp) > NOW() - INTERVAL '6 hours' THEN 'warning'
        ELSE 'critical'
    END as health_status
FROM channels c
LEFT JOIN readings r ON c.channel_id = r.channel_id
    AND r.timestamp >= NOW() - INTERVAL '7 days'
GROUP BY c.channel_id, c.channel_name;

-- 2. Data Quality Scorecard
CREATE OR REPLACE VIEW v_data_quality_scorecard AS
SELECT
    DATE(timestamp) as date,
    COUNT(*) as total_readings,
    COUNT(*) FILTER (WHERE energy_kwh IS NOT NULL) as valid_energy,
    COUNT(*) FILTER (WHERE power_kw IS NOT NULL) as valid_power,
    COUNT(DISTINCT channel_id) as active_channels,
    ROUND(AVG(energy_kwh), 2) as avg_energy_kwh,
    ROUND(AVG(power_kw), 2) as avg_power_kw
FROM readings
WHERE timestamp >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY DATE(timestamp)
ORDER BY date DESC;
```

---

#### 4.2 Automated Alerting

**Alert Rules**:
```yaml
# alerts_config.yaml
alerts:
  - name: stale_data
    condition: last_reading > 1 hour old
    severity: critical
    action: email + slack

  - name: missing_channels
    condition: active_channels < 15
    severity: warning
    action: email

  - name: data_quality_drop
    condition: null_rate > 10%
    severity: warning
    action: email

  - name: ingestion_failure
    condition: no readings in last 30 min
    severity: critical
    action: email + slack + page
```

**Implementation**:
```bash
# Run every 15 minutes
npm run py:operations:check-alerts
```

---

## 🎯 Quick Start: Build Foundation Today

### Step 1: Discover API Capabilities (30 min)

```bash
# Create API discovery script
cat > backend/python_scripts/ingest/discover_api_endpoints.py << 'EOF'
[Script content from earlier]
EOF

# Run discovery
npm run py:ingest:discover

# Review results
cat docs/api_discovery_results.json
```

---

### Step 2: Implement Validation (1 hour)

```bash
# Create validation script
npm run py:govern:validate-ingestion

# Add to ingestion flow
# Edit: backend/python_scripts/ingest/ingest_to_postgres.py
# Add validation before insert
```

---

### Step 3: Create Quality Views (30 min)

```bash
# Add views to govern/run_create_views.py
npm run db:views

# Verify views
npm run db:check-schema
```

---

### Step 4: Set Up Monitoring (30 min)

```bash
# Add quality checks to daily sync
# Edit: backend/python_scripts/operations/daily_sync.sh
# Add: npm run py:govern:quality after ingestion

# Test full flow
npm run py:sync
```

---

## 📋 Foundation Checklist

### Data Capture ✅
- [x] Organizations captured
- [x] Devices captured
- [x] Channels captured
- [x] Core readings captured (energy, power)
- [ ] All available fields captured
- [ ] Environmental data captured (temp, humidity)
- [ ] Metadata captured (data quality, signal strength)

### Data Quality 🔄
- [ ] Validation rules implemented
- [ ] Circuit breakers active
- [ ] Quality views created
- [ ] Alerts configured
- [ ] Gap detection automated

### Monitoring ✅ (Partially Done)
- [x] Health checks running
- [x] Quality reports generated
- [ ] Real-time alerts active
- [ ] Dashboard views created
- [ ] Anomaly detection active

### Documentation 📝
- [x] API authentication documented
- [ ] API endpoints documented
- [ ] Data dictionary created
- [ ] Quality standards defined
- [ ] Runbooks created

---

## 🚀 Priority Actions (Start Here)

### Today (High Priority)
1. **Run API Discovery** - Know what you're missing
2. **Implement Basic Validation** - Catch bad data
3. **Create Quality Views** - See data health

### This Week (Medium Priority)
4. **Backfill Historical Gaps** - Complete data coverage
5. **Add Missing Fields** - Capture all available data
6. **Set Up Automated Alerts** - No silent failures

### Next Week (Low Priority)
7. **Create Data Dictionary** - Document everything
8. **Build Quality Dashboard** - Visualize health
9. **Implement Advanced Validation** - Catch subtle issues

---

## 📚 Scripts to Create

Following your governance rules (stage-based organization):

### Ingest Layer
```bash
# API discovery
backend/python_scripts/ingest/discover_api_endpoints.py
→ npm run py:ingest:discover

# Field mapping
backend/python_scripts/ingest/map_api_fields.py
→ npm run py:ingest:map-fields
```

### Govern Layer
```bash
# Validation
backend/python_scripts/govern/validate_ingestion.py
→ npm run py:govern:validate-ingestion

# Gap detection
backend/python_scripts/govern/detect_data_gaps.py
→ npm run py:govern:find-gaps

# Quality views (enhance existing)
backend/python_scripts/govern/run_create_views.py
→ npm run db:views
```

### Operations Layer
```bash
# Alert checking
backend/python_scripts/operations/check_alerts.py
→ npm run py:operations:check-alerts

# Gap backfill (enhance existing)
backend/python_scripts/operations/backfill_gaps.py
→ npm run py:operations:backfill
```

---

## 💡 Key Principles for Trustworthy Data

1. **Validate Early** - Catch bad data at ingestion, not analysis
2. **Monitor Continuously** - Don't wait for users to report issues
3. **Document Everything** - Future you will thank present you
4. **Fail Loudly** - Alerts are better than silent failures
5. **Version Your Data** - Track schema changes and migrations

---

## 🎯 Success Metrics

### Week 1 Goals
- ✅ 100% API endpoint discovery complete
- ✅ Basic validation rules implemented
- ✅ Quality monitoring views created
- ✅ Automated alerts configured

### Month 1 Goals
- ✅ 99%+ data completeness (no gaps)
- ✅ <1% null rate in core fields
- ✅ <5 min detection time for issues
- ✅ Zero silent failures

### Quarter 1 Goals
- ✅ Advanced anomaly detection active
- ✅ Predictive quality monitoring
- ✅ Automated quality reports to stakeholders
- ✅ Data lineage fully documented

---

**Next Step**: Run API discovery to see what data you're missing!

```bash
# Create and run discovery script
# Results will tell you exactly what to capture next
```
