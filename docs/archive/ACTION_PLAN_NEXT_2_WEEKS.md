# Action Plan: Next 2 Weeks
## Argo Energy Solutions - Critical Path

**Status**: 🚨 Data ingestion stopped Feb 5 (3 days of missing data)
**Priority**: Restore data pipeline and implement monitoring

---

## Week 1: Stabilize & Monitor

### Day 1-2: Fix API Authentication 🚨 CRITICAL

**1. Send Diagnostic Report to Best.Energy Support**
```bash
# Run comprehensive diagnostic
npm run debug:diagnostic

# Copy output and send to support ticket
# Include: SUPPORT_TICKET_RESPONSE.md
```

**Key Questions for Support**:
- Is "API Access" enabled for key `b8006d2d1d257a41ee63ea300fc6b7af`?
- Does user `craig@argoenergysolutions.com` have correct permissions?
- Should we regenerate the API key?

**2. Check Current Data Status**
```bash
# Check ingestion health
npm run monitor:health

# Run quality report
npm run monitor:quality
```

---

### Day 3-4: Implement Monitoring

**1. Set Up Automated Monitoring**
```bash
# Add to crontab (run every hour)
crontab -e

# Add this line:
0 * * * * cd /Users/sargo/argo-energy-solutions && npm run py:operations:health || echo "⚠️ Ingestion health check failed" | mail -s "Argo Energy Alert" craig@argoenergysolutions.com
```

**2. Create Daily Quality Report**
```bash
# Add to crontab (run daily at 8am)
0 8 * * * cd /Users/sargo/argo-energy-solutions && npm run py:govern:quality > /tmp/quality_report.txt && mail -s "Daily Quality Report" craig@argoenergysolutions.com < /tmp/quality_report.txt
```

**3. Document Current State**
```bash
# Generate full report
npm run monitor:quality:30d > docs/baseline_quality_report.txt
```

---

### Day 5: Plan Data Backfill

**1. Identify Missing Data**
- Feb 5 08:56:20 → Feb 8 (current)
- ~3 days × 17 channels × 96 readings = ~4,896 readings missing

**2. Backfill Strategy (Choose One)**

**Option A: If API Fixed**
```bash
# Backfill missing days
npm run py:ingest -- --start-date 2026-02-05 --end-date 2026-02-08
```

**Option B: If API Still Blocked**
```bash
# Export from web portal
# 1. Log into core.eniscope.com
# 2. Navigate to Data Export
# 3. Export Feb 5-8 as CSV
# 4. Manual import (we can create a script)
```

**Option C: Wait for Support**
- Continue using existing data (through Feb 5)
- Resume when API access restored

---

## Week 2: Optimize & Enhance

### Day 6-7: Enable Database Optimization

**1. Enable TimescaleDB Compression**
```sql
-- Connect to Neon database
-- Enable TimescaleDB extension (if not already)
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Convert readings table to hypertable
SELECT create_hypertable('readings', 'timestamp',
    chunk_time_interval => INTERVAL '7 days',
    if_not_exists => TRUE
);

-- Enable compression (10x space savings)
ALTER TABLE readings SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'channel_id'
);

-- Add compression policy (compress data >14 days old)
SELECT add_compression_policy('readings', INTERVAL '14 days');
```

**2. Add Useful Indexes**
```sql
-- Speed up channel queries
CREATE INDEX IF NOT EXISTS idx_readings_channel_time
    ON readings(channel_id, timestamp DESC);

-- Speed up date range queries
CREATE INDEX IF NOT EXISTS idx_readings_time_range
    ON readings(timestamp DESC)
    WHERE timestamp >= CURRENT_DATE - INTERVAL '90 days';
```

**3. Create Continuous Aggregates**
```sql
-- Hourly aggregates (for faster dashboard queries)
CREATE MATERIALIZED VIEW readings_hourly
WITH (timescaledb.continuous) AS
SELECT
    channel_id,
    time_bucket('1 hour', timestamp) AS hour,
    AVG(power_kw) as avg_power_kw,
    MAX(power_kw) as max_power_kw,
    SUM(energy_kwh) as total_energy_kwh,
    COUNT(*) as reading_count
FROM readings
GROUP BY channel_id, hour;

-- Refresh policy (every hour)
SELECT add_continuous_aggregate_policy('readings_hourly',
    start_offset => INTERVAL '3 hours',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour'
);
```

---

### Day 8-9: Audit Node.js Dependencies

