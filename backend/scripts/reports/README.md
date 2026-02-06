# Weekly Exceptions & Opportunities Brief

A comprehensive energy analytics system that generates weekly reports from Eniscope interval data, identifying energy waste, anomalies, and optimization opportunities.

## Features

### 🎯 **NEW: Customer-Ready HTML Reports**

The system now **automatically generates professional HTML reports** ready to deliver to customers:

- **Beautiful, branded design** with Argo Energy Solutions styling
- **Executive summary** with key findings and savings
- **Prioritized recommendations** with cost/benefit analysis
- **Professional tables** with color-coded priorities
- **Print to PDF** for distribution
- **Self-contained** - no external dependencies, works in any browser

**See**: `CUSTOMER_REPORTS.md` for full documentation on customer reports.

### Analytics Capabilities

1. **Sensor & Communications Health**
   - Missing data gap detection
   - Stale meter identification
   - Flatlined sensor detection
   - Data completeness monitoring

2. **After-Hours Energy Waste**
   - Baseline consumption calculation (5th percentile)
   - Excess energy identification during non-business hours
   - Cost impact analysis
   - Top contributor ranking

3. **Anomaly Detection**
   - Week-over-week consumption comparison
   - Statistical outlier identification (IQR method)
   - Event grouping and classification
   - Business hours vs after-hours context

4. **Demand Spike Detection**
   - Peak power anomaly identification
   - Baseline comparison (95th percentile)
   - Short-cycling and equipment startup detection
   - Demand charge impact estimation

5. **Quick Wins Generator**
   - Actionable recommendations ranked by impact
   - Cost/benefit estimates
   - Confidence levels and effort requirements
   - Assigned owner recommendations

## Installation

### Prerequisites

- Node.js 16+ with ES modules support
- Access to Eniscope/Best.Energy API
- Environment variables configured (see below)

### Required Environment Variables

Create a `.env` file in the project root:

```bash
# Eniscope API Credentials
VITE_ENISCOPE_API_URL=https://core.eniscope.com
VITE_ENISCOPE_API_KEY=your_api_key_here
VITE_ENISCOPE_EMAIL=your_email@example.com
VITE_ENISCOPE_PASSWORD=your_password

# Alternative naming (if using Best.Energy branding)
VITE_BEST_ENERGY_API_URL=https://core.eniscope.com
VITE_BEST_ENERGY_API_KEY=your_api_key_here
```

### Install Dependencies

```bash
npm install
```

Dependencies are already included in the main `package.json`:
- `axios` - HTTP client
- `crypto-js` - MD5 hashing for authentication
- `dotenv` - Environment variable management

## Usage

### Basic Usage

Generate a report for the last complete week (Monday-Sunday):

```bash
node backend/scripts/reports/weekly-exceptions-brief.js --site <organization_id>
```

This generates **TWO files**:
1. **JSON** - Raw data for analysis (`weekly-brief-{site}-{date}.json`)
2. **HTML** - Professional customer-ready report (`weekly-brief-{site}-{date}.html`) ✨

The HTML report is ready to:
- Open in any browser
- Print to PDF
- Email to customers
- Upload to portals

### Advanced Options

```bash
node backend/scripts/reports/weekly-exceptions-brief.js \
  --site 12345 \
  --start "2026-01-20T00:00:00Z" \
  --end "2026-01-26T23:59:59Z" \
  --out "reports/weekly-report.json" \
  --timezone "America/New_York"
```

### Options

| Option | Required | Description | Default |
|--------|----------|-------------|---------|
| `--site` | Yes | Organization ID from Eniscope | - |
| `--start` | No | Report start date (ISO format) | Last Monday 00:00 |
| `--end` | No | Report end date (ISO format) | Last Sunday 23:59 |
| `--out` | No | Output file path | `data/weekly-brief-{site}-{date}.json` |
| `--config` | No | Custom config JSON file | Built-in defaults |
| `--timezone` | No | IANA timezone string | `America/New_York` |

### Finding Your Site ID

