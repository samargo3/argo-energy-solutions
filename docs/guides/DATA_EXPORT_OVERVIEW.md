# Wilson Center Data Export - Complete Overview

## What Is This?

A simple, repeatable process to pull raw energy data from the Eniscope API for the Wilson Center and export it as CSV files for use in:

- **Tableau** - Business intelligence and dashboards
- **AI Tools** (ChatGPT, Claude, etc.) - Automated analysis and report generation
- **Python/R** - Statistical analysis and modeling
- **Excel/Google Sheets** - Custom analysis and reporting

## Quick Start

### Export Last Month's Data
```bash
npm run export:wilson:raw
```

### Export Specific Month
```bash
npm run export:wilson:raw 2026 1
```

**Output**: `backend/data/exports/wilson-center-raw-2026-01.csv`

## What You Get

Every export creates **3 files**:

1. **Main Data CSV** - All raw readings with timestamps, channels, power, energy, voltage, etc.
2. **Channel Metadata CSV** - Device information, channel names, types
3. **Summary JSON** - Export statistics and metadata

## Key Features

### Complete Raw Data
- Timestamp (ISO 8601 format)
- Energy (kWh and Wh)
- Power (kW and W)
- Voltage, Current, Power Factor
- Temperature
- Date/time components (Year, Month, Day, Hour, Day of Week)
- Channel and device metadata

### Wilson Center Equipment Coverage
The export includes all 9 active Wilson Center channels:
- 3 RTUs (Roof Top Units)
- 3 AHUs (Air Handling Units)
- 2 Kitchen Electrical Panels
- 1 Air Quality Sensor

### Flexible Resolution
Choose data granularity based on your needs:
- **5 minutes** - Detailed troubleshooting
- **15 minutes** - Default, best for most analysis
- **1 hour** - Monthly trends
- **1 day** - Yearly patterns

### Tableau-Ready Format
- Pre-formatted columns with proper data types
- Date/time dimensions for easy filtering
- Clean, standardized naming conventions
- Ready to join with metadata

### AI-Tool Friendly
- Single CSV file with all context
- Human-readable column names
- Complete metadata included
- Optimized file sizes

## Use Cases

### 1. Monthly Energy Report (Tableau)
```bash
# Export last month
npm run export:wilson:raw

# Open Tableau
# Connect → Text File → Select CSV
# Create dashboard with:
#   - Energy consumption by channel (bar chart)
#   - Power timeline (line chart)
#   - Usage heatmap (hour × day)
#   - Peak demand analysis
```

### 2. AI-Generated Analysis Report
```bash
# Export with hourly resolution (smaller file)
npm run export:wilson:raw 2026 1 -- --resolution=3600

# Upload CSV to ChatGPT/Claude
# Prompt: "Analyze this Wilson Center energy data and create a 
#          comprehensive report with insights and recommendations"
```

### 3. Custom Python Analysis
```bash
# Export data
npm run export:wilson:raw 2026 1

# Run example analysis script
cd backend/data/exports
python example-python-analysis.py wilson-center-raw-2026-01.csv

# Creates:
#   - Visualizations (power timeline, heatmaps, bar charts)
#   - Statistical analysis
#   - Anomaly detection
#   - Text report
```

### 4. Batch Historical Export
```bash
# Export all of 2025
for month in {1..12}; do
  npm run export:wilson:raw 2025 $month
  sleep 5
done
```

### 5. Automated Monthly Reports
```bash
# Schedule with cron (Linux/Mac)
# Run on 1st of each month at 2 AM
0 2 1 * * cd /path/to/project && npm run export:wilson:raw
```

## Documentation Structure

### Quick References
- **This File** - Complete overview
- `WILSON_RAW_EXPORT_QUICKSTART.md` - TL;DR commands and examples

### Detailed Guides
- `backend/scripts/data-collection/README_EXPORT.md` - Full user guide
  - Complete command reference
  - Troubleshooting
  - Best practices
  - Integration examples

### Integration Guides
- `docs/guides/integrations/TABLEAU_INTEGRATION_GUIDE.md` - Tableau setup
- `docs/guides/integrations/TABLEAU_JOINING_GUIDE.md` - Advanced joins
- `backend/data/exports/example-python-analysis.py` - Python example

### API Documentation
- `docs/api/API_CONNECTION_GUIDE.md` - Eniscope API setup
- `docs/api/Core_API_v1.txt` - Complete API reference

## Common Workflows

### Workflow 1: Regular Monthly Reporting
```bash
# Day 1 of each month:
1. Export last month: npm run export:wilson:raw
2. Import to Tableau
3. Update dashboard
4. Share with stakeholders
```

### Workflow 2: Investigating Issues
```bash
# When equipment issue reported:
1. Export specific time period with 15-min resolution
2. Run Python analysis for anomaly detection
3. Create visualizations
4. Generate findings report
```

