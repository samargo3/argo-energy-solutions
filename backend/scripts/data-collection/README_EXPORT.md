# Wilson Center Raw Data Export - User Guide

## Overview

This script provides a simple, repeatable process to pull raw energy data from the Eniscope API for the Wilson Center and export it as CSV files. The exported data is ready for immediate use in:
- **Tableau** for visualization and dashboards
- **AI tools** (ChatGPT, Claude, etc.) for analysis and reporting
- **Excel/Google Sheets** for custom analysis
- **Python/R** for statistical analysis

## Quick Start

### Export Last Month's Data
```bash
node backend/scripts/data-collection/export-wilson-raw-monthly.js
```

### Export Specific Month
```bash
# Format: node script.js YEAR MONTH
node backend/scripts/data-collection/export-wilson-raw-monthly.js 2025 12
node backend/scripts/data-collection/export-wilson-raw-monthly.js 2026 1
```

### Export with Custom Resolution
```bash
# 1 hour resolution (3600 seconds)
node backend/scripts/data-collection/export-wilson-raw-monthly.js 2025 12 --resolution=3600

# 5 minute resolution (300 seconds)
node backend/scripts/data-collection/export-wilson-raw-monthly.js 2026 1 --resolution=300
```

## Output Files

The script creates three files in `backend/data/exports/`:

### 1. Main Data File: `wilson-center-raw-YYYY-MM.csv`
Contains all raw readings with the following columns:

| Column | Description | Example |
|--------|-------------|---------|
| `Timestamp` | ISO 8601 timestamp | 2026-01-15T14:30:00.000Z |
| `Unix_Timestamp` | Unix epoch timestamp | 1736953800 |
| `Date` | Date only (YYYY-MM-DD) | 2026-01-15 |
| `Time` | Time only (HH:MM:SS) | 14:30:00 |
| `Year` | Year | 2026 |
| `Month` | Month (1-12) | 1 |
| `Day` | Day of month | 15 |
| `Hour` | Hour of day (0-23) | 14 |
| `Day_of_Week` | Day name | Wednesday |
| `Channel_ID` | Unique channel identifier | 12345 |
| `Channel_Name` | Descriptive channel name | RTU-1_WCDS_Wilson Ctr |
| `Device_Type` | Type of device | Virtual Energy Meter |
| `Data_Type` | Type of data | Energy |
| `Energy_Wh` | Energy in watt-hours | 1500 |
| `Energy_kWh` | Energy in kilowatt-hours | 1.5 |
| `Power_W` | Power in watts | 5000 |
| `Power_kW` | Power in kilowatts | 5.0 |
| `Voltage_V` | Voltage in volts | 240 |
| `Current_A` | Current in amperes | 20.8 |
| `Power_Factor` | Power factor (0-1) | 0.85 |
| `Temperature_C` | Temperature in Celsius | 22.5 |

### 2. Channel Metadata: `wilson-center-raw-YYYY-MM-channels.csv`
Contains information about each channel:

| Column | Description |
|--------|-------------|
| `Channel_ID` | Unique channel identifier |
| `Channel_Name` | Descriptive channel name |
| `Device_ID` | Device identifier |
| `Device_Name` | Device name |
| `Device_Type` | Type of device/meter |
| `Data_Type` | Type of data collected |
| `Organization_ID` | Organization identifier |
| `Status` | Channel status (1=active) |
| `In_TSDB` | In time-series database (Y/N) |
| `Tariff_ID` | Tariff identifier |
| `Data_Points` | Number of readings in export |
| `Error` | Any errors encountered |

### 3. Summary: `wilson-center-raw-YYYY-MM-summary.json`
JSON file with export metadata:
```json
{
  "year": 2026,
  "month": 1,
  "monthName": "January",
  "resolution": "900",
  "resolutionMinutes": 15,
  "totalChannels": 9,
  "totalDataPoints": 25920,
  "averageDataPointsPerChannel": 2880,
  "exportDate": "2026-02-01T10:30:00.000Z"
}
```

## Resolution Options

Resolution controls how frequently data points are collected:

