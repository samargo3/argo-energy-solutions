# Accessing Wilson Center Data - Portal vs API

## Current Situation

**Device Status:** ✅ Transmitting to Best.Energy portal  
**API Historical Data:** ⏳ Not yet available in time-series database  

## Understanding the Two Data Sources

### 1. Best.Energy Portal (Web Interface)
**What you see:**
- Real-time device status and connectivity
- Current readings and live telemetry  
- Device configuration and settings
- Alerts and notifications
- Real-time dashboards

**Access:** Via web browser at Best.Energy's portal

### 2. Eniscope Core API (Programmatic)
**What you get:**
- Historical time-series readings data
- Aggregated statistics and summaries
- Bulk data export for analysis
- Integration capabilities for Salesforce

**Access:** Via REST API calls (what our scripts use)

---

## Why API Shows No Data (Yet)

### Data Ingestion Pipeline

```
Device → Best.Energy Gateway → Portal Display (Real-time) ✅
                              ↓
                    Data Validation & Processing
                              ↓
                    Time-Series Database ⏳
                              ↓
                    API Access ❌ (not ready yet)
```

### Common Reasons for Delay

1. **New Device Registration**
   - Devices registered May 1, 2025
   - Initial data collection period needed
   - Validation and quality checks

2. **Data Ingestion Lag**
   - Real-time portal data available immediately
   - Historical API data requires processing
   - Can take 24-48 hours for first readings

3. **Database Population**
   - Time-series DB needs sufficient data points
   - Minimum data volume before API exposure
   - Index building and optimization

---

## What to Check on the Portal

When you log into Best.Energy's portal, look for:

### 1. Device Status
- Are devices showing as "Online" or "Connected"?
- What's the last communication timestamp?
- Any error messages or alerts?

### 2. Real-Time Readings
- Can you see current power consumption?
- Are voltage/current values displaying?
- Are values reasonable (not zero or error)?

### 3. Data History
- Does the portal show any historical graphs?
- What date range has data on the portal?
- What's the earliest data timestamp?

### 4. Channel Configuration
- Are channels properly configured?
- Correct phase assignments?
- Proper tariffs and multipliers set?

---

## How to Get API Data Working

### Step 1: Verify Portal Data

**On Best.Energy Portal:**
1. Log in to https://portal.best.energy (or your portal URL)
2. Navigate to Wilson Center facility
3. Check each device/channel for:
   - ✅ Live readings
   - ✅ Historical data graphs
   - 📅 Note the date range with data

### Step 2: Match Portal Timeframe

Once you confirm data exists on the portal (e.g., "data since May 5, 2025"):

```bash
# Try querying that exact date range
npm run diagnose:data

# Or manually test with our scripts using custom dates:
# Edit wilson-center-analysis.js and try:
# daterange: ['2025-05-05', '2025-05-07']
```

### Step 3: Check in_tsdb Flag

Our channel data shows `in_tsdb: 'Y'` for Wilson Center channels, which means they SHOULD be in the time-series database. If data exists on portal but not API, this could indicate:

- Portal shows real-time data not yet historized
- API lag of 24-48 hours
- Data ingestion pipeline issue

### Step 4: Contact Best.Energy Support

**Questions to ask:**
1. "When will historical data be available via API for channel ID 162119?"
2. "I see data on the portal since [date], but API returns 0 data points. Is there an ingestion delay?"
3. "Do I need to enable API access for time-series data?"
4. "Is there a minimum data collection period before API access?"

**Support Contact:**
- Email: support@best.energy
- Include your organization name: Argo Energy Solutions LLC
- Include channel IDs: 162119, 162120, 162121, etc.
- Include API key (for reference)

---

## Alternative: Manual Data Export

If you need data immediately for analysis/reports:

### From Portal

1. **Export Historical Data**
   - Most energy portals have CSV export
   - Select date range and channels
   - Download and import into your analysis tools

2. **Screenshot/Manual Entry**
   - For presentations/reports
   - Capture portal dashboards
   - Note key metrics manually

3. **API Support Request**
   - Ask Best.Energy to enable historical data export
   - Request data backfill to API
   - Ask for bulk export options

---

## When API Data Becomes Available

Once the time-series database is populated, our scripts will work automatically:

### Automated Daily Reports

```bash
# Run daily to fetch latest data
npm run analyze:wilson yesterday 900
```

### Weekly Summary

```bash
# Every Monday
npm run analyze:wilson lastweek 3600
```

### Monthly Analysis

```bash
# First of month
npm run analyze:wilson lastmonth 3600
```

