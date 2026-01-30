# Data Pipeline Guide for Eniscope Energy Data

## Overview

This guide outlines the next steps for building a proper data pipeline after successfully integrating with the Eniscope API. The pipeline will enable you to **store**, **transform**, and **access** energy data for analysis.

## Current State

✅ **What you have:**
- Working Eniscope API integration (`src/services/api/eniscopeApi.ts`)
- React frontend with on-demand data fetching
- Python scripts for report generation
- Data types and interfaces defined

❌ **What's missing:**
- Persistent data storage
- Scheduled data ingestion
- Data transformation layer
- Historical data retention
- Optimized query access

---

## Architecture Options

### Option 1: Simple File-Based Pipeline (Quick Start)

**Best for:** Prototyping, small datasets, getting started quickly

**Components:**
- **Storage:** JSON/CSV files in `data/` directory
- **Ingestion:** Node.js script with cron job
- **Transformation:** In-memory processing during ingestion
- **Access:** Direct file reading or simple API wrapper

**Pros:**
- ✅ No database setup required
- ✅ Easy to understand and debug
- ✅ Quick to implement
- ✅ Good for testing

**Cons:**
- ❌ Limited scalability
- ❌ No concurrent access optimization
- ❌ Manual backup required
- ❌ Slower queries on large datasets

**Implementation Time:** 2-4 hours

---

### Option 2: SQLite + Node.js Pipeline (Recommended for MVP)

**Best for:** Small to medium datasets, single-server deployments, MVP

**Components:**
- **Storage:** SQLite database with time-series tables
- **Ingestion:** Node.js script with cron job
- **Transformation:** SQL queries and Node.js processing
- **Access:** REST API or direct SQL queries

**Pros:**
- ✅ No database server required
- ✅ ACID transactions
- ✅ SQL query capabilities
- ✅ Easy backup (single file)
- ✅ Good performance for < 1M records

**Cons:**
- ❌ Limited concurrent writes
- ❌ No built-in time-series optimizations
- ❌ File size limits

**Implementation Time:** 1-2 days

---

### Option 3: PostgreSQL + TimescaleDB (Production Ready)

**Best for:** Production deployments, large datasets, time-series analytics

**Components:**
- **Storage:** PostgreSQL with TimescaleDB extension
- **Ingestion:** Node.js/Python service with scheduled jobs
- **Transformation:** SQL stored procedures + ETL scripts
- **Access:** REST API (Express/Fastify) or direct SQL

**Pros:**
- ✅ Optimized for time-series data
- ✅ Excellent query performance
- ✅ Automatic data retention policies
- ✅ Continuous aggregates (pre-computed metrics)
- ✅ Full SQL capabilities
- ✅ Production-grade reliability

**Cons:**
- ❌ Requires database server setup
- ❌ More complex deployment
- ❌ Higher resource requirements

**Implementation Time:** 3-5 days

---

### Option 4: Cloud-Based Pipeline (Scalable)

**Best for:** Multi-site deployments, cloud-native architecture, enterprise scale

**Components:**
- **Storage:** AWS RDS (PostgreSQL/TimescaleDB) or Google Cloud SQL
- **Ingestion:** AWS Lambda / Cloud Functions (scheduled)
- **Transformation:** AWS Glue / Dataflow or custom ETL
- **Access:** REST API (API Gateway + Lambda) or direct database access
- **Orchestration:** AWS Step Functions / Airflow

**Pros:**
- ✅ Auto-scaling
- ✅ Managed services
- ✅ Built-in monitoring
- ✅ High availability
- ✅ Enterprise security

**Cons:**
- ❌ Cloud costs
- ❌ Vendor lock-in
- ❌ More complex setup
- ❌ Learning curve

**Implementation Time:** 1-2 weeks

---

## Recommended Implementation Path

### Phase 1: Start with Option 2 (SQLite) - Week 1

Build a working pipeline quickly to validate the approach:

1. **Database Schema Design**
2. **Data Ingestion Script**
3. **Basic Transformation**
4. **Simple Query API**