| Resolution | Description | Use Case |
|------------|-------------|----------|
| `300` (5 min) | Very detailed | Troubleshooting, detailed analysis |
| `900` (15 min) | **Default** | General analysis, Tableau |
| `1800` (30 min) | Standard | Daily/weekly reporting |
| `3600` (1 hour) | Moderate | Monthly trends |
| `86400` (1 day) | Summary | Long-term trends, yearly analysis |

**Note**: More granular resolutions = more data points = larger files

## Wilson Center Channels

The export includes all active Wilson Center channels:

### HVAC Systems
- RTU-1_WCDS_Wilson Ctr (Roof Top Unit 1)
- RTU-2_WCDS_Wilson Ctr (Roof Top Unit 2)
- RTU-3_WCDS_Wilson Ctr (Roof Top Unit 3)
- AHU-1A_WCDS_Wilson Ctr (Air Handling Unit 1A)
- AHU-1B_WCDS_Wilson Ctr (Air Handling Unit 1B)
- AHU-2_WCDS_Wilson Ctr (Air Handling Unit 2)

### Electrical Panels
- Kitchen Main Panel_WCDS_Wilson Ctr
- Kitchen Small Panel_WCDS_Wilson Ctr

### Sensors
- Air Sense Main Kitchen_WCDS_Wilson Ctr

## Using with Tableau

### Basic Import
1. Open Tableau Desktop
2. Click **Connect → Text File**
3. Select `wilson-center-raw-YYYY-MM.csv`
4. Tableau will auto-detect data types
5. Start building visualizations!

### Enhanced Analysis with Channel Metadata
1. Import main data file as above
2. Click **Add** (next to Connections)
3. Add `wilson-center-raw-YYYY-MM-channels.csv`
4. Create a join:
   - Left table: Main data
   - Right table: Channel metadata
   - Join type: Left Join
   - Join clause: `Channel_ID = Channel_ID`
5. Now you have device types and metadata in your analysis!

### Recommended Tableau Visualizations
- **Line Chart**: `Timestamp` vs `Power_kW` (colored by `Channel_Name`)
- **Heatmap**: `Day_of_Week` + `Hour` vs `Power_kW` (to find usage patterns)
- **Bar Chart**: `Channel_Name` vs `SUM(Energy_kWh)` (to compare consumption)
- **Area Chart**: `Timestamp` vs `Power_kW` (stacked by `Channel_Name`)

## Using with AI Tools (ChatGPT, Claude, etc.)

### Direct Upload
1. Export the data
2. Upload `wilson-center-raw-YYYY-MM.csv` to your AI tool
3. Ask questions like:
   - "What are the peak usage hours for the Wilson Center?"
   - "Which equipment uses the most energy?"
   - "Generate a report analyzing energy patterns"
   - "What anomalies do you see in the data?"

### For Large Files
If the CSV is too large (>25MB for most AI tools):
```bash
# Split by channel using Python, R, or Excel
# Or export with coarser resolution
node backend/scripts/data-collection/export-wilson-raw-monthly.js 2026 1 --resolution=3600
```

## Using with Python/R

### Python Example
```python
import pandas as pd

# Load the data
df = pd.read_csv('backend/data/exports/wilson-center-raw-2026-01.csv')

# Convert timestamp to datetime
df['Timestamp'] = pd.to_datetime(df['Timestamp'])

# Load channel metadata
channels = pd.read_csv('backend/data/exports/wilson-center-raw-2026-01-channels.csv')

# Merge with metadata
df_merged = df.merge(channels, on='Channel_ID', how='left')

# Analyze
total_energy = df.groupby('Channel_Name')['Energy_kWh'].sum()
print(total_energy)

# Visualize
import matplotlib.pyplot as plt
df.groupby('Hour')['Power_kW'].mean().plot()
plt.title('Average Power by Hour')
plt.show()
```

### R Example
```r
library(tidyverse)
library(lubridate)

# Load the data
df <- read_csv('backend/data/exports/wilson-center-raw-2026-01.csv')

# Convert timestamp
df$Timestamp <- as_datetime(df$Timestamp)

# Load channel metadata
channels <- read_csv('backend/data/exports/wilson-center-raw-2026-01-channels.csv')

# Join
df_merged <- df %>% left_join(channels, by = "Channel_ID")

# Analyze
df_merged %>%
  group_by(Channel_Name) %>%
  summarise(Total_Energy = sum(Energy_kWh, na.rm = TRUE)) %>%
  arrange(desc(Total_Energy))

# Visualize
df_merged %>%
  ggplot(aes(x = Timestamp, y = Power_kW, color = Channel_Name)) +
  geom_line() +
  theme_minimal() +
  labs(title = "Power Consumption Over Time")
```

