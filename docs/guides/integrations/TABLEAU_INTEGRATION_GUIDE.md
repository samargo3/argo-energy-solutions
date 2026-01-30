# Tableau Integration Guide - Wilson Center Energy Data

## Overview

This guide provides multiple methods to import Wilson Center energy data into Tableau, from simple CSV exports to automated API connections.

---

## Method 1: JSON to CSV Export (Easiest) ⭐ Recommended for Getting Started

### Step 1: Create CSV Export Script

This script converts your JSON analysis data to Tableau-friendly CSV format.

```javascript
// backend/scripts/utilities/export-to-csv.js
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

function exportToCSV(analysisFile, outputName) {
  // Read the analysis JSON
  const data = JSON.parse(
    fs.readFileSync(path.join(__dirname, '..', 'data', analysisFile), 'utf8')
  );

  // Export 1: Channel Summary CSV
  const channelRows = data.channels
    .filter(ch => ch.status === 'success')
    .map(ch => ({
      'Channel ID': ch.channelId,
      'Channel Name': ch.channel,
      'Device Type': ch.deviceType,
      'Total Energy (kWh)': ch.energy?.sum?.toFixed(2) || 0,
      'Average Power (kW)': ch.power?.avg?.toFixed(2) || 0,
      'Peak Power (kW)': ch.power?.max?.toFixed(2) || 0,
      'Operating Hours': ch.operatingHours?.toFixed(1) || 0,
      'Average Voltage (V)': ch.voltage?.avg?.toFixed(1) || 0,
      'Power Factor': ch.powerFactor?.avg?.toFixed(3) || 0,
      'Status': ch.status,
      'Category': categorizeChannel(ch.channel)
    }));

  const channelCSV = objectArrayToCSV(channelRows);
  fs.writeFileSync(
    path.join(__dirname, '..', 'data', `${outputName}-channels.csv`),
    channelCSV
  );

  // Export 2: Time Series CSV (all readings)
  const timeSeriesRows = [];
  data.channels
    .filter(ch => ch.status === 'success' && ch.rawReadings)
    .forEach(ch => {
      ch.rawReadings.forEach(reading => {
        timeSeriesRows.push({
          'Timestamp': new Date(reading.ts * 1000).toISOString(),
          'Channel ID': ch.channelId,
          'Channel Name': ch.channel,
          'Category': categorizeChannel(ch.channel),
          'Energy (kWh)': (reading.E / 1000).toFixed(3),
          'Power (kW)': (reading.P / 1000).toFixed(3),
          'Voltage (V)': reading.V?.toFixed(2) || '',
          'Current (A)': reading.I?.toFixed(2) || '',
          'Power Factor': reading.PF?.toFixed(3) || ''
        });
      });
    });

  const timeSeriesCSV = objectArrayToCSV(timeSeriesRows);
  fs.writeFileSync(
    path.join(__dirname, '..', 'data', `${outputName}-timeseries.csv`),
    timeSeriesCSV
  );

  // Export 3: Summary Statistics CSV
  const summaryRow = {
    'Report Date': new Date().toISOString().split('T')[0],
    'Date Range': data.dateRange,
    'Total Channels': data.summary.totalChannels,
    'Channels with Data': data.summary.channelsWithData,
    'Total Energy (kWh)': data.summary.totalEnergy.toFixed(2),
    'Estimated Cost ($)': data.summary.estimatedCost.toFixed(2),
    'Carbon Footprint (lbs CO2)': data.summary.carbonFootprint.toFixed(2),
    'Average Power (kW)': data.summary.avgPower.toFixed(2),
    'Peak Power (kW)': data.summary.peakPower.toFixed(2),
    'Average Power Factor': data.summary.avgPowerFactor.toFixed(3),
    'PF Correction Savings ($)': data.summary.pfCorrectionSavings?.toFixed(2) || 0
  };

  const summaryCSV = objectArrayToCSV([summaryRow]);
  fs.writeFileSync(
    path.join(__dirname, '..', 'data', `${outputName}-summary.csv`),
    summaryCSV
  );

  console.log(`✅ Exported 3 CSV files:`);
  console.log(`   - ${outputName}-channels.csv (${channelRows.length} channels)`);
  console.log(`   - ${outputName}-timeseries.csv (${timeSeriesRows.length} readings)`);
  console.log(`   - ${outputName}-summary.csv (summary stats)`);
}

function categorizeChannel(channelName) {
  if (channelName.includes('RTU')) return 'HVAC - RTU';
  if (channelName.includes('AHU')) return 'HVAC - AHU';
  if (channelName.includes('Kitchen')) return 'Electrical - Kitchen';
  if (channelName.includes('Sense')) return 'Sensors';
  return 'Other';
}

function objectArrayToCSV(data) {
  if (data.length === 0) return '';
  
  const headers = Object.keys(data[0]);
  const csvRows = [headers.join(',')];
  
  data.forEach(row => {
    const values = headers.map(header => {
      const value = row[header];
      // Escape commas and quotes
      if (typeof value === 'string' && (value.includes(',') || value.includes('"'))) {
        return `"${value.replace(/"/g, '""')}"`;
      }
      return value;
    });
    csvRows.push(values.join(','));
  });
  
  return csvRows.join('\n');
}

