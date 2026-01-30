# Data Analysis Setup Guide

This guide will help you connect to the Eniscope Core API and pull data for analysis in Cursor.

## Quick Start

### 1. Install Dependencies

```bash
npm install
```

### 2. Set Up Environment Variables

Create a `.env` file in the project root with your Eniscope API credentials:

```env
# Eniscope Core API Configuration
VITE_ENISCOPE_API_URL=https://core.eniscope.com
VITE_ENISCOPE_API_KEY=your_api_key_here
VITE_ENISCOPE_EMAIL=your_email@example.com
VITE_ENISCOPE_PASSWORD=your_password_here
```

**Or use the setup script:**
```bash
npm run setup:env
```

### 3. Run the Analysis Script

```bash
npm run analyze:energy
```

This will:
- Authenticate with the Eniscope API
- Fetch organizations, devices, channels, and readings
- Save all data to JSON files in the `/data` directory
- Display basic statistics about the energy data

## What Gets Created

The script creates a `/data` directory with:
- `organizations.json` - All organizations you have access to
- `devices-org-{id}.json` - Devices for each organization
- `channels-org-{id}.json` - Channels for each organization
- `readings-channel-{id}.json` - Energy readings for each channel

## Using the Data in Cursor

### Option 1: Analyze JSON Files Directly

1. Open any JSON file from `/data` in Cursor
2. Use Cursor's AI to analyze the data:
   - "What patterns do you see in this energy data?"
   - "Calculate the average power consumption"
   - "Find the peak energy usage times"

### Option 2: Create Custom Analysis Scripts

Create your own analysis scripts in the `/scripts` directory:

```javascript
// scripts/custom-analysis.js
const fs = require('fs');
const path = require('path');

// Load the readings data
const readings = JSON.parse(
  fs.readFileSync(path.join(__dirname, '../data/readings-channel-12345.json'))
);

// Your custom analysis here
const totalEnergy = readings.result.reduce((sum, r) => sum + (r.E || 0), 0);
console.log(`Total Energy: ${totalEnergy} Wh`);
```

### Option 3: Use in Your React App

The TypeScript API client (`src/services/api/eniscopeApi.ts`) can be used in your React app:

```typescript
import { eniscopeApi } from '@/services/api/eniscopeApi';

// In a React component
const fetchEnergyData = async () => {
  const organizations = await eniscopeApi.getOrganizations();
  const devices = await eniscopeApi.getDevices(organizations[0].organizationId);
  const channels = await eniscopeApi.getChannels(organizations[0].organizationId);
  const readings = await eniscopeApi.getReadings(channels[0].channelId, {
    fields: ['E', 'P', 'V'],
    daterange: 'lastweek',
    res: '3600',
  });
};
```

## API Client Usage Examples

### Get Organizations

```javascript
const client = new EniscopeAPIClient();
await client.authenticate();
const orgs = await client.getOrganizations();
```

### Get Devices for an Organization

```javascript
const devices = await client.getDevices('12345');
```

### Get Channels for a Device

```javascript
const channels = await client.getChannels('12345', '67890');
```

### Get Energy Readings

```javascript
const readings = await client.getReadings('12345', {
  fields: ['E', 'P', 'V', 'I', 'PF'],  // Energy, Power, Voltage, Current, Power Factor
  daterange: 'lastweek',                // or ['2024-01-01', '2024-01-31']
  res: '3600',                          // 1 hour resolution
  action: 'summarize',                  // or 'total', 'averageday', etc.
});
```

## Date Range Options

- Pre-defined: `'today'`, `'yesterday'`, `'lastweek'`, `'lastmonth'`, `'thisyear'`, etc.
- Custom range: `['2024-01-01', '2024-01-31']` or `[1694034000, 1694062800]` (Unix timestamps)

## Resolution Options

- `'60'` - 1 minute
- `'900'` - 15 minutes
- `'1800'` - 30 minutes
- `'3600'` - 1 hour (recommended)
- `'86400'` - 1 day
- `'auto'` - Automatic based on date range

## Available Energy Fields

Common fields you can request:
- `E`, `E1`, `E2`, `E3` - Energy (total, phase 1, 2, 3)
- `P`, `P1`, `P2`, `P3` - Power
- `V`, `V1`, `V2`, `V3` - Voltage
- `I`, `I1`, `I2`, `I3` - Current
- `PF`, `PF1`, `PF2`, `PF3` - Power Factor
- `T`, `T1-T8` - Temperature
- `Q`, `Q1-Q3` - Reactive Power
- `S`, `S1-S3` - Apparent Power

See `Core_API_v1.txt` for the complete list of available fields.

## Troubleshooting

### Authentication Errors

- Check your `.env` file has correct credentials
- Verify your API key is valid
- Ensure your password is correct (it will be MD5 hashed automatically)

### No Data Returned

- Check you have access to the organization/device/channel
- Verify the date range contains data
- Try a different date range (e.g., `'lastmonth'`)

### Rate Limiting

If you get 429 errors:
- Reduce the frequency of requests
- Use pagination for large datasets
- Implement exponential backoff

## Next Steps

1. **Explore the Data**: Open the JSON files in Cursor and ask questions
2. **Create Visualizations**: Use the data in your React app with charts
3. **Build Dashboards**: Create energy monitoring dashboards
4. **Set Up Alerts**: Monitor for unusual energy consumption patterns

## Example Analysis Questions for Cursor

Try asking Cursor:
- "What's the average energy consumption per day?"
- "When are the peak usage hours?"
- "Compare energy usage between different devices"
- "Calculate the cost based on energy readings"
- "Find anomalies in the power consumption data"