## Scheduled/Automated Exports

### Monthly Cron Job (Linux/Mac)
```bash
# Edit crontab
crontab -e

# Add this line to run on the 1st of each month at 2 AM
0 2 1 * * cd /path/to/project && node backend/scripts/data-collection/export-wilson-raw-monthly.js
```

### Windows Task Scheduler
1. Open Task Scheduler
2. Create Basic Task
3. Trigger: Monthly, Day 1, Time 2:00 AM
4. Action: Start a Program
5. Program: `node`
6. Arguments: `backend/scripts/data-collection/export-wilson-raw-monthly.js`
7. Start in: `C:\path\to\project`

### Automation Script (bash)
Create `export-all-months.sh`:
```bash
#!/bin/bash
# Export data for multiple months

for month in {1..12}; do
  echo "Exporting 2025-$month..."
  node backend/scripts/data-collection/export-wilson-raw-monthly.js 2025 $month
  sleep 5  # Avoid rate limiting
done

echo "All exports complete!"
```

## Troubleshooting

### No Data Available
**Problem**: Export shows 0 data points
**Solutions**:
- Verify the month has actual data (Wilson Center started collecting data in May 2025)
- Check date range is not in the future
- Ensure channels are active (`Status = 1`, `In_TSDB = Y`)

### API Authentication Failed
**Problem**: "Authentication failed" error
**Solutions**:
- Check `.env` file has correct credentials:
  ```
  VITE_ENISCOPE_API_URL=https://core.eniscope.com
  VITE_ENISCOPE_API_KEY=your_key_here
  VITE_ENISCOPE_EMAIL=your_email_here
  VITE_ENISCOPE_PASSWORD=your_password_here
  ```
- Verify credentials are correct and not expired
- Check network connectivity

### Channels Data Not Found
**Problem**: "Channels data not found" error
**Solutions**:
```bash
# Run the channels exploration script first
npm run explore:channels
# Or manually:
node backend/scripts/data-collection/explore-channels.js
```

### Rate Limiting
**Problem**: "Rate limited" or 429 errors
**Solutions**:
- Script has built-in retry logic (waits 1s, 2s, 4s)
- If still failing, increase delays in the script
- Export fewer channels or use coarser resolution
- Contact Eniscope support to increase rate limits

### Large File Sizes
**Problem**: CSV files too large for tools
**Solutions**:
- Use coarser resolution (e.g., 3600 instead of 900)
- Split by channel using Excel/Python
- Compress files with gzip/zip before sharing
- Use database instead of CSV for very large datasets

## Best Practices

### Regular Exports
- Export monthly data on the 1st of each month
- Keep organized: one folder per year
- Archive old exports to save space

### Data Quality
- Always check the summary file for data point counts
- Review channel metadata for any errors
- Validate a few records manually

### Backups
- Keep exports in version control (if small)
- Store in cloud storage (Google Drive, Dropbox)
- Keep at least 3 months of rolling data

### Documentation
- Note any anomalies or issues in the export
- Track which exports were shared with stakeholders
- Document any custom analysis or findings

## Integration with Existing Tools

This script complements the existing Wilson Center reports:
- **Unit Health Report** (`/reports/wilson-center`): Real-time analysis of specific units
- **Analysis Scripts** (`wilson-center-analysis.js`): Comprehensive facility analysis
- **Export to CSV** (`export-to-csv.js`): Export analyzed data

Use this raw export when you need:
- Custom analysis not available in existing reports
- Data for external tools (Tableau, AI, etc.)
- Complete raw data for compliance/auditing
- Historical data for trend analysis

## Support

For questions or issues:
- Check the main project README.md
- Review Eniscope API documentation: `docs/api/Core_API_v1.txt`
- Contact: Argo Energy Solutions support

---

**Script Location**: `backend/scripts/data-collection/export-wilson-raw-monthly.js`  
**Created**: February 2026  
**Version**: 1.0
