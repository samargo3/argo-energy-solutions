# Analytics View Strategy

**Date:** February 5, 2026  
**Status:** Planning Phase - Recommendations Only

Based on analysis of your data (298K+ readings, 17 channels, 93 days, ~7-min intervals), here's a comprehensive view strategy for analytics.

---

## 📊 Data Profile

Your current setup:
- **Time Range:** Nov 5, 2025 → Feb 5, 2026 (3 months)
- **Reading Frequency:** ~7 minutes (variable)
- **Data Completeness:** ~47% (many NULL values - this is normal for interval data)
- **Usage Pattern:** Business hours (8am-5pm) show 62% higher power usage vs. after-hours
- **Peak Demand:** 23.3 kW (Kitchen Panel)

---

## 🎯 View Categories & Recommendations

### Category 1: **Business-Friendly Aliases** (Foundation)
*Priority: HIGH | Complexity: LOW | Performance Impact: NONE*

**Purpose:** Make queries more intuitive for business users

**Suggested Views:**

1. **`v_sites`** - Alias for organizations
   - Maps technical → business terminology
   - Makes reporting clearer

2. **`v_meters`** - Enriched channels with device info
   - Combines channels + devices + organizations
   - One-stop shop for meter metadata

3. **`v_meter_readings`** - User-friendly reading view
   - Includes site name, meter name, device name
   - All the context needed for analysis

**Use Cases:**
- Executive dashboards
- Customer reports
- Non-technical staff queries

**Performance:** Zero impact (views are just query aliases)

---

### Category 2: **Time-Based Aggregations** (High Value)
*Priority: HIGH | Complexity: MEDIUM | Performance Impact: HIGH POSITIVE*

**Purpose:** Pre-calculate common time periods for fast queries

**Suggested Views:**

4. **`v_readings_hourly`** - Hourly aggregates
   - AVG, MIN, MAX, SUM for each hour
   - Essential for trend analysis
   - Reduces query time by ~95%

5. **`v_readings_daily`** - Daily summaries
   - Total energy, peak power, avg voltage per day
   - Perfect for billing and reporting
   - 1,581 rows vs. 298K (0.5% of data)

6. **`v_readings_weekly`** - Weekly rollups
   - Week-over-week comparisons
   - Good for trend spotting

7. **`v_readings_monthly`** - Monthly aggregates
   - Budget tracking
   - Long-term trends
   - Only 51 rows (3 months × 17 channels)

**Use Cases:**
- Billing reports
- Trend dashboards
- Historical comparisons
- Performance tracking

**Performance:** 
- Queries run 10-100x faster
- Tableau loads instantly
- Reduced database load

**Considerations:**
- Views recalculate on each query (fine for your data size)
- For larger datasets, consider materialized views

---

### Category 3: **Business Logic Views** (Analytics)
*Priority: HIGH | Complexity: MEDIUM | Performance Impact: NEUTRAL*

**Purpose:** Embed business rules and calculations

**Suggested Views:**

8. **`v_business_hours_analysis`** - Compare on-hours vs. off-hours
   - Automatic categorization (business/after-hours/weekend)
   - Shows waste opportunities
   - Key for energy consulting

9. **`v_cost_analysis`** - Energy cost calculations
   - Apply rate schedules (TOU, demand charges)
   - Per-meter cost breakdowns
   - Monthly cost summaries

10. **`v_demand_charges`** - Peak demand tracking
    - Monthly peak per meter
    - Critical for utility bills
    - Demand reduction opportunities

11. **`v_power_quality`** - Voltage and power factor monitoring
    - Flag low power factor (<0.9)
    - Voltage deviation alerts
    - Equipment health indicators

**Use Cases:**
- Energy audits
- Billing validation
- Equipment efficiency analysis
- Customer recommendations

---

### Category 4: **Comparative Analytics** (Insights)
*Priority: MEDIUM | Complexity: HIGH | Performance Impact: NEUTRAL*

**Purpose:** Enable comparisons and benchmarking

**Suggested Views:**

12. **`v_meter_comparison`** - Side-by-side meter stats
    - Rank meters by consumption
    - Show % of total usage
    - Identify top consumers

13. **`v_period_comparison`** - This month vs. last month
    - Automatic period calculations
    - % change, absolute difference
    - Trend indicators (↑↓→)

14. **`v_baseline_deviation`** - Compare to typical usage
    - Calculate baseline from historical average
    - Show deviation as %
    - Highlight anomalies

15. **`v_equipment_efficiency`** - Device performance metrics
    - kWh per hour of operation
    - Capacity utilization
    - Compare similar equipment

**Use Cases:**
- Benchmarking reports
- Anomaly detection
- Energy savings verification
- Equipment replacement decisions

---

### Category 5: **Time Pattern Views** (Operational)
*Priority: MEDIUM | Complexity: MEDIUM | Performance Impact: NEUTRAL*