```bash
# List all organizations to find your site ID
node backend/scripts/data-collection/explore-channels.js
```

## Configuration

### Default Configuration

The system uses sensible defaults (see `config/report-config.js`):

- **Business Hours**: Mon-Fri 7:00-18:00
- **Interval Resolution**: 15-min preferred (falls back to 30-min or 60-min)
- **Baseline Period**: 4 weeks prior to report week
- **Anomaly Threshold**: 3 × IQR above median
- **Energy Cost**: $0.12/kWh (configurable)

### Custom Configuration

Create a custom config file:

```json
{
  "timezone": "America/Los_Angeles",
  "businessHours": {
    "monday": { "start": 8, "end": 17 },
    "tuesday": { "start": 8, "end": 17 },
    "wednesday": { "start": 8, "end": 17 },
    "thursday": { "start": 8, "end": 17 },
    "friday": { "start": 8, "end": 17 },
    "saturday": null,
    "sunday": null
  },
  "tariff": {
    "defaultRate": 0.15,
    "demandCharge": 12.50
  },
  "baseline": {
    "weeksCount": 8
  }
}
```

Use it with:

```bash
node backend/scripts/reports/weekly-exceptions-brief.js \
  --site 12345 \
  --config my-config.json
```

## Output Format

The report generates a JSON file with the following structure:

```json
{
  "metadata": {
    "generatedAt": "2026-02-01T10:00:00Z",
    "reportVersion": "1.0.0",
    "site": {
      "siteId": "12345",
      "siteName": "Wilson Center",
      "address": "123 Main St",
      "timezone": "America/New_York"
    },
    "period": {
      "start": "2026-01-20T00:00:00Z",
      "end": "2026-01-26T23:59:59Z"
    }
  },
  "summary": {
    "headline": [
      "245 kWh after-hours waste detected",
      "3 anomalous consumption event(s)"
    ],
    "topRisks": [...],
    "topOpportunities": [...],
    "totalPotentialSavings": {
      "weeklyKwh": 245,
      "weeklyCost": 29.40,
      "estimatedAnnual": 1528.80
    }
  },
  "sections": {
    "sensorHealth": {
      "totalIssues": 2,
      "issues": [...]
    },
    "afterHoursWaste": {
      "summary": {...},
      "topMeters": [...]
    },
    "anomalies": {
      "summary": {...},
      "timeline": [...],
      "byChannel": [...]
    },
    "spikes": {
      "summary": {...},
      "topSpikes": [...]
    },
    "quickWins": [
      {
        "title": "Reduce overnight base load on HVAC System",
        "type": "after_hours_waste",
        "priority": "high",
        "impact": {
          "weeklyKwh": 150,
          "weeklyCost": 18.00,
          "annualCost": 936.00
        },
        "description": "...",
        "recommendations": [...],
        "confidence": "high",
        "owner": "Facilities Manager"
      }
    ]
  },
  "charts": {
    "afterHoursRanking": [...],
    "anomalyTimeline": [...],
    "spikeEvents": [...]
  }
}
```

## Testing

Run unit tests:

```bash
node backend/scripts/reports/tests/test-analytics.js
```

Tests cover:
- Statistical calculations (mean, median, percentile)
- Gap detection in time series
- Baseline calculation (non-zero percentile)
- Rolling variance for flatline detection
- Data completeness calculations

## Architecture

### Module Structure

```
backend/scripts/reports/
├── weekly-exceptions-brief.js    # Main CLI entry point
├── config/
│   └── report-config.js          # Configuration and defaults
├── lib/
│   ├── date-utils.js             # Date/time utilities
│   ├── stats-utils.js            # Statistical functions
│   └── data-fetcher.js           # Eniscope API client wrapper
├── analytics/
│   ├── sensor-health.js          # Data quality analysis
│   ├── after-hours-waste.js      # After-hours consumption
│   ├── anomaly-detection.js      # Anomaly identification
│   ├── spike-detection.js        # Demand spike detection
│   └── quick-wins.js             # Recommendation generator
└── tests/
    └── test-analytics.js         # Unit tests
```

