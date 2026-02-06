# Wilson Center Raw Data Export - Quick Start Guide

## TL;DR - Just Give Me The Commands

```bash
# Export last month's data (easiest)
npm run export:wilson:raw

# Export a specific month
npm run export:wilson:raw 2026 1

# Export with hourly resolution (instead of 15-min default)
npm run export:wilson:raw 2026 1 -- --resolution=3600
```

**Output Location**: `backend/data/exports/wilson-center-raw-YYYY-MM.csv`

## What You Get

Three files per export:

1. **Main Data CSV** - All the raw readings
2. **Channel Metadata CSV** - Info about each sensor/device
3. **Summary JSON** - Export statistics

## Common Use Cases

### For Tableau
```bash
# Export data
npm run export:wilson:raw 2026 1

# Import to Tableau
1. Open Tableau Desktop
2. Connect → Text File
3. Select: backend/data/exports/wilson-center-raw-2026-01.csv
4. Done!
```

### For ChatGPT/Claude Analysis
```bash
# Export with hourly resolution (smaller file)
npm run export:wilson:raw 2026 1 -- --resolution=3600

# Upload the CSV file to AI tool
# Ask: "Analyze this Wilson Center energy data and create a report"
```

### For Python/R Analysis
```bash
# Export data
npm run export:wilson:raw 2026 1

# In Python:
import pandas as pd
df = pd.read_csv('backend/data/exports/wilson-center-raw-2026-01.csv')
```

### Export Multiple Months
```bash
# January
npm run export:wilson:raw 2025 1

# February  
npm run export:wilson:raw 2025 2

# March
npm run export:wilson:raw 2025 3
```

## Key Data Columns

| Column | What It Is | Example |
|--------|-----------|---------|
| `Timestamp` | When the reading was taken | 2026-01-15T14:30:00Z |
| `Channel_Name` | Equipment name | RTU-1_WCDS_Wilson Ctr |
| `Energy_kWh` | Energy consumed (kilowatt-hours) | 1.5 |
| `Power_kW` | Power draw (kilowatts) | 5.0 |
| `Voltage_V` | Voltage | 240 |
| `Power_Factor` | Power efficiency (0-1) | 0.85 |

## Resolution Guide

| Resolution | Interval | Best For | File Size |
|------------|----------|----------|-----------|
| 300 | 5 minutes | Troubleshooting | Large |
| **900** | **15 minutes** | **General use (default)** | Medium |
| 3600 | 1 hour | Monthly reports | Small |
| 86400 | 1 day | Yearly trends | Tiny |

## Wilson Center Equipment

The export includes data from:

- **3 RTUs** (Roof Top AC Units)
- **3 AHUs** (Air Handlers)  
- **2 Kitchen Panels** (Electrical)
- **1 Sensor** (Air quality)

## Troubleshooting

### "Channels data not found"
```bash
# Run this first:
npm run explore:channels
# Then try export again
```

### "Authentication failed"
Check your `.env` file has:
```
VITE_ENISCOPE_API_URL=https://core.eniscope.com
VITE_ENISCOPE_API_KEY=your_key
VITE_ENISCOPE_EMAIL=your_email
VITE_ENISCOPE_PASSWORD=your_password
```

### "No data available"
- Wilson Center data starts in **May 2025**
- Can't export future months
- Check month number is 1-12

## Full Documentation

For complete details, see:
- **Full Guide**: `backend/scripts/data-collection/README_EXPORT.md`
- **API Docs**: `docs/api/API_CONNECTION_GUIDE.md`
- **Tableau Guide**: `docs/guides/integrations/TABLEAU_INTEGRATION_GUIDE.md`

## Examples

### Export Current Month
```bash
# Get January 2026 data
npm run export:wilson:raw 2026 1
```

### Batch Export (bash)
```bash
# Export all of 2025
for month in {1..12}; do
  npm run export:wilson:raw 2025 $month
  sleep 5  # Be nice to the API
done
```

### Automated Monthly Export (cron)
```bash
# Run on 1st of month at 2 AM
0 2 1 * * cd /path/to/project && npm run export:wilson:raw
```

## Quick Tips

✅ **DO**:
- Export monthly on the 1st
- Keep exports organized by year/month
- Use 15-min resolution for most analyses
- Check the summary JSON for data quality

❌ **DON'T**:
- Export with <5-min resolution unless needed (huge files)
- Run export too frequently (respect API rate limits)
- Forget to backup important exports
- Share files with credentials

## What's Next?

After export:
1. Open CSV in Tableau/Excel/Python
2. Join with channel metadata for device info
3. Create visualizations
4. Generate insights and reports
5. Share findings with stakeholders

## Need Help?

- **Script Issues**: Check `backend/scripts/data-collection/README_EXPORT.md`
- **API Issues**: Check `docs/api/API_CONNECTION_GUIDE.md`
- **Tableau Help**: Check `docs/guides/integrations/TABLEAU_INTEGRATION_GUIDE.md`

---

**Created**: February 2026  
**Last Updated**: February 2026