### Phase 2: Migrate to Option 3 (PostgreSQL/TimescaleDB) - Week 2-3

Once validated, upgrade for production:

1. **Database Migration**
2. **Enhanced ETL Pipeline**
3. **Optimized Queries**
4. **Monitoring & Alerts**

### Phase 3: Scale to Option 4 (Cloud) - As Needed

When you need scale or multi-region:

1. **Cloud Infrastructure Setup**
2. **Managed Services Integration**
3. **Advanced Orchestration**

---

## Detailed Implementation: Option 2 (SQLite MVP)

### Step 1: Database Schema Design

Create a schema optimized for time-series energy data:

```sql
-- Organizations table (reference data)
CREATE TABLE organizations (
    organization_id TEXT PRIMARY KEY,
    organization_name TEXT NOT NULL,
    parent_id TEXT,
    address1 TEXT,
    city TEXT,
    country TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Devices table (reference data)
CREATE TABLE devices (
    device_id INTEGER PRIMARY KEY,
    device_name TEXT NOT NULL,
    device_type_id INTEGER,
    device_type_name TEXT,
    organization_id INTEGER,
    uuid TEXT UNIQUE,
    status INTEGER,
    registered TIMESTAMP,
    expires TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Channels table (reference data)
CREATE TABLE channels (
    channel_id INTEGER PRIMARY KEY,
    channel_name TEXT NOT NULL,
    device_id INTEGER,
    organization_id INTEGER,
    tariff_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (device_id) REFERENCES devices(device_id),
    FOREIGN KEY (organization_id) REFERENCES organizations(organization_id)
);

-- Readings table (time-series data)
CREATE TABLE readings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    channel_id INTEGER NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    energy_kwh REAL,
    power_kw REAL,
    voltage_v REAL,
    current_a REAL,
    power_factor REAL,
    temperature_c REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (channel_id) REFERENCES channels(channel_id),
    UNIQUE(channel_id, timestamp)
);

-- Indexes for performance
CREATE INDEX idx_readings_channel_timestamp ON readings(channel_id, timestamp);
CREATE INDEX idx_readings_timestamp ON readings(timestamp);
CREATE INDEX idx_devices_organization ON devices(organization_id);
CREATE INDEX idx_channels_device ON channels(device_id);
```

### Step 2: Data Ingestion Script

Create a Node.js script to pull data from Eniscope API and store it:

**File:** `scripts/ingest-eniscope-data.js`

```javascript
import sqlite3 from 'sqlite3';
import { eniscopeApi } from '../src/services/api/eniscopeApi.js';
import { promisify } from 'util';

const DB_PATH = './data/eniscope.db';

class DataIngestionService {
  constructor() {
    this.db = null;
  }

  async initialize() {
    return new Promise((resolve, reject) => {
      this.db = new sqlite3.Database(DB_PATH, (err) => {
        if (err) reject(err);
        else {
          console.log('✅ Connected to SQLite database');
          this.setupSchema().then(resolve).catch(reject);
        }
      });
    });
  }

  async setupSchema() {
    // Run schema creation SQL (from Step 1)
    // ... implementation
  }

  async ingestOrganizations() {
    const orgs = await eniscopeApi.getOrganizations();
    // Insert/update organizations
  }

  async ingestDevices(organizationId) {
    const devices = await eniscopeApi.getDevices({ organization: organizationId });
    // Insert/update devices
  }

  async ingestChannels(organizationId) {
    const channels = await eniscopeApi.getChannels({ organization: organizationId });
    // Insert/update channels
  }

  async ingestReadings(channelId, startDate, endDate) {
    const readings = await eniscopeApi.getReadings(channelId, {
      fields: ['E', 'P', 'V', 'I', 'PF', 'T'],
      daterange: [startDate, endDate],
      res: '3600' // 1-hour resolution
    });
    // Insert readings (with conflict resolution)
  }

  async runFullIngestion() {
    console.log('🔄 Starting data ingestion...');
    
    // 1. Ingest organizations
    await this.ingestOrganizations();
    
    // 2. For each organization, ingest devices
    const orgs = await this.getOrganizations();
    for (const org of orgs) {
      await this.ingestDevices(org.organization_id);
    }
    
    // 3. For each organization, ingest channels
    for (const org of orgs) {
      await this.ingestChannels(org.organization_id);
    }
    
    // 4. For each channel, ingest readings (last 30 days)
    const channels = await this.getChannels();
    const endDate = new Date().toISOString();
    const startDate = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString();
    
    for (const channel of channels) {
      try {
        await this.ingestReadings(channel.channel_id, startDate, endDate);
        console.log(`✅ Ingested readings for channel ${channel.channel_id}`);
      } catch (error) {
        console.error(`❌ Error ingesting channel ${channel.channel_id}:`, error.message);
      }
    }
    
    console.log('✅ Data ingestion complete!');
  }
}
```