### Workflow 3: AI-Assisted Analysis
```bash
# For quick insights:
1. Export with 1-hour resolution (smaller file)
2. Upload to AI tool
3. Request analysis: trends, anomalies, recommendations
4. Refine and iterate with follow-up questions
```

### Workflow 4: Compliance/Auditing
```bash
# For historical records:
1. Export all months of interest
2. Archive CSV files
3. Maintain export summaries
4. Document any anomalies or notes
```

## File Organization

Recommended structure:
```
backend/data/exports/
├── 2025/
│   ├── wilson-center-raw-2025-01.csv
│   ├── wilson-center-raw-2025-01-channels.csv
│   ├── wilson-center-raw-2025-01-summary.json
│   ├── ...
│   └── wilson-center-raw-2025-12.csv
├── 2026/
│   ├── wilson-center-raw-2026-01.csv
│   └── ...
└── README.md
```

## Troubleshooting Quick Reference

| Issue | Solution |
|-------|----------|
| "Channels data not found" | Run `npm run explore:channels` first |
| "Authentication failed" | Check `.env` file credentials |
| "No data available" | Verify month has data (started May 2025) |
| "Rate limited" | Wait and retry, script has auto-retry |
| File too large | Use coarser resolution (e.g., 3600) |

## Integration with Existing Tools

This export complements existing Wilson Center features:

| Tool | Purpose | Export Advantage |
|------|---------|------------------|
| Unit Health Report | Real-time monitoring | Historical analysis |
| Analysis Scripts | Facility-wide analysis | External tool integration |
| Export to CSV | Analyzed data export | Raw data flexibility |

Use raw exports when you need:
- Custom analysis outside existing reports
- Data for external tools (Tableau, AI, Python)
- Complete historical records
- Integration with other systems

## Performance Notes

### Export Speed
- ~9 channels
- ~2,880 readings per channel per month (15-min resolution)
- ~25,920 total readings
- Export time: 30-60 seconds
- Output file: ~4-5 MB

### API Rate Limits
- Built-in delays (300ms between channels)
- Automatic retry on rate limiting
- Exponential backoff (1s, 2s, 4s)
- Respects Eniscope API limits

### File Sizes

| Period | Resolution | Channels | Rows | Size |
|--------|-----------|----------|------|------|
| 1 month | 15 min | 9 | ~26K | 4.5 MB |
| 1 month | 1 hour | 9 | ~6.5K | 1.1 MB |
| 1 year | 1 day | 9 | ~3.3K | 450 KB |

## Best Practices

### Regular Exports
✅ Export monthly on the 1st
✅ Keep at least 3 months locally
✅ Archive older exports to cloud storage
✅ Verify data quality with summary file

### Data Quality
✅ Review summary JSON for completeness
✅ Check channel metadata for errors
✅ Spot-check a few records manually
✅ Document any known issues

### Security
✅ Never commit CSV files to git (already in .gitignore)
✅ Don't share files with embedded credentials
✅ Compress files before email/transfer
✅ Use secure cloud storage for archives

### Organization
✅ Organize by year/month folders
✅ Use consistent naming conventions
✅ Keep metadata with data files
✅ Document custom analysis and findings

## Advanced Features

### Custom Resolution
```bash
# 5-minute data for detailed analysis
npm run export:wilson:raw 2026 1 -- --resolution=300

# Daily data for long-term trends
npm run export:wilson:raw 2025 1 -- --resolution=86400
```

### Scripting Multiple Exports
```bash
# Export script: export-all-months.sh
#!/bin/bash
for month in {1..12}; do
  echo "Exporting 2025-$month..."
  npm run export:wilson:raw 2025 $month
  sleep 5
done
```

### Data Pipeline
```bash
# Complete pipeline
1. npm run export:wilson:raw 2026 1
2. python backend/data/exports/example-python-analysis.py wilson-center-raw-2026-01.csv
3. # Upload results to Tableau Server
4. # Email report to stakeholders
```

## Support & Resources

### Documentation
- Main README: `README.md`
- Quick Start: `docs/guides/WILSON_RAW_EXPORT_QUICKSTART.md`
- Full Guide: `backend/scripts/data-collection/README_EXPORT.md`
- API Docs: `docs/api/`

### Examples
- Python Analysis: `backend/data/exports/example-python-analysis.py`
- Tableau Guide: `docs/guides/integrations/TABLEAU_INTEGRATION_GUIDE.md`

### Getting Help
1. Check documentation first
2. Review error messages carefully
3. Verify environment setup
4. Check API credentials
5. Review Eniscope API status

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | Feb 2026 | Initial release |

## Future Enhancements

Potential future features:
- Multi-organization support
- Direct Tableau Server integration
- Automated report generation
- Email delivery of exports
- Web UI for export configuration
- Real-time export status dashboard
- Custom field selection
- Data filtering options

---

**Script**: `backend/scripts/data-collection/export-wilson-raw-monthly.js`  
**Created**: February 2026  
**Maintained by**: Argo Energy Solutions