### Data Flow

1. **Configuration** → Load defaults or custom config
2. **Period Calculation** → Determine report week and baseline period
3. **Data Fetching** → Pull interval data from Eniscope API
   - Site metadata
   - Channel list (meters/submeters)
   - Report period readings (15-min intervals)
   - Baseline period readings (4 weeks prior)
   - Alarms and events (if available)
4. **Analytics** → Run analysis modules in parallel
   - Sensor health checks
   - After-hours waste calculation
   - Anomaly detection
   - Spike identification
5. **Quick Wins** → Generate actionable recommendations
6. **Report Building** → Assemble JSON output
7. **Output** → Save report and print summary

## API Endpoints Used

The system uses the following Eniscope API endpoints:

| Endpoint | Purpose |
|----------|---------|
| `GET /organizations` | Authentication & site list |
| `GET /organizations/{id}` | Site metadata |
| `GET /channels` | List of meters/channels |
| `GET /readings/{channelId}` | Interval data (power, energy, etc.) |
| `GET /alarms` | System alarms (optional) |
| `GET /events` | System events (optional) |

### Data Fields Retrieved

- `P` - Real Power (kW)
- `E` - Energy (kWh)
- `V` - Voltage (V)
- `I` - Current (A)
- `PF` - Power Factor
- `T` - Temperature (°C) - if available

## Assumptions & Notes

### Inferred vs Direct-from-API

The system marks fields as `inferred` when data is calculated locally rather than provided directly by the API:

- **Direct from API**: Readings, timestamps, channel metadata
- **Inferred**: Flatline detection, gap identification, baseline calculations, anomaly grouping

### Limitations

1. **Temperature/Humidity**: If sensors don't exist, these fields will be null
2. **Alarms/Events**: If API doesn't support date filtering, recent alarms are pulled
3. **Data Completeness**: Gaps in data may affect baseline accuracy
4. **Timezone**: All calculations use the configured timezone (default: America/New_York)

### Best Practices

1. **Run Weekly**: Schedule this report to run every Monday morning for the previous week
2. **Review Baseline**: After major facility changes, consider using a longer baseline period
3. **Validate Findings**: Cross-reference report findings with operational logs
4. **Track Progress**: Save reports weekly to monitor improvement trends
5. **Custom Thresholds**: Adjust detection thresholds based on your facility characteristics

## Troubleshooting

### Common Issues

**Authentication Failed**
```
❌ Authentication failed: 403 Forbidden
```
- Verify API credentials in `.env`
- Check API key has permissions for the organization
- Ensure password is correct (stored as plaintext, hashed to MD5 automatically)

**No Data Returned**
```
⚠️  No readings found for channel 12345
```
- Verify the date range has data in Eniscope
- Check channel ID is correct
- Try a different resolution (60-min vs 15-min)

**Missing Dependencies**
```
Error: Cannot find module 'axios'
```
- Run `npm install` from project root

### Debug Mode

Enable detailed logging:

```bash
DEBUG=1 node backend/scripts/reports/weekly-exceptions-brief.js --site 12345
```

## NPM Scripts

Add to your `package.json`:

```json
{
  "scripts": {
    "report:weekly": "node backend/scripts/reports/weekly-exceptions-brief.js",
    "report:test": "node backend/scripts/reports/tests/test-analytics.js"
  }
}
```

Then run:

```bash
npm run report:weekly -- --site 12345
npm run report:test
```

## Future Enhancements

Potential improvements for future versions:

- [ ] HTML/PDF report rendering
- [ ] Email delivery integration
- [ ] Trend analysis (multi-week comparison)
- [ ] Machine learning anomaly detection
- [ ] Cost allocation by department/tenant
- [ ] Integration with Tableau/Power BI
- [ ] Real-time alerting for critical issues
- [ ] Weather normalization
- [ ] Predictive maintenance alerts

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the existing scripts in `backend/scripts/` for examples
3. Verify API credentials and permissions
4. Enable debug mode for detailed logging

## License

Part of the Argo Energy Solutions project.
