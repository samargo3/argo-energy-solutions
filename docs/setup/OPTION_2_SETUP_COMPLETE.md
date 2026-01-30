# Option 2: SQLite Pipeline - Setup Complete! ✅

## What's Been Set Up

You now have a complete SQLite-based data pipeline ready to use. Here's everything that's been configured:

### ✅ Core Components

1. **Data Ingestion Script** (`backend/scripts/data-collection/ingest-eniscope-data.js`)
   - Pulls data from Eniscope API
   - Stores in SQLite database
   - Supports full and incremental ingestion
   - Handles errors gracefully

2. **Query Service** (`src/services/data/queryService.ts`)
   - TypeScript service for querying stored data
   - Methods for raw readings, aggregations, statistics
   - Organization summaries

3. **React Hooks** (`src/hooks/useStoredEnergyData.ts`)
   - Ready-to-use hooks for React components
   - Integrated with React Query
   - Automatic caching and refetching

4. **Database Check Script** (`backend/scripts/database/check-database.js`)
   - Verify database status
   - View statistics
   - Check data freshness

### ✅ NPM Scripts Available

```bash
# Data ingestion
npm run ingest:data          # Incremental ingestion (default)
npm run ingest:full          # Full historical data ingestion
npm run ingest:incremental   # Explicit incremental ingestion

# Database management
npm run db:check             # Check database status and statistics

# API server
npm run api:server           # Start API server
npm run api:dev              # Start API server with auto-reload (development)
```

## Quick Start (4 Steps)

### Step 1: Install Dependencies

```bash
npm install
```

This installs:
- `sqlite` - Modern SQLite wrapper
- `sqlite3` - SQLite3 native bindings
- `express` - API server framework
- `cors` - CORS middleware

### Step 2: Verify Environment Variables

Make sure your `.env` file has:

```env
VITE_ENISCOPE_API_URL=https://core.eniscope.com
VITE_ENISCOPE_API_KEY=your_api_key
VITE_ENISCOPE_EMAIL=your_email
VITE_ENISCOPE_PASSWORD=your_password

# Optional: API server port (default: 3001)
API_PORT=3001
VITE_STORED_DATA_API_URL=http://localhost:3001
```

### Step 3: Run Initial Data Ingestion

```bash
npm run ingest:full
```

This populates the SQLite database with data from the Eniscope API.

### Step 4: Start the API Server

In a separate terminal, start the API server:

```bash
npm run api:server
```

Or for development with auto-reload:

```bash
npm run api:dev
```

The API server runs on `http://localhost:3001` and provides REST endpoints to access the stored data.

This will:
1. Create the database at `data/eniscope.db`
2. Fetch all organizations
3. Fetch all devices
4. Fetch all channels
5. Fetch readings for the last 30 days

**Expected output:**
```
🔄 Initializing database connection...
✅ Database initialized
✅ Database schema created/verified
📥 Ingesting organizations...
✅ Ingested X organizations
📥 Found X organizations, ingesting devices...
📥 Ingesting channels...
📥 Found X channels, ingesting readings...
✅ Processed X readings...

========================================
📊 INGESTION SUMMARY
========================================
Organizations: X
Devices: X
Channels: X
Readings: X
Errors: 0
========================================
```

## Verify Setup

### Check Database Status

```bash
npm run db:check
```

This shows:
- Database file size
- Record counts per table
- Date ranges of data
- Recent data status
- Index information

### Query Database Directly

```bash
# Using sqlite3 CLI (if installed)
sqlite3 data/eniscope.db

# Example queries:
SELECT COUNT(*) FROM readings;
SELECT * FROM channels LIMIT 5;
SELECT channel_id, COUNT(*) FROM readings GROUP BY channel_id;
```

## Architecture

The React app accesses stored data through an Express API server:

```
React App (Browser)
    ↓ HTTP Requests
Express API Server (Node.js)
    ↓ SQL Queries
SQLite Database (data/eniscope.db)
```

**Why?** SQLite is a file-based database that can't be accessed directly from the browser. The API server acts as a bridge.

## Using Stored Data in React

**Important:** Make sure the API server is running (`npm run api:server`) before using these hooks!

### Example 1: Display Channel Readings

```typescript
import { useStoredChannelReadings } from '../hooks/useStoredEnergyData';

function EnergyChart({ channelId }: { channelId: number }) {
  const { data: readings, isLoading, error } = useStoredChannelReadings(
    channelId,
    '2024-01-01T00:00:00Z',
    '2024-01-31T23:59:59Z'
  );

  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>Error: {error.message}</div>;

  return (
    <div>
      {readings?.map(reading => (
        <div key={reading.id}>
          {reading.timestamp}: {reading.energy_kwh} kWh
        </div>
      ))}
    </div>
  );
}
```

### Example 2: Daily Aggregated Data