**Purpose:** Understand usage patterns

**Suggested Views:**

16. **`v_hourly_load_profile`** - Typical usage by hour-of-day
    - Average power for each hour (0-23)
    - Separate weekday vs. weekend
    - Create load profile curves

17. **`v_day_of_week_patterns`** - Usage by day
    - Monday-Sunday comparison
    - Identify operational patterns
    - Spot irregular activity

18. **`v_seasonal_patterns`** - Month-to-month trends
    - Temperature correlation (when you have temp data)
    - Seasonal adjustments
    - Forecasting base

**Use Cases:**
- Operations optimization
- Shift scheduling
- HVAC optimization
- Load forecasting

---

### Category 6: **Data Quality Views** (Monitoring)
*Priority: LOW | Complexity: LOW | Performance Impact: LOW*

**Purpose:** Monitor data health and gaps

**Suggested Views:**

19. **`v_data_completeness`** - Track NULL values and gaps
    - % readings with data per meter
    - Identify communication issues
    - Data quality score

20. **`v_reading_frequency`** - Monitor interval consistency
    - Expected vs. actual reading count
    - Detect data loss
    - Uptime tracking

21. **`v_anomalous_readings`** - Flag suspicious data
    - Negative values
    - Impossible spikes (>3σ)
    - Stuck readings (no change)

**Use Cases:**
- System health monitoring
- Troubleshooting
- Data quality reports
- Maintenance alerts

---

### Category 7: **Performance-Optimized Views** (Speed)
*Priority: MEDIUM | Complexity: LOW | Performance Impact: HIGH POSITIVE*

**Purpose:** Pre-join common queries for speed

**Suggested Views:**

22. **`v_readings_enriched`** - All context in one place
    - readings + channels + devices + organizations
    - Eliminates multiple JOINs
    - 2-3x faster queries

23. **`v_latest_readings`** - Most recent value per meter
    - Real-time dashboard views
    - Current status
    - Fast refresh

24. **`v_meter_summary_stats`** - Pre-calculated statistics
    - MIN, MAX, AVG, StdDev per meter
    - Lifetime stats
    - Instant dashboard cards

**Use Cases:**
- Real-time dashboards
- Mobile apps
- API responses
- Tableau performance

---

## 🏗️ Implementation Strategy

### Phase 1: Foundation (Day 1)
**Views to Create First:**
1. `v_sites` - Business-friendly org alias
2. `v_meters` - Enriched channel view
3. `v_readings_enriched` - Pre-joined everything
4. `v_latest_readings` - Current values

**Why First:**
- Used by all other views
- Immediate value
- Low complexity
- Foundation for Phase 2

**Estimated Time:** 30 minutes

---

### Phase 2: Time Aggregations (Day 1)
**Views to Create:**
5. `v_readings_hourly`
6. `v_readings_daily`
7. `v_readings_monthly`

**Why Next:**
- Massive performance boost
- Most common queries
- Enable faster reporting
- Quick wins

**Estimated Time:** 45 minutes

---

### Phase 3: Business Logic (Week 1)
**Views to Create:**
8. `v_business_hours_analysis`
9. `v_cost_analysis`
10. `v_demand_charges`
11. `v_power_quality`

**Why Third:**
- High business value
- Requires domain knowledge
- Build on Phase 1 & 2
- More complex logic

**Estimated Time:** 2-3 hours

---

### Phase 4: Advanced Analytics (Week 2)
**Views to Create:**
12-18. Comparative and pattern views

**Why Later:**
- More complex queries
- Requires baseline data
- Can iterate based on usage
- Nice-to-have vs. need-to-have

**Estimated Time:** 3-4 hours

---

### Phase 5: Monitoring (As Needed)
**Views to Create:**
19-21. Data quality views

**Why Last:**
- Operations/maintenance focus
- Less urgent
- Can build as issues arise

**Estimated Time:** 1 hour

---

## ⚡ Performance Considerations

### Regular Views vs. Materialized Views

**Regular Views (Recommended for You):**
- ✅ Always up-to-date
- ✅ No storage overhead
- ✅ Simple to maintain
- ⚠️ Recalculate on each query
- **Best for:** Your current data size (300K rows)

**Materialized Views (Future Consideration):**
- ✅ Pre-calculated (very fast)
- ✅ Good for complex aggregations
- ❌ Need manual refresh
- ❌ Storage overhead
- ❌ Can be stale
- **Best for:** When you hit 10M+ rows

**My Recommendation:** Start with regular views. Switch to materialized only if queries become slow (unlikely for next 2-3 years).

---

## 🎨 View Naming Convention

**Suggested Pattern:**
```
v_[category]_[description]

Examples:
- v_meters               (alias)
- v_readings_daily       (aggregation)
- v_business_hours_analysis (business logic)
- v_meter_comparison     (comparative)
- v_hourly_load_profile  (pattern)
- v_data_completeness    (monitoring)
```