// Run export
const analysisFile = process.argv[2] || 'wilson-center-analysis.json';
const outputName = process.argv[3] || 'wilson-center';
exportToCSV(analysisFile, outputName);
```

### Step 2: Generate CSV Files

```bash
# Export latest Wilson Center analysis
node backend/scripts/utilities/export-to-csv.js wilson-center-analysis.json wilson-center

# Or combine analysis + export
npm run analyze:wilson thismonth 3600 && node backend/scripts/utilities/export-to-csv.js
```

### Step 3: Import to Tableau

**In Tableau Desktop:**

1. **File → Connect → Text File**
2. Select all 3 CSV files:
   - `wilson-center-channels.csv` (summary by channel)
   - `wilson-center-timeseries.csv` (detailed readings)
   - `wilson-center-summary.csv` (overall stats)
3. Tableau will auto-detect data types
4. **Join tables** if needed:
   - Join timeseries to channels on "Channel ID"

**Advantages:**
- ✅ Simple and quick
- ✅ Works with all Tableau versions
- ✅ No additional setup required
- ✅ Easy to refresh (re-export and reload)

**Disadvantages:**
- ⚠️ Manual refresh required
- ⚠️ Separate files for each time period

---

## Method 2: Direct JSON Import (Native Tableau)

Tableau can read JSON directly with some setup.

### Step 1: Flatten JSON Structure

Create a simplified JSON format:

```javascript
// backend/scripts/utilities/export-tableau-json.js
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

function exportTableauJSON(analysisFile, outputName) {
  const data = JSON.parse(
    fs.readFileSync(path.join(__dirname, '..', 'data', analysisFile), 'utf8')
  );

  // Flatten structure for Tableau
  const tableauData = {
    metadata: {
      reportDate: new Date().toISOString(),
      dateRange: data.dateRange,
      organization: "Argo Energy Solutions LLC",
      facility: "Wilson Center"
    },
    summary: data.summary,
    channels: data.channels.map(ch => ({
      channelId: ch.channelId,
      channelName: ch.channel,
      deviceType: ch.deviceType,
      category: categorizeChannel(ch.channel),
      status: ch.status,
      totalEnergy: ch.energy?.sum || 0,
      avgPower: ch.power?.avg || 0,
      peakPower: ch.power?.max || 0,
      operatingHours: ch.operatingHours || 0,
      avgVoltage: ch.voltage?.avg || 0,
      powerFactor: ch.powerFactor?.avg || 0,
      peakTimestamp: ch.peakPowerTimestamp
    })),
    timeseries: data.channels
      .filter(ch => ch.rawReadings)
      .flatMap(ch => ch.rawReadings.map(r => ({
        timestamp: new Date(r.ts * 1000).toISOString(),
        channelId: ch.channelId,
        channelName: ch.channel,
        category: categorizeChannel(ch.channel),
        energyKWh: r.E / 1000,
        powerKW: r.P / 1000,
        voltage: r.V,
        current: r.I,
        powerFactor: r.PF
      })))
  };

  fs.writeFileSync(
    path.join(__dirname, '..', 'data', `${outputName}-tableau.json`),
    JSON.stringify(tableauData, null, 2)
  );

  console.log(`✅ Exported: ${outputName}-tableau.json`);
  console.log(`   Channels: ${tableauData.channels.length}`);
  console.log(`   Time series records: ${tableauData.timeseries.length}`);
}

