# Analysis Scripts

Scripts for connecting to the Eniscope Core API and analyzing energy data.

## Quick Start

1. **Set up your `.env` file** (see root directory `.env.example`)
2. **Run the analysis script:**
   ```bash
   npm run analyze:energy
   ```

## Available Scripts

### `analyze-energy-data.js`

Main script that:
- Authenticates with Eniscope API
- Fetches organizations, devices, channels, and readings
- Saves data to `/data` directory as JSON
- Displays basic statistics

**Usage:**
```bash
node scripts/analyze-energy-data.js
# or
npm run analyze:energy
```

### `setup-env.sh`

Interactive script to create your `.env` file.

**Usage:**
```bash
bash scripts/setup-env.sh
# or
npm run setup:env
```

## Creating Custom Analysis Scripts

You can import the `EniscopeAPIClient` class in your own scripts:

```javascript
const { EniscopeAPIClient } = require('./analyze-energy-data');

const client = new EniscopeAPIClient();
await client.authenticate();

// Your custom analysis here
const orgs = await client.getOrganizations();
console.log('Organizations:', orgs);
```

## Example: Custom Analysis

Create a new file `scripts/my-analysis.js`:

```javascript
const { EniscopeAPIClient } = require('./analyze-energy-data');
const fs = require('fs');

async function myAnalysis() {
  const client = new EniscopeAPIClient();
  await client.authenticate();
  
  // Get readings for a specific channel
  const readings = await client.getReadings('12345', {
    fields: ['E', 'P'],
    daterange: 'lastmonth',
    res: '3600',
  });
  
  // Calculate total energy consumption
  const totalEnergy = readings.result.reduce((sum, r) => {
    return sum + (r.E || 0);
  }, 0);
  
  console.log(`Total Energy: ${totalEnergy} Wh`);
  console.log(`Total Energy: ${(totalEnergy / 1000).toFixed(2)} kWh`);
}

myAnalysis();
```

Run it:
```bash
node scripts/my-analysis.js
```


