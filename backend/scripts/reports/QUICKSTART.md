# Weekly Report Quick Start Guide

Get started with the Weekly Exceptions & Opportunities Brief in 5 minutes.

## Step 1: Verify Environment Setup

Check your `.env` file has the required Eniscope API credentials:

```bash
cat .env | grep ENISCOPE
```

You should see:
```
VITE_ENISCOPE_API_URL=https://core.eniscope.com
VITE_ENISCOPE_API_KEY=your_api_key_here
VITE_ENISCOPE_EMAIL=your_email@example.com
VITE_ENISCOPE_PASSWORD=your_password
```

If missing, copy from `.env.example` and fill in your credentials.

## Step 2: Find Your Site ID

List all available organizations to find your site ID:

```bash
# Using the existing explore script
npm run explore:channels
```

Look for your site in the output and note the `organizationId`.

Example output:
```
Organizations:
  - Wilson Center (ID: 162119)
  - Main Campus (ID: 162120)
```

## Step 3: Run Your First Report

Generate a report for the last complete week:

```bash
npm run report:weekly -- --site 162119
```

This will:
- Pull data for last Monday 00:00 to Sunday 23:59
- Analyze 4 weeks of baseline data
- Generate analytics and recommendations
- Save report to `data/weekly-brief-162119-{date}.json`

## Step 4: View the Results

The report is saved as JSON. You can:

**View in terminal:**
```bash
cat data/weekly-brief-162119-*.json | head -100
```

**Pretty print:**
```bash
cat data/weekly-brief-162119-*.json | python -m json.tool | less
```

**View summary (printed to console during generation):**
The script automatically prints an executive summary when complete.

## Step 5: Customize (Optional)

### Change Date Range

Report on a specific week:

```bash
npm run report:weekly -- \
  --site 162119 \
  --start "2026-01-13T00:00:00Z" \
  --end "2026-01-19T23:59:59Z"
```

### Use Custom Configuration

Create `my-config.json`:

```json
{
  "timezone": "America/Chicago",
  "businessHours": {
    "monday": { "start": 8, "end": 17 },
    "tuesday": { "start": 8, "end": 17 },
    "wednesday": { "start": 8, "end": 17 },
    "thursday": { "start": 8, "end": 17 },
    "friday": { "start": 8, "end": 17 }
  },
  "tariff": {
    "defaultRate": 0.15
  }
}
```

Run with custom config:

```bash
npm run report:weekly -- --site 162119 --config my-config.json
```

### Specify Output Location

```bash
npm run report:weekly -- \
  --site 162119 \
  --out reports/wilson-center-weekly.json
```

## Understanding the Output

### Executive Summary

The console output shows:

1. **Headline** - Top findings this week
2. **Top Risks** - Critical issues requiring attention
3. **Top Opportunities** - Savings potential
4. **Quick Wins** - Actionable recommendations

Example:
```
EXECUTIVE SUMMARY
----------------------------------------------------------------------

Headline:
  • 245 kWh after-hours waste detected
  • 3 anomalous consumption event(s)

Top Opportunities:
  • After-Hours Optimization: 245 kWh/week ($1,529/year)
    Reduce unnecessary equipment operation during unoccupied hours

Potential Savings:
  Weekly: 245 kWh ($29.40)
  Annual: $1,529

Quick Wins:
  1. [HIGH] Reduce overnight base load on HVAC System
     Impact: 150 kWh/week ($18.00)
  2. [MEDIUM] Investigate recurring spikes on Lighting Panel
     Impact: 45 kWh/week ($5.40)
```

### JSON Report Structure

The full JSON report contains:

```json
{
  "metadata": {
    "site": { "siteId": "162119", "siteName": "Wilson Center" },
    "period": { "start": "...", "end": "..." }
  },
  "summary": {
    "headline": [...],
    "topRisks": [...],
    "topOpportunities": [...],
    "totalPotentialSavings": { "weeklyKwh": 245, "weeklyCost": 29.40 }
  },
  "sections": {
    "sensorHealth": { "totalIssues": 2, "issues": [...] },
    "afterHoursWaste": { "summary": {...}, "topMeters": [...] },
    "anomalies": { "timeline": [...], "byChannel": [...] },
    "spikes": { "topSpikes": [...] },
    "quickWins": [...]
  }
}
```

## Automation

### Weekly Scheduled Report

Add to cron (runs every Monday at 8am):

```bash
0 8 * * 1 cd /path/to/project && npm run report:weekly -- --site 162119 >> logs/weekly-report.log 2>&1
```

### Save Reports with Timestamps

The default output already includes timestamps:
```
data/weekly-brief-162119-2026-02-01.json
```

Keep a history by date to track trends over time.

## Troubleshooting

### "Missing required environment variables"

Solution: Check your `.env` file has all required credentials.

```bash
# Test authentication
npm run explore:channels
```

### "No readings found for channel"

Possible causes:
- Date range has no data
- Channel ID is incorrect
- API permissions issue

Solution: Try a different date range or verify channel access.

### "Rate limited"

The script automatically retries with exponential backoff. If you see this:
- Wait a few minutes
- Reduce the number of channels being analyzed
- Contact API provider about rate limits

## Next Steps

1. **Review the README** - See `backend/scripts/reports/README.md` for full documentation
2. **Customize Config** - Adjust thresholds for your facility
3. **Integrate with Reporting** - Build HTML/PDF reports from JSON output
4. **Schedule Automation** - Set up weekly cron jobs
5. **Track Progress** - Compare weekly reports to monitor improvements

## Getting Help

- Check the troubleshooting section in README.md
- Review existing analysis scripts in `backend/scripts/analysis/`
- Enable debug mode: `DEBUG=1 npm run report:weekly -- --site 162119`

## Example Commands

```bash
# Basic report for last week
npm run report:weekly -- --site 162119

# Specific date range
npm run report:weekly -- --site 162119 --start "2026-01-20T00:00:00Z" --end "2026-01-26T23:59:59Z"

# Custom config and output
npm run report:weekly -- --site 162119 --config my-config.json --out reports/weekly.json

# Different timezone
npm run report:weekly -- --site 162119 --timezone "America/Los_Angeles"

# Run tests
npm run report:test
```

## What Gets Analyzed?

✅ **Sensor Health**
- Missing data gaps
- Stale meters
- Flatlined sensors

✅ **After-Hours Waste**
- Overnight consumption above baseline
- Weekend usage
- Cost impact

✅ **Anomalies**
- Unusual consumption patterns
- Week-over-week changes
- Statistical outliers

✅ **Demand Spikes**
- Peak power events
- Short-cycling detection
- Demand charge impact

✅ **Quick Wins**
- Ranked recommendations
- Cost/benefit estimates
- Assigned owners

## Report Frequency Recommendations

| Facility Type | Recommended Frequency | Notes |
|---------------|----------------------|-------|
| Office Building | Weekly | Mon-Fri patterns, clear after-hours |
| Retail | Weekly | Track weekend usage |
| Manufacturing | Weekly | Shift patterns, process variations |
| Multi-tenant | Bi-weekly | Longer trends, tenant variations |
| Data Center | Daily/Weekly | 24/7 operation, anomaly focus |

Start with weekly reports, then adjust based on your facility's needs.
