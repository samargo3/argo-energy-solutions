# Wilson Center Unit Report - User Guide

## Overview

A comprehensive report system has been created to analyze specific units at the Wilson Center using the Eniscope API. The system allows you to:

- **Select any specific unit/channel** from the Wilson Center facility
- **Define custom timeframes** for analysis
- **Automatically detect anomalies** and equipment issues
- **Get actionable recommendations** for maintenance and optimization

## Accessing the Report

1. Navigate to **Reports** in the main navigation
2. Click **"Generate Report"** on the Wilson Center Equipment Report card
3. Or go directly to `/reports/wilson-center`

## Features

### Unit Selection
Choose from 9 available units at Wilson Center:
- **3 RTUs** (Roof Top Units): RTU-1, RTU-2, RTU-3
- **3 AHUs** (Air Handling Units): AHU-1A, AHU-1B, AHU-2
- **2 Electrical Panels**: Kitchen Main Panel, Kitchen Small Panel
- **1 Environmental Sensor**: Air Sense Main Kitchen

### Date Range Selection
- **Quick Range Buttons**: Today, Last 7 Days, Last 30 Days, Last 90 Days
- **Custom Range**: Select specific start and end dates/times
- **Resolution Options**: 
  - 1 minute (for detailed analysis)
  - 15 minutes (recommended for most cases)
  - 30 minutes
  - 1 hour (default)
  - 1 day (for long-term trends)

### Anomaly Detection

The system automatically detects:

1. **Power Spikes** (Critical/High)
   - Detects sudden increases in power consumption
   - Indicates potential equipment malfunction or short circuits
   - Z-score analysis (3+ standard deviations)

2. **Power Drops** (Medium)
   - Sudden equipment shutdowns
   - Unexpected power interruptions
   - Equipment offline detection

3. **Voltage Anomalies** (High/Medium)
   - Voltage deviations >10% from average
   - Power quality issues
   - Electrical supply problems

4. **Power Factor Issues** (High/Medium)
   - Low power factor (<0.7) indicating reactive power draw
   - Potential utility penalties
   - Motor/equipment efficiency problems

5. **Zero Readings** (Medium)
   - Unexpected zero power when equipment should be running
   - Sensor connectivity issues
   - Equipment offline detection

### Equipment Health Assessment

The system provides an overall health rating:
- **Excellent**: No significant issues detected
- **Good**: Minor anomalies, normal operation
- **Fair**: Some issues requiring attention
- **Poor**: Multiple issues, maintenance recommended
- **Critical**: Immediate action required

### Report Sections

1. **Summary Cards**
   - Equipment Health Status
   - Total Energy Consumption (kWh)
   - Average Power (kW)
   - Peak Power (kW)
   - Data Points Collected
   - Average Voltage (V)
   - Power Factor

2. **Anomaly Summary**
   - Count of anomalies by severity level
   - Color-coded severity indicators

3. **Recommendations**
   - Actionable items prioritized by severity
   - Maintenance suggestions
   - Optimization opportunities

4. **Detected Anomalies Table**
   - Detailed list of all anomalies
   - Timestamp, value, description
   - Specific recommendations for each issue

5. **Detailed Statistics**
   - Complete metrics for the selected period
   - Channel information
   - Time range details

## Best Practices

### For Routine Monitoring
- Use **1 hour resolution** for daily/weekly reports
- Check **Last 7 Days** for weekly reviews
- Focus on **Critical** and **High** severity anomalies

### For Troubleshooting
- Use **15 minute resolution** for detailed analysis
- Select specific date ranges around reported issues
- Review all anomaly types, especially power spikes and voltage anomalies

### For Long-term Analysis
- Use **1 day resolution** for monthly/quarterly reports
- Compare different time periods
- Track equipment health trends over time

## Technical Details

### API Integration
- Uses Eniscope Core API v1
- Authenticates automatically
- Handles rate limiting and retries
- Converts data units (Wh → kWh, W → kW)

### Anomaly Detection Algorithm
- Statistical analysis using Z-scores
- Pattern recognition for unusual behavior
- Context-aware detection (considers surrounding readings)
- Configurable thresholds

### Data Processing
- Real-time data fetching
- Automatic unit conversion
- Statistical calculations
- Health scoring algorithm

## Troubleshooting

### No Data Available
- **Check date range**: Ensure dates are after device registration (May 2025)
- **Verify channel ID**: Confirm the selected unit is active
- **Check API credentials**: Ensure `.env` file has correct Eniscope credentials
- **Try different resolution**: Some resolutions may not have data

### API Errors
- Verify environment variables:
  - `VITE_ENISCOPE_API_URL`
  - `VITE_ENISCOPE_API_KEY`
  - `VITE_ENISCOPE_EMAIL`
  - `VITE_ENISCOPE_PASSWORD`
- Check network connectivity
- Review API rate limits

### Anomaly Detection Issues
- Ensure sufficient data points (recommended: 24+ hours)
- Check if equipment was intentionally shut down
- Verify sensor connectivity for zero readings

## Example Use Cases

### Case 1: Routine Weekly Check
1. Select "RTU-1_WCDS_Wilson Ctr"
2. Click "Last 7 Days"
3. Resolution: 1 hour
4. Review Equipment Health status
5. Check for Critical/High anomalies
6. Review recommendations

### Case 2: Investigating Power Spike
1. Select affected unit
2. Set custom date range around the incident
3. Resolution: 15 minutes
4. Review Anomalies Table for power spikes
5. Check timestamp and value
6. Follow recommendation for investigation

### Case 3: Monthly Energy Review
1. Select unit
2. Set date range for last month
3. Resolution: 1 day
4. Review Total Energy consumption
5. Compare with previous periods
6. Check for efficiency opportunities

## Future Enhancements

Planned improvements:
- Export reports to PDF
- Email report delivery
- Scheduled automated reports
- Comparison with historical baselines
- Trend charts and visualizations
- Multi-unit comparison
- Alert notifications

## Support

For questions or issues:
- Check the main README.md
- Review API documentation in `Core_API_v1.txt`
- Check environment setup in `ENV_SETUP_HELP.md`

---

**Created**: January 2026  
**Version**: 1.0