### Step 3: Scheduled Ingestion

Set up a cron job or scheduled task:

**File:** `scripts/schedule-ingestion.sh`

```bash
#!/bin/bash
# Run every hour to ingest new data

cd /path/to/argo-energy-solutions
node scripts/ingest-eniscope-data.js --incremental

# Or use cron:
# 0 * * * * /path/to/scripts/schedule-ingestion.sh
```

### Step 4: Data Transformation Layer

Create transformation utilities:

**File:** `src/services/data/transformations.ts`

```typescript
export interface AggregatedReading {
  date: string;
  channelId: number;
  totalEnergy: number;
  averagePower: number;
  peakPower: number;
  averageVoltage: number;
}

export async function aggregateDailyReadings(
  channelId: number,
  startDate: string,
  endDate: string
): Promise<AggregatedReading[]> {
  // Query SQLite for daily aggregations
  // GROUP BY DATE(timestamp)
  // SUM(energy_kwh), AVG(power_kw), MAX(power_kw)
}
```

### Step 5: Query API

Create a simple API to access the data:

**File:** `src/services/data/queryService.ts`

```typescript
import sqlite3 from 'sqlite3';

export class DataQueryService {
  async getChannelReadings(
    channelId: number,
    startDate: string,
    endDate: string,
    resolution: 'hour' | 'day' | 'week' | 'month' = 'hour'
  ) {
    // Query SQLite with appropriate GROUP BY
  }

  async getOrganizationSummary(organizationId: string, period: string) {
    // Aggregate data across all channels in organization
  }

  async getEnergyStatistics(channelId: number, period: string) {
    // Calculate statistics: total, average, peak, min, max
  }
}
```

---

## Detailed Implementation: Option 3 (PostgreSQL/TimescaleDB)

### Step 1: Install TimescaleDB

```bash
# macOS
brew install timescaledb

# Or use Docker
docker run -d \
  --name timescaledb \
  -p 5432:5432 \
  -e POSTGRES_PASSWORD=yourpassword \
  timescale/timescaledb:latest-pg15
```

### Step 2: Create Hypertable

```sql
-- Create regular tables first
CREATE TABLE readings (
    id BIGSERIAL,
    channel_id INTEGER NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    energy_kwh REAL,
    power_kw REAL,
    voltage_v REAL,
    current_a REAL,
    power_factor REAL,
    temperature_c REAL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Convert to hypertable (TimescaleDB optimization)
SELECT create_hypertable('readings', 'timestamp');

-- Create indexes
CREATE INDEX idx_readings_channel_time ON readings(channel_id, timestamp DESC);
CREATE INDEX idx_readings_timestamp ON readings(timestamp DESC);
```

### Step 3: Continuous Aggregates

Pre-compute daily/hourly aggregations for fast queries:

```sql
-- Daily aggregations
CREATE MATERIALIZED VIEW daily_energy_summary
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 day', timestamp) AS day,
    channel_id,
    SUM(energy_kwh) AS total_energy_kwh,
    AVG(power_kw) AS avg_power_kw,
    MAX(power_kw) AS peak_power_kw,
    MIN(power_kw) AS min_power_kw
FROM readings
GROUP BY day, channel_id;

-- Refresh policy (update every hour)
SELECT add_continuous_aggregate_policy('daily_energy_summary',
    start_offset => INTERVAL '3 days',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour');
```