function categorizeChannel(channelName) {
  if (channelName.includes('RTU')) return 'HVAC - RTU';
  if (channelName.includes('AHU')) return 'HVAC - AHU';
  if (channelName.includes('Kitchen')) return 'Electrical - Kitchen';
  if (channelName.includes('Sense')) return 'Sensors';
  return 'Other';
}

const analysisFile = process.argv[2] || 'wilson-center-analysis.json';
const outputName = process.argv[3] || 'wilson-center';
exportTableauJSON(analysisFile, outputName);
```

### Step 2: Import to Tableau

**In Tableau Desktop:**
1. **File → Connect → JSON File**
2. Select `wilson-center-tableau.json`
3. Tableau will parse the structure
4. Create data source from nested arrays

---

## Method 3: PostgreSQL/MySQL Database (Best for Production)

For ongoing monitoring with automatic updates.

### Architecture

```
Wilson Center → API → Analysis Script → Database → Tableau
```

### Step 1: Set Up Database

```sql
-- PostgreSQL schema
CREATE TABLE energy_sites (
    site_id SERIAL PRIMARY KEY,
    site_name VARCHAR(100),
    organization_name VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE energy_channels (
    channel_id INTEGER PRIMARY KEY,
    site_id INTEGER REFERENCES energy_sites(site_id),
    channel_name VARCHAR(200),
    device_type VARCHAR(100),
    category VARCHAR(50),
    status VARCHAR(20)
);

CREATE TABLE energy_readings (
    reading_id SERIAL PRIMARY KEY,
    channel_id INTEGER REFERENCES energy_channels(channel_id),
    timestamp TIMESTAMP,
    energy_kwh DECIMAL(10,3),
    power_kw DECIMAL(10,3),
    voltage DECIMAL(6,2),
    current DECIMAL(6,2),
    power_factor DECIMAL(4,3),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(channel_id, timestamp)
);

CREATE TABLE energy_summaries (
    summary_id SERIAL PRIMARY KEY,
    site_id INTEGER REFERENCES energy_sites(site_id),
    report_date DATE,
    date_range VARCHAR(50),
    total_energy_kwh DECIMAL(10,2),
    estimated_cost DECIMAL(10,2),
    carbon_footprint_lbs DECIMAL(10,2),
    avg_power_kw DECIMAL(8,2),
    peak_power_kw DECIMAL(8,2),
    avg_power_factor DECIMAL(4,3),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_readings_timestamp ON energy_readings(timestamp);
CREATE INDEX idx_readings_channel ON energy_readings(channel_id);
```

### Step 2: Database Export Script

```javascript
// backend/scripts/utilities/export-to-database.js
import pg from 'pg';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import dotenv from 'dotenv';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

dotenv.config();

const { Pool } = pg;
const pool = new Pool({
  host: process.env.DB_HOST || 'localhost',
  port: process.env.DB_PORT || 5432,
  database: process.env.DB_NAME || 'energy_monitoring',
  user: process.env.DB_USER,
  password: process.env.DB_PASSWORD,
});

async function exportToDatabase(analysisFile) {
  const data = JSON.parse(
    fs.readFileSync(path.join(__dirname, '..', 'data', analysisFile), 'utf8')
  );

  const client = await pool.connect();
  
  try {
    await client.query('BEGIN');

    // 1. Ensure site exists
    const siteResult = await client.query(
      `INSERT INTO energy_sites (site_name, organization_name)
       VALUES ($1, $2)
       ON CONFLICT DO NOTHING
       RETURNING site_id`,
      ['Wilson Center', 'Argo Energy Solutions LLC']
    );
    
    const siteId = siteResult.rows[0]?.site_id || 1;

    // 2. Insert/update channels
    for (const channel of data.channels.filter(ch => ch.status === 'success')) {
      await client.query(
        `INSERT INTO energy_channels (channel_id, site_id, channel_name, device_type, category, status)
         VALUES ($1, $2, $3, $4, $5, $6)
         ON CONFLICT (channel_id) DO UPDATE
         SET channel_name = $3, device_type = $4, category = $5, status = $6`,
        [
          channel.channelId,
          siteId,
          channel.channel,
          channel.deviceType,
          categorizeChannel(channel.channel),
          channel.status
        ]
      );

      // 3. Insert readings
      if (channel.rawReadings) {
        for (const reading of channel.rawReadings) {
          await client.query(
            `INSERT INTO energy_readings (channel_id, timestamp, energy_kwh, power_kw, voltage, current, power_factor)
             VALUES ($1, $2, $3, $4, $5, $6, $7)
             ON CONFLICT (channel_id, timestamp) DO NOTHING`,
            [
              channel.channelId,
              new Date(reading.ts * 1000),
              reading.E / 1000,
              reading.P / 1000,
              reading.V,
              reading.I,
              reading.PF
            ]
          );
        }
      }
    }

    // 4. Insert summary
    await client.query(
      `INSERT INTO energy_summaries (
        site_id, report_date, date_range, total_energy_kwh, estimated_cost,
        carbon_footprint_lbs, avg_power_kw, peak_power_kw, avg_power_factor
      ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)`,
      [
        siteId,
        new Date().toISOString().split('T')[0],
        data.dateRange,
        data.summary.totalEnergy,
        data.summary.estimatedCost,
        data.summary.carbonFootprint,
        data.summary.avgPower,
        data.summary.peakPower,
        data.summary.avgPowerFactor
      ]
    );

    await client.query('COMMIT');
    console.log('✅ Data exported to database successfully');
    
  } catch (error) {
    await client.query('ROLLBACK');
    console.error('❌ Database export failed:', error);
    throw error;
  } finally {
    client.release();
  }
}

function categorizeChannel(channelName) {
  if (channelName.includes('RTU')) return 'HVAC - RTU';
  if (channelName.includes('AHU')) return 'HVAC - AHU';
  if (channelName.includes('Kitchen')) return 'Electrical - Kitchen';
  if (channelName.includes('Sense')) return 'Sensors';
  return 'Other';
}

// Run export
const analysisFile = process.argv[2] || 'wilson-center-analysis.json';
exportToDatabase(analysisFile)
  .then(() => pool.end())
  .catch(error => {
    console.error(error);
    pool.end();
    process.exit(1);
  });
```

### Step 3: Add to .env

```env
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=energy_monitoring
DB_USER=your_username
DB_PASSWORD=your_password
```

### Step 4: Connect Tableau to Database

**In Tableau Desktop:**
1. **Server → PostgreSQL** (or MySQL)
2. Enter connection details
3. Select tables: `energy_readings`, `energy_channels`, `energy_summaries`
4. Create relationships between tables
5. **Live connection** = Real-time updates
6. **Extract** = Faster performance, scheduled refresh

### Step 5: Automate Data Collection

```bash
# Cron job (runs daily at 6 AM)
0 6 * * * cd /path/to/project && npm run analyze:wilson yesterday 900 && node backend/scripts/utilities/export-to-database.js
```

**Advantages:**
- ✅ Automatic updates
- ✅ Historical data retention
- ✅ Multi-user access
- ✅ Tableau can refresh on schedule
- ✅ Best performance for large datasets

---

## Method 4: Web Data Connector (Advanced)

Create a custom Tableau Web Data Connector that fetches data directly from your API.

### Step 1: Create WDC Server

```javascript
// backend/scripts/utilities/tableau-wdc-server.js
import express from 'express';
import cors from 'cors';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
app.use(cors());
app.use(express.static('public'));

// Serve WDC HTML
app.get('/wdc', (req, res) => {
  res.send(`
<!DOCTYPE html>
<html>
<head>
  <title>Wilson Center Energy WDC</title>
  <script src="https://connectors.tableau.com/libs/tableauwdc-2.3.latest.js"></script>
  <script>
    (function() {
      var myConnector = tableau.makeConnector();
      
      myConnector.getSchema = function(schemaCallback) {
        var cols = [
          {id: "timestamp", dataType: tableau.dataTypeEnum.datetime},
          {id: "channelName", dataType: tableau.dataTypeEnum.string},
          {id: "category", dataType: tableau.dataTypeEnum.string},
          {id: "energyKWh", dataType: tableau.dataTypeEnum.float},
          {id: "powerKW", dataType: tableau.dataTypeEnum.float},
          {id: "voltage", dataType: tableau.dataTypeEnum.float},
          {id: "powerFactor", dataType: tableau.dataTypeEnum.float}
        ];
        
        var tableSchema = {
          id: "wilsonCenterEnergy",
          alias: "Wilson Center Energy Data",
          columns: cols
        };
        
        schemaCallback([tableSchema]);
      };
      
      myConnector.getData = function(table, doneCallback) {
        fetch('http://localhost:3000/api/energy-data')
          .then(resp => resp.json())
          .then(data => {
            table.appendRows(data.timeseries);
            doneCallback();
          });
      };
      
      tableau.registerConnector(myConnector);
      
      window.onload = function() {
        document.getElementById('submitButton').addEventListener('click', function() {
          tableau.connectionName = "Wilson Center Energy";
          tableau.submit();
        });
      };
    })();
  </script>
</head>
<body>
  <h1>Wilson Center Energy Data Connector</h1>
  <button id="submitButton">Get Data</button>
</body>
</html>
  `);
});

// API endpoint
app.get('/api/energy-data', (req, res) => {
  const dataPath = path.join(__dirname, '..', 'data', 'wilson-center-analysis.json');
  const data = JSON.parse(fs.readFileSync(dataPath, 'utf8'));
  
  // Format for Tableau
  const tableauData = {
    timeseries: data.channels
      .filter(ch => ch.rawReadings)
      .flatMap(ch => ch.rawReadings.map(r => ({
        timestamp: new Date(r.ts * 1000).toISOString(),
        channelName: ch.channel,
        category: categorizeChannel(ch.channel),
        energyKWh: r.E / 1000,
        powerKW: r.P / 1000,
        voltage: r.V,
        powerFactor: r.PF
      })))
  };
  
  res.json(tableauData);
});

function categorizeChannel(channelName) {
  if (channelName.includes('RTU')) return 'HVAC - RTU';
  if (channelName.includes('AHU')) return 'HVAC - AHU';
  if (channelName.includes('Kitchen')) return 'Electrical - Kitchen';
  return 'Other';
}

const PORT = 3000;
app.listen(PORT, () => {
  console.log(`WDC Server running at http://localhost:${PORT}/wdc`);
});
```

### Step 2: Use in Tableau

```bash
# Start WDC server
node backend/scripts/utilities/tableau-wdc-server.js
```

**In Tableau Desktop:**
1. **Connect → Web Data Connector**
2. Enter URL: `http://localhost:3000/wdc`
3. Click "Get Data"
4. Tableau fetches data via WDC

---

## Recommended Approach by Use Case

### For Quick Analysis & Prototyping
**→ Method 1: CSV Export** ⭐
- Fastest to set up
- No infrastructure needed
- Perfect for testing visualizations

### For Regular Reporting (Weekly/Monthly)
**→ Method 3: Database** ⭐⭐
- Best long-term solution
- Automated updates
- Tableau can refresh on schedule
- Multiple users can access

### For Real-Time Dashboards
**→ Method 4: Web Data Connector**
- Live data updates
- No database needed
- Good for demos

### For Simple File-Based Workflow
**→ Method 2: JSON Import**
- Native Tableau support
- Single file management
- Good middle ground

---

## Tableau Dashboard Ideas

### Dashboard 1: Executive Overview
- Total energy consumption (big number)
- Estimated cost (big number)
- Carbon footprint (big number)
- Trend line (energy over time)
- Top 5 consumers (bar chart)

### Dashboard 2: Equipment Performance
- Heat map (all channels, color by power)
- Time series (multi-line, one per channel)
- Category breakdown (pie chart)
- Operating hours (bar chart)

### Dashboard 3: Power Quality
- Power factor gauge (traffic light)
- Voltage stability chart
- Channels below target PF (table)
- Estimated savings from correction

### Dashboard 4: Peak Demand
- Peak demand timeline (when it occurs)
- Peak by equipment (bar chart)
- Day-of-week analysis
- Time-of-use rate optimization

---

## Quick Start: Get Data into Tableau in 5 Minutes

1. **Generate CSV** (easiest):
```bash
node backend/scripts/utilities/export-to-csv.js
```

2. **Open Tableau Desktop**

3. **Connect → Text File → Select `wilson-center-timeseries.csv`**

4. **Create your first viz:**
   - Drag "Timestamp" to Columns
   - Drag "Power (kW)" to Rows
   - Drag "Channel Name" to Color
   - You now have a multi-line energy chart!

---

## Next Steps

1. Choose your integration method
2. Set up automated data collection (if using DB)
3. Create Tableau dashboards
4. Schedule Tableau Server refreshes (if applicable)
5. Share dashboards with stakeholders

---

**Need Help?** 
- CSV export is the fastest way to start
- Database is the best long-term solution
- Reach out if you need help with PostgreSQL setup or Tableau dashboard design!

