# Data Pipeline Quick Start Guide

## Overview

This guide will help you set up a data pipeline to store, transform, and access Eniscope energy data locally using SQLite.

## Prerequisites

- Node.js installed
- Eniscope API credentials configured in `.env`
- Working Eniscope API integration

## Step 1: Install Dependencies

```bash
npm install
```

This will install:
- `sqlite` - Modern SQLite wrapper for Node.js
- `sqlite3` - SQLite3 native bindings

## Step 2: Run Initial Data Ingestion

### Full Ingestion (All Historical Data)

```bash
npm run ingest:full
```

This will:
1. Create SQLite database at `data/eniscope.db`
2. Fetch all organizations from Eniscope API
3. Fetch all devices for each organization
4. Fetch all channels for each organization
5. Fetch readings for the last 30 days (default) for all channels

### Incremental Ingestion (Only New Data)

```bash
npm run ingest:incremental
```

This will:
- Only fetch new data since the last ingestion
- Much faster for regular updates

### Custom Date Range

```bash
node scripts/ingest-eniscope-data.js --days=90
```

This will fetch the last 90 days of data.

## Step 3: Verify Data Ingestion

Check the database file:

```bash
ls -lh data/eniscope.db
```

You should see a database file created. The size will depend on how much data was ingested.

### Query the Database Directly

You can use any SQLite client to query the data:

```bash
# Using sqlite3 CLI (if installed)
sqlite3 data/eniscope.db

# Then run queries:
SELECT COUNT(*) FROM readings;
SELECT * FROM channels LIMIT 5;
SELECT * FROM readings WHERE channel_id = 123 LIMIT 10;
```

## Step 4: Use the Query Service in Your Code

### In TypeScript/React Components

```typescript
import { dataQueryService } from '../services/data/queryService';

// Get readings for a channel
const readings = await dataQueryService.getChannelReadings(
  channelId,
  '2024-01-01T00:00:00Z',
  '2024-01-31T23:59:59Z'
);

// Get aggregated daily readings
const dailyReadings = await dataQueryService.getAggregatedReadings(
  channelId,
  '2024-01-01T00:00:00Z',
  '2024-01-31T23:59:59Z',
  'day'
);

// Get energy statistics
const stats = await dataQueryService.getEnergyStatistics(
  channelId,
  '2024-01-01T00:00:00Z',
  '2024-01-31T23:59:59Z'
);

// Get all channels
const channels = await dataQueryService.getChannels();

// Get organization summary
const summary = await dataQueryService.getOrganizationSummary(
  organizationId,
  '2024-01-01T00:00:00Z',
  '2024-01-31T23:59:59Z'
);
```

### Create a React Hook

Create `src/hooks/useStoredEnergyData.ts`:

```typescript
import { useQuery } from '@tanstack/react-query';
import { dataQueryService } from '../services/data/queryService';

export function useStoredChannelReadings(
  channelId: number,
  startDate: string,
  endDate: string
) {
  return useQuery({
    queryKey: ['stored-readings', channelId, startDate, endDate],
    queryFn: () => dataQueryService.getChannelReadings(channelId, startDate, endDate),
    enabled: !!channelId && !!startDate && !!endDate,
  });
}

export function useStoredEnergyStatistics(
  channelId: number,
  startDate: string,
  endDate: string
) {
  return useQuery({
    queryKey: ['stored-statistics', channelId, startDate, endDate],
    queryFn: () => dataQueryService.getEnergyStatistics(channelId, startDate, endDate),
    enabled: !!channelId && !!startDate && !!endDate,
  });
}
```

## Step 5: Set Up Scheduled Ingestion

### Option A: Cron Job (macOS/Linux)

Edit your crontab:

```bash
crontab -e
```

Add this line to run incremental ingestion every hour:

```
0 * * * * cd /path/to/argo-energy-solutions && npm run ingest:incremental >> logs/ingestion.log 2>&1
```

### Option B: Node.js Scheduler

Create `scripts/scheduler.js`:

```javascript
import cron from 'node-cron';
import { exec } from 'child_process';

// Run incremental ingestion every hour
cron.schedule('0 * * * *', () => {
  console.log('Running scheduled data ingestion...');
  exec('npm run ingest:incremental', (error, stdout, stderr) => {
    if (error) {
      console.error('Ingestion error:', error);
      return;
    }
    console.log(stdout);
  });
});

console.log('Scheduler started. Ingestion will run every hour.');
```

Run it:

```bash
node scripts/scheduler.js
```

## Step 6: Monitor Data Quality

### Check Data Freshness

```typescript
const dataRange = await dataQueryService.getDataRange(channelId);
console.log('Earliest reading:', dataRange.earliest);
console.log('Latest reading:', dataRange.latest);
console.log('Total readings:', dataRange.count);
```

### Check for Missing Data

```sql
-- Find channels with no recent data (last 24 hours)
SELECT 
  c.channel_id,
  c.channel_name,
  MAX(r.timestamp) as last_reading
FROM channels c
LEFT JOIN readings r ON c.channel_id = r.channel_id
GROUP BY c.channel_id, c.channel_name
HAVING last_reading < datetime('now', '-1 day') OR last_reading IS NULL;
```

## Troubleshooting

### Database Locked Error

If you see "database is locked" errors:
- Make sure only one ingestion process is running at a time
- Close any SQLite clients that have the database open
- Wait for current ingestion to complete

### API Rate Limits

If you hit rate limits:
- Reduce the number of days fetched: `--days=7`
- Add delays between API calls in the ingestion script
- Run ingestion during off-peak hours

### Missing Data

If some channels have no readings:
- Check API credentials and permissions
- Verify channel IDs are correct
- Check date ranges are valid
- Review error logs in the ingestion output

## Next Steps

1. **Set up scheduled ingestion** - Automate regular data updates
2. **Build analytics queries** - Create custom aggregations
3. **Create data exports** - Export to CSV/JSON for external tools
4. **Set up monitoring** - Alert on ingestion failures
5. **Migrate to PostgreSQL/TimescaleDB** - When you need more scale

## Database Schema

The pipeline creates these tables:

- `organizations` - Organization metadata
- `devices` - Device information
- `channels` - Channel information
- `readings` - Time-series energy readings

See `DATA_PIPELINE_GUIDE.md` for full schema details.

## Performance Tips

1. **Use indexes** - Already created automatically
2. **Query specific date ranges** - Don't fetch all data
3. **Use aggregations** - Pre-compute daily/hourly summaries
4. **Limit result sets** - Use LIMIT in queries
5. **Batch operations** - Use transactions for bulk inserts

## Backup Strategy

SQLite databases are easy to backup:

```bash
# Simple file copy
cp data/eniscope.db data/eniscope.db.backup

# Or use SQLite backup command
sqlite3 data/eniscope.db ".backup 'data/eniscope.db.backup'"
```

Set up automated backups:

```bash
# Daily backup script
#!/bin/bash
BACKUP_DIR="./backups"
DATE=$(date +%Y%m%d)
mkdir -p $BACKUP_DIR
cp data/eniscope.db "$BACKUP_DIR/eniscope_$DATE.db"
```

## Support

For more details, see:
- `DATA_PIPELINE_GUIDE.md` - Comprehensive architecture guide
- `scripts/ingest-eniscope-data.js` - Ingestion script source
- `src/services/data/queryService.ts` - Query service source