### Step 4: Data Retention Policy

Automatically delete old data:

```sql
-- Keep only last 2 years of raw data
SELECT add_retention_policy('readings', INTERVAL '2 years');
```

---

## Data Transformation Strategies

### 1. Data Cleaning

```typescript
function cleanReadings(readings: Reading[]): Reading[] {
  return readings
    .filter(r => r.timestamp) // Remove null timestamps
    .filter(r => r.energy_kwh >= 0) // Remove negative values
    .filter(r => !isNaN(r.energy_kwh)) // Remove NaN
    .map(r => ({
      ...r,
      energy_kwh: Math.round(r.energy_kwh * 100) / 100, // Round to 2 decimals
    }));
}
```

### 2. Data Normalization

```typescript
function normalizeReadings(readings: Reading[]): NormalizedReading[] {
  // Convert timestamps to UTC
  // Standardize units
  // Fill missing values
  // Align time intervals
}
```

### 3. Data Enrichment

```typescript
async function enrichWithMetadata(readings: Reading[]): Promise<EnrichedReading[]> {
  // Add organization info
  // Add device metadata
  // Add tariff information
  // Calculate derived metrics
}
```

### 4. Aggregation

```typescript
function aggregateByPeriod(
  readings: Reading[],
  period: 'hour' | 'day' | 'week' | 'month'
): AggregatedReading[] {
  // Group by time period
  // Calculate sums, averages, peaks
  // Handle timezone conversions
}
```

---

## Access Patterns

### Pattern 1: Direct Database Queries

```typescript
// For internal tools, direct SQL access
const db = new Database('./data/eniscope.db');
const results = await db.query(`
  SELECT * FROM readings 
  WHERE channel_id = ? 
  AND timestamp BETWEEN ? AND ?
`, [channelId, startDate, endDate]);
```

### Pattern 2: REST API Layer

```typescript
// Express.js API
app.get('/api/channels/:channelId/readings', async (req, res) => {
  const { channelId } = req.params;
  const { startDate, endDate, resolution } = req.query;
  
  const readings = await queryService.getChannelReadings(
    channelId,
    startDate,
    endDate,
    resolution
  );
  
  res.json(readings);
});
```

### Pattern 3: GraphQL API

```typescript
// For flexible queries
const typeDefs = `
  type Reading {
    timestamp: String!
    energyKwh: Float!
    powerKw: Float!
  }
  
  type Query {
    readings(channelId: ID!, startDate: String!, endDate: String!): [Reading!]!
  }
`;
```

---

## Monitoring & Maintenance

### 1. Data Quality Checks

```typescript
async function validateDataQuality() {
  // Check for missing data gaps
  // Verify data freshness
  // Check for anomalies
  // Validate data ranges
}
```

### 2. Ingestion Monitoring

```typescript
async function monitorIngestion() {
  // Track ingestion success/failure rates
  // Monitor API rate limits
  // Alert on failures
  // Track data volume
}
```

### 3. Performance Monitoring

```typescript
async function monitorPerformance() {
  // Query execution times
  // Database size
  // Index usage
  // Connection pool stats
}
```

---

## Next Steps

1. **Choose your architecture** (recommend starting with Option 2)
2. **Set up database schema**
3. **Build ingestion script**
4. **Set up scheduled jobs**
5. **Create transformation layer**
6. **Build query API**
7. **Add monitoring**
8. **Test with real data**
9. **Optimize based on usage patterns**

---

## Additional Resources

- [TimescaleDB Documentation](https://docs.timescale.com/)
- [SQLite Best Practices](https://www.sqlite.org/bestpractices.html)
- [Node.js Database Best Practices](https://nodejs.org/en/docs/guides/nodejs-database-web-development/)
- [Time-Series Data Modeling](https://docs.timescale.com/timescaledb/latest/how-to-guides/modeling-data/)
