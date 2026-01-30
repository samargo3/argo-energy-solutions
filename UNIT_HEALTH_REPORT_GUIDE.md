# Unit Health Report - Quick Guide

## Overview

A command-line tool that generates comprehensive health assessment reports for individual units at Wilson Center. No web app needed - just run the script with your parameters.

## Quick Start

### Basic Usage

```bash
npm run unit:health <channelId> <startDate> <endDate> [resolution]
```

### Examples

**Analyze RTU-1 for the last week:**
```bash
npm run unit:health 162320 "last 7 days" today 3600
```

**Analyze AHU-2 for a specific date range:**
```bash
npm run unit:health 162121 "2025-01-15" "2025-01-22" 900
```

**Analyze Kitchen Panel for yesterday:**
```bash
npm run unit:health 162285 yesterday today 3600
```

**Analyze RTU-2 for the last month (daily resolution):**
```bash
npm run unit:health 162119 "last 30 days" today 86400
```

## Available Units (Channel IDs)

| Channel ID | Unit Name | Category |
|------------|-----------|----------|
| 162320 | RTU-1_WCDS_Wilson Ctr | HVAC - RTU |
| 162119 | RTU-2_WCDS_Wilson Ctr | HVAC - RTU |
| 162120 | RTU-3_WCDS_Wilson Ctr | HVAC - RTU |
| 162122 | AHU-1A_WCDS_Wilson Ctr | HVAC - AHU |
| 162123 | AHU-1B_WCDS_Wilson Ctr | HVAC - AHU |
| 162121 | AHU-2_WCDS_Wilson Ctr | HVAC - AHU |
| 162285 | CDPK_Kitchen Main Panel(s)_WCDS_Wilson Ctr | Electrical Panel |
| 162319 | CDKH_Kitchen Panel(small)_WCDS_Wilson Ctr | Electrical Panel |
| 162277 | Air Sense_Main Kitchen_WCDS_Wilson | Environmental Sensor |

## Date Formats

### Relative Dates
- `today` - Today (start of day)
- `yesterday` - Yesterday
- `last 7 days` - Last 7 days
- `last 2 weeks` - Last 2 weeks
- `last 30 days` - Last 30 days
- `last 3 months` - Last 3 months

### Absolute Dates
- `"2025-01-15"` - ISO date format
- `"2025-01-15T10:00:00"` - ISO datetime format

## Resolution Options

| Value | Duration | Use Case |
|-------|----------|----------|
| 60 | 1 minute | Detailed troubleshooting |
| 900 | 15 minutes | Standard analysis (recommended) |
| 1800 | 30 minutes | Daily patterns |
| 3600 | 1 hour | Default, good for most cases |
| 86400 | 1 day | Long-term trends |

## What the Report Includes

### 1. Equipment Health Status
- Overall health rating: Excellent → Good → Fair → Poor → Critical
- Color-coded status indicator

### 2. Executive Summary
- Total energy consumption (kWh)
- Average, peak, and minimum power (kW)
- Voltage statistics and stability
- Power factor analysis
- Data point count

### 3. Anomaly Detection
Automatically detects:
- **Power Spikes** (Critical/High) - Sudden increases indicating equipment issues
- **Power Drops** (Medium) - Unexpected shutdowns or interruptions
- **Voltage Anomalies** (High/Medium) - Power quality issues
- **Power Factor Issues** (High/Medium) - Efficiency problems
- **Zero Readings** (Medium) - Equipment offline detection

### 4. Detailed Anomaly List
- Timestamp of each anomaly
- Severity level
- Actual vs expected values
- Description of the issue

### 5. Recommendations
- Prioritized action items
- Maintenance suggestions
- Optimization opportunities

### 6. Statistical Details
- Power distribution statistics
- Energy consumption patterns
- Standard deviations and variance

## Output

Reports are saved to the `data/` directory with the filename format:
```
unit-health-<channelId>-<timestamp>.md
```

Example: `unit-health-162320-2025-01-23T14-30-00.md`

## Common Use Cases

### Weekly Health Check
```bash
npm run unit:health 162320 "last 7 days" today 3600
```

### Troubleshooting a Specific Issue
```bash
# Use 15-minute resolution for detailed analysis
npm run unit:health 162119 "2025-01-20" "2025-01-22" 900
```

### Monthly Review
```bash
# Use daily resolution for overview
npm run unit:health 162285 "last 30 days" today 86400
```

### Compare Units
```bash
# Generate reports for multiple units
npm run unit:health 162320 "last 7 days" today 3600
npm run unit:health 162119 "last 7 days" today 3600
npm run unit:health 162120 "last 7 days" today 3600
```

## Troubleshooting

### No Data Available
- Try a more recent date range (e.g., `yesterday` or `today`)
- Check that the unit is actively collecting data
- Verify the channel ID is correct

### Authentication Errors
- Check your `.env` file has correct Eniscope credentials:
  ```env
  VITE_ENISCOPE_API_URL=https://core.eniscope.com
  VITE_ENISCOPE_API_KEY=your_key
  VITE_ENISCOPE_EMAIL=your_email
  VITE_ENISCOPE_PASSWORD=your_password
  ```

### Rate Limiting
- The script automatically retries with exponential backoff
- If you see rate limit errors, wait a few minutes and try again

## Tips

1. **Start with hourly resolution (3600)** for most analyses
2. **Use 15-minute resolution (900)** when investigating specific issues
3. **Use daily resolution (86400)** for long-term trend analysis
4. **Check the Equipment Health status first** - it gives you an immediate overview
5. **Focus on Critical and High severity anomalies** for immediate action items
6. **Save reports** for comparison over time

## Report Interpretation

### Health Status Guide

- **✅ Excellent**: No issues detected, equipment operating normally
- **🟢 Good**: Minor anomalies, normal operation
- **🟡 Fair**: Some issues requiring attention
- **🟠 Poor**: Multiple issues, maintenance recommended
- **🔴 Critical**: Immediate action required

### Anomaly Severity

- **🔴 Critical**: Equipment malfunction likely, inspect immediately
- **🟠 High**: Significant issue, schedule maintenance within 24-48 hours
- **🟡 Medium**: Monitor and investigate cause
- **🔵 Low**: Minor deviation, may be normal variation

## Next Steps

After reviewing a report:
1. Address Critical and High priority anomalies first
2. Schedule maintenance for recurring issues
3. Compare reports over time to identify trends
4. Share reports with maintenance team for action items

---

**Need help?** Check the script usage with:
```bash
npm run unit:health
```