**1. List All Node.js Scripts**
```bash
# Find all JS files in backend
find backend -name "*.js" -type f

# Count usage in package.json
grep "node backend" package.json | wc -l
```

**2. Identify What's Actually Used**
```bash
# Check recent usage in logs
# Review which endpoints the frontend calls
grep -r "localhost:3000" src/
grep -r "api/" src/services/
```

**3. Create Migration Plan**
- [ ] List endpoints frontend depends on
- [ ] Identify Python equivalents
- [ ] Plan FastAPI migration sequence

---

### Day 10: Cost Analysis Feature

**1. Add Utility Rate Configuration**
```python
# backend/python_scripts/analytics/cost_config.py
UTILITY_RATES = {
    '23271': {  # Org ID
        'rate_per_kwh': 0.12,  # $0.12/kWh
        'demand_charge': 15.00,  # $/kW peak demand
        'currency': 'USD'
    }
}
```

**2. Create Cost Analysis Script**
```bash
# New script: backend/python_scripts/analytics/cost_analysis.py
npm run py:cost-analysis -- --site 23271 --days 30
```

Output:
```
💰 COST ANALYSIS - Last 30 Days
================================
Total Energy:     12,450 kWh
Total Cost:       $1,494.00
Cost/Day:         $49.80
Peak Demand:      145 kW

Top Cost Centers:
  1. HVAC System: $620.00 (41%)
  2. Lighting:    $420.00 (28%)
  3. Equipment:   $454.00 (31%)

Opportunities:
  1. After-hours HVAC: $180/mo savings
  2. Lighting schedule: $85/mo savings
```

---

## Quick Wins Checklist

### This Week ✅
- [ ] Send diagnostic report to Best.Energy support
- [ ] Run health and quality monitoring
- [ ] Set up cron jobs for automated monitoring
- [ ] Document current data coverage
- [ ] Plan backfill strategy

### Next Week ✅
- [ ] Enable TimescaleDB compression
- [ ] Create hourly aggregates (faster queries)
- [ ] Audit Node.js usage
- [ ] Build cost analysis feature
- [ ] Add indexes for performance

---

## Commands Quick Reference

```bash
# Operations (Maintenance & Health)
npm run py:operations:health        # Check if data is fresh

# Govern (Data Quality & Validation)
npm run py:govern:quality           # 7-day quality report
npm run py:govern:quality:30d       # 30-day quality report

# Ingest (Debugging & Diagnostics)
npm run py:ingest:test-auth         # Test API authentication
npm run py:ingest:diagnostic        # Full diagnostic report
npm run py:ingest:test-working      # Test working auth method

# Ingestion
npm run py:ingest                   # Ingest last 1 day
npm run py:ingest:full              # Ingest last 90 days
npm run py:ingest -- --start-date YYYY-MM-DD --end-date YYYY-MM-DD

# Analytics
npm run py:report                   # Weekly report
npm run py:report:customer          # Customer report
npm run py:query                    # Interactive queries

# Database
npm run db:check                    # Database health
npm run db:refresh-views            # Refresh materialized views
```

---

## Success Metrics

Track these daily:

### Reliability
- [ ] Data latency: <1 hour
- [ ] Zero data gaps in last 7 days
- [ ] >95% completeness per channel

### Performance
- [ ] Query response time: <100ms
- [ ] Dashboard load time: <2 sec
- [ ] Report generation: <30 sec

### Business Value
- [ ] Cost analysis in every report
- [ ] ≥3 actionable recommendations per report
- [ ] Customer response: positive feedback

---

## Next Review

**Date**: February 15, 2026 (1 week from now)
**Agenda**:
- API authentication status
- Data backfill completion
- Monitoring effectiveness
- Phase 2 planning (analytics enhancements)

---

## Need Help?

**Documentation**:
- Full recommendations: `CONSULTANT_RECOMMENDATIONS.md`
- Support response draft: `SUPPORT_TICKET_RESPONSE.md`

**New Scripts Created**:
- Health monitoring: `backend/python_scripts/monitoring/check_ingestion_health.py`
- Quality reporting: `backend/python_scripts/monitoring/data_quality_report.py`
- Auth testing: `backend/python_scripts/ingest/test_auth_approaches.py`
- Diagnostics: `backend/python_scripts/ingest/diagnostic_report.py`

**Next Phase**:
See `CONSULTANT_RECOMMENDATIONS.md` for Phase 2-4 roadmap