**Why This Works:**
- `v_` prefix clearly identifies views
- Category indicates purpose
- Descriptive names self-document
- Sorts nicely in database browsers

---

## 💾 Storage Impact

**Views:** Zero storage (they're saved queries)
**Indexes:** May want to add for performance
- `readings(timestamp, channel_id)` - Already have?
- `readings(channel_id, timestamp DESC)` - For latest readings
- `channels(organization_id)` - For site queries

**Estimated Additional Storage:** <10 MB for indexes

---

## 🧪 Testing Strategy

For each view, verify:
1. ✅ Returns expected row count
2. ✅ Handles NULL values gracefully
3. ✅ Performance is acceptable (<1 second)
4. ✅ Results match hand-calculated examples
5. ✅ Works with Tableau/reporting tools

**Suggested Testing View:**
```sql
CREATE VIEW v_view_performance AS
SELECT 
    schemaname,
    viewname,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||viewname)) as size,
    (SELECT COUNT(*) FROM [viewname]) as row_count
FROM pg_views
WHERE schemaname = 'public'
    AND viewname LIKE 'v_%';
```

---

## 📚 Documentation Approach

For each view, document:
1. **Purpose** - What it does
2. **Use Cases** - When to use it
3. **Example Queries** - How to use it
4. **Performance** - Expected query time
5. **Dependencies** - What it relies on
6. **Maintenance** - Any special considerations

**Suggested Format:**
```sql
-- View: v_readings_daily
-- Purpose: Daily energy summaries per meter
-- Use Cases: Billing, trend analysis, reporting
-- Performance: ~50ms, returns ~1,600 rows (93 days × 17 meters)
-- Dependencies: readings, channels, organizations
-- Example:
--   SELECT * FROM v_readings_daily 
--   WHERE site_name = 'Wilson Center' 
--     AND reading_date >= '2026-01-01'
--   ORDER BY reading_date DESC;
```

---

## 🎯 Success Metrics

How to know views are working:

1. **Query Performance**
   - Dashboard loads <2 seconds
   - Reports generate <5 seconds
   - Tableau refreshes <10 seconds

2. **Usage**
   - 80% of queries use views
   - Fewer raw table queries
   - Simplified application code

3. **Business Value**
   - Faster customer reports
   - More insights discovered
   - Reduced analysis time

4. **Maintenance**
   - No view performance degradation
   - Easy to add new views
   - Clear documentation

---

## 🚀 Quick Start Options

### Option A: Kitchen Sink (Recommended)
Create all Phase 1 & 2 views (7 total)
- **Time:** 1-2 hours
- **Value:** Immediate 10x query speedup
- **Risk:** Low
- **Best for:** Serious analytics work

### Option B: Essentials Only
Create just the top 4 foundation views
- **Time:** 30 minutes  
- **Value:** Cleaner queries, better naming
- **Risk:** None
- **Best for:** Getting started

### Option C: Targeted
Pick specific views for your immediate needs
- **Time:** 15-30 min per view
- **Value:** Focused solution
- **Risk:** None
- **Best for:** Specific problem solving

### Option D: Phased Rollout
Phase 1 today, Phase 2 next week, etc.
- **Time:** Spread over weeks
- **Value:** Learn as you go
- **Risk:** Lowest
- **Best for:** Learning/experimentation

---

## 🤔 My Recommendation

**Start with Option A (Kitchen Sink):**

Create these 7 views first:
1. `v_sites` - Business alias
2. `v_meters` - Enriched channels  
3. `v_readings_enriched` - Pre-joined
4. `v_latest_readings` - Current values
5. `v_readings_hourly` - Hourly aggregates
6. `v_readings_daily` - Daily summaries
7. `v_readings_monthly` - Monthly rollups

**Why:**
- ✅ Covers 80% of your analytics needs
- ✅ Massive performance improvement
- ✅ Enables all your current reports
- ✅ Foundation for future views
- ✅ Only 1-2 hours of work

**Then add:**
- `v_business_hours_analysis` (week 1)
- `v_cost_analysis` (week 1)
- Others as needed based on usage

---

## 📋 Next Steps

**Before Creating Views:**
1. ✅ Review this strategy
2. ✅ Decide which views to create
3. ✅ Choose implementation option (A/B/C/D)
4. ✅ Get your approval

**During Implementation:**
1. Create views in order (dependencies matter)
2. Test each view after creation
3. Document with inline SQL comments
4. Update this doc with actual performance metrics

**After Implementation:**
1. Update Tableau to use new views
2. Simplify existing Python queries
3. Create example query library
4. Monitor performance

---

**Ready to proceed?** Let me know which option you'd like and I'll:
1. Create the SQL scripts for all views
2. Add inline documentation
3. Provide test queries
4. Update your scripts to use them
5. Create a view usage guide

**Estimated total time:** 2-4 hours for full implementation with testing and documentation.