```typescript
import { useStoredAggregatedReadings } from '../hooks/useStoredEnergyData';

function DailyEnergyChart({ channelId }: { channelId: number }) {
  const { data: dailyData } = useStoredAggregatedReadings(
    channelId,
    '2024-01-01T00:00:00Z',
    '2024-01-31T23:59:59Z',
    'day' // Aggregate by day
  );

  // dailyData contains: period, total_energy_kwh, average_power_kw, etc.
}
```

### Example 3: Energy Statistics

```typescript
import { useStoredEnergyStatistics } from '../hooks/useStoredEnergyData';

function EnergyStats({ channelId }: { channelId: number }) {
  const { data: stats } = useStoredEnergyStatistics(
    channelId,
    '2024-01-01T00:00:00Z',
    '2024-01-31T23:59:59Z'
  );

  return (
    <div>
      <p>Total Energy: {stats?.total_energy_kwh.toFixed(2)} kWh</p>
      <p>Average Power: {stats?.average_power_kw.toFixed(2)} kW</p>
      <p>Peak Power: {stats?.peak_power_kw.toFixed(2)} kW</p>
    </div>
  );
}
```

### Example 4: List All Channels

```typescript
import { useStoredChannels } from '../hooks/useStoredEnergyData';

function ChannelList() {
  const { data: channels } = useStoredChannels();

  return (
    <ul>
      {channels?.map(channel => (
        <li key={channel.channel_id}>
          {channel.channel_name} ({channel.organization_name})
        </li>
      ))}
    </ul>
  );
}
```

## Scheduled Data Updates

### Option A: Cron Job (Recommended)

Add to your crontab (`crontab -e`):

```bash
# Run incremental ingestion every hour
0 * * * * cd /path/to/argo-energy-solutions && npm run ingest:incremental >> logs/ingestion.log 2>&1
```

### Option B: Manual Updates

Run when needed:

```bash
npm run ingest:incremental
```

## Database Location

- **Database file:** `data/eniscope.db`
- **Backup location:** Create backups in `data/backups/` (create directory first)

### Backup Database

```bash
# Simple file copy
cp data/eniscope.db data/backups/eniscope_$(date +%Y%m%d).db

# Or using sqlite3
sqlite3 data/eniscope.db ".backup 'data/backups/eniscope_backup.db'"
```

## Database Schema

The pipeline creates these tables:

1. **organizations** - Organization metadata
2. **devices** - Device information
3. **channels** - Channel information
4. **readings** - Time-series energy readings (main data)

All tables have:
- Automatic timestamps
- Proper indexes
- Foreign key relationships

## Performance Tips

1. **Use aggregations** - Prefer `useStoredAggregatedReadings` over raw readings for charts
2. **Limit date ranges** - Don't fetch more data than needed
3. **Cache is automatic** - React Query handles caching (5 min default)
4. **Indexes are optimized** - Already created for common queries

## Troubleshooting

### Database Not Found

```bash
# Run initial ingestion
npm run ingest:full
```

### No Recent Data

```bash
# Check database status
npm run db:check

# Run incremental ingestion
npm run ingest:incremental
```

### API Errors

- Check environment variables in `.env`
- Verify API credentials
- Check API rate limits
- Review error messages in ingestion output

### Database Locked

- Only run one ingestion at a time
- Close any SQLite clients
- Wait for current ingestion to complete

## API Endpoints

The API server provides these endpoints:

- `GET /health` - Health check
- `GET /api/channels` - Get all channels (optional: `?organizationId=123`)
- `GET /api/channels/:channelId/readings` - Get raw readings (`?startDate=...&endDate=...`)
- `GET /api/channels/:channelId/readings/aggregated` - Get aggregated readings (`?startDate=...&endDate=...&resolution=day`)
- `GET /api/channels/:channelId/statistics` - Get energy statistics (`?startDate=...&endDate=...`)
- `GET /api/organizations/:organizationId/summary` - Get organization summary (`?startDate=...&endDate=...`)
- `GET /api/channels/:channelId/readings/latest` - Get latest reading
- `GET /api/channels/:channelId/range` - Get data availability range

## Next Steps

1. ✅ **Run initial ingestion** - `npm run ingest:full`
2. ✅ **Verify data** - `npm run db:check`
3. ✅ **Start API server** - `npm run api:server` (in separate terminal)
4. ✅ **Use in React** - Import hooks from `useStoredEnergyData.ts`
5. ⏭️ **Set up scheduling** - Add cron job for regular updates
6. ⏭️ **Build dashboards** - Use stored data in your React components
7. ⏭️ **Add analytics** - Create custom queries and aggregations

## Migration Path (When Ready)

When you need more scale, you can migrate to PostgreSQL/TimescaleDB:

1. Export data from SQLite
2. Import to PostgreSQL
3. Update connection strings
4. Minimal code changes needed (same query service interface)

See `DATA_PIPELINE_GUIDE.md` for Option 3 details.

---

**You're all set!** Start with `npm run ingest:full` and begin using stored data in your React app. 🚀