### Custom Analysis

```javascript
// scripts/wilson-center-analysis.js
// Modify date range and resolution as needed
const dateRange = ['2025-05-01', '2025-05-31'];
const resolution = '900'; // 15 minutes
```

---

## Testing Data Availability

### Quick Test Script

We've created a diagnostic tool that tests multiple configurations:

```bash
npm run diagnose:data
```

This will:
- Test 17 different query combinations
- Try various date ranges and resolutions
- Save results to `data/diagnostic-results.json`
- Report which configurations return data

**Run this daily** until data appears, then you'll know exactly which parameters work.

---

## Immediate Actions You Can Take

### ✅ Right Now

1. **Check Portal Access**
   - Verify you can log into Best.Energy portal
   - Confirm devices are showing data
   - Note the date range with available data

2. **Document Portal Findings**
   - Take screenshots of dashboards
   - Note key metrics (total kWh, peak kW, etc.)
   - Use for immediate reports/presentations

3. **Run Diagnostics Daily**
   ```bash
   npm run diagnose:data
   ```
   Monitor for when data appears in API

### ⏳ Within 24-48 Hours

4. **Re-test API Access**
   - Run diagnostic script daily
   - Check for any successful data retrieval
   - Try exact date ranges from portal

5. **Contact Support if Needed**
   - If portal has data but API doesn't after 48 hours
   - Provide diagnostic results
   - Ask about ingestion timeline

### 🚀 Once Data Available

6. **Establish Baseline**
   - Collect 1-2 weeks of data
   - Run comprehensive analysis
   - Create standard report templates

7. **Automate Reporting**
   - Schedule daily/weekly runs
   - Set up email notifications
   - Integrate with Salesforce

---

## Expected Timeline

Based on typical energy monitoring deployments:

| Milestone | Expected Time | Status |
|-----------|--------------|---------|
| Device registration | Day 0 | ✅ Complete (May 1, 2025) |
| Portal connectivity | Immediate | ✅ Working (per your report) |
| Real-time portal data | Minutes | ✅ Transmitting |
| Historical portal graphs | 1-24 hours | ❓ Check portal |
| API time-series data | 24-72 hours | ⏳ Waiting |
| Full historical backfill | 1-7 days | ⏳ Pending |

---

## Workaround: Portal Screen Capture for Reports

Until API data is available, you can create reports using portal data:

### Option 1: Screenshots + Manual Entry

1. Capture portal dashboards
2. Extract key metrics
3. Create summary in Excel/Word
4. Use our report template structure (WILSON_CENTER_REPORT.md)

### Option 2: Portal CSV Export

1. Export data from portal (if available)
2. Import into our analysis scripts
3. Process locally for Salesforce upload

### Option 3: Request Data Dump

1. Ask Best.Energy for historical data export
2. Provide in CSV/JSON format
3. One-time import to establish baseline

---

## Summary

**Current State:**
- ✅ Devices working and transmitting
- ✅ Data visible on portal
- ❌ API historical data not yet available

**Next Steps:**
1. Check Best.Energy portal for data availability
2. Run `npm run diagnose:data` daily to test API
3. Contact Best.Energy support if data doesn't appear within 48 hours
4. Use portal exports for immediate reporting needs

**When API Works:**
- All our scripts will function automatically
- Automated reports will generate
- Salesforce integration can proceed

---

## Questions for Best.Energy Support

Copy/paste this into your support ticket:

```
Subject: API Access to Historical Time-Series Data

Organization: Argo Energy Solutions LLC
API Key: b8006d2d1d257a41ee63ea300fc6b7af
User: craig@argoenergysolutions.com

Devices: 9 channels at Wilson Center facility
Device IDs: 162119, 162120, 162121, 162122, 162123, 162277, 162285, 162319, 162320
Registration Date: May 1, 2025

Issue:
- Devices are transmitting data visible on the portal
- API queries return 0 data points for all date ranges
- Channel metadata shows in_tsdb: 'Y'

Questions:
1. When will historical readings be available via API?
2. Is there a data ingestion delay we should expect?
3. Do we need to enable historical data access for our API key?
4. Can you confirm data is being stored in the time-series database?

Testing performed:
- Multiple date ranges (today, yesterday, 7 days, 30 days, custom)
- Various resolutions (60s, 900s, 3600s, 86400s)
- Different actions (summarize, total, averageday)
- All return success (200) but 0 data points

Thank you for your assistance.
```

---

*This guide will be updated once API data access is confirmed.*

